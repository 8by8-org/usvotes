import os

from app import create_app
from flask_script import Manager, Shell
from flask import url_for, g

app = create_app(os.getenv('APP_CONFIG') or 'default')
manager = Manager(app)


def make_shell_context():
    g.locale = 'en'
    return dict(app=app)


manager.add_command("shell", Shell(make_context=make_shell_context))


def write_pid_file():
    pid = str(os.getpid())
    with open('server.pid', 'w+') as f:
        f.write(pid + '\n')


@manager.command
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.parse.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    for line in sorted(output):
        print(line)

@manager.command
def generate_demo_uuid():
    import uuid
    this_uuid = uuid.uuid4().hex

    print("\nAdd this to your .env file:")
    print('DEMO_UUID="{}"'.format(this_uuid))


@manager.command
def check_configuration():
    """ Ensure our configuration looks plausible """
    required_env_settings = [
        'SECRET_KEY',
        'APP_CONFIG',
        'CRYPT_KEY',
        'NVRIS_URL',
        'DEMO_UUID',
        'USPS_USER_ID',
    ]
    missing = []

    for key in required_env_settings:
        value = os.getenv(key, None)
        if value is None or value.startswith('{'):
            missing.append(key)

    if missing:
        print("Configuration Errors Detected, these are missing:")
        [print(k) for k in missing]


def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print("#%s: %s:%s: %.1f KiB"
              % (index, frame.filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))

if __name__ == "__main__":
    import tracemalloc
    tracemalloc.start(10)
    import pprint
    import os
    import linecache
    
    write_pid_file()
    try:
        app.jinja_env.cache = {}
        manager.run()
    except:
        snapshot = tracemalloc.take_snapshot()

        display_top(snapshot, 'lineno', 100)
