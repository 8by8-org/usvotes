import base64
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from email.mime.application import MIMEApplication

class EmailService():

    SCOPES = ['https://mail.google.com/']

    def __init__(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {"web":
                        {
                            "client_id":os.getenv('CLIENT_ID'),
                            "project_id":os.getenv('PROJECT_ID'),
                            "auth_uri":"https://accounts.google.com/o/oauth2/auth",
                            "token_uri":"https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
                            "client_secret":os.getenv('CLIENT_SECRET')
                        }
                    },
                    self.SCOPES)
                creds = flow.run_local_server(port=5500)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)

    def send_message(self, message, user_id='me'):
        try:
            message = self.service.users().messages().send(userId=user_id,
                    body=message).execute()

            print('Message Id: {}'.format(message['id']))

            return message
        except Exception as e:
            print('An error occurred: {}'.format(e))
            return None
    
    def create_template_message(self, to, subject, h1, p1='', img1='', btn1='', h2='', img2='', p2='', btn2=''):
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject

        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msgAlternative = MIMEMultipart('alternative')
        message.attach(msgAlternative)

        html = '''<html>
        <head><style>
            body {
                margin:0;
            }
            h1 {
                font-size:2.0em;
                font-weight:bold;
            }
            h2 {
                font-size:1.7em;
                font-weight:bold;
            }
            p {
                font-size:1.5em;
                margin-left:10%;
                margin-right:10%;
            }
            footer > p {
                font-size:1.1em;
            }
            img {
                max-width:420px;
                max-height:296px;
            }
            button {
                background-color:black;
                color:white;
                border:black;
                font-size:1.7em;
                padding:0.5em;
                padding-left:1.6em;
                padding-right:1.6em;
                font-weight:bold;
                border-top-right-radius:25%100%;
                border-top-left-radius:25%100%;
                border-bottom-left-radius:25%100%;
                border-bottom-right-radius:25%100%;
            }
            a {
                color:black;
                font-weight: bold;
            }
            .content {
                text-align:center;
            }
            .settingscontainer {
                display:flex;
                width:fit-content;
                margin:2em;
                margin-left:auto;
                margin-right:auto;
                font-size:1.1em;
            }
            .vr {
                margin:0.5em;
            }
            .divider {
                margin-top:3em;
                margin-bottom:3em;
            }
            footer {
                background-color:black;
                color:white;
                text-align:center;
                padding:1.2em;
            }
        </style></head>
        <body>
        <div class="content">
        <img src="cid:image1">
        <h1>{}</h1>
        <p>{}</p>
        <hr class="divider" width="25%">
        <h2>{}</h2>
        <p>{}</p>
        <button>{}}</button>
        <div class="settingscontainer">
            <a href="">Unsubscribe</a>
            <hr class="vr">
            <a href="">Email settings</a>
        </div>
        </div>
        </body>
        <footer>
            <p>
                Copyright &copy; 2021
            </p>
            <p>
                8BY8 is a nonprofit organization dedicated to stopping hate against Asian American Pacific Islander communities through voter registration and turnout.
            </p>
        </footer>
        </html>'''.format(h1, p1, h2, p2, btn2)
        msgText = MIMEText(html, 'html')
        msgAlternative.attach(msgText)

        # This assumes the image is in the root directory
        fp = open('8by8challenge.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image1>')
        message.attach(msgImage)

        raw_message = \
            base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
        return {'raw': raw_message.decode('utf-8')}

            
    def create_message_with_attachment(self, to, subject, file):
        message = MIMEMultipart()
        message['to'] = to
        #message['from'] = sender
        message['subject'] = subject

        # msg = MIMEText(message_text)
        # message.attach(msg)

        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msgAlternative = MIMEMultipart('alternative')
        message.attach(msgAlternative)

        msgText = MIMEText('This is the alternative plain text message.')
        msgAlternative.attach(msgText)

        # We reference the img in the IMG SRC attribute by the ID we give it below
        html = '''<html>
        <head><style>
            body {
                margin:0;
            }
            h1 {
                font-size:2.0em;
                font-weight:bold;
            }
            h2 {
                font-size:1.7em;
                font-weight:bold;
            }
            p {
                font-size:1.5em;
                margin-left:10%;
                margin-right:10%;
            }
            footer > p {
                font-size:1.1em;
            }
            img {
                max-width:420px;
                max-height:296px;
            }
            button {
                background-color:black;
                color:white;
                border:black;
                font-size:1.7em;
                padding:0.5em;
                padding-left:1.6em;
                padding-right:1.6em;
                font-weight:bold;
                border-top-right-radius:25%100%;
                border-top-left-radius:25%100%;
                border-bottom-left-radius:25%100%;
                border-bottom-right-radius:25%100%;
            }
            a {
                color:black;
                font-weight: bold;
            }
            .content {
                text-align:center;
            }
            .settingscontainer {
                display:flex;
                width:fit-content;
                margin:2em;
                margin-left:auto;
                margin-right:auto;
                font-size:1.1em;
            }
            .vr {
                margin:0.5em;
            }
            .divider {
                margin-top:3em;
                margin-bottom:3em;
            }
            footer {
                background-color:black;
                color:white;
                text-align:center;
                padding:1.2em;
            }
        </style></head>
        <body>
        <div class="content">
        <img src="cid:image1">
        <h1>JUST MAIL IT IN!</h1>
        <p>
            A PDF of your voter registration form is attached.
            Print the form and mail it to your state to finish the voter registration process.
            Instructions are included in the PDF.
        </p>
        <hr class="divider" width="25%">
        <h2>THERE'S MORE YOU CAN DO</h2>
        <p>
            Come back to 8by8 and take another action for the AAPI community!
        </p>
        <button>LEARN MORE</button>
        <div class="settingscontainer">
            <a href="">Unsubscribe</a>
            <hr class="vr">
            <a href="">Email settings</a>
        </div>
        </div>
        </body>
        <footer>
            <p>
                Copyright &copy; 2021
            </p>
            <p>
                8BY8 is a nonprofit organization dedicated to stopping hate against Asian American Pacific Islander communities through voter registration and turnout.
            </p>
        </footer>
        </html>'''
        msgText = MIMEText(html, 'html')
        msgAlternative.attach(msgText)

        # This assumes the image is in the root directory
        fp = open('8by8challenge.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image1>')
        message.attach(msgImage)
        
        img_bin = base64.b64decode(file.replace('data:image/png;base64,', '').replace('"', '').replace("'", ''))

        file_name = 'voterregestrationform.png'
        mime_part = MIMEApplication(img_bin)
        mime_part.add_header('Content-Disposition', 'attachment', filename=file_name)
        mime_part.add_header('Content-Type', 'image/png; name="{}"'.format(file_name))
        message.attach(mime_part)

        raw_message = \
            base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
        return {'raw': raw_message.decode('utf-8')}