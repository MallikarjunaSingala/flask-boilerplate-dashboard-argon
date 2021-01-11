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
