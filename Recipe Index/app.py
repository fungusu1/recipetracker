import os
from flask import Flask, render_template, send_from_directory, redirect, url_for, request, jsonify, session, flash
from models import db, User, Recipe, RecipeIngredient, RecipeImage, Instruction, BaseIngredient
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename, generate_password_hash, check_password_hash
from sqlalchemy import func
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import SignUpForm, LoginForm


app = Flask(__name__, template_folder='html')
base_dir = os.path.abspath(os.path.dirname(__file__))

# Set a secret key (session management)
app.config['SECRET_KEY'] = 'super_duper_secret_key'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define a default image upload location
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'images')

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
    return render_template('HomePage.html')

@app.route('/api/base_ingredients', methods=['POST'])
def add_base_ingredient():
    data = request.get_json() or {}
    raw_name = (data.get('name') or '').strip()
    if not raw_name:
        return jsonify(error="Name is required"), 400
    
    # turn the name to title case
    normalized = raw_name.title()

    # look for any existing ingredient with the same lowercase name
    existing = BaseIngredient.query \
        .filter(func.lower(BaseIngredient.name) == normalized.lower()) \
        .first()

    # if there is one just reuse the same entry
    if existing:
        return jsonify(error=f"‘{normalized}’ already exists"), 409

    # otherwise create a new one
    bi = BaseIngredient(
        name=normalized,
        default_unit=(data.get('default_unit') or '').strip() or None
    )
    db.session.add(bi)
    db.session.commit()

    return jsonify(id=bi.id,
                name=bi.name,
                default_unit=bi.default_unit), 201

# Check if an upload is an allowed filetype
ALLOWED_EXTENSIONS = {'png','jpg','jpeg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create', methods=['GET', 'POST'])
def create():
    # return render_template('CreateRecipe.html')
    if request.method == 'GET':
        # fetch base ingredients for the dropdown
        base_ingredients = BaseIngredient.query.order_by(BaseIngredient.name).all()
        return render_template('CreateRecipe.html', base_ingredients=base_ingredients)

    # POST: parse and save the new recipe
    name        = request.form['title']
    description = request.form.get('description', '')
    cook_time   = int(request.form['cook_time'])
    servings    = int(request.form['servings'])

    # TEMPORARY CHANGE UNTIL LOGINS ARE IMPLEMENTED
    user = User.query.first()
    if not user:
        user = User(
            email='default@example.com',
            password='changeme', 
            display_name='Default User'
        )

    db.session.add(user)
    db.session.commit()  # now user.id exists

    # create Recipe
    recipe = Recipe(
        name=name,
        description=description,
        cook_time=cook_time,
        servings=servings,
        user_id=user.id
    )

    # add recipe to the DB
    db.session.add(recipe)
    db.session.flush()  # assign recipe.id without commit

    # add images to the recipe
    files = request.files.getlist('images')
    upload_folder = app.config['UPLOAD_FOLDER']  # e.g. 'static/uploads'
    for f in files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            save_path = os.path.join(upload_folder, filename)
            f.save(save_path)
            # assume you serve via '/static/uploads/...'
            image_url = url_for('images', filename=filename)
            img = RecipeImage(recipe_id=recipe.id, image_url=image_url)
            db.session.add(img)

    # ingredients
    for name, qty in zip(
    request.form.getlist('ingredient_name'),
    request.form.getlist('quantity')
    ):
        name = name.strip()
        qty  = qty.strip()
        if not name or not qty:
            continue

        base = BaseIngredient.query.filter_by(name=name).first()
        if not base:
            continue

        ri = RecipeIngredient(
            recipe_id     = recipe.id,
            ingredient_id = base.id,
            quantity      = qty
        )
        db.session.add(ri)

    # instructions
    for i, step in enumerate(request.form.getlist('instructions'), start=1):
        if step.strip():
            inst = Instruction(
                recipe_id=recipe.id,
                step_number=i,
                content=step.strip()
            )
            db.session.add(inst)

    db.session.commit()
    # temporary redirect to index until view page is ready
    return redirect(url_for('homepage'))

@app.route('/browse')
def browse():
    return render_template('Browser.html')

@app.route('/recipe')
def view_recipe():
    return render_template('ViewRecipe.html')

@app.route('/profile')
@login_required
def profile():
    flash(f'Welcome back, {current_user.display_name}', 'greeting')
    return render_template('ProfilePage.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Successfully logged in.', 'success')
            return redirect(url_for('profile'))
        flash('Invalid email or password', 'error')
    return render_template('Login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out ;(', 'logout')
    return redirect(url_for('homepage'))

@app.route('/signup')
def signup():
    return render_template('SignUp.html')

#Run Server
if __name__ == '__main__':
    app.run(debug=True)
