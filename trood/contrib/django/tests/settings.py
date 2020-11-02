class MockSettings:
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [],
        'DEFAULT_PERMISSION_CLASSES': [],
        'UNAUTHENTICATED_USER': None,
    }
    INSTALLED_APPS = [
        'trood.contrib.django.tests',
    ]
    DEBUG = True
    LOGGING_CONFIG = {}
    LOGGING = {}
    SECRET_KEY = ''
    FORCE_SCRIPT_NAME = ''
    DEFAULT_TABLESPACE = ''
    DEFAULT_CHARSET = 'utf-8'
    DATABASE_ROUTERS = []
    DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase',
    }}
    ABSOLUTE_URL_OVERRIDES = {}
    SERVICE_DOMAIN = "TEST"
    USE_I18N = False
