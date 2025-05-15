from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Users Table
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(50), nullable=False)
    profile_description = db.Column(db.Text, nullable=True)

    @property
    def total_recipes(self):
        return len(self.recipes)

    @property
    def average_recipe_rating(self):
        if not self.recipes:
            return 0.0
        ratings = [r.average_rating for r in self.recipes if r.ratings]
        if not ratings:
            return 0.0
        return sum(ratings) / len(ratings)

    recipes = db.relationship('Recipe', backref='user', lazy=True)
    ratings = db.relationship('Rating', backref='user', lazy=True)

# Base Ingredient Table
class BaseIngredient(db.Model):
    __tablename__ = 'base_ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    default_unit = db.Column(db.String(20), nullable=True)

    used_in = db.relationship('RecipeIngredient', backref='ingredient', lazy=True)

# Recipes Table
class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cook_time = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_with_ids = db.Column(db.String(255), default='[]')
    access_level = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)

    @property
    def average_rating(self):
        if not self.ratings:
            return 0.0
        return sum(rating.rating for rating in self.ratings) / len(self.ratings)

    ingredients = db.relationship('RecipeIngredient', backref='recipe', cascade="all, delete-orphan", lazy=True)
    instructions = db.relationship('Instruction', backref='recipe', cascade="all, delete-orphan", lazy=True)
    images = db.relationship('RecipeImage', backref='recipe', cascade="all, delete-orphan", lazy=True)
    ratings = db.relationship('Rating', backref='recipe', cascade="all, delete-orphan", lazy=True)

# Recipes' Ingredient Table
class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('base_ingredients.id'), nullable=False)
    quantity = db.Column(db.Float)

# Recipes' Instructions Table
class Instruction(db.Model):
    __tablename__ = 'instructions'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)

# Recipes' Image Table
class RecipeImage(db.Model):
    __tablename__ = 'recipe_images'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

# Ratings and Reviews Table
class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint('recipe_id', 'user_id', name='unique_recipe_user_rating'),
    )

# User Profile Image Table
class UserProfileImage(db.Model):
    __tablename__ = 'user_profile_images'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', backref=db.backref('profile_image', uselist=False))
