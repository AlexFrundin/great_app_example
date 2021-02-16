import json
import datetime
from utility.mailTemplates.emailTemplates import emailTemplates
import math
import os
from rest_framework import status
import ethos_network.settings as settings
from ethos_network.settings import EthosCommonConstants

#from Models.Common.applicationConfig import webConfigKey


class EthosCommon():

    def sendVerificationCode(name, email, otp):

        # Send email
        subject = "Account verification code"
        title = "Welcome to The Ethos Network"
        messageBodyPart1 = "Hello"
        messageBodyPart2 = "Welcome Aboard! Thanks for getting started with The Ethos Network."
        messageBodyPart3 = "Here is your verification code to complete your registration.<br/>"
        messageBodyPart3 += "<strong>OTP: "+otp+"</strong>"
        messageBodyPart5 = "Regards"
        messageBodyPart6 = "The Ethos Network Team"

        message = '<h3>'+messageBodyPart1+" "+name+","+'</h3><p>'
        message += messageBodyPart2+'</p><p>' + \
            messageBodyPart3+'</p><br/><br/>'+'<br/><br/>'
        message += '<p><br/>'+messageBodyPart5+","+'</p><p>'+messageBodyPart6+'</p>'
        emailFrom = EthosCommonConstants.EMAIL_HOST_USER
        emailTo = email
        emailTemplates.sendLinkMail(
            subject, emailFrom, emailTo, message, title)

    def send_content_moderation_email(post_details, invalid_content_type = ''):

        # Send email
        subject = "Inappropriate content detected"
        title = "Inappropriate content detected"
        messageBodyPart1 = "Hello Admin,"
        messageBodyPart2 = "The Ethos Network system detected that inappropriate content has been created or entered on the platform."
        messageBodyPart3 = "The platform sends an email to approve or reject the content.<br/>"
        messageBodyPart3 += "Kindly review the below details:<br/>"
        messageBodyPart3 += "<strong>Inappropriate content detected in: "+invalid_content_type+"</strong><br/>"
        messageBodyPart3 += "<strong>Post title: "+post_details['title']+"</strong><br/>"
        messageBodyPart3 += "<strong>Created date: "+post_details['created_on']+"</strong><br/>"
        messageBodyPart3 += "<strong>Created by: "+post_details['user_detail']['name']+"</strong><br/>"
        messageBodyPart5 = "Regards"
        messageBodyPart6 = "The Ethos Network Team"

        message = '<h3>'+messageBodyPart1+'</h3><p>'
        message += messageBodyPart2+'</p><p>' + \
                    messageBodyPart3+'</p><br/><br/>'+'<br/><br/>'
        message += '<p><br/>'+messageBodyPart5+","+'</p><p>'+messageBodyPart6+'</p>'
        emailFrom = EthosCommonConstants.ADMIN_EMAIL_ID
        emailTo = EthosCommonConstants.ADMIN_EMAIL_ID
        emailTemplates.sendLinkMail(subject, emailFrom, emailTo, message, title)

    def send_user_moderation_email(user_details):

        # Send email
        subject = "Inappropriate content detected"
        title = "Inappropriate content detected"
        messageBodyPart1 = "Hello Admin,"
        messageBodyPart2 = "The Ethos Network system detected that inappropriate content has been created or entered on the platform."
        messageBodyPart3 = "The platform sends an email to approve or reject the content.<br/>"
        messageBodyPart3 += "Kindly review the below details:<br/>"
        messageBodyPart3 += "<strong>Inappropriate content detected in: Users bio</strong><br/>"
        messageBodyPart3 += "<strong>Name: "+user_details['name']+"</strong><br/>"
        messageBodyPart3 += "<strong>Email: "+user_details['email']+"</strong><br/>"
        messageBodyPart3 += "<strong>Bio: "+user_details['bio']+"</strong><br/>"
        messageBodyPart5 = "Regards"
        messageBodyPart6 = "The Ethos Network Team"

        message = '<h3>'+messageBodyPart1+'</h3><p>'
        message += messageBodyPart2+'</p><p>' + \
                    messageBodyPart3+'</p><br/><br/>'+'<br/><br/>'
        message += '<p><br/>'+messageBodyPart5+","+'</p><p>'+messageBodyPart6+'</p>'
        emailFrom = EthosCommonConstants.ADMIN_EMAIL_ID
        emailTo = EthosCommonConstants.ADMIN_EMAIL_ID
        emailTemplates.sendLinkMail(subject, emailFrom, emailTo, message, title)

    def get_file_extention(file_name):
        file_ext = file_name.split(".")[-1]
        return file_ext
