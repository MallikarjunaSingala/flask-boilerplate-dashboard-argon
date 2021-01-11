import sqlite3
from sqlite3 import Error

conn = sqlite3.connect('krp_broadband.db')
c = conn.cursor()

#DROP TABLES
c.execute("DROP TABLE IF EXISTS USERS")
c.execute("DROP TABLE IF EXISTS login_info")
c.execute("DROP TABLE IF EXISTS plans")
c.execute("DROP TABLE IF EXISTS plan_info")
c.execute("DROP TABLE IF EXISTS plan_history")
c.execute("DROP TABLE IF EXISTS transactions")
c.execute("DROP TABLE IF EXISTS balance_info")
c.execute("DROP TABLE IF EXISTS complaints")
c.execute("DROP TABLE IF EXISTS Dept")
c.execute("DROP TABLE IF EXISTS employees")
c.execute("DROP TABLE IF EXISTS complaints_history")

# Users Table
c.execute('''
CREATE TABLE USERS
 (user_id INTEGER PRIMARY KEY,
 user_name text,
  mobile INTEGER,
   mail_id TEXT,
   status TEXT,
   address TEXT,
    TYPE TEXT)''')
# Login Info Table
c.execute('''
CREATE TABLE login_info(user_id INTEGER, password TEXT,
FOREIGN KEY(user_id) REFERENCES USERS(user_id)
)
''')

#Plan Table
c.execute('''
CREATE TABLE plans(plan_id INTEGER, speed INTEGER, FUP INTEGER, CAPACITY INTEGER, PRICE INTEGER, INTERVAL INTEGER
)
''')

#User Plan Details
c.execute('''
CREATE TABLE plan_info(user_id INTEGER, plan_id INTEGER, ACTUAL_AMOUNT INTEGER, Discount DECIMAL, FINAL_AMOUNT DECIMAL, 
FOREIGN KEY(user_id) REFERENCES USERS(user_id),
FOREIGN KEY(plan_id) REFERENCES PLANS(plan_id)
)
''')

#Plan History
c.execute('''
CREATE TABLE plan_history(
user_id INTEGER,
plan_id INTEGER,
START_DATE DATETIME,
END_DATE DATETIME,
FOREIGN KEY(user_id) REFERENCES USERS(user_id),
FOREIGN KEY(plan_id) REFERENCES PLANS(plan_id)
)''')

#Transactions Table
c.execute('''
CREATE TABLE transactions(
user_id INTEGER,
transaction_id INTEGER,
timestamp DATETIME,
AMOUNT INTEGER,
payment_type TEXT,
salesman_id INTEGER,
FOREIGN KEY(user_id) REFERENCES USERS(user_id),
FOREIGN KEY(salesman_id) REFERENCES USERS(user_id)
)''')

#Balance Info
c.execute('''
CREATE TABLE balance_info(
user_id INTEGER,
total_amount DECIMAL,
paid_amount DECIMAL,
due_amount DECIMAL,
FOREIGN KEY(user_id) REFERENCES USERS(user_id)
)
''')
#Complaints
c.execute('''
CREATE TABLE complaints(
complaint_id INTEGER,
reportedby INTEGER,
effected INTEGER,
creation_time DATETIME,
resolved_time DATETIME,
assignee INTEGER,
status TEXT,
FOREIGN KEY(reportedby) REFERENCES USERS(user_id),
FOREIGN KEY(effected) REFERENCES USERS(user_id)
)''')

#Departments
c.execute('''
CREATE TABLE Dept(
dept_id integer,
dept_name TEXT
)
''')
#EMPLOYEES
c.execute('''
CREATE TABLE employees(
emp_id INTEGER,
EMP_NAME TEXT,
POSITION TEXT,
mgr_id INTEGER,
dept_id INTEGER,
FOREIGN KEY(emp_id) REFERENCES USERS(user_id),
FOREIGN KEY(mgr_id) REFERENCES USERS(user_id),
FOREIGN KEY(dept_id) REFERENCES Dept(dept_id)
)''')

#Complaint History
c.execute('''
CREATE TABLE complaints_history(
complaint_id INTEGER,
event_timestamp DATETIME,
status TEXT,
comment TEXT,
assignee INTEGER,
FOREIGN KEY(complaint_id) REFERENCES complaints(complaint_id),
FOREIGN KEY(assignee) REFERENCES EMPLOYEES(emp_id)
)
''')