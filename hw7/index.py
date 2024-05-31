from flask import render_template
from flask.views import MethodView

class Index(MethodView):
    """
    Class-based view for the homepage.
    """
    def get(self):
        """
        Renders the homepage template.
        """
        return render_template('index.html')
