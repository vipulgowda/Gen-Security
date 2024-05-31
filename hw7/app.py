"""
This module defines the Flask web application for handling OAuth authentication.
"""

import os
from flask import Flask, redirect, url_for, session
from flask.views import MethodView

# Import class-based views from separate files
from index import Index
from sign import Sign
from callback import Callback
from logout import Logout

# Create a Flask application instance
app = Flask(__name__)

# Set a secret key for secure session management
app.secret_key = os.urandom(24)

# Define URL rules to map URLs to views
app.add_url_rule('/', view_func=Index.as_view('index'), methods=['GET'])
app.add_url_rule('/callback', view_func=Callback.as_view('callback'), methods=['GET'])
app.add_url_rule('/sign', view_func=Sign.as_view('sign'), methods=['GET', 'POST'])
app.add_url_rule('/logout', view_func=Logout.as_view('logout'), methods=['GET'])

# Run the application if it's executed as the main program
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
