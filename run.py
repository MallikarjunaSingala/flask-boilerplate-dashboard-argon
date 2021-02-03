# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_migrate import Migrate
from os import environ
from sys import exit
from decouple import config
from flask_apscheduler import APScheduler
import schedule
import time
import datetime
from dateutil.relativedelta import *

from config import config_dict
from app import create_app, db
import sqlite3 as sql

# WARNING: Don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True)

# The configuration
get_config_mode = 'Debug'

try:

    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app( app_config )
scheduler = APScheduler()
Migrate(app, db)

import mysql.connector
from mysql.connector.constants import ClientFlag

config = {
    'user': 'krpcommu_admin',
    'password': 'Vikram@123',
    'host': '172.105.56.108',
    'database': 'krpcommu_fibernet',
    'use_pure': True
}

conn = mysql.connector.connect(**config)
db = conn.cursor()

def calculate_periods(plan_cycle,last_date):
    days = (datetime.date.today()-last_date).days
    if(plan_cycle == 1):
        return int(days/30.41)
    if(plan_cycle == 2):
        return int(days/91.25)
    if(plan_cycle == 3):
        return int(days/182.5)
    if(plan_cycle == 4):
        return int(days/365)
    return 0
def next_due_date(plan_cycle,last_date,periods):
    if periods == 0:
        periods = calculate_periods(plan_cycle,last_date)
    if plan_cycle == 1:
        return last_date + relativedelta(months=+periods)
    if plan_cycle == 2:
        return last_date + relativedelta(months=+periods*3)
    if plan_cycle == 3:
        return last_date + relativedelta(months=+periods*6)
    if plan_cycle == 4:
        return last_date + relativedelta(years=+periods)
    # return 
        
def scheduledTask():
    print("Ran")

scheduler.add_job(id ='RefreshPayments', func = scheduledTask, trigger = 'interval', seconds=5)
scheduler.start()

if __name__ == "__main__":
    app.run()