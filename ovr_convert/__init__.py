import os

from flask import Flask, render_template, jsonify
from flask_session import Session
from flask_bootstrap import Bootstrap4

from .api import new_session_configuration
from .gvm_api import get_gvm_sock, login_gvm, get_tasks

app = Flask(__name__)
app.config.from_mapping(
  SECRET_KEY = os.urandom(24),
  UPLOAD_FOLDER = '/var/tmp',
  MAX_CONTENT_LENGTH = 200*1024*1024, # to generate very big reports. ymmv 
  SESSION_PERMANENT = False,
  SESSION_TYPE = 'filesystem',
  SESSION_COOKIE_SAMESITE = "Lax",
  BOOTSTRAP_BOOTSWATCH_THEME = 'cosmo',
  BOOTSTRAP_BTN_SIZE = 'sm',
  GVM_SOCK_PATH = '/run/sock/gvm.sock',
)

# create server-side session
Session(app)

# register general api
try:
    app.register_blueprint(api.api_bp)
except:
    raise Exception('could not register api blueprint.')

# register gvm api
try:
    app.register_blueprint(gvm_api.gvm_bp)
except:
    raise Exception('could not register gvm blueprint.')

# create Bootstrap
bootstrap = Bootstrap4(app)

# create instance dirs if any
try:
    os.makedirs(app.instance_path)
except OSError:
    pass
    
# try to connect to gvm via it's socket
if get_gvm_sock():
    app.add_template_global(name='GVM_SOCK_PRESENT', f=True)
else:
    app.add_template_global(name='GVM_SOCK_PRESENT', f=False)
    
# define filter to jinja2 later use
@app.template_filter('lowerCamelCase')
def lowerCamelCase(s):
    words = s.translate(str.maketrans({'_': ' ', '-': ' ', '#': ' '})).split(' ')
    s = "".join(word[0].upper() + word[1:].lower() for word in words)
    return s[0].lower() + s[1:]

@app.route('/')
def main_route():
    new_session_configuration()

    return render_template('index.html')

@app.route('/test')
def test():
    if app.jinja_env.globals['GVM_SOCK_PRESENT']:
        if login_gvm():
            return render_template('test.html', tasks=get_tasks())
        else:
            return jsonify({'status': 'error', 'messages': 'could not login to gvm with current credentials.'})
    else:
        return jsonify({'status': 'error', 'messages': 'no gvm sock to be used.'})

