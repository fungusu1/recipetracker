import os
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify
# from models import db
from models import db, Recipe, RecipeIngredient, Instruction, BaseIngredient, User



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

@app.route('/api/base_ingredients', methods=['POST'])
def add_base_ingredient():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify(error="Name is required"), 400

    unit = data.get('default_unit')
    bi = BaseIngredient(name=name, default_unit=unit)
    db.session.add(bi)
    db.session.commit()

    # return the new ingredient so JS can append it
    return jsonify(id=bi.id, name=bi.name, default_unit=bi.default_unit), 201

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
    db.session.add(recipe)
    db.session.flush()  # assign recipe.id without commit

    # ingredients
    for ing_id, qty in zip(request.form.getlist('ingredient_id'),
                           request.form.getlist('quantity')):
        if ing_id and qty.strip():
            ri = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=int(ing_id),
                quantity=qty.strip()
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
