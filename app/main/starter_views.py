from __future__ import print_function

from rsa import verify
from app.main import main
from flask import g, url_for, render_template, request, redirect, session as http_session, abort, current_app, flash, jsonify, make_response
from app.main.forms import *
from app.services import SessionManager
from app.services.steps import Step_0
from app.main.helpers import guess_locale
import json
from app.services import FormFillerService
from app.services.usps_api import USPS_API
from app.services.email_service import EmailService
from flask_cors import cross_origin

from datetime import datetime, timedelta, tzinfo
from datetime import date
import os

import tracemalloc
tracemalloc.start(10)

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import smtplib, ssl

cred = credentials.Certificate('by8-318322-9aac6ae02900.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

# backend api endpoint for checking voter registration status
@main.route('/registered', strict_slashes=False, methods=["POST"])
@cross_origin(origin='*')
def registered():
    # accept JSON data, default to Form data if no JSON in request
    if request.json:
        requestData = request.json
    else:
        requestData = request.form
    # do error checking
    missingParams = []
    otherErrors = []
    if 'state' not in requestData:
        missingParams.append('state')
    elif len(requestData.get('state')) != 2:
        otherErrors.append('state must be 2 letter abbreviation')
    if 'city' not in requestData:
        missingParams.append('city')
    if 'street' not in requestData:
        missingParams.append('street')
    if 'name_first' not in requestData:
        missingParams.append('name_first')
    if 'name_last' not in requestData:
        missingParams.append('name_last')
    if 'dob' not in requestData:
        missingParams.append('dob')
    else:
        dob = requestData.get('dob').split('/')
        if len(dob) != 3 or len(dob[0]) not in range(1, 3) or len(dob[1]) not in range(1, 3) or len(dob[2]) != 4:
            otherErrors.append('dob must be in the form mm/dd/yyyy')
    if 'zip' not in requestData:
        missingParams.append('zip')
    elif len(requestData.get('zip')) != 5:
        otherErrors.append('zip must be 5 digits')
    if missingParams:
        error = 'Missing parameters: '
        error += missingParams[0]
        for i in range(1, len(missingParams)):
            error = error + ', ' + missingParams[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    # check if address is valid
    form = FormVR3(
        addr = requestData.get('street'),
        unit = requestData.get('unit'),
        city = requestData.get('city'),
        state = requestData.get('state'),
        zip = requestData.get('zip'),
    )
    usps_api = USPS_API(form.data)
    validated_addresses = usps_api.validate_addresses()
    if not validated_addresses:
        otherErrors.append('(street, city, state, zip) do not form a valid address')
    if otherErrors:
        error = otherErrors[0]
        for i in range(1, len(otherErrors)):
            error = error + ', ' + otherErrors[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    # check if the address is valid (via USPS address verification)
    someJson = requestData
    step = Step_0(someJson)
    regFound = step.lookup_registration(
        state=requestData.get('state'),
        city=requestData.get('city'),
        street=requestData.get('street'),
        name_first=requestData.get('name_first'),
        name_last=requestData.get('name_last'),
        dob=requestData.get('dob'),
        zipcode=requestData.get('zip')
    )
    #print(regFound)
    if (regFound and 'status' not in regFound) or (regFound and 'status' in regFound and regFound['status'] == 'active'):
        return jsonify({ 'registered': True })
    elif regFound and 'status' in regFound:
        return { 'registered': False, 'status': regFound['status'] }
    else:
        return { 'registered': False, 'status': 'not found' }

# backend api endpoint for filling out the Federal Form to register to vote
@main.route('/registertovote', strict_slashes=False, methods=['POST'])
@cross_origin(origin='*')
def reg():
    # accept JSON data, default to Form data if no JSON in request
    if request.json:
        requestData = request.json
    else:
        requestData = request.form
    # do error checking
    missingParams = []
    otherErrors = []
    if 'name_first' not in requestData:
        missingParams.append('name_first')
    if 'name_last' not in requestData:
        missingParams.append('name_last')
    if 'state' not in requestData:
        missingParams.append('state')
    elif len(requestData.get('state')) != 2:
        otherErrors.append('state must be 2 letter abbreviation')
    if 'city' not in requestData:
        missingParams.append('city')
    if 'street' not in requestData:
        missingParams.append('street')
    if 'dob' not in requestData:
        missingParams.append('dob')
    else:
        dobArr = requestData.get('dob').split('/')
        if len(dobArr) != 3 or len(dobArr[0]) not in range(1, 3) or len(dobArr[1]) not in range(1, 3) or len(dobArr[2]) != 4:
            otherErrors.append('dob must be in the form mm/dd/yyyy')
    if 'zip' not in requestData:
        missingParams.append('zip')
    elif len(requestData.get('zip')) != 5:
        otherErrors.append('zip must be 5 digits')
    if 'email' not in requestData:
        missingParams.append('email')
    else:
        emailArr = requestData.get('email').split('@')
        if len(emailArr) != 2 or len(list(filter(None, emailArr[1].split('.')))) != 2:
            otherErrors.append('invalid email')
    if 'citizen' not in requestData:
        missingParams.append('citizen')
    elif requestData.get('citizen') != 'yes':
        otherErrors.append('citizen parameter must be yes')
    if 'eighteenPlus' not in requestData:
        missingParams.append('eighteenPlus')
    elif requestData.get('eighteenPlus') != 'yes':
        otherErrors.append('eighteenPlus parameter must be yes')
    if 'party' not in requestData:
        missingParams.append('party')
    if 'idNumber' not in requestData:
        missingParams.append('idNumber')
    elif not requestData.get('idNumber').isdigit():
        otherErrors.append('invalid ID number')
    if missingParams:
        error = 'Missing parameters: '
        error += missingParams[0]
        for i in range(1, len(missingParams)):
            error = error + ', ' + missingParams[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    form = FormVR3(
        addr = requestData.get('street'),
        unit = requestData.get('unit'),
        city = requestData.get('city'),
        state = requestData.get('state'),
        zip = requestData.get('zip'),
    )
    usps_api = USPS_API(form.data)
    validated_addresses = usps_api.validate_addresses()

    if otherErrors:
        error = otherErrors[0]
        for i in range(1, len(otherErrors)):
            error = error + ', ' + otherErrors[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    # get POST form body parameters
    name_first = requestData.get('name_first')
    name_last = requestData.get('name_last')
    state = requestData.get('state')
    city = requestData.get('city')
    street = requestData.get('street')
    dob = requestData.get('dob')
    zip = requestData.get('zip')
    email = requestData.get('email')
    party = requestData.get('party')
    idNumber = requestData.get('idNumber')
    payload_file = 'app/services/tests/test-vr-en-payload.json'
    with open(payload_file) as payload_f:
        payload = json.load(payload_f)
        payload['01_firstName'] = name_first
        payload['01_lastName'] = name_last
        payload['02_homeAddress'] = street
        payload['02_aptLot'] = ""
        payload['02_cityTown'] = city
        payload['02_state'] = state
        payload['02_zipCode'] = zip
        payload['04_dob'] = dob
        payload['07_party'] = party
        payload['06_idNumber'] = idNumber
        payload['00_citizen_yes'] = True
        payload['00_eighteenPlus_yes'] = True
        # optional parameters
        if 'unit' in requestData:
            payload['02_aptLot'] = requestData.get('unit')
        if 'name_middle' in requestData:
             payload['01_middleName'] = requestData.get('name_middle')
        if 'title' in requestData:
            title = requestData.get('title').lower()
            if title == 'mr.':
                payload['01_prefix_mr'] = True
            if title == 'mrs.':
                payload['01_prefix_mrs'] = True
            if title == 'miss':
                payload['01_prefix_miss'] = True
            if title == 'ms.':
                payload['01_prefix_ms'] = True
        if 'suffix' in requestData:
            suffix = requestData.get('suffix').lower()
            if suffix == 'jr.' or suffix == 'jr':
                payload['01_suffix_jr'] = True
            if suffix == 'sr.' or suffix == 'sr':
                payload['01_suffix_sr'] = True
            if suffix == 'ii':
                payload['01_suffix_ii'] = True
            if suffix == 'iii':
                payload['01_suffix_iii'] = True
            if suffix == 'iv':
                payload['01_suffix_iv'] = True
        if 'race' in requestData:
            payload['08_raceEthnic'] = requestData.get('race')
        if 'change_of_name' in requestData and requestData.get('change_of_name'):
            payload['A_firstName'] = requestData.get('prev_name_first')
            payload['A_lastName'] = requestData.get('prev_name_last')
            if 'name_middle' in requestData:
                payload['A_middleName'] = requestData.get('prev_name_middle')
            if 'prev_title' in requestData:
                title = requestData.get('prev_title').lower()
                if title == 'mr.':
                    payload['A_prefix_mr'] = True
                if title == 'mrs.':
                    payload['A_prefix_mrs'] = True
                if title == 'miss':
                    payload['A_prefix_miss'] = True
                if title == 'ms.':
                    payload['A_prefix_ms'] = True
            if 'prev_suffix' in requestData:
                suffix = requestData.get('prev_suffix').lower()
                if suffix == 'jr.' or suffix == 'jr':
                    payload['A_suffix_jr'] = True
                if suffix == 'sr.' or suffix == 'sr':
                    payload['A_suffix_sr'] = True
                if suffix == 'ii':
                    payload['A_suffix_ii'] = True
                if suffix == 'iii':
                    payload['A_suffix_iii'] = True
                if suffix == 'iv':
                    payload['A_suffix_iv'] = True
        if 'change_of_address' in requestData and requestData.get('change_of_address'):
            payload['B_homeAddress'] = requestData.get('prev_street')
            payload['B_cityTown'] = requestData.get('prev_city')
            payload['B_state'] = requestData.get('prev_state')
            payload['B_zipCode'] = requestData.get('prev_zip')
            if 'unit' in requestData:
                payload['B_aptLot'] = requestData.get('prev_unit')
        if 'diff_mail_address' in requestData and requestData.get('diff_mail_address'):
            payload['03_mailAddress'] = requestData.get('mail_street')
            payload['03_cityTown'] = requestData.get('mail_city')
            payload['03_state'] = requestData.get('mail_state')
            payload['03_zipCode'] = requestData.get('mail_zip')
        # fill out the voter registration form
        ffs = FormFillerService(payload=payload, form_name='/vr/en')
        img = ffs.as_image()
        # use Gmail API to send email to the user with their voter reg form
        emailServ = EmailService()
        to = email
        subject = 'Here’s your voter registration form'
        messageWithAttachment = emailServ.create_message_with_attachment(to, subject, img)
        emailServ.send_message(messageWithAttachment)
        # previously checked if the address is valid (via USPS address verification)
        # instead of an error, send a warning if address is invalid right after email is sent
        if not validated_addresses:
            return { 'status': 'email sent', 'warning': '(street, city, state, zip) do not form a valid address' }
    return { 'status': 'email sent' }


@main.route('/email', strict_slashes=False, methods=['POST'])
@cross_origin(origin='*')
def email():
    # accept JSON data, default to Form data if no JSON in request
    if request.json:
        requestData = request.json
    else:
        requestData = request.form
    # do error checking
    missingParams = []
    if 'email' not in requestData:
        missingParams.append('email')
    else:
        emailArr = requestData.get('email').split('@')
        if len(emailArr) != 2 or len(list(filter(None, emailArr[1].split('.')))) != 2:
            resp = jsonify(error='invalid email: ' + requestData.get('email'))
            return make_response(resp, 400)
    if 'type' not in requestData:
        missingParams.append('type')
    elif requestData.get('type') == 'badgeEarned':
        if 'avatar' not in requestData or 'daysLeft' not in requestData or 'badgesLeft' not in requestData:
            resp = jsonify(error='for badgeEarned emails, parameters avatar, daysLeft, and badgesLeft are required')
            return make_response(resp, 400)
    elif (requestData.get('type') == 'registered' or requestData.get('type') == 'electionReminder') and ('avatar' not in requestData or 'firstName' not in requestData):
        resp = jsonify(error='for ' + requestData.get('type') + ' emails, parameters avatar and firstName are required')
        return make_response(resp, 400)
    elif requestData.get('type') == 'verifyEmail' and 'verifyLink' not in requestData:
        resp = jsonify(error='for ' + requestData.get('type') + ' emails, parameter verifyLink is required')
        return make_response(resp, 400)
    if missingParams:
        error = 'Missing parameters: '
        error += missingParams[0]
        for i in range(1, len(missingParams)):
            error = error + ', ' + missingParams[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    # Initialize email service that uses Gmail API 
    emailServ = EmailService()
    emailTo = requestData.get('email')
    type = requestData.get('type')
    daysLeft = requestData.get('daysLeft')
    badgesLeft = requestData.get('badgesLeft')
    firstName = requestData.get('firstName')
    avatar = requestData.get('avatar')
    isChallenger = requestData.get('isChallenger')
    verifyLink = requestData.get('verifyLink')
    partnerLinks = requestData.get('partnerLinks')
    # Attempt to create the email template that was asked for
    try:
        message = emailServ.create_template_message(emailTo, type, daysLeft, badgesLeft, firstName, avatar, isChallenger, verifyLink, partnerLinks)
        emailServ.send_message(message)
        return { 'status': 'email sent' }
    except ValueError: # value error if email type provided by user is not valid
        resp = jsonify(error='invalid template type, valid types include: challengerWelcome, badgeEarned, challengeWon, challengeIncomplete, playerWelcome, registered, electionReminder, verifyEmail')
        return make_response(resp, 400)
    except Exception as e:
        resp = jsonify(error='invalid email: ' + emailTo)
        return make_response(resp, 400)

@main.route('/challengeIncomplete', strict_slashes=False, methods=['GET', 'POST'])
@cross_origin(origin='*')
def challengeIncomplete():
    # Firestore db is initiallized globally
    users_ref = db.collection('users')
    docs = users_ref.stream()
    numSent = 0
    emailServ = None
    for doc in docs:
        if 'challengeEndDate' in doc.to_dict() and isinstance(doc.to_dict()['challengeEndDate'], datetime):
            # Convert challengeEndTime to UTC-7 (PST)
            endDateTime = doc.to_dict()['challengeEndDate'] - timedelta(hours=7)
            today = datetime.today() - timedelta(hours=7)
            if endDateTime.date() == today.date() and len(doc.to_dict()['badges']) < 8:
                '''
                what doc.to_dict() looks like:
                {'completedActionForChallenger': False, 'avatar': 4, 'invitedBy': '123randomnum123', 'isRegisteredVoter': False, 'inviteCode': '123random123', 'name': 'Person', 'notifyElectionReminders': False, 'badges': [], 'lastActive': DatetimeWithNanoseconds(2022, 3, 19, 16, 46, 22, 375000, tzinfo=<UTC>), 'challengeEndDate': DatetimeWithNanoseconds(2022, 3, 27, 16, 46, 20, 237000, tzinfo=<UTC>), 'sharedChallenge': False, 'email': 'asdf@skdfjs.com', 'startedChallenge': True}
                '''
                emailTo = doc.to_dict()['email']
                try:
                    # Initialize email service that uses Gmail API 
                    if emailServ is None:
                        emailServ = EmailService()
                    message = emailServ.create_template_message(emailTo, 'challengeIncomplete')
                    emailServ.send_message(message)
                    numSent += 1
                except ValueError as err: # value error if email type provided by user is not valid
                    resp = jsonify(error=err)
                    return make_response(resp, 400)
                except Exception as e:
                    resp = jsonify(error='invalid email: ' + emailTo)
                    return make_response(resp, 400)
    return { 'status': 'number of emails sent: ' + str(numSent) }


# backend api endpoint for checking voter registration status
@main.route('/validateAddress', strict_slashes=False, methods=["POST"])
@cross_origin(origin='*')
def validateAddress():
    # accept JSON data, default to Form data if no JSON in request
    if request.json:
        requestData = request.json
    else:
        requestData = request.form
    # do error checking
    missingParams = []
    otherErrors = []
    if 'state' not in requestData:
        missingParams.append('state')
    elif len(requestData.get('state')) != 2:
        otherErrors.append('state must be 2 letter abbreviation')
    if 'city' not in requestData:
        missingParams.append('city')
    if 'street' not in requestData:
        missingParams.append('street')
    if 'zip' not in requestData:
        missingParams.append('zip')
    elif len(requestData.get('zip')) != 5:
        otherErrors.append('zip must be 5 digits')
    if missingParams:
        error = 'Missing parameters: '
        error += missingParams[0]
        for i in range(1, len(missingParams)):
            error = error + ', ' + missingParams[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    if otherErrors:
        error = otherErrors[0]
        for i in range(1, len(otherErrors)):
            error = error + ', ' + otherErrors[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    # check if address is valid
    form = FormVR3(
        addr = requestData.get('street'),
        city = requestData.get('city'),
        state = requestData.get('state'),
        zip = requestData.get('zip'),
    )
    usps_api = USPS_API(form.data)
    validated_addresses = usps_api.validate_addresses()
    if not validated_addresses:
        return { 'isValid': False }
    return { 'isValid': True }

@main.route('/altEmail', strict_slashes=False, methods=['POST'])
@cross_origin(origin='*')
def altemail():
    # accept JSON data, default to Form data if no JSON in request
    if request.json:
        requestData = request.json
    else:
        requestData = request.form
    # do error checking
    missingParams = []
    if 'email' not in requestData:
        missingParams.append('email')
    else:
        emailArr = requestData.get('email').split('@')
        if len(emailArr) != 2 or len(list(filter(None, emailArr[1].split('.')))) != 2:
            resp = jsonify(error='invalid email: ' + requestData.get('email'))
            return make_response(resp, 400)
    if 'type' not in requestData:
        missingParams.append('type')
    elif requestData.get('type') == 'badgeEarned':
        if 'avatar' not in requestData or 'daysLeft' not in requestData or 'badgesLeft' not in requestData:
            resp = jsonify(error='for badgeEarned emails, parameters avatar, daysLeft, and badgesLeft are required')
            return make_response(resp, 400)
    elif (requestData.get('type') == 'registered' or requestData.get('type') == 'electionReminder') and ('avatar' not in requestData or 'firstName' not in requestData):
        resp = jsonify(error='for ' + requestData.get('type') + ' emails, parameters avatar and firstName are required')
        return make_response(resp, 400)
    if missingParams:
        error = 'Missing parameters: '
        error += missingParams[0]
        for i in range(1, len(missingParams)):
            error = error + ', ' + missingParams[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    # Initialize email service without Gmail API
    emailServ = EmailService(gmail=False)
    emailTo = requestData.get('email')
    type = requestData.get('type')
    daysLeft = requestData.get('daysLeft')
    badgesLeft = requestData.get('badgesLeft')
    firstName = requestData.get('firstName')
    avatar = requestData.get('avatar')
    isChallenger = requestData.get('isChallenger')
    # Attempt to create the email template that was asked for
    try:
        message = emailServ.create_template_message(emailTo, type, daysLeft, badgesLeft, firstName, avatar, isChallenger)
        sender_email = os.getenv('FROM_EMAIL')
        receiver_email = emailTo
        password = os.getenv('EMAIL_PWD')
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message
            )
        return { 'status': 'email sent' }
    except ValueError: # value error if email type provided by user is not valid
        resp = jsonify(error='invalid template type, valid types include: challengerWelcome, badgeEarned, challengeWon, challengeIncomplete, playerWelcome, registered, electionReminder')
        return make_response(resp, 400)
    except Exception as e:
        resp = resp = jsonify(error='invalid email: ' + emailTo)
        return make_response(resp, 400)

@main.route('/altReg', strict_slashes=False, methods=['POST'])
@cross_origin(origin='*')
def altreg():
    # accept JSON data, default to Form data if no JSON in request
    if request.json:
        requestData = request.json
    else:
        requestData = request.form
    # do error checking
    missingParams = []
    otherErrors = []
    if 'name_first' not in requestData:
        missingParams.append('name_first')
    if 'name_last' not in requestData:
        missingParams.append('name_last')
    if 'state' not in requestData:
        missingParams.append('state')
    elif len(requestData.get('state')) != 2:
        otherErrors.append('state must be 2 letter abbreviation')
    if 'city' not in requestData:
        missingParams.append('city')
    if 'street' not in requestData:
        missingParams.append('street')
    if 'dob' not in requestData:
        missingParams.append('dob')
    else:
        dobArr = requestData.get('dob').split('/')
        if len(dobArr) != 3 or len(dobArr[0]) not in range(1, 3) or len(dobArr[1]) not in range(1, 3) or len(dobArr[2]) != 4:
            otherErrors.append('dob must be in the form mm/dd/yyyy')
    if 'zip' not in requestData:
        missingParams.append('zip')
    elif len(requestData.get('zip')) != 5:
        otherErrors.append('zip must be 5 digits')
    if 'email' not in requestData:
        missingParams.append('email')
    else:
        emailArr = requestData.get('email').split('@')
        if len(emailArr) != 2 or len(list(filter(None, emailArr[1].split('.')))) != 2:
            otherErrors.append('invalid email')
    if 'citizen' not in requestData:
        missingParams.append('citizen')
    elif requestData.get('citizen') != 'yes':
        otherErrors.append('citizen parameter must be yes')
    if 'eighteenPlus' not in requestData:
        missingParams.append('eighteenPlus')
    elif requestData.get('eighteenPlus') != 'yes':
        otherErrors.append('eighteenPlus parameter must be yes')
    if 'party' not in requestData:
        missingParams.append('party')
    if 'idNumber' not in requestData:
        missingParams.append('idNumber')
    elif not requestData.get('idNumber').isdigit():
        otherErrors.append('invalid ID number')
    if missingParams:
        error = 'Missing parameters: '
        error += missingParams[0]
        for i in range(1, len(missingParams)):
            error = error + ', ' + missingParams[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)
    form = FormVR3(
        addr = requestData.get('street'),
        city = requestData.get('city'),
        state = requestData.get('state'),
        zip = requestData.get('zip'),
    )
    usps_api = USPS_API(form.data)
    validated_addresses = usps_api.validate_addresses()

    if otherErrors:
        error = otherErrors[0]
        for i in range(1, len(otherErrors)):
            error = error + ', ' + otherErrors[i]
        resp = jsonify(error=error)
        return make_response(resp, 400)

    # get POST form body parameters
    name_first = requestData.get('name_first')
    name_last = requestData.get('name_last')
    state = requestData.get('state')
    city = requestData.get('city')
    street = requestData.get('street')
    dob = requestData.get('dob')
    zip = requestData.get('zip')
    email = requestData.get('email')
    party = requestData.get('party')
    idNumber = requestData.get('idNumber')
    payload_file = 'app/services/tests/test-vr-en-payload.json'
    with open(payload_file) as payload_f:
        payload = json.load(payload_f)
        payload['01_firstName'] = name_first
        payload['01_lastName'] = name_last
        payload['02_homeAddress'] = street
        payload['02_aptLot'] = ""
        payload['02_cityTown'] = city
        payload['02_state'] = state
        payload['02_zipCode'] = zip
        payload['04_dob'] = dob
        payload['07_party'] = party
        payload['06_idNumber'] = idNumber
        payload['00_citizen_yes'] = True
        payload['00_eighteenPlus_yes'] = True
        # fill out the voter registration form
        ffs = FormFillerService(payload=payload, form_name='/vr/en')
        img = ffs.as_image()
        # use email service (without Gmail API) to send email to the user with their voter reg form
        emailServ = EmailService(gmail=False)
        to = email
        subject = 'Here’s your voter registration form'
        messageWithAttachment = emailServ.create_message_with_attachment(to, subject, img)
    sender_email = os.getenv('FROM_EMAIL')
    receiver_email = email
    password = os.getenv('EMAIL_PWD')

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, messageWithAttachment
        )
    # previously checked if the address is valid (via USPS address verification)
    # instead of an error, send a warning if address is invalid right after email is sent
    if not validated_addresses:
        return { 'status': 'email sent', 'warning': '(street, city, state, zip) do not form a valid address' }
    return { 'status': 'email sent' }

''' Old endpoints from KSVotes '''
# default route
@main.route('/', methods=["GET"])
def index():
    g.locale = guess_locale()
    return render_template('about.html')

@main.route('/privacy-policy', methods=['GET'])
def privacy():
    g.locale = guess_locale()
    return render_template('privacy-policy.html')

@main.route('/about', methods=['GET'])
def about_us():
    g.locale = guess_locale()
    return render_template('about.html')

# endpoint to check in on the status of the application
@main.route('/memory/', methods=['GET'])
def memory():
    import tracemalloc
    import linecache
    import os
    key_type = 'lineno'
    limit = 20
    snapshot = tracemalloc.take_snapshot()
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    buff = []

    buff.append("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        buff.append("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            buff.append('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        buff.append("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    buff.append("Total allocated size: %.1f KiB" % (total / 1024))

    return jsonify(status='ok', total=total, report=buff, pid=os.getpid())
