from validator import Validator
from config.messages import Messages


# this class is use for create post validation
class PreferredCauseListValidator(Validator):
    var_latitude = 'required'
    var_longitude = 'required'
    radius = 'required'

    message = {
        'var_latitude': {
            'required': Messages.IS_REQUIRED.format(field_name="Latitude")
        },
        'var_longitude': {
            'required': Messages.IS_REQUIRED.format(field_name="Longitude")
        },
        'radius': {
            'required': Messages.IS_REQUIRED.format(field_name="Radius")
        }
    }


# this class is use for validation
class ExplorePostListValidator(Validator):
    var_latitude = 'required'
    var_longitude = 'required'
    page_limit = 'required|numberic'

    message = {
        'var_latitude': {
            'required': Messages.IS_REQUIRED.format(field_name="Latitude")
        },
        'var_longitude': {
            'required': Messages.IS_REQUIRED.format(field_name="Longitude")
        },
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'decimal': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        }
    }


# this class is use for add/remove cause validation
class AddRemoveCauseValidator(Validator):
    type = 'required|between:1, 2'

    message = {
        'type': {
            'required': Messages.IS_REQUIRED.format(field_name="Type"),
            'between': Messages.SHOULD_BE_BETWEEN.format(field_name="Type", min_value=1, max_value=2)
        },
    }