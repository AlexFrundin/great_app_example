from validator import Validator
from config.messages import Messages


# this class is use for edit profile validation
class EditProfileValidator(Validator):
    name = 'required'
    user_causes = 'required'

    message = {
        'name': {'required': Messages.IS_REQUIRED.format(field_name="Name")}
    }

# this class is use for edit post validattion
class create_engagement_validator(Validator):
    title = 'required'
    description = 'required'
    location_address = 'required'
    latitude = 'required'
    longitude = 'required'
    user_causes = 'array|numberic'
    user_sub_causes = 'array|numberic'
    min_age = 'numberic'
    max_age = 'numberic'

    message = {
        'title': {
            'required': Messages.IS_REQUIRED.format(field_name="Title")
        },
        'description': {
            'required': Messages.IS_REQUIRED.format(field_name="Description")
        },
        'location_address': {
            'required': Messages.IS_REQUIRED.format(field_name="Location address")
        },
        'latitude': {
            'required': Messages.IS_REQUIRED.format(field_name="Latitude")
        },
        'longitude': {
            'required': Messages.IS_REQUIRED.format(field_name="Longitude")
        },
        'user_causes': {
            'required': Messages.IS_REQUIRED.format(field_name="User Causes"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User Causes")
        },
        'user_sub_causes': {
            'required': Messages.IS_REQUIRED.format(field_name="User sub-causes"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User sub-causes")
        },
        'min_age': {
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Minimum age")
        },
        'max_age': {
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Maximum age")
        }
    }

# this class is use for edit post validattion
class deletePostValidator(Validator):
    post_id = 'required|numberic'

    message = {
        'post_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Post id")
        }
    }

# this class is use for User's post list validation
class UserPostListValidator(Validator):
    page_limit = 'required|decimal'
    page_offset = 'required|digits'
    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'decimal': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Page offset")
        }
    }
