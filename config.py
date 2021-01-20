# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from   decouple import config

class Config(object):

    basedir    = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    SECRET_KEY = config('SECRET_KEY', default='S#perS3crEt_007')

    # This will create a file in <app> FOLDER
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}/{}'.format(
        config( 'MYSQL_DATABASE_USER' , default='krpcommu_admin'       ),
        config( 'MYSQL_DATABASE_PASSWORD'     , default='Vikram@123'          ),
        config( 'MYSQL_DATABASE_HOST'     , default='172.105.56.108'     ),
        config( 'MYSQL_DATABASE_DB', default='krpcommu_fibernet' )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY  = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}/{}'.format(
        config( 'MYSQL_DATABASE_USER' , default='krpcommu_admin'       ),
        config( 'MYSQL_DATABASE_PASSWORD'     , default='Vikram@123'          ),
        config( 'MYSQL_DATABASE_HOST'     , default='172.105.56.108'     ),
        config( 'MYSQL_DATABASE_DB', default='krpcommu_fibernet' )
    )

class DebugConfig(Config):
    DEBUG = True

# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug'     : DebugConfig
}
