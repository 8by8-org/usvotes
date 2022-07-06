# USVotes

## API Documentation
#### Current Base URL: https://usvotes-6vsnwycl4q-uw.a.run.app
### POST /registered/
This endpoint is used to check the voter registration status of a given person. It outputs whether or not the person is registered to vote.
#### Fields:
* state
* city
* street
* name_first
* name_last
* dob
* zip
#### Success responses (200):
```
{
    "registered": true
}
```
```
{
    "registered": false
    "status": "not found"
}
```
```
{
    "registered": false
    "status": "dropped"
}
```
#### Error responses (400):
```
{
    "error": "Missing parameters: <field 1>, <field 2>, ..."
}
```
```
{
    "error": "(street, city, state, zip) do not form a valid address"
}
```
```
{
    "error": "state must be 2 letter abbreviation"
}
```
```
{
    "error": "zip must be 5 digits"
}
```
```
{
    "error": "dob must be in the form mm/dd/yyyy"
}
```
### POST /registertovote/
This endpoint is used to fill out the [Federal Voter Registration Form](https://www.eac.gov/sites/default/files/eac_assets/1/6/Federal_Voter_Registration_ENG.pdf) and send an email with it attached to the person filling it out.
#### Fields:
* state
* city
* street
* name_first
* name_last
* dob
* zip
* email
* citizen
* eighteenPlus
* party
* idNumber
#### Success responses (200):
If a success response is returned then an email is sent to the given email with a PDF of the filled out voter registration form
```
{
    "status": "email sent"
}
```
#### Error responses (400):
```
{
    "error": "invalid email: <email>"
}
```
```
{
    "error": "invalid ID number"
}
```
```
{
    "error": "citizen parameter must be yes"
}
```
```
{
    "error": "eighteenPlus parameter must be yes"
}
```
```
{
    "error": "Missing parameters: <field 1>, <field 2>, ..."
}
```
```
{
    "error": "(street, city, state, zip) do not form a valid address"
}
```
```
{
    "error": "state must be 2 letter abbreviation"
}
```
```
{
    "error": "zip must be 5 digits"
}
```
```
{
    "error": "dob must be in the form mm/dd/yyyy"
}
```
### POST /email/
This endpoint is used to send an email out based on a template type. Valid template types are:
challengerWelcome, badgeEarned, challengeWon, challengeIncomplete, playerWelcome, registered, electionReminder
#### Fields:
* email
* type
#### Optional Fields (required for certain email types)
* avatar (ex: 1, 2, 3, 4) (required for badgeEarned, challengeWon, registered, and electionReminder)
* firstName (required for registered and electionReminder)
* daysLeft (required for badgeEarned)
* badgesLeft (required for badgeEarned)
#### Success responses (200):
```
{
    "status": "email sent"
}
```
#### Error responses (400):
```
{
    "error": "invalid email: <email>"
}
```
```
{
    "error": "invalid template type, valid types include: challengerWelcome, badgeEarned, challengeWon, challengeIncomplete, playerWelcome, registered, electionReminder"
}
```
```
{
    "error": "Missing parameters: <field 1>, <field 2>, ..."
}
```
```
{
    "error": "for <type> emails, parameter(s) <field 1>, <field 2>, ... are required"
}
```
### POST /validateAddress/
This endpoint is used to check if an address is valid or not according to USPS.
#### Fields:
* state
* city
* street
* zip
#### Success responses (200):
```
{
    "isValid": true
}
```
```
{
    "isValid": false
}
```
#### Error responses (400):
```
{
    "error": "Missing parameters: <field 1>, <field 2>, ..."
}
```
```
{
    "error": "state must be 2 letter abbreviation"
}
```
```
{
    "error": "zip must be 5 digits"
}
```
## Repository and Environment Setup
* [Database Setup](#database-setup)
* [Setup & Installation](#setup-&-installation)
    * [Environmental Variables](#environmental-variables)
    * [Run the application](#run-the-application)
* [Tests](#tests)
* [Styling](styling)
* [Internationalization & Localization](#internationalization-&-localization)

### Database services

You can run PostgreSQL and Redis locally, or via Docker.

For native Mac installations consider [PostgresApp](https://postgresapp.com/).

For Docker, there is a `docker-compose.yml` file in the repo you can use with:

```
# start
$ make start-services
# stop
$ make stop-services
```

Redis is used for caching stats and external API calls.

Once you have PostgreSQL available, you must create database instances for local use.
[DB setup reference](https://medium.com/coding-blocks/creating-user-database-and-adding-access-on-postgresql-8bfcd2f4a91e)

Create databases for development and testing. In the [Environmental Variables](#environmental-variables)
section below we assume the names you picked were `ksvotes_dev` and `ksvotes_test`.


## Setup & Installation
Recommendations for running after cloning:

Install [Python 3.6+](https://www.python.org/downloads/)

Install [pip](https://pypi.org/project/pip/#description)

Install [virtualenv](https://virtualenv.pypa.io/en/stable/)

In app root directory setup your virtualenv and install dependencies to your virtualenv python.

```
$ virtualenv venv -p python3
$ . venv/bin/activate
$(venv) make deps
$(venv) make locales
```

### Environmental Variables
Create a .env file in the root directory and add the following variables.
Note that the commented-out (`#`-prefixed) variables are optional.

```
SECRET_KEY={{generate a secret key}}
APP_CONFIG=development
CRYPT_KEY={{generate a secret key | base64}}

# Set this to enable the /demo endpoint
DEMO_UUID={{generate a UUID and run "make load-demo"}}

# You can grab one from the URL below or take the one from the staging configuration
USPS_USER_ID={{key from https://registration.shippingapis.com/}}

NVRIS_URL=TESTING

# For using the Gmail API to send Emails
CLIENT_ID={{get creds https://developers.google.com/workspace/guides/create-credentials}}
CLIENT_SECRET={{get creds https://developers.google.com/workspace/guides/create-credentials}}
PROJECT_ID={{your project}}

#########################
# OPTIONAL ENV VARS
#########################

# LOG_LEVEL=INFO
# GA_KEY={{google analytics key}}
# RECAPTCHA_KEY={{public key}}
# RECAPTCHA_SECRET={{private key}}
# AWS_ACCESS_KEY_ID={{from role with at least rds access}}
# AWS_SECRET_ACCESS_KEY={{from role with at least rds access}}
# AWS_DEFAULT_REGION={{us-east-1 || or your region where RDS is hosted}}
# SES_ACCESS_KEY_ID={{from role with ses access}}
# SES_SECRET_ACCESS_KEY={{from role with ses access}}

# EMAIL_FROM={{override the From email header in all email}}
# EMAIL_PREFIX={{prefix all Subject lines with a string}}

# Default is not to send actual email unless SEND_EMAIL is set
# SEND_EMAIL=true

# Number of minutes before idle session expires. Default is 10.
# SESSION_TTL=10

# You want the default VV URL unless you are testing error checking.
# VOTER_VIEW_URL=https://myvoteinfo.voteks.org/VoterView/RegistrantSearch.do


# The date and time prior to the Primary election when the Advance Ballot
# option for the Primary disappears. Format is 'YYYY-MM-DD HH:MM:SS' and assumes
# a Central US time zone
# AB_PRIMARY_DEADLINE="2020-05-01 17:00:00"

# Turn the AB flow on. Default is off.
# ENABLE_AB=true

# Turn VIT voting location JS widget on. Default is off.
# ENABLE_VOTING_LOCATION=true

# Turn off HTTPS requirement. Probably set this to true in your local dev.
# SSL_DISABLE=true

# Include the top banner on every page that this is not the live production site.
# STAGE_BANNER=true

```

### Crypt Key

The encryption key is kind of particular, it needs to be 32 bytes long and URl-safe base64 encoded.

### Demo uuid

We need `DEMO_UUID` set to a UUID, use this to generate one for you quickly:

```
$(venv) make demo-uuid
```

### Validate your configuration

You can check that your local env has all of the requried environment variables set by running:

```
($venv) make check
```

### Run the Application

Let's get up and running.
```
$(venv) make run
```

Navigate to [localhost:5000](http://localhost:5000)


## Tests

To run all unit tests:
```
$(venv) make test
```

## Styling
Code is currently setup to SCSS with node scripts to compile.

Edit `scss/source.scss` and compile with `% make css`.

Alternatively you can create your own .css style sheet in *app/static/css* and replace
```
<link href="{{url_for('static', filename='css/compiled.css')}}" rel="stylesheet">
```
in *app/templates/base.html* with
```
<link href="{{url_for('static', filename='css/[[[name of your style sheet]]]')}}" rel="stylesheet">
```

To setup scss watcher in root directory run:
```
$ npm install
```
```
$ npm run watch
```

## Internationalization & Localization
This application is using [Flask-Babel](https://pythonhosted.org/Flask-Babel/)

To add a new string, reference the string in the .py code with `gettext()` or `lazy_gettext()`
and then run `% make locales` to update the corresponding babel files. For example:

```
# in foo.py
lazy_gettext('some_key_string')

# add 'some_key_string' to translations.json
% vi translations.json

# Then in your terminal
# update the translation files
% make locales
```

## Docker Commands to push to GCP
These commands build a docker image of the project, test the image, and push it to GCP Artifact Registry
```
docker build .
docker-slim build --preserve-path=/usr/bin --preserve-path=/usr/include --preserve-path=/usr/local --http-probe-cmd-file probeCmds.json <image>
docker run -it --rm -p 8080:8080 --name dslimflask <image>.slim
docker tag <image ID> us-west2-docker.pkg.dev/by8-318322/images/<image name>
docker push us-west2-docker.pkg.dev/by8-318322/images/<image name>
```

