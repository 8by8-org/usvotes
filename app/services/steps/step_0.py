from app.services.steps import Step
from flask import current_app
import os
import sys
import myvoteinfo
import requests

class Step_0(Step):
    form_requirements = ['state', 'city', 'street', 'name_first', 'name_last', 'dob', 'email']
    step_requirements = ['reg_lookup_complete']
    reg_lookup_complete = False
    reg_found = False
    voter_view_fail = False
    endpoint = '/'
    prev_step = None
    next_step = None

    def run(self, skip_sos=False):
        if self.is_complete:
            return True

        if not self.verify_form_requirements():
            return False

        if not skip_sos:
            self.reg_found = self.lookup_registration(
                state=self.form_payload['state'],
                city=self.form_payload['city'],
                street=self.form_payload['street'],
                name_first=self.form_payload['name_first'],
                name_last=self.form_payload['name_last'],
                dob=self.form_payload['dob'],
                zipcode=self.form_payload['zip'],
            )

        self.is_complete = True
        self.reg_lookup_complete = True

        if self.reg_found:
            self.next_step = 'Step_1'
            return True

        self.next_step = 'Step_1'
        return True

    def lookup_registration(self, state, city, street, name_first, name_last, dob, zipcode):
        try:
            kmvi = myvoteinfo.MyVoteInfo()
            if os.getenv('VOTER_VIEW_URL'):
                kmvi = myvoteinfo.MyVoteInfo(url=os.getenv('VOTER_VIEW_URL'))
            zpcd = int(zipcode)
            if state.upper() == 'AR':
                kmvi = myvoteinfo.MyVoteInfo(state='ar', url='https://www.voterview.ar-nova.org/voterview')
            elif state.upper() != 'KS':
                kmvi = myvoteinfo.MyVoteInfo(state='rockthevote', url='https://register.rockthevote.com/lookup')
            dob = dob.split('/')
            formatted_dob = "{year}-{month}-{day}".format(year=dob[2], month=dob[0], day=dob[1])
            request = kmvi.lookup(
                first_name = name_first,
                last_name = name_last,
                dob = formatted_dob,
                zipcode = zipcode,
                state = state.upper(),
                gender = 'decline',
                street = street,
                city = city,
                email = 'person@email.com'
            )
            if request and (state.upper() == 'AR' or state.upper() == 'KS'):
                sosrecs = request.parsed()
                return sosrecs
            elif request and 'status' in request[0]:
                return request[0]
        except requests.exceptions.ConnectionError as err:
            self.voter_view_fail = kmvi.url
            current_app.logger.warn("voter view connection failure: %s" %(err))
            return False
        except:
            err = sys.exc_info()[0]
            current_app.logger.warn("voter view failure: %s" %(err))
            return False

        return False
