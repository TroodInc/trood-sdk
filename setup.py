from setuptools import setup, find_packages

setup(
    name='trood',
    version=0.6,
    packages=find_packages(),
    include_package_data=True,
    author='Trood CIS',
    url='',
    install_requires=[
        u'requests==2.22.0', 'djangorestframework', 'django', 'pyparsing', 'dateparser', 'django-redis', 'click',
        'pyfiglet', 'tabulate', 'keyring'
    ],
    entry_points='''
        [console_scripts]
        trood=trood.cli.trood:trood
    '''
)