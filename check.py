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
def next_due_date(plan_cycle,last_date):
    periods = calculate_periods(plan_cycle,last_date)
    if plan_cycle == 1:
        return last_date + relativedelta(months=+periods)
    if plan_cycle == 2:
        return last_date + relativedelta(months=+periods*3)
    if plan_cycle == 3:
        return last_date + relativedelta(months=+periods*6)
    if plan_cycle == 4:
        return last_date + relativedelta(years=+periods)
def scheduledTask():
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    db.execute('''DELETE FROM balance_info where user_id in (select id from user where plan_cycle in (0,5) or status NOT IN ('ACTIVE', 'Active'))''')
    conn.commit()
    info = db.execute('''SELECT
         id,last_paid_date,plan_cycle, rate_plan,start_date,discount_amount
          FROM user JOIN balance_info ON user.id = balance_info.user_id
          WHERE status = "Active"''').fetchall()
    for i in range(len(info)):
        last_date = datetime.datetime.strptime(info[i][1],"%Y-%m-%d %H:%M:%S").date()
        if(last_date == datetime.date(1970,1,1)):
            last_date= datetime.datetime.strptime(info[i][4],"%Y-%m-%d").date()
        periods = calculate_periods(info[i][2],last_date)
        amount = info[i][5]
        if(info[i][5] is None):
            amount = 0
        due_amount = periods * amount
        due_date = next_due_date(info[i][2],last_date)
        if(periods > 24):
            due_amount = 0
        db.execute('''UPDATE balance_info set due_amount = ?,due_date = ? WHERE user_id = ?''',[due_amount,due_date,info[i][0]])
        conn.commit()
scheduledTask()