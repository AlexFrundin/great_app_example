# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

"""
Authorization middleware if an image or stored video contains unsafe content,
such as /explicit adult content or violent content.
"""
import os
import boto3
import json
import sys
import time
from better_profanity import profanity
from rest_framework.response import Response
from rest_framework import status
from botocore.config import Config
from botocore.exceptions import ClientError
from ethos_network.settings import BUCKET_NAME, REGION


# Class for detection methods
class ContentDetect:

    # IN_PROGRESS | SUCCEEDED | FAILED
    jobId = ''
    rekognition = boto3.client(
                        "rekognition", REGION,
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID_CUS'), 
                        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY_CUS')
                    )
    bucket = BUCKET_NAME


    # Detecting unsafe image and text
    # The image must be in either a .jpg or a .png format.
    def detect_image_labels(self, photo, max_labels=10, min_confidence=70):
        try:
            response = self.rekognition.detect_moderation_labels(
                Image={"S3Object": {"Bucket": self.bucket, "Name": photo}},
                # MaxLabels=max_labels,
                MinConfidence = min_confidence,
            )

            # To detect unsafe image
            if len(response['ModerationLabels']):
                return {'result': response['ModerationLabels']}
            # To detect unsafe text on image
            response = self.rekognition.detect_text(Image={'S3Object': {'Bucket': self.bucket, 'Name': photo}})

            if len(response['TextDetections']) :
                for text in response['TextDetections']:
                    if profanity.contains_profanity(text['DetectedText']):
                        return {'result': 'Detected text: ' + text['DetectedText'] + '  Confidence: ' + "{:.2f}".format(text['Confidence']) + "%"}

            return {'result': []}
        except (ClientError, Exception) as e:
            return {'error': str(e)}


    # Starts asynchronous detection of unsafe content in a stored video.
    def detect_video_labels(self, video):
        try:
            response = self.rekognition.start_content_moderation(
                Video = {
                    'S3Object': {
                        'Bucket': self.bucket,
                        'Name':video
                    }
                },
                NotificationChannel = {
                    'SNSTopicArn': 'arn:aws:sns:eu-west-2:668895672969:ethos-SNS',
                    'RoleArn': 'arn:aws:iam::668895672969:role/Rekognition-iam-role'
                },
                JobTag='detect-content'
            )
            self.jobId = response['JobId']
            return {'result': self.jobId}
        except (ClientError, Exception) as e:
            return {'error': str(e)}


    # Starts asynchronous detection of text in a stored video.
    def detect_video_text_labels(self, video):
        try:
            response = self.rekognition.start_text_detection(
                Video = {
                    'S3Object': {
                        'Bucket': self.bucket,
                        'Name': video
                    }
                },
                NotificationChannel = {
                    'SNSTopicArn': 'arn:aws:sns:eu-west-2:668895672969:ethos-SNS',
                    'RoleArn': 'arn:aws:iam::668895672969:role/Rekognition-iam-role'
                },
                JobTag='detect-text'
            )
            self.jobId = response['JobId']
            return {'result': self.jobId}
        except (ClientError, Exception) as e:
            return {'error': str(e)}               


    # Gets the results of unsafe content label detection by calling
    # GetContentModeration. Analysis is started by a call to StartContentModeration.
    # jobId is the identifier returned from StartContentModeration
    def get_results_moderation_labels(self, job_id):
        try:
            max_results = 10
            pagination_token = ''
            finished = False
            check_count = 0

            # Start detection of unsafe video
            while not finished:
                response = self.rekognition.get_content_moderation(JobId = job_id, MaxResults = max_results, NextToken = pagination_token)
                if response['JobStatus'] == 'IN_PROGRESS':
                    if check_count < 20:
                        check_count = check_count + 1
                    else:
                        check_count = 0
                    sys.stdout.flush()
                    time.sleep(3)
                    continue
                elif response['JobStatus'] == 'SUCCEEDED':
                    finished = True
                    if len(response['ModerationLabels']) :
                        return {'result': response['ModerationLabels']}
                    else :
                        return {'result': []}    

                elif response['JobStatus'] == 'FAILED':
                    finished = True
                    return {'error': response['StatusMessage']}             
        except ClientError as e:
            return {'error': str(e)}


    # Gets the text detection results of a Amazon Rekognition Video analysis started by StartTextDetection .
    def get_text_results_moderation_labels(self, job_id):
        try:
            max_results = 10
            pagination_token = ''
            finished = False
            check_count = 0

            # Start detection of unsafe video
            while not finished:
                # Start detection of unsafe text in video
                response = self.rekognition.get_text_detection(JobId = job_id, MaxResults = max_results, NextToken = pagination_token)
                if response['JobStatus'] == 'IN_PROGRESS':
                    if check_count < 20:
                        check_count = check_count + 1
                    else:
                        check_count = 0
                    sys.stdout.flush()
                    time.sleep(3)
                    continue
                elif response['JobStatus'] == 'SUCCEEDED':
                    if len(response['TextDetections']):
                        for textDetection in response['TextDetections']:
                            text = textDetection['TextDetection']
                            if profanity.contains_profanity(text['DetectedText']):
                                finished = True
                                return {'result': 'Detected text: ' + text['DetectedText']}
                    return {'result': []}
                elif response['JobStatus'] == 'FAILED':
                    finished = True
                    return {'error': response['StatusMessage']}
            return {'result':[]}
        except ClientError as e:
            return {'error': str(e)}             
