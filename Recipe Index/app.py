import os
from flask import Flask, render_template, send_from_directory, redirect, url_for, request, session, flash
from models import db, User
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import SignUpForm, LoginForm


app = Flask(__name__, template_folder='html')
base_dir = os.path.abspath(os.path.dirname(__file__))

# Set a secret key (session management)
app.config['SECRET_KEY'] = 'super_duper_secret_key'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Function to load users
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
    print("Flas is running")
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
@login_required
def profile():
    return render_template('ProfilePage.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Successfully logged in.')
            return redirect(url_for('profile'))
        flash('Invalid email or password')
    return render_template('Login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out!!!')
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('SignUp.html')

#Run Server
if __name__ == '__main__':
    app.run(debug=True)
