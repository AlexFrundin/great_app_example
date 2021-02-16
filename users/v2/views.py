import hashlib
import random as r
from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from config.messages import Messages
from ethos_network.settings import JwtConstants
from users.models import User, RefreshToken
from users.requestSchema import AppleSignupValidator
from users.serializers import UserSerializer
from users.v2.validator import SignupValidator, PreDataValidator, AgeValidator
from utility.encryptionHelper import encryptionHelper
from utility.ethosCommon import EthosCommon
from utility.hashingUtility import hashingUtility
from utility.loggerService import logerror
from utility.requestErrorFormate import requestErrorMessagesFormate


def generate_tokens(user_id):
    # Generate the access token & refresh token
    access_token = encryptionHelper().jwtAccessToken(user_id)
    refresh_token = encryptionHelper().jwtRefreshToken(user_id)

    # Generate hash token to store in DB
    hashed_token = hashlib.sha256(
        JwtConstants.REFRESH_TOKEN_SALT.encode() +
        refresh_token.encode()
    ).hexdigest()
    refresh_token_object = RefreshToken.objects.create(
        token=hashed_token
    )
    refresh_token_object.save()

    return access_token, refresh_token


@api_view(['POST'])
def verify_email(request):
    """
    GET v2/user/isemail?email=user@email
    Response:
    if email existing:
        HTTP/1.1 200 OK
        {
            "error": "Email already exists"
        }
    if no valid email:
        HTTP/1.1 200 OK
        {
            "error": "Invalid email address"
        }
    if not email:
        HTTP/1.1 200 OK
        {
            "error": "Email is required"
        }
    if email OK:
        HTTP/1.1 200 OK
        {
            "message": "Ok"
        }
    """
    validator = PreDataValidator(request.data)
    if validator.validate():
        return Response({'message':'Ok'}, status=status.HTTP_200_OK)
    return Response({'error':  requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)


@api_view(['POST'])
def create(request):
    """
    @api {post} v2/user/create User registration
    @apiName User registration
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiParam {string} name full name, Default "" in case of apple sign-in
    @apiParam {string} email email
    @apiParam {string} password password
    @apiParam {string} profile_pic Profile pic, Default "" in case of apple sign-in
    @apiParam {string} dob date of birth => year only, Default "" in case of apple sign-in
    @apiParam {string} device_token device token
    @apiParam {integer} device_type device type 1 => android, 2 => ios
    @apiParam {string} social_token social login token for facebook, google or apple
    @apiParam {string} social_login_id Flag maintained for type of login 0 -> native login, 1 -> facebook login, 2 -> apple login, 3 -> google
    @apiParam {boolean} is_registration_bypass Registration bypass, Default -> False
    @apiSuccessExample Success-Response:
    HTTP/1.1 201 Created
    {
        "email": "test32@yopmail.com",
        "name": "Test 32",
        "user_id": "35"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Email already exists"
    }
    """
    try:
        is_apple_sign_in = False
        if 'is_registration_bypass' in request.data and bool(request.data['is_registration_bypass']):

            # If social_token already exist in DB
            if User.objects.filter(social_token=request.data.get('social_token').lower()).exists():
                # Get user info using email
                user_info = User.objects.filter(social_token=request.data.get('social_token')).values()
                access_token, refresh_token = generate_tokens(user_info[0]['id'])

                data = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "email": user_info[0]['email'],
                    "image": user_info[0]['profile_pic'],
                    "is_email_verified": user_info[0]['is_otp_verified'],
                    "name": user_info[0]['name'],
                    "user_id": user_info[0]['id'],
                    "user_role_id": user_info[0]['role_id'],
                    "is_active": user_info[0]['is_active']
                }

                return Response(data, status=status.HTTP_200_OK)

            validator = AppleSignupValidator(request.data)
            is_otp_verified = 1
            generated_otp = 0
            is_apple_sign_in = True
        else:
            validator = SignupValidator(request.data)
            is_otp_verified = 0
            # Generate random OTP
            generated_otp = "".join(str(r.randint(1, 9)) for _ in range(4))
        # Validate the request
        valid = validator.validate()

        if valid:
            # Encrypted password
            utility = hashingUtility()
            hashed_model = utility.getHashedPassword(request.data.get('password'))

            age = None
            dob = None
            if request.data.get('dob'):
                dob = request.data.get('dob')
                current_year = date.today().year
                age = current_year - int(dob)

            if is_apple_sign_in:
                user_info_exist = User.objects.filter(social_token=request.data.get('social_token').lower()).exists()
           

            # if email is not exists
            if not user_info_exist:
                # insert data in db
                user = User.objects.create(
                    name=request.data.get('name'),
                    email=request.data.get('email').lower(),
                    profile_pic=request.data.get('profile_pic'),
                    password=str(hashed_model.Password, 'utf-8'),
                    password_salt=str(hashed_model.Salt, 'utf-8'),
                    dob=dob,
                    bio=request.data.get('bio'),
                    location=request.data.get('location'),
                    age=age,
                    device_type=request.data.get('device_type'),
                    device_token=request.data.get('device_token'),
                    social_token=request.data.get('social_token'),
                    social_login_id=request.data.get('social_login_id'),
                    verification_code=generated_otp,
                    is_otp_verified=is_otp_verified,
                    is_active=1
                )
                user.save()
            if is_apple_sign_in:
                # Get user info using email
                user_info = User.objects.filter(id=user.id).values()
                # Generate the access token & refresh token
                access_token, refresh_token = generate_tokens(user.id)

                data = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "email": user_info[0]['email'],
                    "image": user_info[0]['profile_pic'],
                    "is_email_verified": user_info[0]['is_otp_verified'],
                    "name": user_info[0]['name'],
                    "user_id": user_info[0]['id'],
                    "user_role_id": user_info[0]['role_id'],
                    "is_active": user_info[0]['is_active']
                }

                return Response(data, status=status.HTTP_200_OK)

            # Encrypted password
            utility = hashingUtility()
            hashed_model = utility.getHashedPassword(request.data.get('password'))


            age = None
            dob = None
            if not request.data.get('dob') == '':
                dob = request.data.get('dob')
                current_year = date.today().year
                age = current_year - int(request.data.get('dob', 0))#exception None to int

            # insert data in db
            user = User.objects.create(
                name=request.data.get('name'),
                email=request.data.get('email').lower(),
                profile_pic=request.data.get('profile_pic'),
                password=str(hashed_model.Password, 'utf-8'),
                password_salt=str(hashed_model.Salt, 'utf-8'),
                dob=dob,
                bio=request.data.get('bio'),
                location=request.data.get('location'),
                age=age,
                device_type=request.data.get('device_type'),
                device_token=request.data.get('device_token'),
                social_token=request.data.get('social_token'),
                social_login_id=request.data.get('social_login_id'),
                verification_code=generated_otp,
                is_otp_verified=is_otp_verified,
                is_active=1
            )
            user.save()

            EthosCommon.sendVerificationCode(request.data.get('name'), request.data.get('email'), generated_otp)
            user_data = User.objects.get(id=user.id)
            serializer = UserSerializer(user_data, many=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/create', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
