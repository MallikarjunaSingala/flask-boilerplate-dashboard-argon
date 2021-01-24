import pymysql
import pandas as pd
import mysql.connector
from mysql.connector.constants import ClientFlag
import datetime
from dateutil.relativedelta import *
config = {
    'user': 'krpcommu_admin',
    'password': 'Vikram@123',
    'host': '172.105.56.108',
    'database': 'krpcommu_fibernet',
    'use_pure': True
}
conn = mysql.connector.connect(**config)
db = conn.cursor()

users = pd.read_csv('latest_info.csv')
users = users.fillna(0)

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
    # if row['Account Id'] == 'krp_anraju':
        if row['Billing From'] == '0' or row['Billing From'] == 0:
            row['Billing From'] = '1970-01-01'
        billing_time = datetime.datetime.strptime(str(row['Billing From']),"%Y-%m-%d")
        billing_date = billing_time.date()
        if row['M'].strip() == 'M':
            plan_cycle = 1
        elif row['M'].strip() == 'H':
            plan_cycle = 3
        elif row['M'].strip() == 'Y' or row['M'].strip() == 'y':
            plan_cycle = 4
        elif row['M'].strip() == 'F' or row['M'].strip() == 'f':
            plan_cycle = 5
        elif row['M'].strip() == 'C' or row['M'].strip() == 'c' or row['M'].strip() == 'PO':
            plan_cycle = 6
        else:
            plan_cycle = 7
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
        due_amount_total = periods * amount_calc * row['Discount']
        due_amount_total = int(due_amount_total)
        one_period_amount = row['Discount'] * amount_calc
        one_period_amount = int(one_period_amount)
        
        due_amount = due_amount_total - one_period_amount
        if due_amount < 0:
            due_amount = 0
        if billing_date >= datetime.date.today():
            next_invoice_date = billing_date
        else:
            next_invoice_date = next_due_date(plan_cycle,billing_date,periods)
        invoice_date = datetime.date.today()
        # print(next_invoice_date)
        db.execute('''
        INSERT INTO latest_process_info
        VALUES(%s,%s,%s
        ,%s,%s,%s
        ,%s,%s,%s)
        ''',[due_amount_total,periods,one_period_amount,due_amount,invoice_date,next_invoice_date,row['Account Id'],billing_date,plan_cycle])
        conn.commit()
        # db.execute('''
        # UPDATE user_latest_info
        # set plan_cycle = %s
        # WHERE accountid = %s
        # ''',[plan_cycle,row['Account Id']])
        # conn.commit()
        # if row['Account Id'] != '' or row['Account Id'] != ' ':
        #     db.execute('''
        #     UPDATE user_latest_info
        #     SET bal_due_amount = %s,
        #     bal_pending_intervals = %s,
        #     one_interval_amount = %s,
        #     inv_due_amount = %s,
        #     current_cycle_amount = %s,
        #     invoice_date = %s,
        #     next_invoice_date = %s
        #     WHERE accountid = %s
        #     ''',[due_amount_total,periods,one_period_amount,due_amount,one_period_amount,invoice_date,next_invoice_date,row['Account Id']])
        #     conn.commit()














##### Update user latest info #######
# db.execute('''
    # UPDATE user_latest_info
    # SET billing_date = %s
    # where accountid = %s
    # ''',[billing_date,row['Account Id']])
# from sqlalchemy import create_engine

# # create sqlalchemy engine
# engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
#                        .format(user="krpcommu_admin",
#                                pw="Vikram@123",
#                                host = '172.105.56.108',
#                                db="krpcommu_fibernet"))
# users.to_sql('user_latest_info', con = engine, if_exists = 'replace', chunksize = 1000)
# SELECT DISTINCT substr(RatePlan,1,2) ,if (substr(substr(RatePlan,1,2),2,1) NOT RLIKE '^[A-Z]',substr(RatePlan,1,2),substr(RatePlan,1,1)),RatePlan FROM `user_latest_info` ;
# UPDATE user_latest_info
# set RatePlan = 
# (case when RatePlan <= 10 then 'Krp-10Mbps-UL-M'
# when RatePlan <= 15 then 'Krp-15Mbps-UL-M'
# when RatePlan <= 20 then 'Krp-20Mbps-UL-M'
# when RatePlan <= 50 then 'Krp-50Mbps-UL-M'
# else 'krp-100Mbps'
# end
# );
# UPDATE user_latest_info
# set rate_plan = (
#     case
#     when RatePlan = 'Krp-10Mbps-UL-M' then 1
#     when RatePlan = 'Krp-15Mbps-UL-M' then 2
#     when RatePlan = 'Krp-20Mbps-UL-M' then 3
#     when RatePlan = 'Krp-50Mbps-UL-M' then 4
#         when RatePlan = 'Krp-100Mbps-UL-M' then 5
#     end)
# UPDATE User_data a
# set rate_plan = (select DISTINCT rate_plan from user_latest_info b where a.username = b.AccountId)
# ;
# UPDATE User_data a
# set actual_amount = (select  max(amount) from user_latest_info b where a.username = b.AccountId)
# , discount_amount = (select  max(discount) from user_latest_info b where a.username = b.AccountId)
# ;
# update `user_latest_info` a
# set userid = (select max(id) from User_data b where a.accountid = b.username)
# ;
# update `User_data` a
# set zone = (select max(zone_id) from user_latest_info b where a.username = b.AccountId)
# ;
# commit;
# commit;
# commit;
# commit;
# commit;

# insert into unsettled_balance
# select userid,TotalBalance,1 from user_latest_info
# where amount is null
# and M in ('H','Y','M')
# ;
# commit;

# UPDATE user_latest_info
# set rateplan = if (substr(substr(RatePlan,1,2),2,1) NOT RLIKE '^[A-Z]',substr(RatePlan,1,2),substr(RatePlan,1,1))
# ;
# commit;
# sql.write_frame(users, con=conn, name='user_latest_info', 
#                 if_exists='replace', flavor='mysql')
# for i, row in users.iterrows():
#     db.execute('''
#     INSERT INTO user_latest_info(
#         username,plan_cycle,actual_amount
#         ,discount_amount,pending_amount,billing_from 
#         ,name,mobile,address
#         ,rate_plan,kbps
#         )
#     VALUES(
#         %s,%s,%s
#         ,%s,%s,%s
#         ,%s,%s,%s
#         ,%s,%s
#     )
#      ''',[row['Account Id'],row['M'],row['Amount'],row['Discount'],row['Total Balance '],row['Billing From'],row['Name'],row['Phone'],row['Address'],row['Rate Plan'],row['kbps']])
#     conn.commit()
#  UPDATE User_data a 
#  set billing_date = (select max(billing_date) from user_latest_info b where a.id = b.userid)
#  ;
#  commit;
# ;