import sqlite3 as sql
import pandas as pd
import datetime
from dateutil.relativedelta import *

conn = sql.connect('db.sqlite3')
db = conn.cursor()

db.execute('''SELECT id,username FROM user where username in (select username from user_latest_info)
''')