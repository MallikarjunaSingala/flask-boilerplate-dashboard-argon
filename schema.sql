
DROP TABLE IF EXISTS USERS;
DROP TABLE IF EXISTS login_info;
DROP TABLE IF EXISTS plans;
DROP TABLE IF EXISTS plan_info;
DROP TABLE IF EXISTS plan_history;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS balance_info;
DROP TABLE IF EXISTS complaints;
DROP TABLE IF EXISTS Dept;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS complaints_history;

# Users Table

CREATE TABLE USERS
 (user_id INTEGER PRIMARY KEY,
 user_name VARCHAR NOT NULL,
  mobile INTEGER,
   email VARCHAR NOT NULL,
   status VARCHAR,
   address VARCHAR,
   type VARCHAR,
   user_level INTEGER,
   created DATETIME DEFAULT CURRENT_TIMESTAMP,
   modified DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_history
 (
	 user_id INTEGER PRIMARY KEY,
	 change_type VARCHAR,
	 new_value VARCHAR,
	 modified DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ALTER TABLE USER
-- ADD COLUMN status VARCHAR;
-- ALTER TABLE USER
-- ADD COLUMN address VARCHAR;
-- ALTER TABLE USER
-- ADD COLUMN type VARCHAR;
-- ALTER TABLE USER
-- ADD COLUMN user_level INTEGER;
-- ALTER TABLE USER
-- ADD COLUMN created DATETIME DEFAULT CURRENT_TIMESTAMP;
-- ALTER TABLE USER
-- ADD COLUMN modified DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE USER
ADD COLUMN zone INTEGER;

ALTER TABLE USER
ADD COLUMN USERID VARCHAR;

DROP TABLE if exists user_levels;
CREATE TABLE user_levels (
    user_level_id INTEGER PRIMARY KEY autoincrement,
    user_level_name VARCHAR NOT NULL
);
# Login Info Table

CREATE TABLE login_info(user_id INTEGER, password TEXT,
FOREIGN KEY(user_id) REFERENCES USERS(user_id)
)
;

#Plan Table

CREATE TABLE plans(plan_id INTEGER, speed INTEGER, FUP INTEGER, CAPACITY INTEGER, PRICE INTEGER, INTERVAL INTEGER
)
;

#User Plan Details

CREATE TABLE plan_info(user_id INTEGER, plan_id INTEGER, ACTUAL_AMOUNT INTEGER, Discount DECIMAL, FINAL_AMOUNT DECIMAL, 
FOREIGN KEY(user_id) REFERENCES USERS(user_id),
FOREIGN KEY(plan_id) REFERENCES PLANS(plan_id)
)
;

#Plan History

CREATE TABLE plan_history(
user_id INTEGER,
plan_id INTEGER,
START_DATE DATETIME ,
END_DATE DATETIME,
FOREIGN KEY(user_id) REFERENCES USERS(user_id),
FOREIGN KEY(plan_id) REFERENCES PLANS(plan_id)
);

#Transactions Table

CREATE TABLE transactions(
user_id INTEGER,
transaction_id INTEGER,
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
AMOUNT INTEGER,
payment_type TEXT,
salesman_id INTEGER,
FOREIGN KEY(user_id) REFERENCES USERS(user_id),
FOREIGN KEY(salesman_id) REFERENCES USERS(user_id)
);

#Balance Info

CREATE TABLE balance_info(
user_id INTEGER,
total_amount DECIMAL,
paid_amount DECIMAL,
last_paid_date DATETIME,
due_date DATETIME,
due_amount DECIMAL,
FOREIGN KEY(user_id) REFERENCES USERS(user_id)
)
;
#Complaints

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
);

#Departments

CREATE TABLE Dept(
dept_id integer PRIMARY KEY,
dept_name VARCHAR NOT NULL,
department_admin INTEGER,
created DATETIME DEFAULT CURRENT_TIMESTAMP,
modified DATETIME DEFAULT CURRENT_TIMESTAMP
)
;
#EMPLOYEES

CREATE TABLE employees(
emp_id INTEGER,
EMP_NAME TEXT,
POSITION TEXT,
mgr_id INTEGER,
dept_id INTEGER,
FOREIGN KEY(emp_id) REFERENCES USERS(user_id),
FOREIGN KEY(mgr_id) REFERENCES USERS(user_id),
FOREIGN KEY(dept_id) REFERENCES Dept(dept_id)
);

#Complaint History

CREATE TABLE complaints_history(
complaint_id INTEGER,
event_timestamp DATETIME,
status TEXT,
comment TEXT,
assignee INTEGER,
FOREIGN KEY(complaint_id) REFERENCES complaints(complaint_id),
FOREIGN KEY(assignee) REFERENCES EMPLOYEES(emp_id)
)
;


#Issue Tracker Tables
DROP TABLE if exists issues;
CREATE TABLE issues (
    issue_id INTEGER PRIMARY KEY autoincrement,
    description TEXT,
    department INTEGER,
    assigned_to INTEGER,
    status INTEGER DEFAULT 1,
    priority INTEGER,
    raised_by INTEGER,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE if exists issue_status;
CREATE TABLE issue_status (
    issue_status_id INTEGER PRIMARY KEY autoincrement,
    status_name VARCHAR NOT NULL
);

DROP TABLE if exists issue_priorities;
CREATE TABLE issue_priorities (
    priority_id INTEGER PRIMARY KEY autoincrement,
    priority_name VARCHAR
);

DROP TABLE if exists issue_comments;
CREATE TABLE issue_comments (
    comment_id INTEGER PRIMARY KEY autoincrement,
    issue INTEGER NOT NULL,
    commenter INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE if exists notifications;
CREATE TABLE notifications (
    notification_id INTEGER PRIMARY KEY autoincrement,
    origin INTEGER NOT NULL,
    source INTEGER NOT NULL,
    issue INTEGER NOT NULL,
    read BOOLEAN DEFAULT 0,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payment_confirmation(
	confirmation_date DATE,
	amount INTEGER,
	confirmed BOOLEAN
);

INSERT INTO user_levels (user_level_id, user_level_name) VALUES ('1', 'Super Admin'),('2', 'Department Admin'),('3', 'Client'),('4', 'Support Representative');

INSERT INTO issue_priorities (priority_name) VALUES ('Low'),('Medium'),('High');

INSERT INTO issue_status (issue_status_id, status_name) VALUES ('1', 'Open'),('2', 'In-Progress'),('3', 'Closed');

INSERT INTO dept (dept_id, dept_name, department_admin) VALUES (1,'Sales','2'),(2,'Services','3'),(3,'Admin','4');

INSERT INTO issues (description, department, priority, raised_by) VALUES ('This is the first issue','2','1','9'),('Second issue raised on the system','3','3','10');

DROP TABLE IF EXISTS zones;
CREATE TABLE zones(id INTEGER PRIMARY KEY AUTOINCREMENT,name VARCHAR,modified DATETIME DEFAULT CURRENT_TIMESTAMP);
INSERT INTO zones(name) VALUES('NGOs Colony');
INSERT INTO zones(name) VALUES('Saibaba Nagar');
INSERT INTO zones(name) VALUES('SBI Colony');
INSERT INTO zones(name) VALUES('Srinivas Center');
INSERT INTO zones(name) VALUES('Girinath Center');
INSERT INTO zones(name) VALUES('Gandhi Chowk');
INSERT INTO zones(name) VALUES('Birmal Street');
INSERT INTO zones(name) VALUES('Balaji Complex');
INSERT INTO zones(name) VALUES('Sanjeev Nagar');
INSERT INTO zones(name) VALUES('Sai Aiswaryam');
INSERT INTO zones(name) VALUES('Saleem Nagar');
INSERT INTO zones(name) VALUES('Bommala Satram');
INSERT INTO zones(name) VALUES('Girinath Center');


