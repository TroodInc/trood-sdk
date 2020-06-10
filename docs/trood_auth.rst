Connect your django service
===========================

Django settings
---------------
To use trood authorization in your django service use following settings.

::

    AUTH_TYPE = os.environ.get('AUTHENTICATION_TYPE')

    if AUTH_TYPE == 'TROOD':
        TROOD_AUTH_SERVICE_URL = os.environ.get(
            'TROOD_AUTH_SERVICE_URL', 'http://authorization.trood:8000/'
        )
        SERVICE_DOMAIN = os.environ.get("SERVICE_DOMAIN", "FILESERVICE")
        SERVICE_AUTH_SECRET = os.environ.get("SERVICE_AUTH_SECRET")

        REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
           'trood.contrib.django.auth.authentication.TroodTokenAuthentication',
        )

        REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = (
            'rest_framework.permissions.IsAuthenticated',
        )

Service token
-------------
Use service token in your service.
Setup SERVICE_DOMAIN and SERVICE_AUTH_SECRET environment variables in your service.

::

    from trood.core.utils import get_service_token

    token = get_service_token()