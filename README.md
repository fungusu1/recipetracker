# recipetracker
Project for CITS3403 UWA

Recipe Index is a social platform for sharing and viewing user created cooking recipes! Users are able to create Recipes using our own created template to publish or privately add to the Index. 
Do you ever ask yourself what to make for lunch or dinner?
This website will help you decide what to make by looking at our browsing page, where you can put in ingredients that you have laying around and it will give you recipes to try out!

# CITS3403 - Group Project - Recipe Tracker

|Student ID|Name|GitHub Username|
|----|----|----|
|23922739|Wei Le Dillon John Teo|misD-T|
|23975858|Vincent Ta|SkyFate72|
|23974898|Lucy Caluya|caluyaL|
|23750573|Ryan Williams|fungusu1|

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
Next, in the 'Recipe Index' directory create the SQLAlchemy database by running:
```
python3 CreateDB.py
```
You can run the populate database script here to fill it with dummy data, or alternatively it's called when running the selenium tests. We recommend running here with 20 entries:
```
python3 PopulateDB.py [amount of entries to be created]
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
To run the unit tests navigate to the 'tests' folder and run:
```
python3 unit_test.py

```
To run selenium tests, in the same folder run:
```
python3 seleniumtests.py

```

The creation of the web application should be done in a private GitHub repository that includes a README containing:
- a description of the purpose of the application, explaining its design and use.
- a table with with each row containing the
  - i) UWA ID
  - ii) name and
  - iii) Github user name of the group members.
- instructions for how to launch the application.
- instructions for how to run the tests for the application.

