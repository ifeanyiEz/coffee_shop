import os
from turtle import title
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from flask import session, redirect, url_for
from flask_caching import Cache

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth, verify_decode_jwt

#________________________REFERENCES____________________________#

# https://auth0.com/docs/quickstart/backend/python/01-authorization
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
# https://github.com/ifeanyiEz/trivia_api
# https://flask-cors.readthedocs.io/en/latest/
# https://stackoverflow.com/questions/55497383/how-to-perform-update-partially-in-flask
# https://www.programiz.com/python-programming/list
# https://www.programiz.com/python-programming/methods/built-in/list
# https://dfarq.homeip.net/json-loads-vs-json-dumps-in-python/
# https://stackoverflow.com/questions/12952546/sqlite3-interfaceerror-error-binding-parameter-1-probably-unsupported-type
# https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_updating_objects.htm
# https://github.com/david4096/flask-auth0-example/blob/master/app.py


#_____________________INITIALIZE THE APP______________________#

app = Flask(__name__)
setup_db(app)
CORS(app)
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

#_____________________INITIALIZE THE DATABASE___________________#
'''
DONE uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
#db_drop_and_create_all()


#____________________DEFINE ENDPOINTS__________________________#

#__________________Get All Drinks: Public___________________#
'''
@DONE implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        # Get all the drinks form the DB and present them in the drink.short() format.
        all_drinks = Drink.query.all()
        formatted_drinks = [drink.short() for drink in all_drinks]

        # Confirm that there are drinks in the DB, otherwise show a "404: not found" error message.
        if len(formatted_drinks) == 0:
            abort(404)

        #If there are drinks in the DB, show success and the list of drinks.
        return jsonify({
            "success": True,
            "drinks": formatted_drinks
        })
    
    except:
        abort(422)


#__________________Get All Drinks: Authorised Users___________________#

'''
@DONE implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=['GET'])

# Ensure that the user has the permissions to access this endpoint
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):

    try:

        # Get all the drinks form the DB and present them in the drink.long() format.
        all_drinks = Drink.query.all()
        formatted_drinks = [drink.long() for drink in all_drinks]

        # Confirm that there are drinks in the DB, otherwise show a "404: not found" error message.
        if len(formatted_drinks) == 0:
            abort(404)

        # If there are drinks in the DB, show success and the list of drinks.
        return jsonify({
            "success": True,
            "drinks": formatted_drinks 
        })

    except:
        abort(422)

#__________________Get Specific Drink: Authorised Users___________________#

'''
This is a new endpoint.
It is added to allow users with proper permissions to retrieve and view details of a specific drink, then decide how/what to PATCH.
Also it allows permitted users to view a drink before deciding to DELETE it.

'''
@app.route('/drinks/<int:drink_id>', methods=['GET'])

# Ensure that the user has the permissions to access this endpoint
@requires_auth('get:drinks')
def get_drink_by_id(payload, drink_id):

    try:
        # From the DB, fetch the drink using the drink_id
        drink = Drink.query.filter_by(id = drink_id).one_or_none()

        # If there's no drink with the specified drink_id, raise a "404: not found" error
        if drink is None:
            abort(404)
        
        # If the drink is found present it in the long() format 
        formatted_drink = drink.long()

        # Return success and the formatted drink
        return jsonify({
            "success": True,
            "drink": formatted_drink
        })
    except:
        abort(422)


#__________________Make New Drink: Authorised Users___________________#

'''
@DONE implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])

# Ensure that the user has the permissions to access this endpoint
@requires_auth('post:drinks')
def make_new_drink(payload):

    # Get the data from the request body
    data = request.get_json()
    title = data.get('title', None)
    recipe = data.get('recipe', None)

    try:
        # Make a new drink using the data from the request body
        new_drink = Drink(title = title, recipe = json.dumps(recipe))

        # If any of the request fields is blank, raise a "400: bad syntax" error.
        if new_drink.title == "" or new_drink.recipe == "":
            return jsonify({
                "success": False,
                "message": 'The server could not understand the request due to invalid syntax'
            }), 400

        # If everything is okay, insert the new drink to the DB
        else:
            new_drink.insert()

        # Return success and the new drink in  the long() format
        return jsonify({
            "success": True,
            "drinks": new_drink.long()
        }), 200

    except:
        abort(422)

#__________________Update Specific Drink: Authorised Users___________________#

'''
@DONE implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])

# Ensure that the user has the permissions to access this endpoint
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):

    # Get the data from the request body
    data = request.get_json()
    title = data.get('title', None)
    recipe = data.get('recipe', None)

    try:
        # From the DB, fetch the drink to be updated using the drink_id
        drink = Drink.query.filter_by(id = drink_id).one_or_none()

        # If there's no drink with the specified drink_id, raise a "404: not found" error
        if drink is None:
            abort(404)

        # If the drink is found check:
        # If only the title is to be changed, assign a new value to the drink title
        if recipe is None and title is not None:
            drink.title = title

            # Update the DB
            drink.update()

        # If only the recipe is to be changed, assign a new value to the drink recipe
        elif title is None and recipe is not None:
            drink.recipe = json.dumps(recipe)

            # Update the DB
            drink.update()

        # If no values are provided for both title and recipe, raise a "400: bad syntax" error.
        elif drink.title is None and drink.recipe is None:
            return jsonify({
                "success": False,
                "message": 'The server could not understand the request, no values were provided for title or recipe'
            }), 400

        # If both values are provided, assign new values for both title and recipe
        else:
            drink.title = title
            drink.recipe = json.dumps(recipe)
            drink.update()

        # Get the new updated drink from the DB
        updated_drink = Drink.query.filter_by(id = drink_id).one_or_none()

        # Present the required JSON success output
        return jsonify({
            "success": True,
            "drinks": [updated_drink.long()]
        }), 200

    except:
        abort(422)

#__________________Delete Specific Drink: Authorised Users___________________#

'''
@DONE implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])

# Ensure that the user has the permissions to access this endpoint
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):

    try:
        # From the DB, fetch the drink to be deleted using the drink_id
        drink = Drink.query.filter_by(id = drink_id).one_or_none()

        # If there's no drink with the specified drink_id, raise a "404: not found" error
        if drink is None:
            abort(404)

        # If the drink is found, delete it from the DB
        drink.delete()

        # Confirm that the drink was deleted by searching for it in the DB
        deleted_drink = Drink.query.filter_by(id = drink_id).one_or_none()

        # If it is found, then it was not deleted. Raise a "422: unable to be followed" error.
        if deleted_drink is not None:
            return jsonify({
                "success": False,
                "message": "Drink was not deleted"
            }), 422
        
        else:
            # If it is not found, then it was deleted. Return success and the drink id
            deleted_drink_id = drink.id

            return jsonify({
                "success": True,
                "delete": deleted_drink_id
            }), 200

    except:
        abort(422)

# @app.route('/login')
# @requires_auth()
# def login_user():
#     return auth0.authorize_redirect(redirect_uri='CALLBACK_URL')

@app.route('/logout')
@requires_auth()
def logout_user():
    key = session.get('key')
    session.clear()
    cache.set(key, None)
    return redirect('https://ezufsnd.us.auth0.com/u/login?access_token={}&?client_id=RuBUGVhuWSJL7dBoWekcOeOf462x3NL7'.format(key), 'http://localhost:8100')


#__________________HANDLING ERRORS________________________#
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "The request was unable to be followed due to semantic errors"
    }), 422


'''
@DONE implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "The server could not understand the request due to invalid syntax."
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
      "success": False,
      "error": 401,
      "message": "Client must authenticate itself to get the requested resource."
    }), 401

@app.errorhandler(403)
def forbiden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "Client does not have access rights to the requested resource"
    }), 403
'''
@DONE implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "The server can not find the requested resource"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": "This method is not allowed for the requested URL"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
      "success": False,
      "error": 500,
      "message": "The server has encountered an internal error"
    }), 500

'''
@DONE implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def handle_auth_error(exception):
    response = jsonify(exception.error)
    response.status_code = exception.status_code
    return response

if __name__ == "__main__":
    app.debug = True
    app.run()
