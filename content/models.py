from rest_framework import status
from django.db import models

class StaticContent(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    terms_and_conditions = models.TextField()
    privacy_policy = models.TextField()
    about_us = models.TextField()

    class Meta:
        db_table = 'static_content'

class Newsletter(models.Model):
    id = models.IntegerField(default=False, null=False, primary_key=True)
    content = models.TextField()
    created_at =models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'newsletters'

"""
class ContentModel():

    def content_list_model(self, request):
        try:

            # DB query
            database = databaseConnection()
            content_result = database.readProcedureJson(
                "ethos_getContentList", [])
            database.dispose()

            # If there is result
            if len(content_result) > 0:

                return[{"data": toJsonResult(True, 'Content list has been fetched.', content_result),
                        "status": status.HTTP_200_OK}]
            return[{"data": toJsonResult(False, 'No result found.', []),
                    "status": status.HTTP_200_OK}]

        except (BaseException, mysql.connector.Error) as error:
            logerror('content_list_model', str(error))
            return[{"data": toJsonResult(False, "Exception."+str(error), {}),
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR}]

    def insert_content(self, request):
        try:
            # DB query
            database = databaseConnection()
            param = []
            param.append(request['content'])
            database.readProcedureJson("ethos_insertContent", param)
            database.dispose()
            return[{"data": toJsonResult(True, 'Content created successfully', {}),
                    "status": status.HTTP_200_OK}]
        except mysql.connector.Error as exception:
            logerror('insert_content', str(exception))
            return[{"data": toJsonResult(False, "Exception."+str(exception), {}),
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR}]
"""
