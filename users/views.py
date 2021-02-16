import random as r
import hashlib
import base64
import secrets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from config.messages import Messages
from utility.encryptionHelper import encryptionHelper
from utility.hashingUtility import hashingUtility
from utility.requestErrorFormate import requestErrorMessagesFormate
from utility.ethosCommon import EthosCommon
from .models import User, UserCauses, UserSubCauses, Role, RefreshToken, UserBlockedContacts
from user_interest.models import UserInterest
from .requestSchema import (SignupValidator, VerifyOtpValidator,
                            ResendOtpValidator, LoginValidator, SocialLoginValidator,
                            ForgotValidator, ResetValidator,
                            RefreshValidator, ChangePasswordValidator,
                            BlockUnblockValidator, SettingToggleValidator,
                            UserBlockedValidator, InterestedUserListValidator, AppleSignupValidator)
from causes_subcauses.models import Cause, SubCause
from user_interest.models import UserInterestsRequest
from .serializers import UserSerializer, UserSettingSerializer, UserBlockedContactSerializer
from ethos_network.settings import EthosCommonConstants, EmailConstants, JwtConstants
from utility.mailTemplates.emailTemplates import emailTemplates
from utility.authMiddleware import isAuthenticate
from utility.rbacService import RbacService
from user_interest.serializers import SuggestedUsersSerializer
from datetime import date
from utility.loggerService import logerror
import redis
import _pickle
from utility.redisCommon import RedisCommon

@api_view(['POST'])
def create(request):
    """
    @api {post} v1/user/create User registration
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
    @apiParam {array} user_causes [1,2,3]
    @apiParam {array} user_sub_causes [1,2,3], Default [] in case of apple sign-in
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
        if 'is_registration_bypass' in request.data and request.data['is_registration_bypass'] == True:

            # If social_token already exist in DB
            if User.objects.filter(social_token=request.data.get('social_token').lower()).exists():
                # Get user info using email
                user_info = User.objects.filter(social_token=request.data.get('social_token')).values()

                # Generate the access token & refresh token
                access_token = encryptionHelper().jwtAccessToken(user_info[0]['id'])
                refresh_token = encryptionHelper().jwtRefreshToken(user_info[0]['id'])

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

                # Generate hash token to store in DB
                hashed_token = hashlib.sha256(
                    JwtConstants.REFRESH_TOKEN_SALT.encode() +
                    refresh_token.encode()
                ).hexdigest()
                refresh_token_object = RefreshToken.objects.create(
                    token=hashed_token
                )
                refresh_token_object.save()

                return Response(data, status=status.HTTP_200_OK)

            validator = AppleSignupValidator(request.data)
            is_otp_verified = 1
            generated_otp = 0
            is_apple_sign_in = True
        else:
            validator = SignupValidator(request.data)
            is_otp_verified = 0
            # Generate random OTP
            otp = ""
            for i in range(4):
                otp += str(r.randint(1, 9))
            generated_otp = otp

        # Validate the request
        valid = validator.validate()

        if valid:
            # Encrypted password
            utility = hashingUtility()
            hashed_model = utility.getHashedPassword(request.data.get('password'))

            if is_apple_sign_in:
                user_info_exist = User.objects.filter(social_token=request.data.get('social_token').lower()).exists()
            else:
                user_info_exist = User.objects.filter(email=request.data.get('email').lower()).exists()

            # if email is not exists
            if not user_info_exist:

                # calculate age of user
                age = None
                dob = None
                if not request.data.get('dob') == '':
                    dob = request.data.get('dob')
                    current_year = date.today().year
                    age = current_year - int(request.data.get('dob'))

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

                # get inserted user id
                user_obj = User.objects.latest('id')
                user_id = user_obj.id

                # insert causes
                user_causes = request.data.get('user_causes')
                if len(user_causes) > 0:
                    for cause_id in user_causes:
                        cause = Cause.objects.get(id=cause_id)
                        UserCauses.objects.create(
                            user_id=user_obj,
                            causes_id=cause,
                        )

                # insert sub-causes
                user_sub_causes = request.data.get('user_sub_causes')
                if len(user_sub_causes) > 0:
                    for sub_cause_id in user_sub_causes:
                        sub_cause = SubCause.objects.get(id=sub_cause_id)
                        UserSubCauses.objects.create(
                            user_id=user_obj,
                            sub_causes_id=sub_cause
                        )

                # Apple sign in
                if is_apple_sign_in:
                    # Get user info using email
                    user_info = User.objects.filter(id=user_id).values()

                    # Generate the access token & refresh token
                    access_token = encryptionHelper().jwtAccessToken(user_id)
                    refresh_token = encryptionHelper().jwtRefreshToken(user_id)

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

                    # Generate hash token to store in DB
                    hashed_token = hashlib.sha256(
                        JwtConstants.REFRESH_TOKEN_SALT.encode() +
                        refresh_token.encode()
                    ).hexdigest()
                    refresh_token_object = RefreshToken.objects.create(
                        token=hashed_token
                    )
                    refresh_token_object.save()

                    return Response(data, status=status.HTTP_200_OK)

                # Normal Sign in
                EthosCommon.sendVerificationCode(request.data.get('name'), request.data.get('email'), otp)
                user_data = User.objects.get(id=user_id)
                serializer = UserSerializer(user_data, many=False)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': Messages.EMAIL_EXITS}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/create', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def verify_otp(request):
    """
    @api {post} v1/user/verify-otp Verify otp
    @apiName Verify otp
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiParam {String} user_email Email id
    @apiParam {Integer} otp OTP
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 OK
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxMjAsImV4cCI6MTU5NzEzOTAzMn0.CtOQ8J_MUc65ZLta_yR2dw88RnkEF3fnie2m7DmrO0g",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxMjAsImV4cCI6MTYwMjIzNjYzMn0.V3iwWP7WHg7O1czQ5JpsXKXv5dUEhYGh4r0xIDEfsxc",
        "email": "nikhil12@techaheadcorp.com",
        "image": "profilepic.png",
        "is_email_verified": 1,
        "name": "Nikhil 1",
        "user_id": 120,
        "user_role_id": 3,
        "is_active": 1
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Wrong OTP"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "OTP already verified"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Email id not registered"
    }
    """
    try:
        validator = VerifyOtpValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            user_email = request.data.get('user_email')
            otp = request.data.get('otp')

            # if email exists
            if User.objects.filter(email=user_email.lower()).exists():

                # if OTP is not verified already
                if not User.objects.filter(email=user_email.lower(), is_otp_verified=1).exists():

                    # if OTP is correct
                    if User.objects.filter(email=user_email.lower(), verification_code=otp).exists():

                        # Update data in db
                        User.objects.filter(email=user_email).update(
                            verification_code=0,
                            is_otp_verified=1,
                            is_login=1
                        )

                        # Get user info using email
                        user_info = User.objects.filter(email=user_email).values()

                        # Generate the access token & refresh token
                        access_token = encryptionHelper().jwtAccessToken(user_info[0]['id'])
                        refresh_token = encryptionHelper().jwtRefreshToken(user_info[0]['id'])

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

                        # Generate hash token to store in DB
                        hashed_token = hashlib.sha256(
                            JwtConstants.REFRESH_TOKEN_SALT.encode() +
                            refresh_token.encode()
                        ).hexdigest()
                        refresh_token_object = RefreshToken.objects.create(
                            token=hashed_token
                        )
                        refresh_token_object.save()

                        return Response(data, status=status.HTTP_200_OK)
                    else:
                        return Response({'error': Messages.WRONG_OTP}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': Messages.OTP_ALREADY_VERIFIED}, status=status.HTTP_200_OK)
            else:
                return Response({'error': Messages.EMAIL_NOT_REGISTER}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/verify_otp', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def resend_otp(request):
    """
    @api {post} v1/user/resend-otp Resend otp
    @apiName Resend otp
    @apiGroup User
    @apiHeader {String} Content-Type application/json
    @apiParam {String} user_email Email id
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "OTP sent"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Email id not registered"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "OTP already verified"
    }
    """
    try:
        validator = ResendOtpValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            user_email = request.data.get('user_email')

            # if email exists
            if User.objects.filter(email=user_email.lower()).exists():

                # if OTP is not verified already
                if not User.objects.filter(email=user_email.lower(), is_otp_verified=1).exists():

                    # Generate randor OTP
                    otp = ""
                    for i in range(4):
                        otp += str(r.randint(1, 9))

                    # update data in db
                    User.objects.filter(email=user_email).update(
                        verification_code=otp,
                        is_otp_verified=0
                    )

                    # Send email
                    EthosCommon.sendVerificationCode("", user_email, otp)
                    return Response({'message': Messages.OTP_SENT}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': Messages.OTP_ALREADY_VERIFIED}, status=status.HTTP_200_OK)
            else:
                return Response({'error': Messages.EMAIL_NOT_REGISTER}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/resend_otp', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login(request):
    """
        @api {POST} v1/user/login Login
        @apiName Login
        @apiGroup User
        @apiDescription login
        @apiParam {string} email email
        @apiParam {string} password password
        @apiParam {string} device_token device token
        @apiParam {integer} device_type device type 1 for android, 2 for ios
        @apiParam {integer} user_role_id user role id, 1->admin, 2-> sub admin, 3-> app user
        @apiParam {string} social_token social login token for facebook, google or apple
        @apiSuccessExample Success-Response:
        HTTP/1.1 200 OK
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.
            eyJ1c2VyX2lkIjoxLCJleHAiOjE1OTM3NzE2MTh9.
            wFKbwgqua5qN7AUaucagCgfpj3D_HcegzVDZJK5NHvo",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.
            eyJ1c2VyX2lkIjoxLCJleHAiOjE1OTg4NjkyMTh9.
            lYLNr47OwiMIB0vWvIIm3UE11rAr8FcIOykCJFjDztE",
            "email": "nitesh.jangir@techaheadcorp.com",
            "image": null,
            "is_email_verified": 1,
            "name": "Nitesh Jangir",
            "user_id": 1,
            "user_role_id": 3
        }
        @apiErrorExample Error-Response:
        HTTP/1.1 200 OK
        {
            "error": "Email id not registered"
        }
        @apiErrorExample Error-Response:
        HTTP/1.1 200 OK
        {
            "social_signup": 0
        }
        @apiErrorExample Error-Response:
        HTTP/1.1 200 OK
        {
            "access_token": "",
            "refresh_token": "",
            "email": "rits.chaudhary6572@gmail.com",
            "image": "",
            "is_email_verified": 0,
            "name": "vivek chaudhary",
            "user_id": 100,
            "user_role_id": 3,
            "is_active": 0
        }
    """
    try:
        utility = hashingUtility()
        # get the credintial email and password
        check_pass = False
        apple_login = False
        email = request.data['email'].lower()
        password = request.data['password']
        device_token = request.data['device_token']
        device_type = request.data['device_type']
        social_token = request.data['social_token']
        user_role_id = request.data['user_role_id']

        if 'social_login_id' in request.data and request.data['social_login_id'] == "2":
            validator = SocialLoginValidator(request.data)
        else:
            validator = LoginValidator(request.data)
        valid = validator.validate()  # validate the input request
        if valid:
            if social_token != '':
                # if user try to login with apple
                if 'social_login_id' in request.data and request.data['social_login_id'] == "2":
                    if not User.objects.filter(is_deleted=0, social_token=social_token,role=user_role_id).exists():
                        data = {
                            "social_signup": 0
                        }
                        return Response(data, status=status.HTTP_200_OK)
                    apple_login = True
                # user send social token bu does not exist in our db
                else:
                    if not User.objects.filter(email=email, is_deleted=0, social_token=social_token,role=user_role_id).exists():
                        data = {
                            "social_signup": 0
                        }
                        return Response(data, status=status.HTTP_200_OK)

            # if user try to login with apple
            if apple_login:
                user_object = User.objects.filter(social_token=social_token, is_deleted=0, role=user_role_id).exists()
                user_info = User.objects.filter(social_token=social_token).values()
            else:
                # if email exists continue
                user_object = User.objects.filter(email=email, is_deleted=0, role=user_role_id).exists()
                user_info = User.objects.filter(email=email).values()

            if user_object:
                data = {
                    "access_token": "",
                    "refresh_token": "",
                    "email": user_info[0]['email'],
                    "image": user_info[0]['profile_pic'],
                    "is_email_verified": user_info[0]['is_otp_verified'],
                    "name": user_info[0]['name'],
                    "user_id": user_info[0]['id'],
                    "user_role_id": user_info[0]['role_id'],
                    "is_active": user_info[0]['is_active']
                }
                if social_token != '':
                    # in case of social login check_pass will be true because no need of password when user came through social login
                    check_pass = True
                else:
                    if utility.matchHashedPassword(user_info[0]['password'], user_info[0]['password_salt'], password):
                        # match the password, if same then check_pass will be true
                        check_pass = True
                    else:
                        # match the password, if not match then check_pass will be false
                        check_pass = False
                if check_pass:
                    if user_info[0]['is_active']==1 and user_info[0]['is_otp_verified'] == 1:
                        # generate the access token
                        access_token = encryptionHelper().jwtAccessToken(
                            user_info[0]['id'])
                        # generate the refresh token
                        refresh_token = encryptionHelper().jwtRefreshToken(
                            user_info[0]['id'])
                        # update the user information
                        User.objects.filter(id=user_info[0]['id']).update(
                            device_token=device_token,
                            device_type=device_type,
                            is_login=1
                        )
                        # generate hash token to store in DB
                        hashed_token = hashlib.sha256(
                            JwtConstants.REFRESH_TOKEN_SALT.encode() +
                            refresh_token.encode()).hexdigest()
                        # create refresh token in DB . .
                        refresh_token_object = RefreshToken.objects.create(
                            token=hashed_token
                        )
                        # save tha object
                        refresh_token_object.save()
                        # update token values
                        update_tokens = {
                            "access_token": access_token,
                            "refresh_token": refresh_token
                        }
                        data.update(update_tokens)
                        return Response(data, status=status.HTTP_200_OK)
                    else:
                        return Response(data, status=status.HTTP_200_OK)
                else:
                    return Response({'error': Messages.INVALID_PASSWORD}, status=status.HTTP_200_OK)
            else:
                return Response({'error': Messages.EMAIL_NOT_REGISTER}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/login', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# This method is used to send the verification link in forget password
@api_view(['POST'])
def forgot_password(request):
    """
    @api {POST} v1/user/forgot-password Forgot password
    @apiName Forgot password
    @apiGroup User
    @apiDescription When user enter the email then a link will be sent to email
    @apiParam {string} email
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "A link is sent to your Registered email address"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Email id not registered"
    }
    """
    try:
        validator = ForgotValidator(request.data)
        valid = validator.validate()  # validate the request
        if valid:
            email = request.data['email'].lower()
            user_info = User.objects.filter(email=email, is_active = 1, is_deleted = 0).values()  # check email exists or not
            token = base64.b64encode(email.encode('utf-8', 'strict'))
            # generate a random hex key
            token_value = secrets.token_hex(20)
            if user_info:
                # update the verification key
                User.objects.filter(id=user_info[0]['id']).update(
                    password_reset_token = token_value
                )
                # generate a link to send over mail
                link = EmailConstants.verificationLink+"reset-password?tokenValue=" + \
                    token_value+"&token=" + token.decode('utf-8')
                # message body of mail
                message = '<h3>'+"Hello"+" "+user_info[0]['name']+","+'</h3><p>'+" "+"Hopefully you have requested to reset the password for your The Ethos Network account.. If you did not perform this request, you can safely ignore this email. Otherwise, click the link below to complete the process."+'</p><br><br>' + \
                    '<a href='+link+' target="_blank" style="display:inline-block;background:#2c8ae3; padding:7px 10px;color:#fff; text-decoration:none; display:inline-block; text-align:center; margin:10px auto 0; border-radius:4px">' + \
                    "Click here"+'</a><br><br>'
                email_from = EthosCommonConstants.EMAIL_HOST_USER
                email_to = email
                # send mail using sendgrid
                emailTemplates.sendLinkMail(
                    "Password Reset Link", email_from, email_to, message, "Welcome to The Ethos Network")

                return Response({'message': Messages.FORGOT_PASSWORD}, status=status.HTTP_200_OK)
            else:
                return Response({'error': Messages.EMAIL_NOT_REGISTER}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/forgot_password', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# This method is used to reset password through link
@api_view(['PUT'])
def reset_password(request):
    """
    @api {PUT} v1/user/reset-password Reset password
    @apiName Reset password
    @apiGroup User
    @apiDescription Reset password when user enter new password
    @apiParam {string} tokenValue associate with link
    @apiParam {string} token associate with link
    @apiParam {string} password Enter new password
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": Password Updated!"
    }
    """
    try:
        validator = ResetValidator(request.data)
        valid = validator.validate()  # validate the request
        if valid:
            utility = hashingUtility()
            token_value = request.data["tokenValue"]
            token = request.data["token"]
            password = request.data["password"]
            encoded_email = base64.b64decode(token)
            email = encoded_email.decode('utf-8')
            # check token is expired or not
            user_info = User.objects.filter(email=email, password_reset_token=token_value).values()
            # generate a random hex key
            token_value = secrets.token_hex(20)
            if user_info:
                hashed_model = utility.getHashedPassword(password)
                # update the verification key as well as password
                User.objects.filter(id=user_info[0]['id']).update(
                    password = str(hashed_model.Password, 'utf-8'),
                    password_salt = str(hashed_model.Salt, 'utf-8'),
                    password_reset_token = token_value
                )
                return Response({'message': Messages.PASSWORD_UPDATE}, status=status.HTTP_200_OK)
            else:
                return Response({'error': Messages.LINK_EXPIRED}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/reset_password', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# This method is used to logout the user
@api_view(['GET'])
@isAuthenticate
def logout(request):
    """
    @api {GET} v1/user/logout Logout users
    @apiName Logout users
    @apiHeader {String} authorization Users unique access-token.
    @apiGroup Auth
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "user logged out successfully!"
    }
    """
    try:
        user_id = request.user_id
        User.objects.filter(id=user_id).update(
            is_login = 0,
            device_token=""
        )
        return Response({'message': Messages.USER_LOGOUT}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/logout', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# This method is used to renew the refresh token
@api_view(['POST'])
def refresh_token(request):
    """
    @api {post} v1/user/refresh-token Refresh access token
    @apiName Refresh access token
    @apiGroup User
    @apiDescription Need to pass valid refresh token to get access token.
    @apiHeader {String} content_type Use type "application/json".
    @apiParam {string} refresh_token Refresh token to get new access token.
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.
        eyJ1c2VyX2lkIjoxLCJleHAiOjE1OTM3NzE1NjR9.
        BH4ohXP6qGeVj374Dk4ydoTPNcjS_G-8IawRvIMhd08",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.
        eyJ1c2VyX2lkIjoxLCJleHAiOjE1OTg4NjkxNjR9.
        zpB7KvQDR3m3IZKgQnCCkFgqTwbbgQIxfDMd_adNypg"
    }
    """
    try:
        validator = RefreshValidator(request.data)
        valid = validator.validate()  # validate the request
        if valid:
            result = encryptionHelper().getNewAccessToken(request.data["refresh_token"])
            return Response(result[0]["data"], status = result[0]["status"])
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/refresh_token', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# This method is used to renew the refresh token
@api_view(['PUT'])
@isAuthenticate
def change_password(request):
    """
    @api {PUT} v1/user/change-password To change the password
    @apiName To change the password
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {string} password current password
    @apiParam {string} new_password new Password
    @apiSuccessExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Password changed successfully!"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Email id not registered"
    }
    @apiErrorExample Error-Response:
    HTTP/1.1 200 OK
    {
        "error": "Old password not matched"
    }
    """
    try:
        validator = ChangePasswordValidator(request.data)
        valid = validator.validate()  # validate the request
        password = request.data['password']
        new_password = request.data['new_password']
        if valid:
            utility = hashingUtility()
            user_info = User.objects.filter(id=request.user_id).values()
            if user_info:
                if utility.matchHashedPassword(user_info[0]['password'], user_info[0]['password_salt'], password):
                    hashed_model = utility.getHashedPassword(new_password)
                    # update the verification key as well as password
                    User.objects.filter(id=user_info[0]['id']).update(
                        password = str(hashed_model.Password, 'utf-8'),
                        password_salt = str(hashed_model.Password, 'utf-8')
                    )
                    return Response({'message': Messages.PASSWORD_UPDATE}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': Messages.OLD_PASS_NOT_MATCHED}, status=status.HTTP_200_OK)
            else:
                return Response({'error': Messages.EMAIL_NOT_REGISTER}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/change_password', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# block-unblock user
@api_view(['POST'])
@isAuthenticate
@RbacService('profile:update')
def user_block_unblock(request):
    """
    @api {POST} v1/user/block-unblock Block-Unblock user
    @apiName Bloc and unblock user
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {integer} blocked_user_id id of user which you want to block or unblock
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "user_block_id": "1"
    }
    @apiErrorExample Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "User has been unblocked"
    }
    """
    try:
        validator = BlockUnblockValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:
            user_id = request.user_id
            blocked_user_id = request.data.get('blocked_user_id')
            if UserBlockedContacts.objects.filter(user_id=user_id, blocked_user_id=blocked_user_id).exists():
                UserBlockedContacts.objects.filter(user_id=user_id, blocked_user_id=blocked_user_id).delete()
                return Response({'message':Messages.REMOVE_USER_BLOCK}, status=status.HTTP_200_OK)
            user_obj = User.objects.get(id=user_id)
            blocked_user_obj = User.objects.get(id=blocked_user_id)
            if UserInterest.objects.filter(user_id=user_id, interested_user_id=blocked_user_id).exists():
                UserInterest.objects.filter(user_id=user_id, interested_user_id=blocked_user_id).delete()
            UserBlockedContacts.objects.create(
                user_id = user_obj,
                blocked_user_id = blocked_user_obj
            )
            latest_user_obj = UserBlockedContacts.objects.latest('id')
            return Response({'user_block_id':latest_user_obj.id}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_block_unblock', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# notification on/off
@api_view(['POST'])
@isAuthenticate
@RbacService('user:setting:write')
def user_change_setting(request):
    """
    @api {POST} v1/user/change-setting Change Setting Toggles
    @apiName Change Setting Toggle (Notification, Saved Post, Location, Private account)
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token.
    @apiParam {string} request_type Notification toggle - `notification` or
                                    Location toggle - `location` or
                                    Saved post toggle - `savedpost` or
                                    Account private toggle - `account`
                                    App location toggle - 'app_location'
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "message": "Notification setting updated"
    }
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1.1 200 OK
    {
        "message": "Location setting updated"
    }
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1.1 200 OK
    {
        "message": "Saved Post setting updated"
    }
    HTTP/1.1 200 OK
    {
        "message": "Your Account has been private"
    }
    HTTP/1.1 200 OK
    {
        "message": "Your Account has been public"
    }
    """
    try:
        validator = SettingToggleValidator(request.data)
        valid = validator.validate()  # Validate the request
        if valid:

            user_id = request.user_id
            request_type = request.data.get('request_type')
            user_obj = User.objects.filter(id=user_id).values()

            # change notification setting
            if request_type == 'notification':
                if user_obj[0]['is_notification_active']:
                    User.objects.filter(id=user_id).update(
                        is_notification_active=0
                    )
                else:
                    User.objects.filter(id=user_id).update(
                        is_notification_active=1
                    )
                message = Messages.NOTIFICATION_SETTING_CHANGED

            # change location setting
            if request_type == 'location':
                if user_obj[0]['is_location_public']:
                    User.objects.filter(id=user_id).update(
                        is_location_public=0
                    )
                else:
                    User.objects.filter(id=user_id).update(
                        is_location_public=1
                    )
                message = Messages.LOCATION_SETTING_CHANGED

            # change saved post setting
            if request_type == 'savedpost':
                if user_obj[0]['is_saved_post_public']:
                    User.objects.filter(id=user_id).update(
                        is_saved_post_public=0
                    )
                else:
                    User.objects.filter(id=user_id).update(
                        is_saved_post_public=1
                    )
                message = Messages.SAVED_POST_SETTING_CHANGED

            # change private account setting
            if request_type == 'account':
                if user_obj[0]['is_account_private']:
                    User.objects.filter(id=user_id).update(
                        is_account_private=0
                    )
                    message = Messages.PUBLIC_ACCOUNT
                else:
                    User.objects.filter(id=user_id).update(
                        is_account_private=1
                    )
                    message = Messages.PRIVATE_ACCOUNT

            # change app location setting
            if request_type == 'app_location':
                if user_obj[0]['app_location_setting']:
                    User.objects.filter(id=user_id).update(
                        app_location_setting=0
                    )
                    message = Messages.APP_LOCATION_OFF
                else:
                    User.objects.filter(id=user_id).update(
                        app_location_setting=1
                    )
                    message = Messages.APP_LOCATION_ON

            # Update data in redis
            redis_object = redis.Redis(EthosCommonConstants.REDIS_HOST)  # Redis object
            redis_key = RedisCommon.user_own_details + str(user_id)  # Key in which we will store data

            # Check if already exist in Redis then don't need to call SQL
            if redis_object.get(redis_key):
                user_details = _pickle.loads(redis_object.get(redis_key))
                user_details['is_notification_active'] = int(user_obj[0]['is_notification_active'])
                user_details['is_location_public'] = int(user_obj[0]['is_location_public'])
                user_details['is_saved_post_public'] = int(user_obj[0]['is_saved_post_public'])
                user_details['is_account_private'] = int(user_obj[0]['is_account_private'])
                user_details['app_location_setting'] = int(user_obj[0]['app_location_setting'])

                # Set data in Redis
                RedisCommon().set_data(redis_key, user_details)

            return Response({'message': message}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_change_setting', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# get user setting details
@api_view(['GET'])
@isAuthenticate
@RbacService('user:setting:read')
def user_setting(request):
    """
    @api {GET} v1/user/get-setting Get User setting details
    @apiName Get User setting details
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "is_notification_active": 0,
        "is_location_public": 1,
        "is_saved_post_public": 1,
        "app_location_setting": 0
    }
    """
    try:
        user_id = request.user_id
        user_info = User.objects.get(id=user_id)
        serializer = UserSettingSerializer(user_info, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_setting', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# get blocked user listing
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def user_blocked_list(request):
    """
    @api {GET} v1/user/blocked/list Get blocked user list
    @apiName Get blocked user list
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} page_limit
    @apiHeader {integer} page_offset
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "name": "Test 03",
                "id": 2,
                "email": "test03@yopmail.com",
                "profile_pic": "profilepic.png"
            }
        ]
    }
    HTTP/1.1 200 OK
    {
        "data": []
    }
    """
    try:
        validator = UserBlockedValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            user_id = request.user_id
            user_ids = list(UserBlockedContacts.objects.filter(user_id=user_id).values_list('blocked_user_id', flat=True).distinct()[page_offset:page_limit+page_offset])
            user_info = User.objects.filter(id__in=user_ids)
            if len(user_info) > 0:
                serializer = SuggestedUsersSerializer(user_info, many=True)
                return Response({'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'data':[]}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_blocked_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# get blocked user listing
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def user_unblocked_list(request):
    """
    @api {GET} v1/user/unblocked/list Get User Unblocked List
    @apiName Get User Unblocked List
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} page_limit
    @apiHeader {integer} page_offset
    @apiHeader {string} name
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "name": "Test 03",
                "id": 2,
                "email": "test03@yopmail.com",
                "profile_pic": "profilepic.png"
            },
            {
                "name": "Test 06",
                "id": 3,
                "email": "test06@yopmail.com",
                "profile_pic": "profilepic.png"
            },
            {
                "name": "Test 04",
                "id": 4,
                "email": "test04@yopmail.com",
                "profile_pic": "profilepic.png"
            },
            {
                "name": "Test 25",
                "id": 5,
                "email": "test25@yopmail.com",
                "profile_pic": ""
            },
            {
                "name": "xyz",
                "id": 6,
                "email": "xyz@yopmail.com",
                "profile_pic": ""
            },
            {
                "name": "new",
                "id": 7,
                "email": "ethos@yopmail.com",
                "profile_pic": ""
            },
            {
                "name": "Test 26",
                "id": 8,
                "email": "test26@yopmail.com",
                "profile_pic": ""
            },
            {
                "name": "new",
                "id": 9,
                "email": "ethos123@yopmail.com",
                "profile_pic": ""
            },
            {
                "name": "xyz",
                "id": 10,
                "email": "xyz123@yopmail.com",
                "profile_pic": ""
            },
            {
                "name": "test",
                "id": 11,
                "email": "test@yopmail.com",
                "profile_pic": ""
            }
        ]
    }
    HTTP/1.1 200 OK
    {
        "data": []
    }
    """
    try:
        validator = UserBlockedValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])
            name = request.GET['name']
            user_id = request.user_id

            # blocked user ids
            blocked_user_list = list(UserBlockedContacts.objects.filter(
                user_id=user_id
            ).values_list('blocked_user_id', flat=True).distinct())
            user_interested_list = list(UserInterest.objects.filter(
                user_id=user_id
            ).values_list('interested_user_id', flat=True).distinct())
            blocked_user_list.append(user_id)
            user_info = User.objects.filter(id__in=user_interested_list, name__icontains=name).exclude(id__in=blocked_user_list)[page_offset:page_limit+page_offset]
            if len(user_info) > 0:
                serializer = SuggestedUsersSerializer(user_info, many=True)
                return Response({'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'data':[]}, status=status.HTTP_200_OK)
        else:
            return Response({'error':requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_unblocked_list', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# get interested user listing
@api_view(['GET'])
@isAuthenticate
@RbacService('user:read')
def user_interested_list(request):
    """
    @api {GET} v1/user/interested/list Get interested user list
    @apiName Get interested user list
    @apiGroup User
    @apiHeader {String} authorization Users unique access-token
    @apiHeader {integer} type 1 => logged in user interested list, 2 => Users who added logged in user as their interest
    @apiParam {integer} page_limit Page limit
    @apiParam {integer} page_offset Page offset
    @apiParam {integer} user_id Other user id, Default => 0
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "name": "pawan",
                "id": 106,
                "email": "psrathore13081992@gmail.com",
                "profile_pic": "",
                "is_interested": 0,
                "is_request_sent": false
            },
            {
                "name": "newuser",
                "id": 17,
                "email": "newuser@yopmail.com",
                "profile_pic": "",
                "is_interested": 1,
                "is_request_sent": false
            }
        ]
    }
    HTTP/1.1 200 OK
    {
        "data": []
    }
    """
    try:
        validator = InterestedUserListValidator(request.GET)
        valid = validator.validate()  # Validate the request
        if valid:
            list_type = int(request.GET['type'])
            user_id = int(request.GET['user_id'])
            current_user_id = request.user_id

            # Other user profile
            if user_id > 0:
                user_id_interested = user_id
            else:
                user_id_interested = request.user_id

            page_limit = int(request.GET['page_limit'])
            page_offset = int(request.GET['page_offset'])

            # Logged in user interested list
            if list_type == 1:
                user_ids = UserInterest.objects.filter(
                    user_id=user_id_interested
                ).values_list(
                    'interested_user_id', flat=True
                ).distinct()

                if user_id > 0:
                    user_interest = UserInterest.objects.filter(
                        user_id=current_user_id
                    ).values_list(
                        'interested_user_id', flat=True
                    ).distinct()
                else:
                    user_interest = user_ids

            # Users who added logged in user as their interest
            if list_type == 2:
                user_ids = UserInterest.objects.filter(
                    interested_user_id=user_id_interested
                ).values_list(
                    'user_id', flat=True
                ).distinct()

                if user_id > 0:
                    user_interest = UserInterest.objects.filter(
                        user_id=current_user_id
                    ).values_list('interested_user_id', flat=True).distinct()
                else:
                    user_interest = UserInterest.objects.filter(
                        user_id=user_id_interested
                    ).values_list('interested_user_id', flat=True).distinct()

            if len(user_ids) > 0:

                user_list = User.objects.filter(
                    id__in=user_ids,
                    is_deleted=0
                ).values().exclude(
                    id=user_id_interested
                ).order_by('id').reverse()[page_offset:page_limit+page_offset]

                serializer = SuggestedUsersSerializer(user_list, many=True)

                response = []
                if len(serializer.data) > 0:

                    for data in serializer.data:
                        if data['id'] in user_interest:
                            is_interested = 1
                        else:
                            is_interested = 0

                        is_request_sent = UserInterestsRequest.objects.filter(
                            user_id=current_user_id, interested_user_id=data['id']
                        ).exists()

                        response.append({
                            'name': data['name'],
                            'id': data['id'],
                            'email': data['email'],
                            'profile_pic': data['profile_pic'],
                            'is_interested': is_interested,
                            'is_request_sent': is_request_sent
                        })

                return Response({'data': response}, status=status.HTTP_200_OK)
            else:
                return Response({'data': []}, status=status.HTTP_200_OK)
        else:
            return Response({'error': requestErrorMessagesFormate(validator.get_message())}, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/user_interested_list', str(exception))
        return Response({'error': str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# version check
@api_view(['POST'])
def version_check(request):
    """
    @api {POST} v1/user/version-check Version check
    @apiName Version check
    @apiGroup User
    @apiParam {string} app_version App version
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "is_registration_bypass": true,
        "causes_ids": [2, 3, 4, 5, 6, 7, 8]
    }
    """
    try:
        review_app_version = "1.3"
        app_version = request.data.get('app_version')
        is_registration_bypass = False

        # Check the uploaded version
        if app_version == review_app_version:
            is_registration_bypass = True

        # Get active causes Ids
        causes_ids = Cause.objects.filter(is_deleted=0, is_active=1).values_list('id', flat=True).distinct()

        response = {
            "is_registration_bypass": is_registration_bypass,
            "causes_ids": list(causes_ids)
        }

        return Response(response, status=status.HTTP_200_OK)
    except Exception as exception:
        logerror('users/views.py/version_check', str(exception))
        return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
