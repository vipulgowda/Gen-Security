"""
This module defines constants and retrieves credentials for OAuth 2.0 authentication with Google.
"""

import os

# Client credentials from environment variables
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
redirect_callback = os.environ.get('REDIRECT_CALLBACK')

# Google OAuth 2.0 endpoints
authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://accounts.google.com/o/oauth2/token"
