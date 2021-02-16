from ethos_network.settings import EthosCommonConstants
import redis
import _pickle

class RedisCommon():

    redis_host = EthosCommonConstants.REDIS_HOST
    redis_expiration = EthosCommonConstants.REDIS_EXPIRATION

    # Redis keys in which we will store data
    post_details = 'post-details-'
    post_upvote_users = 'post-upvote-users-'
    upvote_post_count = 'upvote-post-count-'
    comment_upvote_users = 'comment-upvote-users-'
    upvote_comment_count = 'upvote-comment-count-'
    save_post_users = 'save-post-users-'
    cause_details = 'cause-details-'
    subcause_details = 'subcause-details-'
    static_content = 'static-content'
    user_own_details = 'user-own-details-'
    user_saved_post_count = 'user-saved-post-count-'
    user_interests_count = 'user-interests-count-'
    user_added_as_interested_count = 'user-added-as-interested-'
    other_user_profile = 'other-user-profile-'
    user_interests_users = 'user-interests-users-'

    # Set data in redis
    def set_data(self, redis_key, redis_data):

        # Redis object
        redis_object = redis.Redis(self.redis_host)

        # Set data in Redis
        redis_object.set(redis_key, _pickle.dumps(redis_data))
        redis_object.expire(redis_key, self.redis_expiration)
        
        return True

    # Get data from redis based on key
    def get_data(self, redis_key):
        # Redis object
        redis_object = redis.Redis(self.redis_host)

        # Check if already exist in Redis then delete
        if redis_object.get(redis_key):
            return redis_object.get(redis_key)

        return 0

    # Delete data from redis on any updating
    def delete_data(self, redis_key):

        # Redis object
        redis_object = redis.Redis(self.redis_host)

        # Check if already exist in Redis then delete
        if redis_object.get(redis_key):
            redis_object.delete(redis_key)
        
        return True
