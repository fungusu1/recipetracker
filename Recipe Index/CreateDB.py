from app import app
from models import db

# Initialize and create the database
with app.app_context():
    db.create_all()
    print("✅ Database has been created successfully.")

#This file will create a db with the tables written in models.py, you can add data to test out your code in here.