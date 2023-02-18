import logging

import boto3
from django.conf import settings
from watchtower import CloudWatchLogHandler

AWS_CLOUDWATCH_CONFIG = getattr(settings, 'AWS_CLOUDWATCH', {})

DEVELOPER_MODE = AWS_CLOUDWATCH_CONFIG.get('DEVELOPER_MODE', False)


class BaseAWSCloudWatchHandler(CloudWatchLogHandler):
    def __init__(self, **kwargs):
        log_group_name = kwargs.get(
            'log_group_name',
            AWS_CLOUDWATCH_CONFIG.get('LOG_GROUP_NAME'),
        )
        boto3_client = boto3.client(
            'logs',
            aws_access_key_id=AWS_CLOUDWATCH_CONFIG.get('ACCESS_KEY_ID'),
            aws_secret_access_key=AWS_CLOUDWATCH_CONFIG.get('SECRET_ACCESS_KEY'),
            region_name=AWS_CLOUDWATCH_CONFIG.get('REGION_NAME'),
        )
        super().__init__(log_group_name=log_group_name, boto3_client=boto3_client)


class DummyHandler(logging.Handler):
    def emit(self, *args, **kwargs):
        pass


AWSCloudWatchHandler = DummyHandler if DEVELOPER_MODE else BaseAWSCloudWatchHandler
