from app.models import *
from app.main.VR.example_form import signature_img_string

def create_registrant(db_session):
    registrant = Registrant(
        registration_value={
            "name_first": "foo",
            "name_last": "bar",
            "dob":"01/01/2000",
            "email":"foo@example.com",
            "addr": "707 Vermont St",
            "unit": "Room A",
            "city": "Lawrence",
            "state": "KANSAS",
            "zip": "66044",
            "identification": "nnnnn",
            "signature_string": signature_img_string, # dummy
            "ab_forms": [signature_img_string], # dummy
        },
        county="TEST",
        reg_lookup_complete=True,
        addr_lookup_complete=True,
        is_citizen=True,
        party="unaffiliated",
    )
    db_session.add(registrant)
    db_session.commit()
    return registrant

def test_no_affirmation(app, db_session, client):
    registrant = create_registrant(db_session)
    with client.session_transaction() as http_session:
        http_session['session_id'] = str(registrant.session_id)

    form_payload = {}
    response = client.post('/ab/affirmation', data=form_payload, follow_redirects=False)
    assert response.status_code != 302

def test_with_affirmation(app, db_session, client):
    registrant = create_registrant(db_session)
    with client.session_transaction() as http_session:
        http_session['session_id'] = str(registrant.session_id)

    form_payload = {"affirmation": "true"}

    response = client.post('/ab/affirmation', data=form_payload, follow_redirects=False)
    redirect_data = response.data.decode()
    assert response.status_code == 302
    assert ('/ab/submission' in redirect_data) == True
    assert registrant.try_value('ab_forms_message_id') == 'set SEND_EMAIL env var to enable email'
    assert registrant.try_value('ab_id_action_email_sent') == 'set SEND_EMAIL env var to enable email'

def test_with_affirmation_and_ab_id(app, db_session, client):
    registrant = create_registrant(db_session)
    registrant.update({'ab_identification': 'xxxxx'})
    registrant.save(db_session)
    with client.session_transaction() as http_session:
        http_session['session_id'] = str(registrant.session_id)

    form_payload = {"affirmation": "true"}

    response = client.post('/ab/affirmation', data=form_payload, follow_redirects=False)
    redirect_data = response.data.decode()
    assert response.status_code == 302
    assert ('/ab/submission' in redirect_data) == True
    assert registrant.try_value('ab_forms_message_id') == 'set SEND_EMAIL env var to enable email'
    assert registrant.try_value('ab_id_action_email_sent') == ''
