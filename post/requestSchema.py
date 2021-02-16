from validator import Validator
from config.messages import Messages


# this class is use for create post validattion
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

# this class is use for get post validation
class post_details_validator(Validator):
    post_id = 'required|numberic'
    message = {
        'post_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Post id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Post id")
        }
    }

# this class is use for get post comments validation
class post_comments_validator(Validator):
    post_id = 'required|digits'
    comment_id = 'required|digits'
    page_limit = 'required|digits'
    page_offset = 'required|digits'
    message = {
        'post_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Post id"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Post id")
        },
        'comment_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Comment id"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Comment id")
        },
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Page limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Page offset")
        }
    }

# this class is use for get post commented by user validation
class post_comment_by_user_validator(Validator):
    post_id = 'required|numberic'
    type = 'required|between:0, 3'
    comment = 'required'
    message = {
        'post_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Post id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Post id")
        },
        'comment_id': {
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Comment id")
        },
        'type': {
            'required': Messages.IS_REQUIRED.format(field_name="Type"),
            'between': Messages.SHOULD_BE_BETWEEN.format(field_name="Type", min_value=0, max_value=3)
        },
        'comment': {
            'required': Messages.IS_REQUIRED.format(field_name="Comment")
        }
    }

# this class is use for get post upvote by user validation
class post_upvote_validator(Validator):
    post_id = 'required|digits'
    type = 'required|between:0, 3'
    message = {
        'post_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Post id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Post id")
        },
        'type': {
            'required': Messages.IS_REQUIRED.format(field_name="Type"),
            'between': Messages.SHOULD_BE_BETWEEN.format(field_name="Type", min_value=0, max_value=3)
        }
    }

# this class is use for validattion
class PostListValidator(Validator):
    page_limit = 'required|decimal'
    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'decimal': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        }
    }

# this class is use for validattion
class UpvoteUsersListValidator(Validator):
    page_limit = 'required|numberic'
    page_offset = 'required|digits'
    data_id = 'required|numberic'
    data_type = 'required'

    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Post Limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Post Offset")
        },
        'data_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Data Id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Data Id")
        },
        'data_type': {
            'required': Messages.IS_REQUIRED.format(field_name="Data Type")
        },
    }

# this class is use for save post validattion
class SavePostValidator(Validator):
    post_id = 'required|numberic'
    message = {
        'post_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Post id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Post id")
        }
    }

class ReportPostValidator(Validator):
    post_id = 'required|numberic'
    reason_id = 'required|numberic'

    message = {
        'post_id': {
            'required': Messages.IS_REQUIRED.format(field_name="post_id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="post_id")
        },
        'reason_id': {
            'required': Messages.IS_REQUIRED.format(field_name="reason_id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="reason_id")
        }
    }

# this class is use for validattion
class ReportReasonListValidator(Validator):
    page_limit = 'required|numberic'
    page_offset = 'required|digits'

    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Post Limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Post Offset")
        }
    }

class PostReceiveNotificationValidator(Validator):
    post_id = 'required|numberic'

    message = {
        'post_id': {
            'required': Messages.IS_REQUIRED.format(field_name="post_id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="post_id")
        }
    }
