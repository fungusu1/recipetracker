
#!/usr/bin/env python3
import sys
import random
from datetime import datetime
from faker import Faker
from werkzeug.security import generate_password_hash

from app import app
from models import db, User, BaseIngredient, Recipe, RecipeIngredient, Instruction, RecipeImage, Rating


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
        # 1. Seed base ingredients
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

        # 2. Create users
        num_users = min(max(1, num_recipes // 2), 10)
        users = []
        for _ in range(num_users):
            email = fake.unique.email()
            raw_pw = fake.password(length=12)
            hashed_pw = generate_password_hash(raw_pw)
            display_name = fake.name()
            profile_description = fake.paragraph(nb_sentences=3)
            user = User(
                email=email,
                password=hashed_pw,
                display_name=display_name,
                profile_description=profile_description
            )
            db.session.add(user)
            users.append(user)
        db.session.commit()

        all_ingredients = BaseIngredient.query.all()

        # 3. Generate recipes
        for _ in range(num_recipes):
            recipe = Recipe(
                name=fake.sentence(nb_words=3).rstrip('.'),
                description=fake.paragraph(nb_sentences=3),
                cook_time=random.randint(10, 180),
                servings=random.randint(1, 8),
                user_id=random.choice(users).id,
                view_count=random.randint(0, 1000)
            )
            db.session.add(recipe)
            db.session.commit()  # to get recipe.id

            # 3a. Ingredients (float quantity)
            for ingr in random.sample(all_ingredients, random.randint(3, 7)):
                qty = round(random.uniform(0.5, 500), 2)
                db.session.add(RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingr.id,
                    quantity=qty
                ))

            # 3b. Instructions
            for step_num in range(1, random.randint(3, 6) + 1):
                text = fake.sentence(nb_words=10)
                db.session.add(Instruction(
                    recipe_id=recipe.id,
                    step_number=step_num,
                    content=text
                ))

            # 3c. Images
            for _ in range(random.randint(1, 3)):
                url = fake.image_url(width=640, height=480)
                db.session.add(RecipeImage(
                    recipe_id=recipe.id,
                    image_url=url
                ))

            db.session.commit()

            # 3d. Ratings & Reviews (3 unique users)
            reviewers = random.sample(users, k=min(3, len(users)))
            for reviewer in reviewers:
                rating_value = random.randint(1, 5)
                review_text = fake.sentence(nb_words=12)
                dt = fake.date_time_between(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 12, 31)
                )
                db.session.add(Rating(
                    recipe_id=recipe.id,
                    user_id=reviewer.id,
                    rating=rating_value,
                    review=review_text,
                    created_at=dt,
                    updated_at=dt
                ))
            db.session.commit()

        print(f"✅ Added {num_recipes} recipes, users, ingredients, instructions, images, and ratings to the database.")


if __name__ == '__main__':
    main()

