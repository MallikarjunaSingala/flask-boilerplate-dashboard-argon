import sqlite3 as sql
import pandas as pd
import datetime
from dateutil.relativedelta import *

conn = sql.connect('db.sqlite3')
db = conn.cursor()

users = pd.read_csv('latest_info.csv')

users['Amount'] = users['Amount'].fillna(0)
users['Discount'] = users['Discount'].fillna(0)
users['Total Balance '] = users['Total Balance '].fillna(0)
users['kbps'] = users['Rate Plan'].str.lower().str.contains('kbps',regex=False)
for i, row in users.iterrows():
    db.execute('''
    INSERT INTO user_latest_info VALUES(
        ?,?,?,?,?,?,?,?,?,?
    )
    ''',[row['Account Id'],row['M'],row['Amount'],row['Discount'],row['Total Balance '],row['Billing From'],row['Name'],row['Phone'],row['Address'],row['Rate Plan']])
    conn.commit()