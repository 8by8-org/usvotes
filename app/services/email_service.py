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
from datetime import timedelta, date

class EmailService():

    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    emailTypes = {
        'challengerWelcome': {
            'subject': 'Welcome to the 8by8 Challenge!',
            'h1': 'INVITE YOUR FRIENDS',
            'p1': 'The challenge is on! Get 8 of your friends to take action on your 8by8 Challenge by ',
            'img1': '',
            'img1Class': 'hidden',
            'btn1': 'INVITE FRIENDS',
            'h2': 'REMAINING...',
            'img2': 'img/daysleft8.png',
            'img2Class': '',
            'p2': ' before ending the challenge',
            'p3': ' badges winning!',
            'btn2': 'INVITE FRIENDS'
        },
        'badgeEarned': {
            'subject': 'You got badges!',
            'h1': 'GREAT PROGRESS!',
            'p1': 'You’ve earned badges! Go to 8by8 to check them out.',
            'img1': 'img/badges3.png',
            'img1Class': '',
            'btn1': 'CHECK OUT YOUR BADGES',
            'h2': 'REMAINING...',
            'img2': '',
            'img2Class': '',
            'p2': ' before ending the challenge',
            'p3': ' badges winning!',
            'btn2': 'INVITE FRIENDS'
        },
        'challengeWon': {
            'subject': '8by8 Rewards',
            'h1': 'YOUR REWARD',
            'p1': "Woo! You completed the 8by8 Challenge, getting 8 friends to register to vote in 8 days. You've helped uplift AAPI voices. Go you! Enjoy your reward, and keep spreading the word!",
            'img1': '',
            'img1Class': 'hidden',
            'btn1': 'GO TO REWARDS',
            'h2': 'WHY 8BY8?',
            'img2': '',
            'img2Class': 'hidden',
            'p2': 'Your participation is important to closing the voter registration gap in the AAPI community.',
            'p3': '',
            'btn2': 'LEARN MORE'
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
            'img1': '',
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
            'img1': '',
            'img1Class': '',
            'btn1': 'SHARE WITH FRIENDS',
            'h2': 'THERE\'S MORE YOU CAN DO',
            'img2': '',
            'img2Class': 'hidden',
            'p2': 'Come back to 8by8 and take another action for the AAPI community!',
            'p3': '',
            'btn2': 'TAKE ANOTHER ACTION'
        },
        'verifyEmail': {
            'subject': 'Verify your email with 8by8',
            'h1': 'LET’S FIRST VERIFY YOUR EMAIL.',
            'p1': 'For your security, we ask that you verify your recent 8by8 Challenge sign in. Click on the “Verify Now” button below to sign in!',
            'img1': '',
            'img1Class': '',
            'btn1': 'VERIFY NOW',
            'h2': 'WHY 8BY8?',
            'img2': '',
            'img2Class': 'hidden',
            'p2': 'Your participation is important to closing the voter registration gap in the AAPI community.',
            'p3': '',
            'btn2': 'LEARN MORE'
        }
    }

    def __init__(self, gmail=True):
        if gmail:
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
        else:
            # Not using Gmail API (will throw error if send_message is called)
            self.service = None

    def send_message(self, message, user_id='me'):
        try:
            message = self.service.users().messages().send(userId=user_id,
                    body=message).execute()

            print('Message Id: {}'.format(message['id']))

            return message
        except Exception as e:
            print('An error occurred: {}'.format(e))
            raise e
    
    def create_template_message(self, to, type, daysLeft='', badgesLeft='', firstName='', avatar=None, isChallenger='', verifyLink='', partners=''):
        # Depending on the type of email, get the contents
        if type in self.emailTypes:
            content = self.emailTypes[type]
        else:
            print('value error')
            raise ValueError("invalid email type")

        message = MIMEMultipart()
        message['to'] = to
        message['from'] = '8by8 Challenge <8by8.app@gmail.com>'
        message['subject'] = content['subject']

        # Encapsulate the plain and HTML versions of the message body in an
        # 'alternative' part, so message agents can decide which they want to display.
        msgAlternative = MIMEMultipart('Seems like your emailing service doesn\'t support HTML :(')
        message.attach(msgAlternative)

        btn1Link = 'https://challenge.8by8.us/progress'
        btn2Link = 'https://challenge.8by8.us/actions'
        paragraph = content['p1']
        img0 = ''
        verifyP = ''
        ourPartners = ''
        divider = '<hr class="divider" width="25%">'
        if type == 'badgeEarned':
            content['img2'] = 'img/daysleft' + daysLeft + '.png'
            if daysLeft == '1':
                daysLeft = daysLeft + ' day'
            else:
                daysLeft = daysLeft + ' days'
            if badgesLeft == '1':
                content['p3'] = content['p3'][:6] + content['p3'][7:]
            badgesLeft =  badgesLeft + ' more'
        elif type != 'challengerWelcome':
            daysLeft = ''
            badgesLeft =  ''
        if type == 'challengerWelcome':
            endDate = date.today() + timedelta(days=8)
            endDateStr = endDate.strftime("%B %d, %Y") + '.'
            daysLeft = '8 days'
            badgesLeft =  '8 more'
        else:
            endDateStr = ''
        if type == 'registered' or type == 'electionReminder':
            firstName = '<div class="imgcontainer"><h2 class="imgtext">' + firstName.upper() + '</h2></div>'
            content['img1'] = 'img/avatar' + avatar + '.png'
            if isChallenger and isChallenger.lower() != 'false':
                index = content['p1'].find('Your friend has')
                paragraph = content['p1'][:index]
        else:
            firstName = ''
        if type == 'badgeEarned':
            buttonSize = '14'
        else:
            buttonSize = '16'
        if type == 'playerWelcome' or (type == 'challengeWon' and (not isChallenger or isChallenger == 'false')):
            btn2Link = 'https://challenge.8by8.us/progress'
            btn1Link = 'https://challenge.8by8.us/actions'
            content['p1'] = "Woo! A friend you supported has won the 8by8 Challenge! You've helped uplift AAPI voices. Go you! Enjoy your reward, and keep spreading the word!"
        if type == 'verifyEmail':
            verifyP = 'Or paste this link into your browser:'
            btn1Link = verifyLink
            img0 = 'img/party.png'
        else:
            verifyLink = ''
        if type == 'challengeWon':
            divider = ''
            if partners:
                ourPartners = 'OUR PARTNERS'
                urls = partners.split(',')
                partners = ''
                for index, url in enumerate(urls):
                    if index % 2 == 0 and index + 1 == len(urls):
                        partners += '<table class="center"><tr><td class="partnerTd" valign="top"><img class="partner" src="' + url + '"></td></tr></table>'
                    if index % 2 == 1:
                        partners += '<table class="center"><tr><td class="partnerTd" valign="top"><img class="partner" src="' + urls[index - 1] + '"></td><td class="partnerTd leftmarg" valign="top"><img class="partner" src="' + url + '"></td></tr></table>'
            else:
                partners = ''
        else:
            partners = ''
        # Make HTML for email, inputting all the variable content
        # make sure to escape curly braces by doubling them {{}}
        # No Email Settings or Unsubscribe in alpha
        '''
        <div class="settingscontainer">
            <a href="https://www.8by8.us/">Unsubscribe</a>
            <hr class="vr">
            <a href="https://www.8by8.us/">Email settings</a>
        </div>
        '''

        html = '''<html>
        <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Lato&family=Oswald&display=swap');
            .app {{
                margin: 0 auto;
                max-width: 500px;
                min-width: 375px;
                background-color: white;
            }}
            h1 {{
                font-size:22pt;
                font-weight:bold;
                font-family: 'Oswald', sans-serif;
            }}
            h2 {{
                font-size:16pt;
                font-weight:bold;
                font-family: 'Oswald', sans-serif;
            }}
            p {{
                font-size:1.5em;
                margin-left:10%;
                margin-right:10%;
                font-family: 'Lato', sans-serif;
            }}
            footer > p {{
                font-size:1.1em;
            }}
            .head1 {{
                margin-top:6%;
            }}
            .leftmarg {{
                padding-left: 8%;
            }}
            .contain {{
                display: grid;
                align-items: center;
            }}
            .minip {{
                font-size:10pt;
                margin-left:15%;
                margin-right:15%;
            }}
            .img8by8 {{
                width:100%;
            }}
            .img1 {{
                max-width:16em;
                max-height:222px;
            }}
            .img2 {{
                max-width:252px;
                max-height:179px;
            }}
            .partner {{
                max-width:220px;
                max-height:220px;
            }}
            .partnerTd {{
                vertical-align:middle;
                height:auto;
                padding-top:4%;
                padding-bottom:4%
            }}
            .center {{
                margin-left: auto;
                margin-right: auto;
                max-height:240px;
            }}
            .imgcontainer {{
                max-height:0;
                position:relative;
                opacity:0.999;
            }}
            .imgtext {{
                font-size:13pt;
                margin-top:153px;
                margin-right: 8px;
                display:inline-block;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                width: 138px
            }}
            button {{
                font-family: 'Oswald', sans-serif;
                border: solid #101010 0.25rem;
                font-size:16pt;
                padding:0.4em;
                padding-left:1.4em;
                padding-right:1.4em;
                font-weight:bold;
                border-top-right-radius:2.3em 100%;
                border-top-left-radius:2.3em 100%;
                border-bottom-left-radius:2.3em 100%;
                border-bottom-right-radius:2.3em 100%;
                cursor: pointer;
            }}
            .btn1, .btn2 {{
                font-size:{buttonSize}pt;
            }}
            .btn1 {{
                background: linear-gradient(90deg, #02DDC3, #FFED10);
                color: #101010;
                margin-top: 0.8em;
            }}
            .btn2 {{
                background-color: #101010;
                color:white;
                margin-top: 0.7em;
                margin-bottom: 1.5em;
            }}

            .btn2 > span {{
                color: white;
                background-image: linear-gradient(90deg, #02DDC3, #FFED10);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;  
            }}

            a {{
                color: #101010 !important;
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
            .socialmedia a {{
                margin: 14px
            }}
            .socialmedia {{
                margin: 24px
            }}
            .footer {{
                background-color: #101010;
                color:white;
                text-align:center;
                padding:1.2em;
            }}
            img {{
                margin: 0 auto;
            }}
            @media only screen and (max-width: 500px) {{
                p {{
                    font-size:1.2em !important;
                }}
                .footer > p, .settingscontainer {{
                    font-size:1.0em !important;
                }}
                .img1 {{
                    max-width:11em;
                }}
                .img2 {{
                    max-width:13em;
                }}
                .partner {{
                    max-width:11em;
                    max-height:11em;
                }}
                .head1 {{
                    margin-top:8%;
                }}
            }}
        </style>
        </head>
        <body>
        <div class="app">
        <div class="content">
        <img class="img8by8" src="cid:image8">
        <img class="img1 {img1Class}" src="cid:image0">
        <h1>{h1}</h1>
        <p>{p1}{endDate}</p>
        {firstName}
        <img class="img1 {img1Class}" src="cid:image1">
        <div>
        <a href="{btn1Link}" >
            <button class="btn1">{btn1}</button>
        </a>
        <h1 class="head1">{h1Partner}</h1>
        {partners}
        <p class="minip">{miniP}</p>
        <p class="minip">{miniLink}</p>
        </div>
        {div}
        <h2>{h2}</h2>
        <img class="img2 {img2Class}" src="cid:image2">
        <p><b>{daysLeft}</b>{p2}</p>
        <p><b>{badgesLeft}</b>{p3}</p>
        <a class="abtn2" href="{btn2Link}">
        <button class="btn2">{btn2}</button>
        </a>
        
        </div>
        <div class="footer">
            <div class="socialmedia">
                <a href="https://www.facebook.com/8by8vote" target="_blank">
                    <img width="20" height="20" src="cid:facebook">
                </a>
                <a href="https://www.linkedin.com/company/8by8vote/" target="_blank">
                    <img width="20" height="20" src="cid:linkedin">
                </a>
                <a href="https://www.instagram.com/8by8vote/" target="_blank">
                    <img width="20" height="20" src="cid:instagram">
                </a>
            </div>
            <p>
                Copyright &copy; 2021
            </p>
            <p>
                8BY8 is a nonprofit organization dedicated to stopping hate against Asian American Pacific Islander communities through voter registration and turnout.
            </p>
        </div>
        </div>
        </body>
        </html>'''.format(buttonSize=buttonSize, h1=content['h1'], p1=paragraph, endDate=endDateStr, firstName=firstName, img1Class=content['img1Class'], 
                          btn1Link=btn1Link, btn1=content['btn1'], h1Partner=ourPartners, partners=partners, miniP=verifyP, miniLink=verifyLink, div=divider,
                          h2=content['h2'], img2Class=content['img2Class'], daysLeft=daysLeft, p2=content['p2'], badgesLeft=badgesLeft, p3=content['p3'], 
                          btn2Link=btn2Link, btn2=content['btn2'])
        msgText = MIMEText(html, 'html')
        msgAlternative.attach(msgText)

        # This assumes the image is in the /img folder
        fp = open('img/8by8challenge.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        # Define the image's ID as referenced above
        msgImage.add_header('Content-ID', '<image8>')
        message.attach(msgImage)

        # add images (img1, img2) if they are part of the template type
        if img0 != '':
            fp = open(img0, 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            # Define the image's ID as referenced above
            msgImage.add_header('Content-ID', '<image0>')
            message.attach(msgImage)
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
        
        fp = open('img/facebook.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<facebook>')
        message.attach(msgImage)
        fp = open('img/linkedin.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<linkedin>')
        message.attach(msgImage)
        fp = open('img/instagram.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<instagram>')
        message.attach(msgImage)
        
        raw_message = \
            base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
        return {'raw': raw_message.decode('utf-8')}

            
    def create_message_with_attachment(self, to, subject, file):
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = '8by8 Challenge <8by8.app@gmail.com>'
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
        # No Email Settings or Unsubscribe for alpha
        '''
        <div class="settingscontainer">
            <a href="https://www.8by8.us/">Unsubscribe</a>
            <hr class="vr">
            <a href="https://www.8by8.us/">Email settings</a>
        </div>
        '''

        html = '''<html>
        <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Lato&family=Oswald&display=swap');
            body {
                margin:0;
            }
            h1 {
                font-size:22pt;
                font-weight:bold;
                font-family: 'Oswald', sans-serif;
            }
            h2 {
                font-size:16pt;
                font-weight:bold;
                font-family: 'Oswald', sans-serif;
            }
            p {
                font-size:1.5em;
                margin-left:10%;
                margin-right:10%;
                font-family: 'Lato', sans-serif;
            }
            footer > p {
                font-size:1.1em;
            }
            img {
                max-width:420px;
                max-height:296px;
            }
            button {
                font-family: 'Oswald', sans-serif;
                background-color:black;
                color:white;
                letter-spacing: 0.03em;
                border: solid black 0.25rem;
                font-size:16pt;
                padding:0.4em;
                padding-left:1.4em;
                padding-right:1.4em;
                font-weight:bold;
                border-top-right-radius:2.3em 100%;
                border-top-left-radius:2.3em 100%;
                border-bottom-left-radius:2.3em 100%;
                border-bottom-right-radius:2.3em 100%;
                margin-bottom: 1.5em;
            }
            a {
                color:black !important;
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
            .hidden {
                display:none;
            }
            .socialmedia a {
                margin: 14px
            }
            .socialmedia {
                margin: 24px
            }
            footer {
                background-color:black;
                color:white;
                text-align:center;
                padding:1.2em;
            }
            @media only screen and (max-width: 500px) {
                p {
                    font-size:1.2em !important;
                }
                footer > p, .settingscontainer {
                    font-size:1.0em !important;
                }
            }
        </style>
        </head>
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
        <a href='https://challenge.8by8.us/'>
        <button>LEARN MORE</button>
        </a>
        
        </div>
        </body>
        <footer>
            <div class="socialmedia">
                <a href="https://www.facebook.com/8by8vote" target="_blank">
                    <img width="20" height="20" src="cid:facebook">
                </a>
                <a href="https://www.linkedin.com/company/8by8vote/" target="_blank">
                    <img width="20" height="20" src="cid:linkedin">
                </a>
                <a href="https://www.instagram.com/8by8vote/" target="_blank">
                    <img width="20" height="20" src="cid:instagram">
                </a>
            </div>
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

        fp = open('img/facebook.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<facebook>')
        message.attach(msgImage)
        fp = open('img/linkedin.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<linkedin>')
        message.attach(msgImage)
        fp = open('img/instagram.png', 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msgImage.add_header('Content-ID', '<instagram>')
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