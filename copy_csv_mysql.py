import pandas as pd
import datetime
from dateutil.relativedelta import *

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

db.execute('''delete from User_data''')
db.execute('''delete from balance_info''')
db.execute('''delete from invoices''')
db.execute('''delete from scheduler_log''')
conn.commit()
db.execute('ALTER TABLE User_data AUTO_INCREMENT = 1')
db.execute('ALTER TABLE invoices AUTO_INCREMENT = 1')
db.execute('ALTER TABLE transactions AUTO_INCREMENT = 1')
db.execute('ALTER TABLE issues AUTO_INCREMENT = 1')
conn.commit()

users = pd.read_csv('final_2.csv')
users = users.fillna('0')
# users['billing_from'] = users['billing_from'].fillna('1970-01-01')
# users['Creation_Date'] = users['Creation_Date'].fillna('1970-01-01')

db.execute('''SELECT plan_id,plan_name from plans''')
plans = db.fetchall()
db.execute('''SELECT id,name from zones''')
zones =  db.fetchall()

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
    if(row['billing_from']=='1900-01-00' or row['billing_from']=='0'):
        row['billing_from']='1970-01-01'
    if(row['Creation_Date']=='1900-01-00' or row['Creation_Date']=='0'):
        row['Creation_Date']='1970-01-01'

    if row['Plan Cycle'].strip() == 'F' or row['Plan Cycle'].strip() == 'FR' or row['Plan Cycle'].strip() == 'f':
        plan_cycle = 5
    elif row['Plan Cycle'].strip() == 'H':
        plan_cycle = 3
    elif row['Plan Cycle'].strip() == 'TH':
        plan_cycle = 2
    elif row['Plan Cycle'].strip() == 'Y' or row['Plan Cycle'] == 'y':
        plan_cycle = 4
    elif row['Plan Cycle'].strip() == 'C':
        plan_cycle = 6
    elif row['Plan Cycle'].strip() == 'M':
        plan_cycle = 1
    else:
        plan_cycle = 7
    if (row['Plan Cycle'] == 'C' or row['Plan Cycle'] == 'PO') and row['Account Status'] == 'Active':
        plan_cycle = 7
    
    rate_plan = 0
    if '10mbps' in row['Rate_Plan'].lower():
        rate_plan = 1
    elif '15mbps' in row['Rate_Plan'].lower():
        rate_plan = 2
    elif '20mbps' in row['Rate_Plan'].lower():
        rate_plan = 3
    elif '50mbps' in row['Rate_Plan'].lower():
        rate_plan = 4
    elif '100mbps' in row['Rate_Plan'].lower():
        rate_plan = 5
    else:
        rate_plan = 1
    zone_id = 0
    for zone in zones:
        if(row['zone'].strip()==zone[1]):
            zone_id = zone[0]
            break
    if row['Creation_Date'] == '' or row['Creation_Date'] is None:
        row['Creation_Date'] = '1970-01-01'
    if row['billing_from'] == '' or row['billing_from'] is None:
        row['billing_from'] = '1970-01-01'
    creation_date = datetime.datetime.strptime(row['Creation_Date'],"%Y-%m-%d").date()
    billing_date_time = datetime.datetime.strptime(row['billing_from'],"%Y-%m-%d")
    billing_date = billing_date_time.date()
    db.execute('''
    INSERT INTO User_data(
        username, email, mobile,
        address, zone,name,
        rate_plan, plan_cycle, sub_status,
        account_status, ip,
        status,discount_amount,actual_amount,
        creation_date,billing_date)
     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',[row['Account ID'],row['Email'],row['Phone'],row['Address'],zone_id,
     row['Name'],rate_plan,plan_cycle, row['Subscription Status'],row['Account Status'],row['IP ADDRESS'],
     row['Account Status'],int(row['Discount']),int(row['Amount']),creation_date,billing_date])
    conn.commit()
    db.execute('''select id from User_data where username = %s''',[row['Account ID']])
    user_id = db.fetchall()[0][0]
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

    due_amount_total = periods * amount_calc * int(row['Discount'])
    one_period_amount = int(row['Discount']) * amount_calc

    db.execute('''INSERT INTO balance_info(user_id,due_amount,customer_status,due_start_date, pending_intervals,one_interval_amount,paid_amount)
    VALUES(%s,%s,%s,%s,%s,%s,%s)
    ''',[user_id,due_amount_total,row['Account Status'],billing_date,periods,one_period_amount,0])

    conn.commit()
    due_amount = due_amount_total - one_period_amount
    if due_amount < 0:
        due_amount = 0
    if billing_date >= datetime.date.today():
        next_invoice_date = billing_date
    else:
        next_invoice_date = next_due_date(plan_cycle,billing_date,periods)
    invoice_date = datetime.date.today()

    db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
     VALUES(%s,%s,%s,%s,%s,%s,%s)''',[user_id,due_amount,one_period_amount,row['Account Status'],invoice_date,next_invoice_date,0])
    conn.commit()

db.execute('''INSERT INTO scheduler_log VALUES(%s,"Success")''',[datetime.date.today()])
conn.commit()