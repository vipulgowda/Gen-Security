from flask import redirect, request, url_for, session
from requests_oauthlib import OAuth2Session
from flask.views import MethodView
from oauth_config import client_id, client_secret, token_url, redirect_callback

class Callback(MethodView):
    def get(self):
        """
        Handles the OAuth 2.0 callback from Google.
        """
        google = OAuth2Session(client_id, redirect_uri=redirect_callback, state=session['oauth_state'])
        authorization_response = request.url.replace("http://", "https://")  # Ensure HTTPS
        token = google.fetch_token(
            token_url, client_secret=client_secret, authorization_response=authorization_response
        )
        session['oauth_token'] = token
        return redirect(url_for('sign'))
