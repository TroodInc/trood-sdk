import base64
import hashlib
import hmac
import os


def get_attribute_path(obj, path: str, default=None):
    attributes = path.split(".")
    for i in attributes:
        try:
            if type(obj) is dict:
                obj = obj.get(i)
            else:
                obj = getattr(obj, i)
        except AttributeError:
            if default:
                return default
            else:
                raise
    return obj


def get_service_token():
    domain = os.environ.get('SERVICE_DOMAIN')
    secret = os.environ.get('SERVICE_AUTH_SECRET')

    key = hashlib.sha1(b'trood.signer' + secret.encode('utf-8')).digest()
    signature = hmac.new(key, msg=domain.encode('utf-8'), digestmod=hashlib.sha1).digest()
    signature = base64.urlsafe_b64encode(signature).strip(b'=')
    return str(f'Service {domain}:{signature.decode("utf-8")}')
