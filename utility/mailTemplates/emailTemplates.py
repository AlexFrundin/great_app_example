# This template file is using to share common email template

import datetime
import smtplib
from ethos_network.settings import EthosCommonConstants
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from utility.loggerService import logerror


class emailTemplates:

    # Send email with link
    def sendLinkMail(subject, from_email, to_emails, body, title):

        try:
            date = datetime.datetime.now()

            currentDate = datetime.datetime.now()
            currentYear = currentDate.strftime("%Y")

            msgBody = f'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml">'
            msgBody += '<head>'
            msgBody += '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
            msgBody += '<meta name="format-detection" content="telephone=no">'
            msgBody += '<meta name="viewport" content="width=device-width; initial-scale=1.0; maximum-scale=1.0; "user-scalable=no;">'
            msgBody += '<meta http-equiv="X-UA-Compatible" content="IE=9; IE=8; IE=7; IE=EDGE" />'
            msgBody += '<title>'+title+'</title>'
            msgBody += '<style type="text/css">'
            msgBody += '/* Some resets and issue fixes */'
            # outlook a { padding:0; }
            msgBody += 'body{ width:100% !important; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; margin:0; padding:0; }.ReadMsgBody { width: 100%; } .ExternalClass {width:100%;} .backgroundTable {margin:0 auto; padding:0; width:100% !important;} table td {border-collapse: collapse;} .ExternalClass * {line-height: 115%;}   * End reset */  h1,h2,h3,h4,h5,h6,p { margin: 0; padding: 0; line-height: 1.1;  font-family: "Helvetica", "Arial", sans-serif; } p,a,li { font-family: "Helvetica", "Arial", sans-serif; } img { /* width: 100%; */ display: block; } *[class="100pad"] {width:100% !important; padding: 0 70px;}  @media screen and (max-width: 600px) { *[class="mobile-column"] {display: block;} *[class="100p"] {width:100% !important; height:auto !important;}  }'
            msgBody += '</style>'
            msgBody += '</head>'

            msgBody += '<body style="padding:0; margin:0">'
            msgBody += '<table width="100%" bgcolor="#FFFFFF" border="0" cellpadding="0" cellspacing="0">'
            msgBody += '<tr>'
            msgBody += '<td align="center" valign="top">'
            msgBody += '<table width="600" cellspacing="0" cellpadding="0" border="0" class="100p">'
            msgBody += '<tr>'
            msgBody += '<td height="30"></td>'
            msgBody += '</tr>'
            msgBody += '<tr>'
            msgBody += '<td align="center">'
            msgBody += '<img src="https://ethosnetworkassets.s3.eu-west-2.amazonaws.com/logo.png" alt="" >'
            msgBody += '</td>'
            msgBody += '</tr>'
            msgBody += '<tr>'
            msgBody += '<td height="40"></td>'
            msgBody += '</tr>'
            msgBody += '<tr>'
            msgBody += '<td align="center">'
            msgBody += '<img src="https://sitescommonblobstorage.blob.core.windows.net/assets/message.svg" alt="" >'
            msgBody += '</td>'
            msgBody += '</tr>'
            msgBody += '<tr>'
            msgBody += '<td height="60"></td>'
            msgBody += '</tr>'
            msgBody += '<tr>'
            msgBody += '<td align="center" class="100pad">'
            msgBody += '<h1 style="font-size: 36px; font-weight: bold; margin-bottom: 30px;">'+title+'</h1>'
            msgBody += body
            msgBody += '</td>'
            msgBody += '</tr>'
            msgBody += '<tr>'
            msgBody += '<td align="center">'
            msgBody += '<p style="font-size: 12px; line-height: 20px;">'
            msgBody += 'Regards,<br>The Ethos Network Ltd., London, UK <br><br>©The Ethos Network Ltd.'
            msgBody += '</p>'
            msgBody += '</td>'
            msgBody += '</tr>'
            msgBody += '<tr>'
            msgBody += '<td height="30"></td>'
            msgBody += '</tr>'
            msgBody += '</table>'
            msgBody += '</td>'
            msgBody += '</tr>'
            msgBody += '</table>'
            msgBody += '</body>'
            msgBody += '</html>'

            # Mail Configuration
            subject = subject
            html_content = msgBody
            to = [to_emails]
            from_email = from_email
            sg = send_mail(subject, None, from_email,to,html_message=html_content,fail_silently=True)
            return True
        except smtplib.SMTPException as exception:
            logerror('utility/mailTemplates/emailTemplates.py', str(exception))
            return Response({'error':str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
