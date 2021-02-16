# This helper file is using to generate access and referesh token
import jwt
import hashlib
from rest_framework import status
from datetime import datetime, timedelta
from ethos_network.settings import JwtConstants
from utility.hashingUtility import hashingUtility
from django.http import HttpResponse, HttpRequest
from users.models import RefreshToken
from config.messages import Messages

class encryptionHelper():
    # Encryption helper function for access token generation
    def jwtAccessToken(self, user_id):

        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(seconds=JwtConstants.JWT_EXP_DELTA_SECONDS)
            }
            accessToken = jwt.encode(payload, JwtConstants.TOKEN_SECRET,
                                     algorithm=JwtConstants.JWT_ALGORITHM)
            return accessToken.decode('utf-8')
        except Exception as e:
            return False

    # Encryption helper function for refresh token generation
    def jwtRefreshToken(self, user_id):

        try:

            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(seconds=JwtConstants.JWT_REF_EXP_DELTA_SECONDS)
            }
            refreshToken = jwt.encode(payload, JwtConstants.REFRESH_TOKEN_SECRET,
                                      algorithm=JwtConstants.JWT_ALGORITHM)
            return refreshToken.decode('utf-8')
        except Exception as e:
            return False

    # Use the refresh token to get a new access token
    def getNewAccessToken(self, refreshToken):
        try:
            decoded = jwt.decode(refreshToken,
                                 JwtConstants.REFRESH_TOKEN_SECRET,
                                 algorithms=[JwtConstants.JWT_ALGORITHM])

            # Signature is valid take second step to verify
            hashed_token = hashlib.sha256(
                JwtConstants.REFRESH_TOKEN_SALT.encode() + refreshToken.encode()).hexdigest()
            
            refresh_info = RefreshToken.objects.filter(token = str(hashed_token)).exists()
            if refresh_info:
                RefreshToken.objects.filter(token = str(hashed_token)).delete()
                # Generating auth tokens
                access_token = self.jwtAccessToken(decoded["user_id"])
                refresh_token = self.jwtRefreshToken(decoded["user_id"])
                # Getting hashed token value
                hashed_token = hashlib.sha256(
                    JwtConstants.REFRESH_TOKEN_SALT.encode() + refresh_token.encode()).hexdigest()
                refresh_token_object = RefreshToken.objects.create(
                    token=hashed_token
                )
                return [{"data": {"access_token": access_token, "refresh_token": refresh_token}, "status": status.HTTP_200_OK}]
            else:
                return [{"data": {Messages.SIGN_FAILED}, "status": status.HTTP_403_FORBIDDEN}]
        except (jwt.exceptions.DecodeError,
                jwt.exceptions.InvalidSignatureError,
                jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidTokenError) as exception:
            return [{"data": {str(exception)}, "status": status.HTTP_403_FORBIDDEN}]
