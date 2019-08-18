from setuptools import setup, find_packages

setup(
    name='trood',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    author='Trood CIS',
    url='',
    install_requires=[
        u'requests==2.18.4', 'djangorestframework', 'django',
    ]
)