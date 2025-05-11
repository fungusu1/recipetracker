import sys
import random
import json
from faker import Faker
from werkzeug.security import generate_password_hash

from app import app
from models import db, User, BaseIngredient, Recipe, RecipeIngredient, Instruction, RecipeImage


def main():
    if len(sys.argv) < 2:
        print("Usage: python populate_db.py <num_recipes>")
        sys.exit(1)
    try:
        num_recipes = int(sys.argv[1])
    except ValueError:
        print("<num_recipes> must be an integer.")
        sys.exit(1)

    fake = Faker()

    with app.app_context():
        # Seed some common base ingredients
        base_list = [
            ("Flour", "g"), ("Sugar", "g"), ("Salt", "tsp"), ("Butter", "g"),
            ("Eggs", "pcs"), ("Milk", "ml"), ("Olive Oil", "ml"), ("Onion", "pcs"),
            ("Garlic", "cloves"), ("Tomato", "pcs"), ("Chicken", "g"), ("Beef", "g"),
            ("Rice", "g"), ("Pasta", "g"), ("Cheese", "g"), ("Pepper", "tsp"),
            ("Baking Powder", "tsp"), ("Vanilla Extract", "ml"), ("Cocoa Powder", "g"), ("Yeast", "g")
        ]
        for name, unit in base_list:
            if not BaseIngredient.query.filter_by(name=name).first():
                db.session.add(BaseIngredient(name=name, default_unit=unit))
        db.session.commit()

        # Create a handful of users
        num_users = min(max(1, num_recipes // 2), 10)
        users = []
        for _ in range(num_users):
            email = fake.unique.email()
            password = fake.password(length=12)
            hashed_pw = generate_password_hash(password)
            display_name = fake.name()
            user = User(email=email, password=hashed_pw, display_name=display_name)
            db.session.add(user)
            users.append(user)
        db.session.commit()

        all_ingredients = BaseIngredient.query.all()

        for i in range(num_recipes):
            # Create a recipe
            name = fake.sentence(nb_words=3).rstrip('.')
            description = fake.paragraph(nb_sentences=3)
            cook_time = random.randint(10, 180)
            servings = random.randint(1, 8)
            owner = random.choice(users)
            recipe = Recipe(
                name=name,
                description=description,
                cook_time=cook_time,
                servings=servings,
                user_id=owner.id
            )
            db.session.add(recipe)
            db.session.commit()  # assign recipe.id

            # Add ingredients
            num_ing = random.randint(3, 7)
            chosen = random.sample(all_ingredients, k=num_ing)
            for ingr in chosen:
                qty = random.randint(1, 500)
                db.session.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=ingr.id, quantity=qty))

            # Add instructions
            steps = random.randint(3, 6)
            for step in range(1, steps + 1):
                text = fake.sentence(nb_words=10)
                db.session.add(Instruction(recipe_id=recipe.id, step_number=step, content=text))

            # Add images
            imgs = random.randint(1, 3)
            for _ in range(imgs):
                url = fake.image_url(width=640, height=480)
                db.session.add(RecipeImage(recipe_id=recipe.id, image_url=url))

            db.session.commit()

        print(f"✅ Added {num_recipes} recipes (with users, ingredients, instructions, images) to the database.")


if __name__ == '__main__':
    main()
