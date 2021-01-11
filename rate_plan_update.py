import sqlite3 as sql
import pandas as pd
import datetime
from dateutil.relativedelta import *

conn = sql.connect('db.sqlite3')
db = conn.cursor()

users_info = db.execute('''SELECT id,username FROM user where rate_plan = 0''').fetchall()
zero_count = db.execute('''SELECT count(*) FROM user where rate_plan = 0''').fetchall()[0][0]
print(zero_count)

users = pd.read_csv('rate_plan_update.csv')
users['Billing Month'] = users['Billing Month'].fillna(1)
users['Billing Year'] = users['Billing Year'].fillna(1970)
users['Billing Day'] = users['Billing Day'].fillna(1)
#
users['Billing Month'] = users['Billing Month'].astype(int)
users['Billing Year'] = users['Billing Year'].astype(int)
users['Billing Day'] = users['Billing Day'].astype(int)
    # billing_string = str(row['Billing Year'])+'-'+str(row['Billing Month'])+'-'+str(row['Billing Day'])
    # billing_date_time = datetime.datetime.strptime(billing_string,"%Y-%m-%d")
    # billing_date = billing_date_time.date()
# for user in users_info:
    # print(user)
# print(users)