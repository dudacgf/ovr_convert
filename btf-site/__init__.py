import os
from flask import Flask, render_template, session
from flask_session import Session
from flask_bootstrap import Bootstrap
from . import api
from .api import new_session_configuration

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
      SECRET_KEY = os.urandom(24),
      UPLOAD_FOLDER = '/var/tmp',
      MAX_CONTENT_LENGTH = 200*1024*1024, # to generate very big reports. ymmv 
      SESSION_PERMANENT = False,
      SESSION_TYPE = 'filesystem',
      BOOTSTRAP_BOOTSWATCH_THEME = 'cosmo',
      BOOTSTRAP_BTN_SIZE = 'sm',
    )

    # create server-side session
    Session(app)
    
    # register api
    try:
        app.register_blueprint(api.api_bp)
    except:
        raise Exception('could not register api blueprint.')

    # create Bootstrap
    bootstrap = Bootstrap(app)

    # create instance dirs if any
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    @app.route('/')
    def btf():
        new_session_configuration()

        return render_template('index.html')

    return app

