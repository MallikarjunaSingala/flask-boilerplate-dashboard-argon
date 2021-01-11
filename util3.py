import datetime
from dateutil.relativedelta import *
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
    return 0
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

def payment_add(user_id):
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    user = list(db.execute('''SELECT user_id,due_amount,username,due_date,pending_due_time, plan_cycle
                 FROM balance_info JOIN user ON user_id = id WHERE user_id = ?''',[user_id]).fetchall()[0])
    billing_date = datetime.datetime.strptime(user[3],"%Y-%m-%d").date()
    print(type(user[3]))
    print(type(billing_date))
    print(billing_date)
    print(user[3])
    due_date = next_due_date(user[5],billing_date)
    print(due_date)
payment_add(5344)