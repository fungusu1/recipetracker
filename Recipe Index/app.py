import os
from flask import Flask, render_template, send_from_directory
from models import db

app = Flask(__name__, template_folder='html')
base_dir = os.path.abspath(os.path.dirname(__file__))

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

#Auto-correcting CSS, JS and Images routing
@app.route('/css/<path:filename>')
def css(filename):
    return send_from_directory('css', filename)

@app.route('/js/<path:filename>')
def js(filename):
    return send_from_directory('js', filename)

@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('images', filename)

#Page Routing
@app.route('/')
def homepage():
    return render_template('HomePage.html')

@app.route('/create')
def create():
    return render_template('CreateRecipe.html')

@app.route('/browse')
def browse():
    return render_template('Browser.html')

@app.route('/recipe')
def view_recipe():
    return render_template('ViewRecipe.html')

@app.route('/profile')
def profile():
    return render_template('ProfilePage.html')

@app.route('/login')
def login():
    return render_template('Login.html')

@app.route('/signup')
def signup():
    return render_template('SignUp.html')

#Run Server
if __name__ == '__main__':
    app.run(debug=True)
