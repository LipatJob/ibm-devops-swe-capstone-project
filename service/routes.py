"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################

@app.route("/accounts", methods=["GET"])
def list_accounts():
    """
    List all account
    This end point will return the information of all accounts
    """
    app.logger.info(f"Request to view all Accounts")

    accounts = Account.all()
    accounts_serializable = [account.serialize() for account in accounts]
    return accounts_serializable, status.HTTP_200_OK

######################################################################
# READ AN ACCOUNT
######################################################################

@app.route("/accounts/<id>", methods=["GET"])
def read_account(id):
    """
    Read an account
    This end point will return the information of the Account with the given id
    """
    app.logger.info(f"Request to view an Account with id: {id}")

    # Validate that id is a number
    parsed_id = try_parse_id(id)
    
    # Validate that account with id exists
    account = try_get_account(parsed_id)
    
    # Return account
    return account.serialize(), status.HTTP_200_OK


######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################

@app.route("/accounts/<id>", methods=["PUT"])
def update_account(id):
    """
    Update an account
    This end point will update the Account based on the posted data
    """
    # Log request
    app.logger.info(f"Request to update an Account with id: {id}")
    
    # Validate that id is a number
    parsed_id = try_parse_id(id)
    
    # Validate that account with id exists
    account = try_get_account(parsed_id)
    
    # Update account
    account.deserialize(request.get_json())
    account.update()

    return account.serialize(), status.HTTP_200_OK


######################################################################
# DELETE AN ACCOUNT
######################################################################

@app.route("/accounts/<id>", methods=["DELETE"])
def delete_account(id):
    """
    Delete an account
    This end point will delete the Account with the given id
    """
    app.logger.info(f"Request to delete an Account with id: {id}")

    # Validate that id is a number
    parsed_id = try_parse_id(id)
    
    # Validate that account with id exists
    account = try_get_account(parsed_id)

    # delete account
    account.delete()

    return "", status.HTTP_204_NO_CONTENT


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )

def try_parse_id(id):
    """ Tries to parse id if valid """
    if not id.isnumeric():
        app.logger.error(f"Id not valid: {id}")
        abort(status.HTTP_400_BAD_REQUEST, "Id parameter must be numeric")
    parsed_id = int(id)
    return parsed_id

def try_get_account(id):
    """ Tries to get account with id if exists"""
    account = Account.find(id)
    if account == None:
        app.logger.error(f"Account with id not found: {id}")
        abort(status.HTTP_404_NOT_FOUND, "Account not found")
    return account