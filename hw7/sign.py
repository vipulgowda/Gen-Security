from flask import redirect, render_template, session
from requests_oauthlib import OAuth2Session
from flask.views import MethodView
from oauth_config import client_id, authorization_base_url, redirect_callback

class Sign(MethodView):
    def get(self):
        """
        Handles GET requests to initiate OAuth flow or display user info.
        """
        if 'oauth_token' in session:
            # User is already authenticated, fetch user info
            google = OAuth2Session(client_id, token=session['oauth_token'])
            user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
            return render_template('sign.html', user=user_info)
        else:
            # Initiate OAuth flow
            google = OAuth2Session(client_id, redirect_uri=redirect_callback, scope=['email', 'profile'])
            authorization_url, state = google.authorization_url(authorization_base_url, prompt='login')
            session['oauth_state'] = state
            return redirect(authorization_url)
