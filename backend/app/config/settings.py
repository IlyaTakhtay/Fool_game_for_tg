import os

# Set DEBUG to True if the ENV environment variable is 'dev', otherwise False.
# Defaults to False (production mode) if ENV is not set.
DEBUG = os.environ.get('ENV') == 'dev'

# You can add other global settings here in the future.
# For example:
# SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key') 