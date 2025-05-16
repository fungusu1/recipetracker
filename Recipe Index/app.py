import os
from flask import Flask, render_template, send_from_directory, redirect, url_for, request, jsonify, session, flash, get_flashed_messages
from models import db, User, Recipe, RecipeIngredient, RecipeImage, Instruction, BaseIngredient, Rating
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import SignUpForm, LoginForm
from datetime import datetime

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
#========================================================================================================================================
#========================================================================================================================================
@app.route('/')
def homepage():

    # Get top 3 chefs (based on # of recipes)
    top_chefs = (
        db.session.query(User)
        .options(joinedload(User.profile_image))
        .join(Recipe)
        .group_by(User.id)
        .order_by(func.count(Recipe.id).desc())
        .limit(3)
        .all()
    )

    # Get top 3 recipes (based on highest avg ratings)
    top_recipes = (
        db.session.query(Recipe)
        .join(Rating)
        .options(
            joinedload(Recipe.user)                     # Recipe → user  (JOIN)
            .joinedload(User.profile_image)             # user  → image (JOIN)
        )   
        .group_by(Recipe.id)
        .order_by(func.avg(Rating.rating).desc(),
                    func.count(Rating.id).desc(),
                    func.max(Rating.created_at).desc()
        )
        .limit(3)
        .all()
    )

    # Get the 3/5 latest recipes
    latest_reviews = (
        db.session.query(Rating, User, Recipe)
        .join(User, Rating.user_id == User.id)
        .join(Recipe, Rating.recipe_id == Recipe.id)
        .options(joinedload(User.profile_image))
        .order_by(Rating.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template('HomePage.html', top_chefs=top_chefs, top_recipes=top_recipes, latest_reviews=latest_reviews)

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

#========================================================================================================================================
#========================================================================================================================================
@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        base_ingredients = BaseIngredient.query.order_by(BaseIngredient.name).all()
        ingredient_units = {bi.name: bi.default_unit or '' for bi in base_ingredients}
        return render_template('CreateRecipe.html', base_ingredients=base_ingredients, ingredient_units=ingredient_units)

    # POST: parse and save the new recipe
    name        = request.form['title']
    description = request.form.get('description', '')
    cook_time   = int(request.form['cook_time'])
    servings    = int(request.form['servings'])

    # Map privacy radio button to access_level
    privacy_str = request.form.get('privacy', 'public')
    privacy_map = {'public': 0, 'private': 1, 'shared': 2}
    access_level = privacy_map.get(privacy_str, 0)

    # Use current_user instead of querying for a default user
    user = current_user

    # create Recipe
    recipe = Recipe(
        name=name,
        description=description,
        cook_time=cook_time,
        servings=servings,
        user_id=user.id,
        access_level=access_level
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

    # After db.session.commit() for the recipe
    shared_user_ids = request.form.get('shared_user_ids', '')
    if access_level == 2 and shared_user_ids:
        user_ids = [int(uid) for uid in shared_user_ids.split(',') if uid]
        recipe.shared_with_ids = str(user_ids)

    db.session.commit()
    return redirect(url_for('view_recipe', id=recipe.id))

@app.route('/api/find_user', methods=['POST'])
@login_required
def find_user():
    data = request.get_json() or {}
    display_name = (data.get('display_name') or '').strip()
    if not display_name:
        return jsonify(error="Display name required"), 400
    user = User.query.filter(func.lower(User.display_name) == display_name.lower()).first()
    if not user:
        return jsonify(error="User not found"), 404
    return jsonify(id=user.id, display_name=user.display_name)

#========================================================================================================================================
#========================================================================================================================================
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

    # Only show public recipes (access_level == 0)
    query = query.filter(Recipe.access_level == 0)

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
        partials = []
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
                missing_item = {
                    'name': ing_name,
                    'amount': f"{missing_amt:g} {ri.ingredient.default_unit}",
                    'partial': (user_has > 0)
                }
                if user_has > 0:
                    partials.append(missing_item)
                else:
                    missing.append(missing_item)
        # Put partials at the top
        recipe_missing_amounts[recipe.id] = partials + missing

    filtered_recipes = []
    filtered_missing_ingredients = {}
    filtered_missing_amounts = {}

    for recipe in recipes:
        missing = recipe_missing_ingredients.get(recipe.id, [])
        # Show recipes with up to 5 missing ingredients
        if len(missing) <= 5:
            filtered_recipes.append(recipe)
            filtered_missing_ingredients[recipe.id] = missing
            # For the browser card, only show the first 4, and a flag if more
            missing_amounts = recipe_missing_amounts.get(recipe.id, [])
            filtered_missing_amounts[recipe.id] = {
                'list': missing_amounts[:4],
                'more': len(missing_amounts) > 4
            }

    recipe_images = {}
    for recipe in filtered_recipes:
        if recipe.images and len(recipe.images) > 0:
            recipe_images[recipe.id] = recipe.images[0].image_url
        else:
            recipe_images[recipe.id] = url_for('images', filename='no-image-available-icon-vector.jpg')

    # Apply main sort first (already done above)
    # Now sort by main sort, then missing count, then rating
    def main_sort_key(recipe):
        if sort == 'cook-time-asc':
            return recipe.cook_time
        elif sort == 'cook-time-desc':
            return -recipe.cook_time
        elif sort == 'quantity-desc':
            return -recipe.servings
        elif sort == 'quantity-asc':
            return recipe.servings
        else:
            return recipe.cook_time
    def missing_count(recipe):
        missing = filtered_missing_ingredients.get(recipe.id, [])
        return len(missing)
    def rating(recipe):
        return getattr(recipe, 'average_rating', 0) or 0
    filtered_recipes.sort(key=lambda r: (main_sort_key(r), missing_count(r), -rating(r)))

    # Pagination for recipe previews
    page = int(request.args.get('page', 1))
    per_page = 40
    start = (page - 1) * per_page
    end = start + per_page
    paginated_recipes = filtered_recipes[start:end]
    show_more = end < len(filtered_recipes)

    return render_template(
        'Browser.html',
        recipes=paginated_recipes,
        ingredients=all_ingredients,
        ingredient_units=ingredient_units,
        selected_ingredients=ingredients,
        selected_servings=servings,
        selected_sort=sort,
        recipe_missing_ingredients=filtered_missing_ingredients,
        recipe_missing_amounts=filtered_missing_amounts,
        recipe_images=recipe_images,
        show_more=show_more,
        next_page=page+1 if show_more else None
    )
@app.route('/browse/load_more')
def browse_load_more():
    ingredients = request.args.getlist('ingredient[]')
    servings = request.args.getlist('servings[]')
    sort = request.args.get('sort', type=str)
    page = int(request.args.get('page', 1))
    per_page = 40
    # (reuse all filtering/sorting logic from /browse)
    # ... (copy logic from /browse up to filtered_recipes)
    all_ingredients = BaseIngredient.query.order_by(BaseIngredient.name).all()
    ingredient_units = {ing.name: ing.default_unit for ing in all_ingredients}
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
    # Only show public recipes (access_level == 0)
    query = query.filter(Recipe.access_level == 0)
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
        partials = []
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
                missing_item = {
                    'name': ing_name,
                    'amount': f"{missing_amt:g} {ri.ingredient.default_unit}",
                    'partial': (user_has > 0)
                }
                if user_has > 0:
                    partials.append(missing_item)
                else:
                    missing.append(missing_item)
        recipe_missing_amounts[recipe.id] = partials + missing
    filtered_recipes = []
    filtered_missing_ingredients = {}
    filtered_missing_amounts = {}
    for recipe in recipes:
        missing = recipe_missing_ingredients.get(recipe.id, [])
        if len(missing) <= 5:
            filtered_recipes.append(recipe)
            filtered_missing_ingredients[recipe.id] = missing
            missing_amounts = recipe_missing_amounts.get(recipe.id, [])
            filtered_missing_amounts[recipe.id] = {
                'list': missing_amounts[:4],
                'more': len(missing_amounts) > 4
            }
    def main_sort_key(recipe):
        if sort == 'cook-time-asc':
            return recipe.cook_time
        elif sort == 'cook-time-desc':
            return -recipe.cook_time
        elif sort == 'quantity-desc':
            return -recipe.servings
        elif sort == 'quantity-asc':
            return recipe.servings
        else:
            return recipe.cook_time
    def missing_count(recipe):
        missing = filtered_missing_ingredients.get(recipe.id, [])
        return len(missing)
    def rating(recipe):
        return getattr(recipe, 'average_rating', 0) or 0
    filtered_recipes.sort(key=lambda r: (main_sort_key(r), missing_count(r), -rating(r)))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_recipes = filtered_recipes[start:end]
    show_more = end < len(filtered_recipes)
    recipe_images = {}
    for recipe in paginated_recipes:
        if recipe.images and len(recipe.images) > 0:
            recipe_images[recipe.id] = recipe.images[0].image_url
        else:
            recipe_images[recipe.id] = url_for('images', filename='no-image-available-icon-vector.jpg')
    html = render_template('RecipeCards.html',
        recipes=paginated_recipes,
        recipe_images=recipe_images,
        recipe_missing_ingredients=filtered_missing_ingredients,
        recipe_missing_amounts=filtered_missing_amounts,
        selected_ingredients=ingredients
    )
    return jsonify({'html': html, 'show_more': show_more, 'next_page': page+1 if show_more else None})

#========================================================================================================================================
#========================================================================================================================================
@app.route('/recipe')
def view_recipe():
    recipe_id = request.args.get('id')
    if not recipe_id:
        return redirect(url_for('browse'))
    
    recipe = Recipe.query.get_or_404(recipe_id)

    # Privacy logic
    if recipe.access_level == 1:
        # Private: only author
        if not current_user.is_authenticated or current_user.id != recipe.user_id:
            flash('You do not have permission to view this recipe.', 'error')
            return redirect(url_for('homepage'))
    elif recipe.access_level == 2:
        # Shared: only author and shared users
        allowed_ids = []
        try:
            import ast
            allowed_ids = ast.literal_eval(recipe.shared_with_ids) if recipe.shared_with_ids else []
        except Exception:
            allowed_ids = []
        if not current_user.is_authenticated or (current_user.id != recipe.user_id and current_user.id not in allowed_ids):
            flash('You do not have permission to view this recipe.', 'error')
            return redirect(url_for('homepage'))

    recipe.view_count += 1
    db.session.commit()
    
    return render_template('ViewRecipe.html', recipe=recipe)

@app.route('/api/recipes/<int:recipe_id>')
def get_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # Privacy logic for API
    if recipe.access_level == 1:
        if not current_user.is_authenticated or current_user.id != recipe.user_id:
            return jsonify({'error': 'You do not have permission to view this recipe.'}), 403
    elif recipe.access_level == 2:
        allowed_ids = []
        try:
            import ast
            allowed_ids = ast.literal_eval(recipe.shared_with_ids) if recipe.shared_with_ids else []
        except Exception:
            allowed_ids = []
        if not current_user.is_authenticated or (current_user.id != recipe.user_id and current_user.id not in allowed_ids):
            return jsonify({'error': 'You do not have permission to view this recipe.'}), 403
    author = recipe.user
    # Try to get profile image
    profile_pic_url = None
    if hasattr(author, "profile_image") and author.profile_image and author.profile_image.image_url:
        profile_pic_url = author.profile_image.image_url
    else:
        profile_pic_url = "/images/profile_placeholder.jpg"

    def get_user_profile_pic(user):
        if hasattr(user, "profile_image") and user.profile_image and user.profile_image.image_url:
            return user.profile_image.image_url
        return "/images/profile_placeholder.jpg"

    return jsonify({
        'id': recipe.id,
        'title': recipe.name,
        'description': recipe.description,
        'cook_time': recipe.cook_time,
        'servings': recipe.servings,
        'privacy': recipe.access_level,
        'view_count': recipe.view_count,
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
                'comment': rating.review or '',
                'created_at': rating.created_at.strftime('%Y-%m-%d'),
                'user': {
                    'id': rating.user.id,
                    'display_name': rating.user.display_name,
                    'profile_pic_url': get_user_profile_pic(rating.user)
                }
            }
            for rating in recipe.ratings
        ],
        'author': {
            'id': author.id,
            'name': author.display_name,
            'profile_pic_url': profile_pic_url
        },
        'current_user_id': (current_user.id if current_user.is_authenticated else None)
    })

@app.route('/api/recipes/<int:recipe_id>/reviews', methods=['POST'])
@login_required
def add_review(recipe_id):
    data = request.get_json()
    rating = int(data.get('rating', 0))
    comment = data.get('comment', '').strip()
    if not (1 <= rating <= 5):
        return jsonify({'error': 'Invalid rating'}), 400
    if not comment:
        return jsonify({'error': 'Review text required'}), 400

    # Prevent duplicate review by the same user for the same recipe
    existing = Rating.query.filter_by(recipe_id=recipe_id, user_id=current_user.id).first()
    if existing:
        return jsonify({'error': 'You have already reviewed this recipe.'}), 400

    review = Rating(
        recipe_id=recipe_id,
        user_id=current_user.id,
        rating=rating,
        review=comment,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(review)
    db.session.commit()

    # Return the new review in the same format as your GET endpoint
    user = current_user
    profile_pic_url = user.profile_image.image_url if hasattr(user, "profile_image") and user.profile_image and user.profile_image.image_url else "/images/profile_placeholder.jpg"
    return jsonify({
        'rating': review.rating,
        'comment': review.review,
        'created_at': review.created_at.strftime('%Y-%m-%d'),
        'user': {
            'id': user.id,
            'display_name': user.display_name,
            'profile_pic_url': profile_pic_url
        }
    }), 201

#========================================================================================================================================
#========================================================================================================================================
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
    
    # Filter recipes based on privacy settings
    if current_user.is_authenticated and current_user.id == user.id:
        # Show all recipes to the owner
        recipes = query.all()
    else:
        # For other users, only show public recipes or shared recipes
        recipes = []
        for recipe in query.all():
            if recipe.access_level == 0:  # Public
                recipes.append(recipe)
            elif recipe.access_level == 2 and current_user.is_authenticated:  # Shared
                try:
                    shared_ids = eval(recipe.shared_with_ids) if recipe.shared_with_ids else []
                    if current_user.id in shared_ids:
                        recipes.append(recipe)
                except:
                    pass
    
    # Apply sorting
    if sort == 'rating':
        recipes = sorted(recipes, key=lambda r: r.average_rating, reverse=True)
    elif sort == 'cook-time':
        recipes = sorted(recipes, key=lambda r: r.cook_time)
    elif sort == 'quantity':
        recipes = sorted(recipes, key=lambda r: r.servings, reverse=True)
    else: #alphabetical
        recipes = sorted(recipes, key=lambda r: r.name)
        
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

#========================================================================================================================================
#========================================================================================================================================
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

#========================================================================================================================================
#========================================================================================================================================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out ;(', 'logout')
    return redirect(url_for('homepage'))

#========================================================================================================================================
#========================================================================================================================================
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

#========================================================================================================================================
#========================================================================================================================================
@app.route('/search')
def search():
    query = request.args.get('q', '').strip()

    # build a single filter for public (0) or shared-with-you (2 + your ID)
    access_filter = Recipe.access_level == 0
    if current_user.is_authenticated:
        access_filter = (
            access_filter
            | (
                (Recipe.access_level == 2)
                & Recipe.shared_with_ids.ilike(f'%"{current_user.id}"%')
            )
        )
    recipes = (
        Recipe.query
              .filter(
                  Recipe.name.ilike(f'%{query}%'),
                  access_filter
              )
              .order_by(Recipe.cook_time.asc())
              .all()
    )
    recipe_images = {
        r.id: (
            r.images[0].image_url
            if r.images
            else url_for('images', filename='no-image-available-icon-vector.jpg')
        )
        for r in recipes
    }
    return render_template(
        'SearchResults.html',
        query=query,
        recipes=recipes,
        recipe_images=recipe_images
    )

#========================================================================================================================================
#========================================================================================================================================
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    if recipe.user_id != current_user.id:
        flash('You do not have permission to edit this recipe.', 'error')
        return redirect(url_for('view_recipe', id=id))

    base_ingredients = BaseIngredient.query.order_by(BaseIngredient.name).all()
    ingredient_units = {bi.name: bi.default_unit or '' for bi in base_ingredients}

    if request.method == 'GET':
        # Prepare shared user display names if shared
        shared_users = []
        if recipe.access_level == 2 and recipe.shared_with_ids:
            import ast
            user_ids = ast.literal_eval(recipe.shared_with_ids)
            shared_users = User.query.filter(User.id.in_(user_ids)).all()
        return render_template(
            'EditRecipe.html',
            recipe=recipe,
            base_ingredients=base_ingredients,
            ingredient_units=ingredient_units,
            shared_users=shared_users
        )

    # POST: update the recipe
    recipe.name = request.form['title']
    recipe.description = request.form.get('description', '')
    recipe.cook_time = int(request.form['cook_time'])
    recipe.servings = int(request.form['servings'])

    privacy_str = request.form.get('privacy', 'public')
    privacy_map = {'public': 0, 'private': 1, 'shared': 2}
    access_level = privacy_map.get(privacy_str, 0)
    recipe.access_level = access_level

    # Handle image upload (replace old image if new one is uploaded)
    files = request.files.getlist('images')
    upload_folder = app.config['UPLOAD_FOLDER']
    if files and files[0] and files[0].filename:
        # Remove old images
        for img in recipe.images:
            try:
                os.remove(os.path.join(app.root_path, img.image_url.replace('/images/', 'images/')))
            except Exception:
                pass
            db.session.delete(img)
        for f in files:
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                save_path = os.path.join(upload_folder, filename)
                f.save(save_path)
                image_url = url_for('images', filename=filename)
                img = RecipeImage(recipe_id=recipe.id, image_url=image_url)
                db.session.add(img)

    # Update ingredients
    RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
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

    # Update instructions
    Instruction.query.filter_by(recipe_id=recipe.id).delete()
    for i, step in enumerate(request.form.getlist('instructions'), start=1):
        if step.strip():
            inst = Instruction(
                recipe_id=recipe.id,
                step_number=i,
                content=step.strip()
            )
            db.session.add(inst)

    # Update shared users
    shared_user_ids = request.form.get('shared_user_ids', '')
    if access_level == 2 and shared_user_ids:
        user_ids = [int(uid) for uid in shared_user_ids.split(',') if uid]
        recipe.shared_with_ids = str(user_ids)
    else:
        recipe.shared_with_ids = None

    db.session.commit()
    return redirect(url_for('view_recipe', id=recipe.id))

#Run Server
if __name__ == '__main__':
    app.run(debug=True)
