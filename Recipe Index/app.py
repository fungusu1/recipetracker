import os
from flask import Flask, render_template, send_from_directory, redirect, url_for, request, jsonify, session, flash, get_flashed_messages
from models import db, User, Recipe, RecipeIngredient, RecipeImage, Instruction, BaseIngredient
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
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
login_manager.login_message = None

# Function to load users
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        return jsonify(error=f"'{normalized}' already exists"), 409

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

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        base_ingredients = BaseIngredient.query.order_by(BaseIngredient.name).all()
        return render_template('CreateRecipe.html', base_ingredients=base_ingredients)

    # POST: parse and save the new recipe
    name        = request.form['title']
    description = request.form.get('description', '')
    cook_time   = int(request.form['cook_time'])
    servings    = int(request.form['servings'])

    # Use current_user instead of querying for a default user
    user = current_user

    # create Recipe
    recipe = Recipe(
        name=name,
        description=description,
        cook_time=cook_time,
        servings=servings,
        user_id=user.id
    )
    db.session.add(recipe)
    db.session.flush()  # assign recipe.id without commit

    # add images to the recipe
    files = request.files.getlist('images')
    upload_folder = app.config['UPLOAD_FOLDER']
    for f in files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            save_path = os.path.join(upload_folder, filename)
            f.save(save_path)
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
            recipe_id=recipe.id,
            ingredient_id=base.id,
            quantity=qty
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
    return redirect(url_for('homepage'))

@app.route('/browse')
def browse():
    ingredients = request.args.getlist('ingredient[]')
    servings = request.args.getlist('servings[]')
    sort = request.args.get('sort', type=str)

    all_ingredients = BaseIngredient.query.order_by(BaseIngredient.name).all()
    ingredient_units = {ing.name: ing.default_unit for ing in all_ingredients}

    # Get ingredient IDs for selected ingredients
    selected_ingredient_ids = []
    selected_ingredient_names = []
    for ingredient in ingredients:
        if not ingredient:
            continue
        base_ingredient = BaseIngredient.query.filter(BaseIngredient.name == ingredient).first()
        if base_ingredient:
            selected_ingredient_ids.append(base_ingredient.id)
            selected_ingredient_names.append(base_ingredient.name)

    recipe_ids_with_any = set()
    if selected_ingredient_ids:
        recipe_ids_with_any = set(
            ri.recipe_id for ri in RecipeIngredient.query.filter(RecipeIngredient.ingredient_id.in_(selected_ingredient_ids)).all()
        )

    query = Recipe.query

    # Sorting logic
    if sort == 'cook-time-asc':
        query = query.order_by(Recipe.cook_time.asc())
    elif sort == 'cook-time-desc':
        query = query.order_by(Recipe.cook_time.desc())
    elif sort == 'quantity-desc':
        query = query.order_by(Recipe.servings.desc())
    elif sort == 'quantity-asc':
        query = query.order_by(Recipe.servings.asc())
    else:
        query = query.order_by(Recipe.cook_time.asc())

    recipes = query.all()

    recipe_missing_ingredients = {}
    if selected_ingredient_ids:
        selected_ingredient_names_set = set(selected_ingredient_names)
        for recipe in recipes:
            recipe_ingredient_names = [ri.ingredient.name for ri in recipe.ingredients]
            missing = [name for name in recipe_ingredient_names if name not in selected_ingredient_names_set]
            recipe_missing_ingredients[recipe.id] = missing
    else:
        recipe_missing_ingredients = {}

    user_ingredient_amounts = dict(zip(ingredients, servings))

    recipe_missing_amounts = {}
    for recipe in recipes:
        missing = []
        for ri in recipe.ingredients:
            ing_name = ri.ingredient.name
            required = float(ri.quantity) if ri.quantity else 0
            if ing_name in user_ingredient_amounts:
                if user_ingredient_amounts[ing_name] in [None, '', 'None']:
                    user_has = 9999
                else:
                    user_has = float(user_ingredient_amounts[ing_name])
            else:
                user_has = 0
            if user_has < required:
                missing_amt = required - user_has
                missing.append(f"{ing_name} ({missing_amt:g} {ri.ingredient.default_unit})")
        recipe_missing_amounts[recipe.id] = missing

    filtered_recipes = []
    filtered_missing_ingredients = {}
    filtered_missing_amounts = {}

    for recipe in recipes:
        missing = recipe_missing_ingredients.get(recipe.id, [])
        if len(missing) <= 3:
            filtered_recipes.append(recipe)
            filtered_missing_ingredients[recipe.id] = missing
            filtered_missing_amounts[recipe.id] = recipe_missing_amounts.get(recipe.id, [])

    recipe_images = {}
    for recipe in filtered_recipes:
        if recipe.images and len(recipe.images) > 0:
            recipe_images[recipe.id] = recipe.images[0].image_url
        else:
            recipe_images[recipe.id] = url_for('images', filename='no-image-available-icon-vector.jpg')

    return render_template(
        'Browser.html',
        recipes=filtered_recipes,
        ingredients=all_ingredients,
        ingredient_units=ingredient_units,
        selected_ingredients=ingredients,
        selected_servings=servings,
        selected_sort=sort,
        recipe_missing_ingredients=filtered_missing_ingredients,
        recipe_missing_amounts=filtered_missing_amounts,
        recipe_images=recipe_images
    )

@app.route('/recipe')
def view_recipe():
    return render_template('ViewRecipe.html')

@app.route('/api/recipes/<int:recipe_id>')
def get_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    return jsonify({
        'id': recipe.id,
        'title': recipe.name,
        'description': recipe.description,
        'cook_time': recipe.cook_time,
        'servings': recipe.servings,
        'privacy': recipe.access_level,
        'ingredients': [
            f"{ri.quantity} {ri.ingredient.default_unit or ''} {ri.ingredient.name}"
            for ri in recipe.ingredients
        ],
        'instructions': [
            instr.content for instr in sorted(recipe.instructions, key=lambda x: x.step_number)
        ],
        'image_url': recipe.images[0].image_url if recipe.images else None,
        'reviews': [
            {
                'rating': rating.rating,
                'comment': rating.review or ''
            }
            for rating in recipe.ratings
        ]
    })


@app.route('/profile')
@login_required
def profile():
    flash(f'Welcome back, {current_user.display_name}', 'greeting')
    sort = request.args.get('sort', 'title')
    query = Recipe.query.filter_by(user_id=current_user.id)
    if sort == 'rating':
        recipes = sorted(query.all(), key=lambda r: r.average_rating, reverse=True)
    elif sort == 'cook-time':
        recipes = query.order_by(Recipe.cook_time.asc()).all()
    elif sort == 'quantity':
        recipes = query.order_by(Recipe.servings.desc()).all()
    else:  # 'title' or default
        recipes = query.order_by(Recipe.name.asc()).all()
    return render_template('ProfilePage.html', user=current_user, recipes=recipes, selected_sort=sort)

@app.route('/profile/<int:user_id>')
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    sort = request.args.get('sort', 'title')
    query = Recipe.query.filter_by(user_id=user.id)
    if sort == 'rating':
        recipes = sorted(query.all(), key=lambda r: r.average_rating, reverse=True)
    elif sort == 'cook-time':
        recipes = query.order_by(Recipe.cook_time.asc()).all()
    elif sort == 'quantity':
        recipes = query.order_by(Recipe.servings.desc()).all()
    else:  # 'title' or default
        recipes = query.order_by(Recipe.name.asc()).all()
    return render_template('ProfilePage.html', user=user, recipes=recipes, selected_sort=sort)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        new_bio = request.form.get('profile_description', '').strip()
        if new_bio:
            current_user.profile_description = new_bio
        # Handle profile image upload
        file = request.files.get('profile_image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(img_path)
            # Remove old image if exists
            if current_user.profile_image:
                old_path = current_user.profile_image.image_url
                if old_path and os.path.exists(os.path.join(app.root_path, old_path.replace('/images/', 'images/'))):
                    try:
                        os.remove(os.path.join(app.root_path, old_path.replace('/images/', 'images/')))
                    except Exception:
                        pass
                current_user.profile_image.image_url = url_for('images', filename=filename)
            else:
                from models import UserProfileImage
                db.session.add(UserProfileImage(user_id=current_user.id, image_url=url_for('images', filename=filename)))
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('EditProfile.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    # Redirect to login page from other pages requiring login
    if request.args.get("next") == "/create":
        flash("Please log in to create a recipe", "error")
    elif request.args.get("next") == "/profile":
        flash("Please log in to view your profile", "error")

    # Handle login form submission
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            get_flashed_messages()
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        # Checking if email/user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('An account with that email already exists.', 'error')
            return redirect(url_for('signup'))
    
        # Hash password
        hashed_pw = generate_password_hash(form.password.data)

        # Create user
        new_user = User(
            email=form.email.data,
            password=hashed_pw,
            display_name=form.display_name.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Great! Successfully signed up! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('SignUp.html', form=form)

#Run Server
if __name__ == '__main__':
    app.run(debug=True)
