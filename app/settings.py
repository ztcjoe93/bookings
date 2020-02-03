from environs import Env
import os.path
import redis

env = Env()
env.read_env()

ENV = env.str("FLASK_ENV")
DEBUG = env.str("DEBUG")
SQLALCHEMY_DATABASE_URI = env.str("SQLALCHEMY_DATABASE_URI")
SECRET_KEY = env.str("SECRET_KEY")

SQLALCHEMY_TRACK_MODIFICATIONS = False

RECAPTCHA_USE_SSL = env.str("RECAPTCHA_USE_SSL")
RECAPTCHA_PUBLIC_KEY = env.str("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = env.str("RECAPTCHA_PRIVATE_KEY")
RECAPTCHA_OPTIONS = {'theme':'white'}

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app/uploads'))
LOGS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
MAX_CONTENT_LENGTH = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

MAIL_SERVER = env.str("MAIL_SERVER")
MAIL_PORT = env.str("MAIL_PORT")
MAIL_USE_TLS = True
MAIL_DEBUG = True
MAIL_USERNAME = env.str("MAIL_USERNAME")
MAIL_PASSWORD = env.str("MAIL_PASSWORD")

SESSION_TYPE = 'redis'
