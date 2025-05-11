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

    recipes = db.relationship('Recipe', backref='user', lazy=True)

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

    ingredients = db.relationship('RecipeIngredient', backref='recipe', cascade="all, delete-orphan", lazy=True)
    instructions = db.relationship('Instruction', backref='recipe', cascade="all, delete-orphan", lazy=True)
    images = db.relationship('RecipeImage', backref='recipe', cascade="all, delete-orphan", lazy=True)

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
