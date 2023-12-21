from flask_jwt_extended import get_jwt_identity
from flask import jsonify, make_response
from functools import wraps


# https://stackoverflow.com/a/51820573
def only_roles(allowed_roles=[]):  # roles is a list of roles that will be allowed
    def _roles_decorator(f):
        @wraps(f)
        def __roles_decorator(*args, **kwargs):
            # check user identity
            current_user = get_jwt_identity()
            # check if the user-types in the allowed roles
            if (current_user['user_type'] in allowed_roles):
                return f(*args, **kwargs)
            else:
                return make_response(jsonify({"msg": "access-denied", "status": False}), 403)
        return __roles_decorator
    return _roles_decorator
