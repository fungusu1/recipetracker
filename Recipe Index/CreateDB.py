from app import app
from models import db, User, BaseIngredient, Recipe, RecipeIngredient, Instruction, RecipeImage

# Initialize and create the database
with app.app_context():
    # Clear existing data and create tables
    db.drop_all()
    db.create_all()

    # Create a user
    user = User(
        email="baker@example.com",
        password="baking123",
        display_name="Master Baker"
    )
    db.session.add(user)
    db.session.commit()

    # Create base ingredients
    base_ingredients = [
        BaseIngredient(name="All-purpose flour", default_unit="g"),
        BaseIngredient(name="Granulated sugar", default_unit="g"),
        BaseIngredient(name="Brown sugar", default_unit="g"),
        BaseIngredient(name="Butter", default_unit="g"),
        BaseIngredient(name="Eggs", default_unit="quantity"),
        BaseIngredient(name="Milk", default_unit="mL"),
        BaseIngredient(name="Vanilla extract", default_unit="mL"),
        BaseIngredient(name="Baking powder", default_unit="g"),
        BaseIngredient(name="Baking soda", default_unit="g"),
        BaseIngredient(name="Salt", default_unit="g"),
        BaseIngredient(name="Chocolate chips", default_unit="g"),
        BaseIngredient(name="Cocoa powder", default_unit="g"),
        BaseIngredient(name="Vegetable oil", default_unit="mL"),
        BaseIngredient(name="Cinnamon", default_unit="g"),
        BaseIngredient(name="Nutmeg", default_unit="g"),
        BaseIngredient(name="Yeast", default_unit="g"),
        BaseIngredient(name="Honey", default_unit="mL"),
        BaseIngredient(name="Maple syrup", default_unit="mL"),
        BaseIngredient(name="Powdered sugar", default_unit="g"),
        BaseIngredient(name="Cream cheese", default_unit="g"),
        BaseIngredient(name="Pasta", default_unit="g"),
        BaseIngredient(name="Lettuce", default_unit="g"),
        BaseIngredient(name="Carrots", default_unit="g"),
        BaseIngredient(name="Chicken", default_unit="g"),
        BaseIngredient(name="Broth", default_unit="mL"),
        BaseIngredient(name="Strawberries", default_unit="g"),
        BaseIngredient(name="Whipped Cream", default_unit="g")
    ]
    db.session.add_all(base_ingredients)
    db.session.commit()

    #Create Chocolate Chip Cookies recipe
    cookies = Recipe(
        name="Classic Chocolate Chip Cookies",
        description="Delicious homemade chocolate chip cookies that are soft on the inside and crispy on the outside.",
        cook_time=25,
        servings=24,
        user_id=user.id
    )
    db.session.add(cookies)
    db.session.commit()

    # Add ingredients for cookies
    cookie_ingredients = [
        RecipeIngredient(recipe_id=cookies.id, ingredient_id=1, quantity="250"),  #flour
        RecipeIngredient(recipe_id=cookies.id, ingredient_id=2, quantity="200"),  #sugar
        RecipeIngredient(recipe_id=cookies.id, ingredient_id=4, quantity="225"),  #butter
        RecipeIngredient(recipe_id=cookies.id, ingredient_id=5, quantity="2"),    #eggs
        RecipeIngredient(recipe_id=cookies.id, ingredient_id=7, quantity="5"),    #vanilla
        RecipeIngredient(recipe_id=cookies.id, ingredient_id=8, quantity="5"),    #baking powder
        RecipeIngredient(recipe_id=cookies.id, ingredient_id=10, quantity="2"),   #salt
        RecipeIngredient(recipe_id=cookies.id, ingredient_id=11, quantity="300")  #chocolate chips
    ]
    db.session.add_all(cookie_ingredients)

    # Add instructions for cookies
    cookie_instructions = [
        Instruction(recipe_id=cookies.id, step_number=1, content="Preheat oven to 350°F (175°C)."),
        Instruction(recipe_id=cookies.id, step_number=2, content="Cream together butter and sugar until light and fluffy."),
        Instruction(recipe_id=cookies.id, step_number=3, content="Beat in eggs one at a time, then stir in vanilla."),
        Instruction(recipe_id=cookies.id, step_number=4, content="Combine flour, baking powder, and salt; gradually stir into the creamed mixture."),
        Instruction(recipe_id=cookies.id, step_number=5, content="Fold in chocolate chips."),
        Instruction(recipe_id=cookies.id, step_number=6, content="Drop by rounded tablespoonfuls onto ungreased baking sheets."),
        Instruction(recipe_id=cookies.id, step_number=7, content="Bake for 10-12 minutes until edges are golden brown.")
    ]
    db.session.add_all(cookie_instructions)

    # Create Banana Bread recipe
    banana_bread = Recipe(
        name="Classic Banana Bread",
        description="Moist and delicious banana bread that's perfect for breakfast or as a snack.",
        cook_time=60,
        servings=12,
        user_id=user.id
    )
    db.session.add(banana_bread)
    db.session.commit()

    # ingredients for banana bread
    banana_ingredients = [
        RecipeIngredient(recipe_id=banana_bread.id, ingredient_id=1, quantity="250"),  #flour
        RecipeIngredient(recipe_id=banana_bread.id, ingredient_id=2, quantity="200"),  #sugar
        RecipeIngredient(recipe_id=banana_bread.id, ingredient_id=4, quantity="115"),  #butter
        RecipeIngredient(recipe_id=banana_bread.id, ingredient_id=5, quantity="2"),    #eggs
        RecipeIngredient(recipe_id=banana_bread.id, ingredient_id=6, quantity="60"),   #milk
        RecipeIngredient(recipe_id=banana_bread.id, ingredient_id=8, quantity="5"),    #baking powder
        RecipeIngredient(recipe_id=banana_bread.id, ingredient_id=10, quantity="2"),   #salt
        RecipeIngredient(recipe_id=banana_bread.id, ingredient_id=14, quantity="2")    #cinnamon
    ]
    db.session.add_all(banana_ingredients)

    #instructions for banana bread
    banana_instructions = [
        Instruction(recipe_id=banana_bread.id, step_number=1, content="Preheat oven to 350°F (175°C). Grease a 9x5 inch loaf pan."),
        Instruction(recipe_id=banana_bread.id, step_number=2, content="In a large bowl, cream together butter and sugar until light and fluffy."),
        Instruction(recipe_id=banana_bread.id, step_number=3, content="Beat in eggs one at a time, then stir in milk and mashed bananas."),
        Instruction(recipe_id=banana_bread.id, step_number=4, content="Combine flour, baking powder, salt, and cinnamon; stir into the banana mixture."),
        Instruction(recipe_id=banana_bread.id, step_number=5, content="Pour batter into prepared loaf pan."),
        Instruction(recipe_id=banana_bread.id, step_number=6, content="Bake for 60 minutes, or until a toothpick inserted into the center comes out clean.")
    ]
    db.session.add_all(banana_instructions)

    # Add 5 more recipes
    additional_recipes = [
        Recipe(name="Quick Pasta", description="A simple and quick pasta dish.", cook_time=15, servings=2, user_id=user.id),
        Recipe(name="Simple Salad", description="A refreshing and easy salad.", cook_time=10, servings=1, user_id=user.id),
        Recipe(name="Easy Stir Fry", description="A quick and delicious stir fry.", cook_time=20, servings=3, user_id=user.id),
        Recipe(name="Basic Soup", description="A comforting and simple soup.", cook_time=30, servings=4, user_id=user.id),
        Recipe(name="Simple Dessert", description="A sweet and easy dessert.", cook_time=25, servings=6, user_id=user.id)
    ]
    db.session.add_all(additional_recipes)
    db.session.commit()

    for recipe in additional_recipes:
        if recipe.name == "Quick Pasta":
            recipe_ingredients = [
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=21, quantity="200"),  #Pasta
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=24, quantity="100"),  #Chicken
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=25, quantity="50")    #Broth
            ]
        elif recipe.name == "Simple Salad":
            recipe_ingredients = [
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=22, quantity="100"),  #Lettuce
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=23, quantity="50"),   #Carrots
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=27, quantity="30")    #Whipped Cream
            ]
        elif recipe.name == "Easy Stir Fry":
            recipe_ingredients = [
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=23, quantity="100"),  #Carrots
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=24, quantity="150"),  #Chicken
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=13, quantity="30")    #Vegetable oil
            ]
        elif recipe.name == "Basic Soup":
            recipe_ingredients = [
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=25, quantity="200"),  #Broth
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=23, quantity="50"),   #Carrots
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=24, quantity="100")   #Chicken
            ]
        elif recipe.name == "Simple Dessert":
            recipe_ingredients = [
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=26, quantity="100"),  #Strawberries
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=27, quantity="50"),   #Whipped Cream
                RecipeIngredient(recipe_id=recipe.id, ingredient_id=2, quantity="30")     #Granulated sugar
            ]
        db.session.add_all(recipe_ingredients)
        #placeholder instruction
        instruction = Instruction(recipe_id=recipe.id, step_number=1, content="Instruction 1")
        db.session.add(instruction)
    db.session.commit()
    print("✅ Database created successfully!")

#This file will create a db with the tables written in models.py, you can add data to test out your code in here.
