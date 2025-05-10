import os
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify
from models import db, Recipe, RecipeIngredient, RecipeImage, Instruction, BaseIngredient, User
from werkzeug.utils import secure_filename
from sqlalchemy import func

app = Flask(__name__, template_folder='html')
base_dir = os.path.abspath(os.path.dirname(__file__))

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define a default image upload location
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'images')

# Initialize SQLAlchemy
db.init_app(app)

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

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
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
        db.session.commit()

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
