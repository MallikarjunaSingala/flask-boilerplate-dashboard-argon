import sqlite3 as sql
import pandas as pd
import datetime
from dateutil.relativedelta import *

conn = sql.connect('db.sqlite3')
db = conn.cursor()

db.execute('''delete from user''')
db.execute('''delete from balance_info''')
db.execute('''delete from invoices''')
db.execute('''delete from scheduler_log''')
db.execute('''DELETE FROM sqlite_sequence WHERE name IN ('User','invoices','transactions','issues')''')
conn.commit()

users = pd.read_csv('final_2.csv')
users['Billing Month'] = users['Billing Month'].fillna(1)
users['Billing Year'] = users['Billing Year'].fillna(1970)
users['Billing Day'] = users['Billing Day'].fillna(1)
#
users['Billing Month'] = users['Billing Month'].astype(int)
users['Billing Year'] = users['Billing Year'].astype(int)
users['Billing Day'] = users['Billing Day'].astype(int)
#
users['Month'] = users['Month'].fillna(1)
users['Year'] = users['Year'].fillna(1970)
users['Day'] = users['Day'].fillna(1)
users['Month'] = users['Month'].astype(int)
users['Year'] = users['Year'].astype(int)
users['Day'] = users['Day'].astype(int)
#
#
plans = db.execute('''SELECT plan_id,plan_name from plans''').fetchall()
zones = db.execute('''SELECT id,name from zones''').fetchall()

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

for i, row in users.iterrows():
    if(row['Billing Year']==1900):
        row['Billing Year']=1970
        row['Billing Month']=1
        row['Billing Day']=1

    if row['Plan Cycle'] == 'F' or row['Plan Cycle'] == 'FR' or row['Plan Cycle'] == 'f':
        plan_cycle = 5
    elif row['Plan Cycle'] == 'H' or row['Plan Cycle'] == 'H ':
        plan_cycle = 3
    elif row['Plan Cycle'] == 'TH':
        plan_cycle = 2
    elif row['Plan Cycle'] == 'Y' or row['Plan Cycle'] == 'y' or row['Plan Cycle'] == 'Y ' :
        plan_cycle = 4
    elif row['Plan Cycle'] == 'C':
        plan_cycle = 6
    elif row['Plan Cycle'] == 'M' or row['Plan Cycle'] == 'M ':
        plan_cycle = 1
    else:
        plan_cycle = 7
    if (row['Plan Cycle'] == 'C' or row['Plan Cycle'] == 'PO') and row['Account Status'] == 'Active':
        plan_cycle = 7
    rate_plan = 0
    for plan in plans:
        if(row['Rate_Plan']==plan[1]):
            rate_plan = plan[0]
            break
    zone_id = 0
    for zone in zones:
        if(row['zone']==zone[1]):
            zone_id = zone[0]
            break

    starting_string = str(row['Year'])+'-'+str(row['Month'])+'-'+str(row['Day'])
    start_date = datetime.datetime.strptime(starting_string,"%Y-%m-%d").date()
    billing_string = str(row['Billing Year'])+'-'+str(row['Billing Month'])+'-'+str(row['Billing Day'])
    billing_date_time = datetime.datetime.strptime(billing_string,"%Y-%m-%d")
    billing_date = billing_date_time.date()

    db.execute('''INSERT INTO user(username, email, mobile, address, zone,
     name, rate_plan, plan_cycle, sub_status, account_status, ip,
      status,discount_amount,actual_amount,creation_date,billing_date)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',[row['Account ID'],row['Email'],row['Phone'],row['Address'],zone_id,
     row['Name'],rate_plan,plan_cycle, row['Subscription Status'],row['Account Status'],row['IP ADDRESS'],
     row['Account Status'],row['Amount'],row['Amount'],start_date,billing_date])
    user_id = db.execute('''select id from user where username = ?''',[row['Account ID']]).fetchall()[0][0]
    if billing_date >= datetime.date.today():
        periods = 0
    else:
        periods = calculate_periods(plan_cycle,billing_date) + 1

    amount_calc = 1
    if plan_cycle == 1:
        amount_calc = 1
    if plan_cycle == 2:
        amount_calc = 3
    if plan_cycle == 3:
        amount_calc = 6
    if plan_cycle == 4:
        amount_calc = 12
    if plan_cycle == 5 or plan_cycle == 6 or plan_cycle == 7 or plan_cycle == 0:
        amount_calc = 0
    if(row['Account Status'] == 'Inactive'):
        amount_calc = 0

    due_amount_total = periods * amount_calc * row['Amount']
    one_period_amount = row['Amount'] * amount_calc

    db.execute('''INSERT INTO balance_info(user_id,due_amount,customer_status,due_start_date, pending_intervals,one_interval_amount,paid_amount)
    VALUES(?,?,?,?,?,?,?)
    ''',[user_id,due_amount_total,row['Account Status'],billing_date,periods,one_period_amount,0])

    due_amount = due_amount_total - one_period_amount
    if due_amount < 0:
        due_amount = 0
    if billing_date >= datetime.date.today():
        next_invoice_date = billing_date
    else:
        next_invoice_date = next_due_date(plan_cycle,billing_date,periods)
    invoice_date = datetime.date.today()

    db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
     VALUES(?,?,?,?,?,?,?)''',[user_id,due_amount,one_period_amount,row['Account Status'],invoice_date,next_invoice_date,0])
    conn.commit()

db.execute('''INSERT INTO scheduler_log VALUES(?,"Success")''',[datetime.date.today()])
conn.commit()