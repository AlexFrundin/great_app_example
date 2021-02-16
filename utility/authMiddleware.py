""" 
Authorization middleware to validate is request valid or not.
"""
import jwt
from rest_framework import status
from ethos_network.settings import JwtConstants
from config.messages import Messages
from rest_framework.response import Response

# Decorator function to check user authentication
def isAuthenticate(function):
    def wrap(request, *args, **kwargs):
        try:
            if request.headers['Authorization'] and request.headers['Authorization'] != 'invalidtoken':
                token = request.headers['Authorization']
                # validating access token
                try:
                    # Decode payload
                    payload = jwt.decode(token, JwtConstants.TOKEN_SECRET,
                                         algorithms=[JwtConstants.JWT_ALGORITHM])
                    request.user_id = payload["user_id"]
                    # Token is valid pass the request
                    return function(request, *args, **kwargs)
                except (jwt.exceptions.DecodeError,
                        jwt.exceptions.InvalidSignatureError,
                        jwt.exceptions.ExpiredSignatureError,
                        jwt.exceptions.InvalidTokenError) as exception:
                    return Response({'error': str(exception)}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({'error': Messages.AUTH_CRED_NOT_PROVIDE}, status=status.HTTP_401_UNAUTHORIZED)
        except BaseException as exception:
            return Response({'error': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
    return wrap


def process_exception(self, request, exception):
    print(exception.__class__.__name__)
    print(exception.message)
    return None
