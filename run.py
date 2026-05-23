<<<<<<< HEAD
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import redirect, url_for

app = create_app()

# Redirect root URL to login
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True)
=======
import os

from app import create_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
>>>>>>> 97de5e1540905497f4b5c931e91c6ee8dc690f79
