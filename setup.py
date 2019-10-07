from setuptools import setup, find_packages

setup(
    name='trood',
    version=0.4,
    packages=find_packages(),
    include_package_data=True,
    author='Trood CIS',
    url='',
    install_requires=[
        u'requests==2.22.0', 'djangorestframework', 'django', 'pyparsing'
    ]
)