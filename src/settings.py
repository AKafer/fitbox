import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = 'static'
INSTRUCTIONS_FOLDER = 'instructions'
SIGNATURES_FOLDER = 'signatures'
TEMPLATES_FOLDER = 'templates'
TRAINING_MODULES_FOLDER = 'training_modules'
UPLOAD_DIR = os.path.join(BASE_DIR, STATIC_FOLDER)
INSTRUCTIONS_DIR = os.path.join(UPLOAD_DIR, INSTRUCTIONS_FOLDER)
SIGNATURES_DIR = os.path.join(UPLOAD_DIR, SIGNATURES_FOLDER)
TEMPLATES_DIR = os.path.join(UPLOAD_DIR, TEMPLATES_FOLDER)
TRAINING_MODULES_DIR = os.path.join(UPLOAD_DIR, TRAINING_MODULES_FOLDER)
OUTPUT_DIR = "/tmp/generated_docs"
ZIP_NAME = "documents.zip"

BASE_URL = os.getenv('BASE_URL')

DATABASE_POOL_SIZE = os.getenv('DB_POOL_SIZE', default=20)
DATABASE_POOL_MAX_OVERFLOW = os.getenv('DB_POOL_MAX_OVERFLOW', default=5)
DATABASE_HOST = os.getenv('DB_HOST', default='localhost')
DATABASE_PORT = os.getenv('DB_PORT', default=5432)
DATABASE_NAME = os.getenv('POSTGRES_DB', default='')
DATABASE_USER = os.getenv('POSTGRES_USER', default='')
DATABASE_PASSWORD = os.getenv('POSTGRES_PASSWORD', default='')
DATABASE_URL = f'postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'

# superuser
SUPERUSER_EMAIL = os.getenv('SUPERUSER_EMAIL')
SUPERUSER_PASSWORD = os.getenv('SUPERUSER_PASSWORD')
SUPERUSER_NAME = os.getenv('SUPERUSER_NAME')
SUPERUSER_LAST_NAME = os.getenv('SUPERUSER_LAST_NAME')

SUPERUSER_EMAIL_2 = os.getenv('SUPERUSER_EMAIL_2')
SUPERUSER_PASSWORD_2 = os.getenv('SUPERUSER_PASSWORD_2')
SUPERUSER_NAME_2 = os.getenv('SUPERUSER_NAME_2')
SUPERUSER_LAST_NAME_2 = os.getenv('SUPERUSER_LAST_NAME_2')

SUPERUSER_EMAILS_LIST = [SUPERUSER_EMAIL, SUPERUSER_EMAIL_2]

SECRET_KEY = os.getenv('SECRET_KEY')

LOG_HANDLERS = ['console', 'file']
LOG_LEVEL = os.getenv('LOG_LEVEL', default='DEBUG')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            '()': 'logging.Formatter',
            'format': (
                '%(levelname)s [%(asctime)s] [%(name)s] %(filename)s:%(lineno)s %(message)s'
            ),
            'datefmt': '%d/%b/%Y:%H:%M:%S %z',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default',
        },
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 1,
            'encoding': 'utf8',
        },
    },
    'loggers': {
        'control': {
            'level': LOG_LEVEL,
            'handlers': LOG_HANDLERS,
            'propagate': False,
        },
    },
}
