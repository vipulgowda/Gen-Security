from flask import redirect, url_for, session
from flask.views import MethodView

class Logout(MethodView):
    """
    View for handling user logout.
    """
    def get(self):
        """
        Logs the user out by clearing the session and redirecting to the homepage.
        """
        session.clear()  # Remove all session data
        return redirect(url_for('index'))  # Redirect to the homepage
