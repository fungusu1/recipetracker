#!/usr/bin/env python3
"""
Populate the SQLite database with fake data.

Exactly the same behaviour as the original script, plus:

• Each user now receives **four** guaranteed recipes:
    1. Public   (access_level = 0)
    2. Private  (access_level = 1)
    3. Shared with user-id 1         (access_level = 3)
    4. Shared with *any* user ≠ 1    (access_level = 3)

All other logic (ingredients, instructions, images, view counts, reviews/
ratings, random extra recipes, etc.) is unchanged.
"""

import sys
import random
import json
from datetime import datetime

from faker import Faker
from werkzeug.security import generate_password_hash

from app import app
from models import (
    db,
    User,
    BaseIngredient,
    Recipe,
    RecipeIngredient,
    Instruction,
    RecipeImage,
    Rating,
    UserProfileImage,
)


# ---------------------------------------------------------------------
# Helper ─ complete recipe generator (identical inner logic to original)
# ---------------------------------------------------------------------
def _create_full_recipe(
    fake,
    owner,
    all_ingredients,
    review_pool,
    access_level: int,
    shared_ids=None,
):
    """Create one recipe with ingredients, steps, images, view-count & reviews."""
    shared_ids = shared_ids or []
    recipe = Recipe(
        name=fake.sentence(nb_words=3).rstrip("."),
        description=fake.paragraph(nb_sentences=3),
        cook_time=random.randint(10, 180),
        servings=random.randint(1, 8),
        user_id=owner.id,
        access_level=access_level,
        shared_with_ids=json.dumps(shared_ids),
    )
    db.session.add(recipe)
    db.session.commit()  # assigns recipe.id

    # --- Ingredients --------------------------------------------------
    for ingr in random.sample(all_ingredients, k=random.randint(3, 7)):
        db.session.add(
            RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingr.id,
                quantity=random.randint(1, 500),
            )
        )

    # --- Instructions -------------------------------------------------
    for step in range(1, random.randint(3, 6) + 1):
        db.session.add(
            Instruction(
                recipe_id=recipe.id,
                step_number=step,
                content=fake.sentence(nb_words=10),
            )
        )

    # --- Images -------------------------------------------------------
    for _ in range(random.randint(1, 3)):
        db.session.add(
            RecipeImage(
                recipe_id=recipe.id,
                image_url=fake.image_url(width=640, height=480),
            )
        )

    # --- View count ---------------------------------------------------
    recipe.view_count = random.randint(0, 1_000)
    db.session.commit()

    # --- Reviews / ratings -------------------------------------------
    review_users = random.sample(review_pool, k=min(3, len(review_pool)))
    for reviewer in review_users:
        created_at = fake.date_time_between(
            start_date=datetime(2024, 1, 1, 0, 0, 0),
            end_date=datetime(2024, 12, 31, 23, 59, 59),
        )
        db.session.add(
            Rating(
                recipe_id=recipe.id,
                user_id=reviewer.id,
                rating=random.randint(1, 5),
                review=fake.sentence(nb_words=12),
                created_at=created_at,
                updated_at=created_at,
            )
        )
    db.session.commit()


# ---------------------------------------------------------------------
# Main seeding routine
# ---------------------------------------------------------------------
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python populate_db.py <num_recipes>")
        sys.exit(1)

    try:
        num_recipes_requested = int(sys.argv[1])
    except ValueError:
        print("<num_recipes> must be an integer.")
        sys.exit(1)

    fake = Faker()

    with app.app_context():
        # --------------------------------------------------------------
        # 1.  Base ingredients (unchanged)
        # --------------------------------------------------------------
        base_list = [
            ("Flour", "g"),
            ("Sugar", "g"),
            ("Salt", "tsp"),
            ("Butter", "g"),
            ("Eggs", "pcs"),
            ("Milk", "ml"),
            ("Olive Oil", "ml"),
            ("Onion", "pcs"),
            ("Garlic", "cloves"),
            ("Tomato", "pcs"),
            ("Chicken", "g"),
            ("Beef", "g"),
            ("Rice", "g"),
            ("Pasta", "g"),
            ("Cheese", "g"),
            ("Pepper", "tsp"),
            ("Baking Powder", "tsp"),
            ("Vanilla Extract", "ml"),
            ("Cocoa Powder", "g"),
            ("Yeast", "g"),
        ]
        for name, unit in base_list:
            if not BaseIngredient.query.filter_by(name=name).first():
                db.session.add(BaseIngredient(name=name, default_unit=unit))
        db.session.commit()

        # --------------------------------------------------------------
        # 2.  Three fixed test users (ids will typically be 1-3)
        # --------------------------------------------------------------
        test_users_data = [
            {
                "email": "test1@email.com",
                "password": "password111",
                "display_name": "Test User 1",
                "profile_description": "Test user 1 profile description!",
            },
            {
                "email": "test2@email.com",
                "password": "password222",
                "display_name": "Test User 2",
                "profile_description": "Hi, this is test user 2 profile description.",
            },
            {
                "email": "test3@email.com",
                "password": "password333",
                "display_name": "Test User 3",
                "profile_description": "Test user 3 profile description is here.",
            },
        ]

        users: list[User] = []
        for u in test_users_data:
            existing = User.query.filter_by(email=u["email"]).first()
            if existing:
                users.append(existing)
                continue
            new_u = User(
                email=u["email"],
                password=generate_password_hash(u["password"]),
                display_name=u["display_name"],
                profile_description=u["profile_description"],
            )
            db.session.add(new_u)
            users.append(new_u)
        db.session.commit()

        # --------------------------------------------------------------
        # 3.  Extra random users (up to 10 total, unchanged)
        # --------------------------------------------------------------
        extra_user_count = min(max(1, num_recipes_requested // 2), 10)
        for _ in range(extra_user_count):
            new_user = User(
                email=fake.unique.email(),
                password=generate_password_hash(fake.password(length=12)),
                display_name=fake.name(),
                profile_description=fake.paragraph(nb_sentences=3),
            )
            db.session.add(new_user)
            users.append(new_user)
        db.session.commit()

        # --------------------------------------------------------------
        # 4.  Profile images (unchanged)
        # --------------------------------------------------------------
        for user in users:
            if not user.profile_image:
                db.session.add(
                    UserProfileImage(
                        user_id=user.id,
                        image_url=fake.image_url(width=256, height=256),
                    )
                )
        db.session.commit()

        # --------------------------------------------------------------
        # 5.  Four baseline recipes per user
        # --------------------------------------------------------------
        all_ingredients = BaseIngredient.query.all()
        for user in users:
            # Public
            _create_full_recipe(fake, user, all_ingredients, users, access_level=0)

            # Private
            _create_full_recipe(fake, user, all_ingredients, users, access_level=1)

            # Shared with user #1
            _create_full_recipe(
                fake,
                user,
                all_ingredients,
                users,
                access_level=3,
                shared_ids=[1],
            )

            # Shared with any user whose id ≠ 1
            other_user_ids = [u.id for u in users if u.id != 1]
            if other_user_ids:
                _create_full_recipe(
                    fake,
                    user,
                    all_ingredients,
                    users,
                    access_level=3,
                    shared_ids=[random.choice(other_user_ids)],
                )
        db.session.commit()

        baseline_total = 4 * len(users)

        # --------------------------------------------------------------
        # 6.  Remaining random recipes (identical logic to original)
        # --------------------------------------------------------------
        remaining = max(0, num_recipes_requested - baseline_total)
        for _ in range(remaining):
            owner = random.choice(users)
            _create_full_recipe(fake, owner, all_ingredients, users, access_level=0)

        # --------------------------------------------------------------
        # 7.  Summary
        # --------------------------------------------------------------
        print(
            f"✅ Added {Recipe.query.count()} recipes "
            f"(with users, ingredients, instructions, images, reviews) "
            f"to the database."
        )


# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
