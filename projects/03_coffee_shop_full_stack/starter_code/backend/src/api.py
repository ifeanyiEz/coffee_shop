import os
from turtle import title
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

#________________________REFERENCES____________________________#

# https://auth0.com/docs/quickstart/backend/python/01-authorization
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
# https://github.com/ifeanyiEz/trivia_api
# https://flask-cors.readthedocs.io/en/latest/
# https://stackoverflow.com/questions/55497383/how-to-perform-update-partially-in-flask
# https://www.programiz.com/python-programming/list
# https://www.programiz.com/python-programming/methods/built-in/list


#_____________________INITIALIZE THE APP______________________#

app = Flask(__name__)
setup_db(app)
CORS(app)


#_____________________INITIALIZE THE DATABASE___________________#
'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
# db_drop_and_create_all()


#____________________DEFINE ENDPOINTS__________________________#
'''
@TODO implement endpoint
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

        # Confirm that there are drinks in the DB, otherwise show a "not found error message".
        if len(formatted_drinks) == 0:
            abort(404)

        #If there are drinks in the DB, show success and the list of drinks.
        return jsonify({
            "success": True,
            "drinks": formatted_drinks
        })
    
    except:
        abort(422)

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
# Ensure that the user has the permissions to access this endpoint
@requires_auth('get:drinks-detail')
def get_drinks_detail():
    try:
        # Get all the drinks form the DB and present them in the drink.long() format.
        all_drinks = Drink.query.all()
        formatted_drinks = [drink.long() for drink in all_drinks]

        # Confirm that there are drinks in the DB, otherwise show a "not found error message".
        if len(formatted_drinks) == 0:
            abort(404)

        # If there are drinks in the DB, show success and the list of drinks.
        return jsonify({
            "success": True,
            "drinks": formatted_drinks 
        })

    except:
        abort(422)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
# Ensure that the user has the permissions to access this endpoint
@requires_auth('post:drinks')

def make_new_drink():

    data = request.get_json()
    title = data.get('title', None)
    recipe = data.get('recipe', None)

    try:
        new_drink = Drink(title = title, recipe = recipe)

        if new_drink.title == "" or new_drink.recipe == "":
            return jsonify({
                "success": False,
                "message": 'The server could not understand the request due to invalid syntax'
            }), 400

        else:
            new_drink.insert()

        return jsonify({
            "success": True,
            "drinks": new_drink.long()
        })

    except:
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>')
# Ensure that the user has the permissions to access this endpoint
@requires_auth('patch:drinks')

def update_drink(drink_id):

    try:
        drink = Drink.query.filter_by(id = drink_id).one_or_none()

        if drink is None:
            abort(404)

        data = request.get_json()
        title = data.get('title', None)
        recipe = data.get('recipe', None)

        drink.title = title
        drink.recipe = json.dumps(recipe)

        if drink.title == "" and drink.recipe == "":
            return jsonify({
                "success": False,
                "message": 'The server could not understand the request due to invalid syntax'
            }), 400

        drink.update()

        return jsonify({
            "success": True,
            "drinks": list(drink.long())
        })

    except:
        abort(422)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>')
# Ensure that the user has the permissions to access this endpoint
@requires_auth('delete:drinks')

def delete_drink(drink_id):

    try:
        drink = Drink.query.filter_by(id = drink_id).one_or_none()

        if drink is None:
            abort(404)

        deleted_drink_id = drink.id

        drink.delete()

        return jsonify({
            "success": True,
            "delete": deleted_drink_id
        })

    except:
        abort(422)



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
@TODO implement error handlers using the @app.errorhandler(error) decorator
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
@TODO implement error handler for 404
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
@TODO implement error handler for AuthError
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
