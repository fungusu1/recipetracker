# recipetracker
Project for CITS3403 UWA

The creation of the web application should be done in a private GitHub repository that includes a README containing:
- a description of the purpose of the application, explaining its design and use.
- a table with with each row containing the
  - i) UWA ID
  - ii) name and
  - iii) Github user name of the group members.
- instructions for how to launch the application.
- instructions for how to run the tests for the application.

# CITS3403 - Group Project - Recipe Tracker

|Student ID|Name|GitHub Username|
|----|----|----|
|23922739|Wei Le Dillon John Teo|misD-T|
|23975858|Vincent Ta|SkyFate72|
|23974898|Lucy Caluya|caluyaL|
|23750573|Ryan Williams|fungusu1|

RecipeTracker is a social platform for sharing and viewing user authored cooking recipes. fill in later
info about tech stack used goes here

## Running
Create a python virtual environment:
```cpp
python3 -m venv path/venv

# Like:
python3 -m venv ~/.env

# Activate the environment
source path/bin/activate
```
Next install the requirements. In the main project directory 'recipetracker' run the following to install all packages and dependencies used in the project:
```
pip install -r requirements.txt
```
Next create the SQLAlchemy database in the main directory by running:
```
python3 CreateDB.py
```
Finally to run the flask app run:
```
flask run
```
Or alternatively:
```
python3 app.py
```

## Testing
fill in later
