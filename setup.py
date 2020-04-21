import os
from setuptools import setup, find_packages


def get_version():
    with open(os.path.join(os.path.curdir, 'VERSION')) as version_file:
        return version_file.read().strip()


setup(
    name='trood',
    version=get_version(),
    packages=find_packages(),
    include_package_data=True,
    author='Trood Inc',
    url='',
    tests_require=[
        'pytest', 'pytest-coverage', 'pyhamcrest', 'teamcity-messages'
    ],
    install_requires=[
        u'requests==2.22.0', 'djangorestframework', 'django', 'pyparsing', 'dateparser', 'django-redis',
    ],
)
