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

    # Should convert this into a JSON file
    emailTypes = {
        'challengerWelcome': {
            'subject': 'Welcome to the 8by8 Challenge!',
            'h1': 'INVITE YOUR FRIENDS',
            'p1': 'The challenge is on! Get 8 of your friends to take action on your 8by8 Challenge by [countdown_end_date].',
            'img1': '',
            'img1Class': 'hidden',
            'btn1': 'INVITE FRIENDS',
            'h2': 'REMAINING...',
            'img2': 'img/daysleft8.png',
            'img2Class': '',
            'p2': '8 days before ending the challenge',
            'p3': '8 more badges winning!',
            'btn2': 'INVITE FRIENDS'
        },
        'badgeEarned': {
            'subject': 'You got badges!',
            'h1': 'GREAT PROGRESS!',
            'p1': 'You’ve earned badges! Go to 8by8 to check them out.',
            'img1': 'img/avatar.png',
            'img1Class': '',
            'btn1': 'CHECK OUT YOUR BADGES',
            'h2': 'REMAINING...',
            'img2': 'img/daysleft6.png',
            'img2Class': '',
            'p2': '6 days before ending the challenge',
            'p3': '5 more badges winning!',
            'btn2': 'INVITE FRIENDS'
        },
        'challengeWon': {
            'subject': 'You won the 8by8 Challenge!',
            'h1': 'CONGRATULATIONS!',
            'p1': 'You earned all 8 badges! We really appreciate you and your friends’ efforts in helping the AAPI community!',
            'img1': 'img/badges8.png',
            'img1Class': '',
            'btn1': 'CHECK OUT YOUR BADGES',
            'h2': 'TELL YOUR FRIENDS',
            'img2': '',
            'img2Class': 'hidden',
            'p2': 'Share your achievement and encourage others to take the challenge as well! ',
            'p3': '',
            'btn2': 'SHARE WITH FRIENDS'
        },
        'challengeIncomplete': {
            'subject': 'Restart your 8by8 Challenge',
            'h1': 'LET\'S TRY IT AGAIN',
            'p1': 'Your challenge ended before you’ve earned all 8 badges. Restart your challenge to try again!',
            'img1': '',
            'img1Class': 'hidden',
            'btn1': 'RESTART CHALLENGE',
            'h2': 'WHY 8BY8?',
            'img2': '',
            'img2Class': 'hidden',
            'p2': 'Your participation is important to closing the voter registration gap in the AAPI community.',
            'p3': '',
            'btn2': 'LEARN MORE'
        },
        'playerWelcome': {
            'subject': 'Welcome to the 8by8 Challenge!',
            'h1': 'TAKE ACTION NOW',
            'p1': 'Welcome to the 8by8 Challenge! Take action now towards your friend’s challenge.',
            'img1': '',
            'img1Class': 'hidden',
            'btn1': 'TAKE ACTION',
            'h2': 'WHAT ELSE?',
            'img2': '',
            'img2Class': 'hidden',
            'p2': 'Take the 8by8 challenge yourself or spread the word!',
            'p3': '',
            'btn2': 'VIEW 8BY8 CHALLENGE'
        },
        'registered': {
            'subject': 'You\'ve registered to vote!',
            'h1': 'THANK YOU FOR DOING YOUR PART.',
            'p1': 'You completed the first step in your voter registration! Remember to finish your registration at your state website or by mailing in your form. Your friend has earned a badge in their 8by8 Challenge!',
            'img1': 'img/yang.png',
            'img1Class': '',
            'btn1': 'SHARE WITH FRIENDS',
            'h2': 'THERE\'S MORE YOU CAN DO',
            'img2': '',
            'img2Class': 'hidden',
            'p2': 'Come back to 8by8 and take another action for the AAPI community!',
            'p3': '',
            'btn2': 'TAKE ANOTHER ACTION'
        },
        'electionReminder': {
            'subject': 'Your election reminders are set!',
            'h1': 'THANK YOU FOR DOING YOUR PART.',
            'p1': 'You’ve set up election reminders. Your friend has earned a badge in their 8by8 Challenge!',
            'img1': 'img/yang.png',
            'img1Class': '',
            'btn1': 'SHARE WITH FRIENDS',
            'h2': 'THERE\'S MORE YOU CAN DO',
            'img2': '',
            'img2Class': 'hidden',
            'p2': 'Come back to 8by8 and take another action for the AAPI community!',
            'p3': '',
            'btn2': 'TAKE ANOTHER ACTION'
        }
    }

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
    
    def create_template_message(self, to, type):
        # Depending on the type of email, get the contents
        content = self.emailTypes[type]

        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = content['subject']

        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msgAlternative = MIMEMultipart('alternative')
        message.attach(msgAlternative)

        # Make HTML for email, inputting all the variable content
        # make sure to escape curly braces by doubling them {{}}
        html = '''<html>
        <head><style>
            body {{
                margin:0;
            }}
            h1 {{
                font-size:2.0em;
                font-weight:bold;
            }}
            h2 {{
                font-size:1.7em;
                font-weight:bold;
            }}
            p {{
                font-size:1.5em;
                margin-left:10%;
                margin-right:10%;
            }}
            footer > p {{
                font-size:1.1em;
            }}
            img {{
                max-width:420px;
                max-height:296px;
            }}
            button {{
                border: solid black 0.25rem;
                font-size:1.7em;
                padding:0.5em;
                padding-left:1.4em;
                padding-right:1.4em;
                font-weight:bold;
                border-top-right-radius:3em 100%;
                border-top-left-radius:3em 100%;
                border-bottom-left-radius:3em 100%;
                border-bottom-right-radius:3em 100%;
            }}
            .btn1 {{
                background: linear-gradient(90deg, #02DDC3, #FFED10);
                color: black;
                margin-top: 0.8em;
            }}
            .btn2 {{
                background-color:black;
                color:white;
            }}
            a {{
                color:black;
                font-weight: bold;
            }}
            .content {{
                text-align:center;
            }}
            .settingscontainer {{
                display:flex;
                width:fit-content;
                margin:2em;
                margin-left:auto;
                margin-right:auto;
                font-size:1.1em;
            }}
            .vr {{
                margin:0.5em;
            }}
            .divider {{
                margin-top:3em;
                margin-bottom:3em;
            }}
            .hidden {{
                display:none;
            }}
            footer {{
                background-color:black;
                color:white;
                text-align:center;
                padding:1.2em;
            }}
        </style></head>
        <body>
        <div class="content">
        <img src="cid:image0">
        <h1>{h1}</h1>
        <p>{p1}</p>
        <img class="{img1Class}" src="cid:image1">
        <div>
            <button class="btn1">{btn1}</button>
        </div>
        <hr class="divider" width="25%">
        <h2>{h2}</h2>
        <img class="{img2Class}" src="cid:image2">
        <p>{p2}</p>
        <p>{p3}</p>
        <button class="btn2">{btn2}</button>
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
        </html>'''.format(h1=content['h1'], p1=content['p1'], img1Class=content['img1Class'], btn1=content['btn1'], h2=content['h2'], img2Class=content['img2Class'], p2=content['p2'], p3=content['p3'], btn2=content['btn2'])
        msgText = MIMEText(html, 'html')
        msgAlternative.attach(msgText)

        # This assumes the image is in the /img folder
        fp = open('img/8by8challenge.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image0>')
        message.attach(msgImage)

        # add images (img1, img2) if they are part of the template type
        if content['img1']:
            fp = open(content['img1'], 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            # Define the image's ID as referenced above
            msgImage.add_header('Content-ID', '<image1>')
            message.attach(msgImage)
        if content['img2']:
            fp = open(content['img2'], 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            # Define the image's ID as referenced above
            msgImage.add_header('Content-ID', '<image2>')
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
        fp = open('img/8by8challenge.png', 'rb')
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