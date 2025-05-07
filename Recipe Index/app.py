import os
from flask import Flask, render_template, send_from_directory
from models import db, User, Recipe, BaseIngredient, RecipeIngredient
from collections import defaultdict

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

    # Find all recipes that have at least one of the selected ingredients
    recipe_ids_with_any = set()
    if selected_ingredient_ids:
        recipe_ids_with_any = set(
            ri.recipe_id for ri in RecipeIngredient.query.filter(RecipeIngredient.ingredient_id.in_(selected_ingredient_ids)).all()
        )

    # Find all recipes with 2 or fewer ingredients
    recipes_with_few_ingredients = set(
        r.id for r in Recipe.query.all() if len(r.ingredients) <= 2
    )

    if selected_ingredient_ids:
        # Show recipes that have at least have 2 or fewer ingredients
        final_recipe_ids = recipe_ids_with_any.union(recipes_with_few_ingredients)
        query = Recipe.query.filter(Recipe.id.in_(final_recipe_ids))
    else:
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
        print("Selected ingredients:", selected_ingredient_names)
        for recipe in recipes:
            recipe_ingredient_names = [ri.ingredient.name for ri in recipe.ingredients]
            missing = [name for name in recipe_ingredient_names if name not in set(selected_ingredient_names)]
            print(f"Recipe: {recipe.name}, Ingredients: {recipe_ingredient_names}, Missing: {missing}")
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
                print(f"Recipe: {recipe.name}, Ingredient: {ing_name}, Required: {required}, User has: {user_has}, Missing: {missing_amt} {ri.ingredient.default_unit}")
        recipe_missing_amounts[recipe.id] = missing

    return render_template(
        'Browser.html',
        recipes=recipes,
        ingredients=all_ingredients,
        ingredient_units=ingredient_units,
        selected_ingredients=ingredients,
        selected_servings=servings,
        selected_sort=sort,
        recipe_missing_ingredients=recipe_missing_ingredients,
        recipe_missing_amounts=recipe_missing_amounts
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
