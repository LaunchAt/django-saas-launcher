from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage

AWS_S3_CONFIG = getattr(settings, 'AWS_S3', {})

DEVELOPER_MODE = AWS_S3_CONFIG.get('DEVELOPER_MODE', False)


def is_url_valid(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme == 'https' and parsed_url.netloc


class AWSS3Storage(S3Boto3Storage):
    def __init__(self, *, base_url='', location=''):
        base_url = base_url.replace(r'/?$', '/') if is_url_valid(base_url) else ''
        parsed_url = urlparse(urljoin(base_url, location.replace(r'^/?', '/')))
        super().__init__(
            access_key=AWS_S3_CONFIG.get('ACCESS_KEY_ID'),
            secret_key=AWS_S3_CONFIG.get('SECRET_ACCESS_KEY'),
            bucket_name=AWS_S3_CONFIG.get('BUCKET_NAME'),
            location=parsed_url.path.lstrip('/'),
            custom_domain=parsed_url.netloc,
            region_name=AWS_S3_CONFIG.get('REGION_NAME'),
        )


class BaseAWSS3StaticStorage(AWSS3Storage):
    def __init__(self):
        super().__init__(base_url=settings.STATIC_URL, location=settings.STATIC_ROOT)


class BaseAWSS3MediaStorage(AWSS3Storage):
    def __init__(self):
        super().__init__(base_url=settings.MEDIA_URL, location=settings.MEDIA_ROOT)


AWSS3StaticStorage = StaticFilesStorage if DEVELOPER_MODE else BaseAWSS3StaticStorage

AWSS3MediaStorage = FileSystemStorage if DEVELOPER_MODE else BaseAWSS3MediaStorage
