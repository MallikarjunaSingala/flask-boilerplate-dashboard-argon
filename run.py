# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_migrate import Migrate
from os import environ
from sys import exit
from decouple import config
from flask_apscheduler import APScheduler
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
    conn = mysql.connector.connect(**config)
    db = conn.cursor()
    
    db.execute('''SELECT max(last_run_date) FROM scheduler_log where status = "Success"''')
    last_success_date = db.fetchall()[0][0]
    # last_success_date = datetime.datetime.strptime(last_success_date,"%Y-%m-%d").date()
    today = datetime.datetime.now().date()
    
    db.execute('''
    SELECT
        user.id,
        plan_cycle,
        rate_plan,
        next_invoice_date,
        balance_info.due_amount AS due_amount,
        discount_amount,
        pending_intervals,
        invoices.id
    FROM User_data user JOIN invoices
    ON user.id = invoices.user_id
    JOIN balance_info ON balance_info.user_id = user.id
    WHERE status = "Active"
    AND invoices.next_invoice_date between %s and %s
    AND processed = 0
    ORDER BY next_invoice_date ASC
    ''',[last_success_date,today])

    info = db.fetchall()

    for i in range(len(info)):
        due_amount = int(info[i][4])
        
        amount_calc = 1
        plan_cycle = int(info[i][1])

        if plan_cycle == 1:
            amount_calc = 1
        if plan_cycle == 2:
            amount_calc = 3
        if plan_cycle == 3:
            amount_calc = 6
        if plan_cycle == 4:
            amount_calc = 12
        
        db.execute('''UPDATE invoices SET processed = 1 where id = %s''',[int(info[i][7])])
        current_amount = int(info[i][5]) * amount_calc
        invoice_date = info[i][3]
        # datetime.datetime.strptime(info[i][3],"%Y-%m-%d").date()
        next_invoice_date = next_due_date(plan_cycle,invoice_date,1)
        db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
        VALUES(%s,%s,%s,%s,%s,%s,0)
        ''',[int(info[i][0]),due_amount,current_amount,"Active",invoice_date,next_invoice_date])
        
        due_amount = int(info[i][4]) + current_amount
        intevals = int(info[i][6]) + 1
        db.execute('''UPDATE balance_info SET due_amount = due_amount + %s, one_interval_amount = %s, pending_intervals = %s WHERE user_id = %s
        ''',[current_amount,current_amount,intevals,int(info[i][0])])
        conn.commit()
    db.execute('''INSERT INTO scheduler_log(last_run_date,status) VALUES(%s,"Success")''',[datetime.date.today()])
    conn.commit()

scheduler.add_job(id ='Scheduled task', func = scheduledTask, trigger = 'interval', minutes=1440)
scheduler.start()

if __name__ == "__main__":
    app.run()