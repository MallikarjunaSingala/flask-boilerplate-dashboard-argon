# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from app.home import blueprint
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound
import sqlite3 as sql

from flask_moment import Moment
from flask_socketio import *
import os
from werkzeug.utils import secure_filename
import datetime
from dateutil.relativedelta import *

import requests

url = "https://www.smsgatewayhub.com/api/mt/SendSMS"
apikey = "zlK4AxVdjEW230uUT6FVaQ"
senderid = "SMSTST"

# from google.cloud import storage
def next_due_date(plan_cycle,last_date,periods):
    if plan_cycle == 1:
        return last_date + relativedelta(months=+periods)
    if plan_cycle == 2:
        return last_date + relativedelta(months=+periods*3)
    if plan_cycle == 3:
        return last_date + relativedelta(months=+periods*6)
    if plan_cycle == 4:
        return last_date + relativedelta(years=+periods)

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


@blueprint.route('/index')
@login_required
def index():
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    pending_payments = db.execute('''
        SELECT SUM(due_amount),COUNT(*) FROM balance_info LEFT JOIN user ON user_id = id WHERE due_amount > 0
        AND status = 'Active'
        ''').fetchall()[0]

    pending_issues = db.execute('''
    SELECT COUNT(*)
    FROM issues LEFT JOIN issue_status ON status = issue_status_id
    WHERE issue_type_id <> 1
    and issues.status < 3
    ''').fetchall()[0][0]

    pending_new_requests = db.execute('''
    SELECT COUNT(*)
    FROM issues LEFT JOIN issue_status ON status = issue_status_id
    WHERE issue_type_id = 1
    and issues.status < 3
    ''').fetchall()[0][0]

    collection = db.execute('''
    SELECT IFNULL(SUM(amount),0),count(user_id)
    FROM transactions WHERE strftime('%Y-%m',timestamp) = strftime('%Y-%m','now')
    ''').fetchall()[0]

    today_collection = db.execute('''
    SELECT IFNULL(SUM(amount),0),count(user_id)
    FROM transactions WHERE strftime('%Y-%m-%d',timestamp) = strftime('%Y-%m-%d','now')
    ''').fetchall()[0]
    yesterday_collection = db.execute('''
    SELECT IFNULL(SUM(amount),0),count(user_id)
    FROM transactions WHERE strftime('%Y-%m-%d',timestamp) = strftime('%Y-%m-%d',datetime('now','-1 day'))
    ''').fetchall()[0]

    total_collection = db.execute('''
    SELECT IFNULL(SUM(amount),0),count(user_id)
    FROM transactions
    ''').fetchall()[0]

    total_connections = db.execute('''
    SELECT COUNT(*)
    FROM user WHERE status = 'Active'
    ''').fetchall()[0][0]

    free_connections = db.execute('''
    SELECT COUNT(*)
    FROM user WHERE plan_cycle = '5'
    AND status = 'Active'
    ''').fetchall()[0][0]

    recent_inactives = db.execute('''SELECT count(*) from recent_inactives WHERE updated_portal = 0''').fetchall()[0][0]
    unsettled = db.execute('''SELECT IFNULL(SUM(due_amount),0) from unsettled_balance WHERE due_amount > 0''').fetchall()[0][0]
    data = db.execute('''select p.name,count(*) from plan_cycles p join user on p.id = user.plan_cycle group by 1 order by 2''').fetchall()
    values = []
    lables = []
    for d in data:
      lables.append(d[0])
      values.append(d[1])
    data = db.execute('''select strftime("%d-%m-%Y",timestamp),sum(amount) from transactions
      WHERE strftime("%m-%Y",timestamp) = strftime("%m-%Y",date('now'))  group by 1 order by 1''').fetchall()
    values2 = []
    lables2 = []
    for d in data:
      lables2.append(d[0])
      values2.append(d[1])
    data = db.execute(''' SELECT

  (CASE Strftime('%m', timestamp)
           WHEN '01' THEN 'Jan'
           WHEN '02' THEN 'Feb'
           WHEN '03' THEN 'Mar'
           WHEN '04' THEN 'Apr'
           WHEN '05' THEN 'May'
           WHEN '06' THEN 'Jun'
           WHEN '07' THEN 'Jul'
           WHEN '08' THEN 'Aug'
           WHEN '09' THEN 'Sept'
           WHEN '10' THEN 'Oct'
           WHEN '11' THEN 'Nov'
           WHEN '12' THEN 'Dec'
           ELSE ''
         END) || '-' || Strftime('%Y', timestamp)
    ,
       Sum(amount)
FROM   transactions
GROUP  BY 1
ORDER  BY 1  ''').fetchall()
    values3 = []
    lables3 = []
    for d in data:
      lables3.append(d[0])
      values3.append(d[1])
    data = db.execute('''select salesman,sum(amount) from transactions
      WHERE strftime("%m-%Y",timestamp) = strftime("%m-%Y",date('now'))  group by 1 order by 1''').fetchall()
    values4 = []
    lables4 = []
    for d in data:
      lables4.append(d[0])
      values4.append(d[1])
    conn.close()
    if yesterday_collection[0] == 0:
        percent_collection = ((today_collection[0]-yesterday_collection[0]))*100
    else:
        percent_collection = ((today_collection[0]-yesterday_collection[0])/yesterday_collection[0])*100
    return render_template('index.html', segment='index',
    pending_payments=pending_payments,pending_issues=pending_issues,
    pending_new_requests=pending_new_requests,collection = collection,
    total_connections=total_connections,free_connections=free_connections,
    today_collection=today_collection,total_collection=total_collection,
    inactives_recent = recent_inactives, unsettled=unsettled,lables = lables,values=values
    ,lables2=lables2,values2=values2,lables3=lables3,values3=values3
    ,percent_collection=percent_collection
    ,lables4=lables4,values4=values4
    )

@blueprint.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if current_user.department == 3 or current_user.department == 4:
        conn = sql.connect('db.sqlite3')
        db = conn.cursor()
        zone=''
        plan_cycle=''
        customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name
         FROM user LEFT JOIN zones ON user.zone = zones.id
         LEFT JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
         ORDER BY status
         ''').fetchall()
        zones = db.execute('''SELECT * FROM zones''').fetchall()
        cycles = db.execute('''SELECT * FROM plan_cycles''').fetchall()
        if request.method == "POST":
            zone = request.form['zone']
            cycle = request.form['plan_cycle']
            if(zone == '' and cycle == ''):
                customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name
                        FROM user JOIN zones ON user.zone = zones.id
                        JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
                        ORDER BY status
                        ''').fetchall()
            elif cycle == '':
                zone = int(zone)
                customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
                JOIN zones ON user.zone = zones.id
                JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
                WHERE zone = ?
                ORDER BY status
                ''',[zone]).fetchall()
            elif zone == '':
                cycle = int(cycle)
                customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
                JOIN zones ON user.zone = zones.id
                JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
                WHERE plan_cycle = ?
                ORDER BY status
                ''',[cycle]).fetchall()
            else:
                cycle = int(cycle)
                zone = int(zone)
                customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
                JOIN zones ON user.zone = zones.id
                JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
                WHERE plan_cycle = ? and zone = ?
                ORDER BY status
                ''',[cycle,zone]).fetchall()
            return render_template('users.html', users=customers,zones = zones,cycles = cycles,segment='users')
        conn.close()
        return render_template('users.html', users = customers,zones = zones,cycles = cycles,segment='users')
    else:
        return redirect(url_for('home_blueprint.index'))

@blueprint.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    if current_user.department != 2:
        conn = sql.connect('db.sqlite3')
        db = conn.cursor()
        transactions = db.execute('''SELECT username,user.id,amount,TIMESTAMP,salesman,billno,name,transactions.trasaction_id
         FROM transactions LEFT JOIN user ON user.id = transactions.user_id
         ''').fetchall()
        conn.close()
        return render_template('transactions.html', segment='transactions',transactions = transactions)
    else:
        return redirect(url_for('home_blueprint.index'))

@blueprint.route('/inactives', methods=['GET', 'POST'])
@login_required
def inactives():
    if current_user.department == 3 or current_user.department == 4:
      conn = sql.connect('db.sqlite3')
      db = conn.cursor()
      customers = db.execute('''SELECT user.username,email,mobile,status,user.id,zones.name,plan_cycles.name
       FROM user JOIN zones ON user.zone = zones.id
       JOIN recent_inactives ON user.id = recent_inactives.user_id
       JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
       WHERE updated_portal = 0
       ''').fetchall()
      zones = db.execute('''SELECT * FROM zones''').fetchall()
      cycles = db.execute('''SELECT * FROM plan_cycles''').fetchall()
      if request.method == "POST":
          zone = request.form['zone']
          cycle = request.form['plan_cycle']
          if(zone == '' and cycle == ''):
              customers = db.execute('''SELECT user.username,email,mobile,status,user.id,zones.name,plan_cycles.name
                      FROM user JOIN zones ON user.zone = zones.id
                      JOIN recent_inactives ON user.id = recent_inactives.user_id
                      JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
                      WHERE updated_portal = 0
                      ''').fetchall()
          elif cycle == '':
              zone = int(zone)
              customers = db.execute('''SELECT user.username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
              JOIN zones ON user.zone = zones.id
              JOIN recent_inactives ON user.id = recent_inactives.user_id
              JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
              WHERE zone = ?
              AND updated_portal = 0
              ''',[zone]).fetchall()
          elif zone == '':
              cycle = int(cycle)
              customers = db.execute('''SELECT user.username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
              JOIN zones ON user.zone = zones.id
              JOIN recent_inactives ON user.id = recent_inactives.user_id
              JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
              WHERE plan_cycle = ?
              AND updated_portal = 0
              ''',[cycle]).fetchall()
          else:
              cycle = int(cycle)
              zone = int(zone)
              customers = db.execute('''SELECT user.username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
              JOIN zones ON user.zone = zones.id
              JOIN recent_inactives ON user.id = recent_inactives.user_id
              JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
              WHERE plan_cycle = ? and zone = ? AND updated_portal = 0
              ''',[cycle,zone]).fetchall()
          return render_template('recently_inactive.html', segment='inactives',users=customers,zones = zones,cycles = cycles)
      conn.close()
      return render_template('recently_inactive.html', segment='inactives',users = customers,zones = zones,cycles = cycles)
    else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/edit/inactive/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_inactives(user_id):
    if current_user.department == 3 or current_user.department == 4:
      conn = sql.connect('db.sqlite3')
      db = conn.cursor()
      customer = db.execute('''
      SELECT user_id,user.username,inactive_date,portal_inactivated_date,updated_portal,user.name
       FROM recent_inactives JOIN user ON user_id = id WHERE user_id = ?''',[user_id]).fetchall()[0]
      if request.method == "POST":
          if request.form['status'] == 'Y':
              db.execute('''UPDATE recent_inactives SET updated_portal = 1 WHERE user_id = ?''',[user_id])
              db.execute('''UPDATE user SET account_status = "Inactive",sub_status="Inactive" WHERE id = ?''',[user_id])
              conn.commit()
              return redirect(url_for('home_blueprint.inactives'))
          return render_template('edit_inactives.html', user=customer)
      conn.close()
      return render_template('edit_inactives.html', user = customer)
    else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/raise_issue', methods=['GET', 'POST'])
@login_required
def raise_issue():
  if current_user.department == 3 or current_user.department == 4:
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name
     FROM user LEFT JOIN zones ON user.zone = zones.id
     LEFT JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
     ''').fetchall()
    zones = db.execute('''SELECT * FROM zones''').fetchall()
    cycles = db.execute('''SELECT * FROM plan_cycles''').fetchall()
    if request.method == "POST":
        zone = request.form['zone']
        cycle = request.form['plan_cycle']
        if(zone == '' and cycle == ''):
            customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name
                    FROM user LEFT JOIN zones ON user.zone = zones.id
                    LEFT JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
                    ''').fetchall()
        elif cycle == '':
            zone = int(zone)
            customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
            LEFT JOIN zones ON user.zone = zones.id
            LEFT JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
            WHERE zone = ?
            ''',[zone]).fetchall()
        elif zone == '':
            cycle = int(cycle)
            customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
            LEFT JOIN zones ON user.zone = zones.id
            LEFT JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
            WHERE plan_cycle = ?
            ''',[cycle]).fetchall()
        else:
            cycle = int(cycle)
            zone = int(zone)
            customers = db.execute('''SELECT username,email,mobile,status,user.id,zones.name,plan_cycles.name FROM user
            LEFT JOIN zones ON user.zone = zones.id
            LEFT JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
            WHERE plan_cycle = ? and zone = ?
            ''',[cycle,zone]).fetchall()
        return render_template('raise_issue copy.html', segment='raise_issue',users=customers,zones = zones,cycles = cycles)
    conn.close()
    return render_template('raise_issue copy.html', segment='raise_issue',users = customers,zones = zones,cycles = cycles)
  else:
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/raising/<user_id>',methods=['GET','POST'])
@login_required
def raising(user_id):
   if current_user.department == 3 or current_user.department == 4:
     errors = []
     valid = False
     conn = sql.connect('db.sqlite3')
     db = conn.cursor()
     output = db.execute('''SELECT * FROM issue_priorities''')
     priorities = output.fetchall()
     output = db.execute('''SELECT * FROM dept''')
     departments = output.fetchall()
     issue_types = db.execute('''SELECT * FROM complaint_type''').fetchall()
     reps = db.execute('''SELECT id,username,name FROM users''').fetchall()
     user_info = db.execute('''
     SELECT username, mobile, email, status, zones.name,user.id,user.name,address
     FROM user
     LEFT JOIN zones ON user.zone = zones.id
     WHERE user.id = ?
     ''',[user_id]).fetchall()[0]
     if request.method == 'POST':
         if not request.form['description']:
             errors.append('You have to enter a description')
         if not request.form['priority']:
             errors.append('You have to select a priority')
         if not request.form['department']:
             errors.append('You have to select a department')
         else:
             valid = True
         if valid:
             description = "UserName: " +  str(user_info[0]) + " Customer Name: " + str(user_info[6]) + " Zone: " + str(user_info[4]) + " Mobile: " + str(user_info[1]) + " Address: " + str(user_info[7])
             db.execute('''INSERT INTO issues (
               description, priority, department, raised_by, created, modified,issue_type_id,effected_customer_email,complaint_type,effected_customer,assigned_to)
               VALUES (?, ?, ?, ?, ?, ?,?,?, ?,?,?)''',
                        [description,
                         request.form['priority'],
                         request.form['department'],
                         current_user.username,
                         datetime.datetime.now(),
                         datetime.datetime.now(),
                     2,
                     request.form['email'],
                     request.form['type'],
                     user_id,
                     int(request.form['assignee'])
                 ])
             issue_id = db.execute('''SELECT MAX(issue_id) FROM issues''').fetchall()[0][0]
             assignee = int(request.form['assignee'])
             conn.commit()
             message="Thank you!! We got your complaint for " + request.form['type'] + ". Our team will reach you soon --Team KRP Broadband"
             mobile= str(user_info[1])
             querystring = {
                 "APIKey":apikey,
                 "senderid":senderid,
                 "channel":"2",
                 "DCS":"0",
                 "flashsms":"0",
                 "number":mobile,
                 "text":message,
                 "route":"0"}
             payload = ""
             headers = {
                'cache-control': "no-cache",
                }
             try:
                response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
                db.execute('''UPDATE issues SET customer_message_start = ? WHERE issue_id = ?''',[response.text,issue_id])
                conn.commit()
             except:
                db.execute('''UPDATE issues SET customer_message_start = ? WHERE issue_id = ?''',[sys.exc_info()[0],issue_id])
                conn.commit()

             message= "Customer Name: "+ user_info[6] + "\nComplaint: " + request.form['type'] + "\nCustomer Address:" + user_info[7] + "\nCustomer Mobile:" + str(user_info[1]) +"\nPlease act fast, make us proud --Team KRP Broadband"
             mobile=str(db.execute('''SELECT mobile FROM users where id = ?''',[assignee]).fetchall()[0][0])
             querystring = {
                 "APIKey":apikey,
                 "senderid":senderid,
                 "channel":"2",
                 "DCS":"0",
                 "flashsms":"0",
                 "number":mobile,
                 "text":message,
                 "route":"0"}
             payload = ""
             headers = {
                'cache-control': "no-cache",
                }
             try:
                response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
                db.execute('''UPDATE issues SET assignee_message_start = ? WHERE issue_id = ?''',[response.text,issue_id])
                conn.commit()
             except:
                db.execute('''UPDATE issues SET assignee_message_start = ? WHERE issue_id = ?''',["Message did not sent",issue_id])
                conn.commit()
             return redirect(url_for('home_blueprint.dashboard'))
     conn.close()
     return render_template('raise_issue.html',segment='raise_issue', priorities=priorities,departments=departments, errors=errors,user_info = user_info,issue_types = issue_types,reps = reps)
   else:
       return redirect(url_for('home_blueprint.index'))

@blueprint.route('/dashboard')
@login_required
def dashboard():
    if current_user.department != 1:
      issues = None
      conn = sql.connect('db.sqlite3')
      conn.row_factory = sql.Row

      db = conn.cursor()
      output = db.execute('''
      SELECT
           issues.issue_id AS issue_id,
           issues.description as description,
           issues.raised_by as raised_by,
           issues.created as created,
           issues.status as status,
           issue_status.status_name AS status_name,
           users.name AS assignee_name,
           users.username AS assignee_username
      FROM issues LEFT JOIN issue_status ON status = issue_status_id
      LEFT JOIN users ON issues.assigned_to = users.id
      WHERE issue_type_id <> 1
      and issues.status < 3
      ''').fetchall()
      closed = db.execute('''
      SELECT
           issues.issue_id AS issue_id,
           issues.description as description,
           issues.raised_by as raised_by,
           issues.created as created,
           issues.status as status,
           issue_status.status_name AS status_name,
           users.name AS assignee_name
      FROM issues LEFT JOIN issue_status ON status = issue_status_id
      LEFT JOIN users ON issues.assigned_to = users.id
      WHERE issue_type_id <> 1
      and issues.status = 3
      ''').fetchall()
      conn.close()
      return render_template('dashboard.html', issues=output,type=0,closed=closed)
    else:
        return redirect(url_for('home_blueprint.index'))

@blueprint.route('/issues/update/<issue_id>', methods=['GET', 'POST'])
@login_required
def update_issue(issue_id):
  if current_user.department != 1:
    errors = []
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    issue = list(db.execute('''SELECT issues.*,user.username FROM issues
    LEFT JOIN user ON issues.effected_customer = user.id
     WHERE issue_id = ?''',[issue_id]).fetchall()[0])
    if request.method == 'POST':
        if int(request.form['status']) < 0:
            status = issue[4]
        else:
            status = request.form['status']
        if not request.form['status']:
            errors.append('You have to select a status')
        else:
            if request.form['status'] ==  3:
                message="Thank you!! Our team has resolved your request, if you are still facing the issue, please contact us again --Team KRP Broadband"
                mobile= str(db.execute('''SELECT mobile FROM user where id = (SELECT effected_customer FROM issues where issue_id = ?)''',[issue_id]).fetchall()[0][0])
                querystring = {
                    "APIKey":apikey,
                    "senderid":senderid,
                    "channel":"2",
                    "DCS":"0",
                    "flashsms":"0",
                    "number":mobile,
                    "text":message,
                    "route":"0"}
                payload = ""
                headers = {
                   'cache-control': "no-cache",
                   }
                try:
                    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
                    db.execute('''UPDATE issues SET customer_message_end = ? WHERE issue_id = ?''',[response.text,issue_id])
                    conn.commit()
                except:
                    db.execute('''UPDATE issues SET customer_message_end = ? WHERE issue_id = ?''',["Message Did not send",issue_id])
                    conn.commit()
            db.execute('''UPDATE issues SET assigned_to = ?, status = ?
                    WHERE issue_id = ?''',
                       [request.form['assigned_to'], status, issue_id])
            fiber_cable = 0
            lockwire = 0
            onu = 0
            terminationbox = 0
            patchcord = 0
            terminationsmall = 0
            terminationlarge = 0
            split12 = 0
            split14 = 0
            split18 = 0
            cat5cable = 0
            rj45 = 0
            if request.form['fibercable']:
                fiber_cable = request.form['fibercable']
            if request.form['lockwire']:
                lockwire = request.form['lockwire']
            if request.form['onu']:
                onu = request.form['onu']
            if request.form['terminationbox']:
                terminationbox = request.form['terminationbox']
            if request.form['patchcord']:
                patchcord = request.form['patchcord']
            if request.form['terminationsmall']:
                terminationsmall = request.form['terminationsmall']
            if request.form['terminationlarge']:
                terminationlarge = request.form['terminationlarge']
            if request.form['split12']:
                split12 = request.form['split12']
            if request.form['split14']:
                split14 = request.form['split14']
            if request.form['split18']:
                split18 = request.form['split18']
            if request.form['cat5cable']:
                cat5cable = request.form['cat5cable']
            if request.form['rj45']:
                cat5cable = request.form['rj45']
            db.execute('''
            UPDATE products SET available_quantity = available_quantity - (
            CASE
             WHEN id = 16 THEN ?
             WHEN id = 17 THEN ?
             WHEN id = 15 THEN ?
             WHEN id = 14 THEN ?
             WHEN id = 13 THEN ?
             WHEN id = 12 THEN ?
             WHEN id = 11 THEN ?
             WHEN id = 10 THEN ?
             WHEN id = 9 THEN ?
             WHEN id = 7 THEN ?
             WHEN id = 6 THEN ?
             ELSE 0
             END),
             used_quanity = used_quanity + (
            CASE
             WHEN id = 16 THEN ?
             WHEN id = 17 THEN ?
             WHEN id = 15 THEN ?
             WHEN id = 14 THEN ?
             WHEN id = 13 THEN ?
             WHEN id = 12 THEN ?
             WHEN id = 11 THEN ?
             WHEN id = 10 THEN ?
             WHEN id = 9 THEN ?
             WHEN id = 7 THEN ?
             WHEN id = 6 THEN ?
             ELSE 0
             END)
            ''',[fiber_cable,cat5cable,split18,split14,split12,patchcord,terminationbox,terminationlarge,terminationsmall,rj45,onu,fiber_cable,cat5cable,split18,split14,split12,patchcord,terminationbox,terminationlarge,terminationsmall,rj45,onu])
            if issue[7] == 1:
                aadhar = request.files['aadhar']
                if aadhar.filename != '':
                    filename = secure_filename(aadhar.filename)
                    aadhar.save(os.path.join('app/home/uploads', str(issue[9]) + '_aadhar_' + filename))
                    db.execute('''UPDATE user SET aadhar_status = 1 WHERE id = ?''',[issue[9]])
                    conn.commit()
                photo = request.files['photo']
                if photo.filename != '':
                    filename = secure_filename(photo.filename)
                    photo.save(os.path.join('app/home/uploads', str(issue[9]) + '_photo_' + filename))
                    db.execute('''UPDATE user SET photo_status = 1 where id = ?''',[issue[9]])
                    conn.commit()
                caf = request.files['caf']
                if caf.filename != '':
                    filename = secure_filename(caf.filename)
                    photo.save(os.path.join('app/home/uploads', str(issue[9]) + '_photo_' + filename))
                    db.execute('''UPDATE user SET caf_status = 1 where id = ?''',[issue[9]])
                    conn.commit()
                if request.form['username']:
                    db.execute('''UPDATE user SET username = ?
                    WHERE id = ?''',[request.form['username'],issue[9]])
                    db.execute('''UPDATE issues SET new_customer_id = ? WHERE issue_id = ?''',[request.form['username'],issue_id])
                    conn.commit()
                if(int(request.form['status'])==3):
                    current_time = datetime.datetime.now().date()
                    plan_cycle = int(db.execute('''SELECT plan_cycle from user where id = ?''',[issue[9]]).fetchall()[0][0])

                    due_start_date = next_due_date(plan_cycle,current_time,1)
                    amount_info = db.execute('''SELECT due_amount,one_interval_amount FROM balance_info where user_id = ?''',[issue[9]]).fetchall()[0]
                    amount = int(amount_info[0])
                    one_interval_amount = int(amount_info[1])

                    db.execute('''UPDATE balance_info
                    SET due_start_date = ?,last_paid_date = ?,paid_amount = ?,due_amount = 0,customer_status= 'Active'
                    ,pending_intervals = 0
                     WHERE user_id = ?''',
                            [due_start_date,current_time,amount,issue[9]])

                    db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                    VALUES(?,0,?,"Active",?,?,0)
                    ''',[issue[9],one_interval_amount,current_time,due_start_date])

                    db.execute('''UPDATE user SET account_status = 'Active',sub_status = "Active", status = "Active" WHERE id = ?''',[issue[9]])
                    db.execute('''INSERT INTO transactions(user_id,amount,payment_type,salesman,billno,timestamp)
                    VALUES(?,?, ?, ?, ?, ?)
                    ''',[issue[9],amount,'CASH',current_user.username,request.form['billno'],current_time])
                    if plan_cycle == 2:
                        db.execute('''UPDATE user SET plan_cycle = 1 WHERE id = ?''',[issue[9]])
                        conn.commit()
                    conn.commit()
            conn.commit()

            url_return_link = 'home_blueprint.new_requests' if issue[7] == 1 else 'home_blueprint.dashboard'
            return redirect(url_for(url_return_link))

    priorities = db.execute('''SELECT * FROM issue_priorities''').fetchall()
    departments = db.execute('''SELECT * FROM dept''').fetchall()
    statuses = db.execute('''SELECT * FROM issue_status''').fetchall()
    reps = db.execute('''SELECT * FROM users''').fetchall()
    issue_type = db.execute('''SELECT issue_type_id FROM issues WHERE issue_id = ?''',[issue_id]).fetchall()[0][0]
    conn.close()
    return render_template('update_issue.html', issue=issue,
                           priorities=priorities, departments=departments,
                           reps=reps, statuses=statuses, errors=errors)
  else:
      return redirect(url_for('home_blueprint.index'))
# Need to update credential work from here
@blueprint.route('/new_connection', methods=['GET', 'POST'])
@login_required
def new_connection():
  if current_user.department == 3 or current_user.department == 4:
    errors = []
    valid = False
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    if request.method == 'POST':
       if not request.form['name']:
           errors.append('Please enter the Customer Name')
       if not request.form['add']:
           errors.append('Please enter the Customer Address')
       if not request.form['mobile']:
           errors.append('Please enter a Mobile Number')
       if not request.form['rate_plan']:
           errors.append('Please enter a Plan Details')
       if not request.form['plan_cycle']:
           errors.append('Please enter the Payment Cycle')
       else:
           valid = True
       if valid:
           print(request.form['zone'])
           print(type(request.form['zone']))
           discount = int(0 if request.form['discount'] == '' else request.form['discount'])
           actual_price = db.execute('''select price FROM plans WHERE plan_id = ?''',[request.form['rate_plan']]).fetchall()[0][0]
           discounted_price = int((100-discount)*actual_price/100)
           time_now = datetime.datetime.now()
           db.execute('''INSERT INTO user (
             name, address, mobile, altMobile, email, rate_plan, plan_cycle, zone,actual_amount,discount_amount, modifer,installation_charge,modified_timestamp
             ,account_status)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      [request.form['name'],
                       request.form['add'],
                       request.form['mobile'],
                       request.form['altmobile'],
                       request.form['email'],
                       int(request.form['rate_plan']),
                       int(request.form['plan_cycle']),
                       int(request.form['zone']),
                       actual_price,
                       discounted_price,
                       current_user.username,
                       int(request.form['installprice']),
                       time_now,
                   'Inactive'])
           user_info = db.execute('''SELECT id,plan_cycle FROM user WHERE modified_timestamp=?''',[time_now]).fetchall()[0]
           latest_user = int(user_info[0])
           plan_cycle = int(user_info[1])
           amount_calc = 1
           if plan_cycle == 1:
               amount_calc = 1
           if plan_cycle == 2:
               amount_calc = 3
           if plan_cycle == 3:
               amount_calc = 6
           if plan_cycle == 4:
               amount_calc = 12

           one_interval_amount = amount_calc * discounted_price
           db.execute('''INSERT INTO issues (
             description, priority, department, raised_by, created, modified,issue_type_id,effected_customer,new_customer_id)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?,'')''',
                      ['Name: ' + request.form['name'] + '\nAddress: '+request.form['add'] + '\nMobile: '+request.form['mobile']
                      +'\nAlternate Mobile: '+request.form['altmobile']
                      ,
                       0,
                       2,
                       current_user.username,
                       datetime.datetime.now(),
                       datetime.datetime.now(),
                       1,
                       latest_user
                   ])
           db.execute('''INSERT INTO balance_info (
             user_id, due_amount, paid_amount,  one_interval_amount, pending_intervals)
             VALUES (?, ?, ?, ?, ?)''',
                      [
                       latest_user,
                       discounted_price + int(request.form['installprice']),
                       0,
                       one_interval_amount,
                       1
                   ])
           message="Thank you for choosing KRP Broadband!! Our team will reach and update you the next steps, please make us the payment at the time of installation --Team KRP Broadband"
           mobile= request.form['mobile']
           querystring = {
               "APIKey":apikey,
               "senderid":senderid,
               "channel":"2",
               "DCS":"0",
               "flashsms":"0",
               "number":mobile,
               "text":message,
               "route":"0"}
           payload = ""
           headers = {
              'cache-control': "no-cache",
              }
           issue_id = db.execute('''SELECT MAX(issue_id) FROM issues''').fetchall()[0][0]
           try:
                response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
                db.execute('''UPDATE issues SET customer_message_start = ? WHERE issue_id = ?''',[response.text,issue_id])
                conn.commit()
           except:
                db.execute('''UPDATE issues SET customer_message_start = ? WHERE issue_id = ?''',["Message Not Sent",issue_id])
                conn.commit()
           return redirect(url_for('home_blueprint.new_requests'))

    zones = db.execute('''SELECT * FROM zones''').fetchall()
    output = db.execute('''SELECT * FROM plan_cycles''')
    cycles = output.fetchall()
    output = db.execute('''SELECT * FROM plans''')
    plans = output.fetchall()
    conn.close()
    # return render_template('index.html')
    return render_template('new_connection.html', cycles=cycles,zones=zones, plans=plans, errors=errors)
  else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/new_requests')
@login_required
def new_requests():
  if current_user.department != 1:
    issues = None
    # user_id = g.user['user_id']
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row

    db = conn.cursor()
    output = db.execute('''
    SELECT
         issues.issue_id AS issue_id,
         issues.description as description,
         issues.raised_by as raised_by,
         issues.created as created,
         issues.status as status,
         issue_status.status_name AS status_name,
         users.name AS assignee_name,
           users.username AS assignee_username
    FROM issues LEFT JOIN issue_status ON status = issue_status_id
    LEFT JOIN users ON issues.assigned_to = users.id
    WHERE issue_type_id = 1
    AND status < 3
    ''').fetchall()
    closed = db.execute('''
    SELECT
         issues.issue_id AS issue_id,
         issues.description as description,
         issues.raised_by as raised_by,
         issues.created as created,
         issues.status as status,
         issue_status.status_name AS status_name,
         users.name AS assignee_name,
           users.username AS assignee_username
    FROM issues LEFT JOIN issue_status ON status = issue_status_id
    LEFT JOIN users ON issues.assigned_to = users.id
    WHERE issue_type_id = 1
    AND status = 3
    ''').fetchall()
    conn.close()
    return render_template('dashboard.html', issues=output,type=1,closed=closed)
  else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/payments/add/<user_id>', methods=['GET', 'POST'])
@login_required
def payment_add(user_id):
  if current_user.department != 2:
    errors = []
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    user = list(db.execute('''
    SELECT user_id,due_amount,username,due_start_date,pending_intervals, plan_cycle,one_interval_amount,
    name,address
                 FROM balance_info JOIN user ON user_id = id WHERE user_id = ?''',[user_id]).fetchall()[0])
    modes = db.execute('''SELECT * FROM modes''').fetchall()
    if request.method == 'POST':
        current_time = datetime.datetime.now().replace(microsecond = 0)
        due_amount = int(request.form['due_amount'])
        paid_amount = int(request.form['paid_amount'])
        mode = request.form['mode']
        paid_intervals = int(paid_amount / user[6])
        pending_intervals = user[4] - paid_intervals

        billing_date = datetime.datetime.strptime(user[3],"%Y-%m-%d").date()
        due_date = next_due_date(user[5],billing_date,paid_intervals)

        db.execute('''UPDATE balance_info SET paid_amount = paid_amount + ?, due_amount = due_amount - ?, due_start_date = ?,last_paid_date = ?
                WHERE user_id = ?''',
                   [paid_amount, paid_amount, due_date, current_time.date(),user_id])
        #Message API
        message="We have received your payment of " + str(paid_amount) + "You have paid to our collection executive "+current_user.username +"--Team KRP Broadband"
        mobile= db.execute('''SELECT mobile FROM USER where id = ?''',[user_id]).fetchall()[0][0]
        querystring = {
            "APIKey":apikey,
            "senderid":senderid,
            "channel":"2",
            "DCS":"0",
            "flashsms":"0",
            "number":mobile,
            "text":message,
            "route":"0"}
        payload = ""
        headers = {
           'cache-control': "no-cache",
           }
        try:
            response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
            db.execute('''INSERT INTO transactions(user_id,amount,payment_type,salesman,billno,timestamp,payment_receipt_message)
        VALUES(?,?, ?, ?, ?,?,?)
        ''',[user_id,paid_amount,mode,current_user.username,request.form['billno'],current_time,response.text])
            conn.commit()
        except:
            db.execute('''INSERT INTO transactions(user_id,amount,payment_type,salesman,billno,timestamp,payment_receipt_message)
        VALUES(?,?, ?, ?, ?,?,?)
        ''',[user_id,paid_amount,mode,current_user.username,request.form['billno'],current_time,'Message Did not sent'])
            conn.commit()

        db.execute('''UPDATE unsettled_balance SET due_amount = due_amount - ? WHERE user_id = ?''',[paid_amount,user_id])
        conn.commit()
        return redirect(url_for('home_blueprint.payment'))
    conn.close()
    return render_template('add_payment.html', user=user,modes=modes)
  else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/update_user_profile/<user_id>', methods=['GET', 'POST'])
@login_required
def update_user_profile(user_id):
  if current_user.department == 3:
    errors = []
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    current_time = datetime.datetime.now()
    user_info = list(db.execute('''
    SELECT
    id, username, email ,
    mobile , status , address ,
    zone ,name ,    altMobile ,
    rate_plan ,    plan_cycle ,    modifer ,
    modified_timestamp,    sub_status ,account_status,
    discount_amount,billing_date  FROM user WHERE id = ?''',[user_id]).fetchall()[0])
    if request.method == 'POST':
        if ( request.form['mobile']==user_info[3]
         and request.form['status']==user_info[4] and request.form['add']==user_info[5]
         and int(request.form['zone'])==user_info[6] and request.form['altmobile']==user_info[8]
         and int(request.form['plan'])==user_info[9] and int(request.form['cycle'])==user_info[10]
         and request.form['account']==user_info[14] and request.form['sub']==user_info[13]
        ):
            return redirect(url_for('home_blueprint.users'))
        else:
            db.execute('''
            INSERT INTO user_history VALUES(
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            ''',[user_id,user_info[1],user_info[2],request.form['mobile'],request.form['status'],request.form['add'],
            'NA',request.form['zone'],user_info[5],request.form['altmobile'],request.form['plan'],request.form['cycle'],current_user.username,current_time,
            request.form['sub'],request.form['account'],int(request.form['final_amount'])])

            if(user_info[4]=='Active' and request.form['status'] == 'Inactive' and user_info[10] != 7):
                due_amount = int(db.execute('''SELECT due_amount FROM balance_info WHERE user_id = ?''',[user_id]).fetchall()[0][0])
                if due_amount != 0 :
                    check = db.execute('''SELECT * FROM unsettled_balance WHERE user_id = ?''',[user_id]).fetchall()
                    if(len(check) == 0):
                        db.execute('''INSERT INTO unsettled_balance VALUES(?,?,1)''',[user_id,due_amount])
                        conn.commit()
                    else:
                        db.execute('''UPDATE unsettled_balance SET due_amount = due_amount + ?,no_of_times = no_of_times+1 WHERE user_id = ?''',due_amount,user_id)
                        conn.commit()

                db.execute('''INSERT INTO recent_inactives(user_id,username,inactive_date,updated_portal)
                VALUES(?,?,?,?)''',[user_id,user_info[1],datetime.datetime.now().date(),0])
                db.execute('''UPDATE balance_info SET customer_status = "Inactive" WHERE user_id =?''',[user_id])
                conn.commit()

            if(user_info[4]=='Active' and request.form['status'] == 'Inactive' and user_info[10] == 7):
                db.execute('''INSERT INTO balance_info VALUES(?,?,?,?,?,"Inactive",?,?)''',[user_id,0,0,None,None,0,0])
                db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                VALUES(?,?,?,"Inactive",?,?,?)''',[user_id,0,0,None,None,0])
                conn.commit()

            if(user_info[4]=='Inactive' and request.form['status'] == 'Active'):

                previous_due_amount = int(db.execute('''SELECT due_amount FROM balance_info where user_id = ?''',[user_id]).fetchall()[0][0])
                plan_cycle = int(request.form['cycle'])
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

                plan_amount = int(db.execute('''SELECT price FROM plans where plan_id = ?''',[int(request.form['plan'])]).fetchall()[0][0])
                new_amount = plan_amount * amount_calc

                db.execute('''UPDATE balance_info SET due_amount = due_amount + ?,due_start_date = ?,customer_status="Active",
                one_interval_amount = ?,pending_intervals = pending_intervals + 1 WHERE user_id = ?
                ''',[new_amount,datetime.datetime.now().date(),new_amount,user_id])
                next_invoice_date = next_due_date(plan_cycle,datetime.datetime.now().date(),1)
                db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                VALUES(?,?,?,"Active",?,?,?)
                ''',[user_id,previous_due_amount,new_amount,datetime.datetime.now().date(),next_invoice_date,0])
                conn.commit()

            if(user_info[10]==7 and int(request.form['cycle']) != 7 and request.form['status'] == 'Active'):
                plan_amount = user_info[15]
                plan_cycle = int(request.form['cycle'])
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

                billing_date = user_info[16]
                if billing_date > datetime.date.today():
                    periods = 0
                else:
                    periods = calculate_periods(plan_cycle,billing_date) + 1

                due_amount_total = periods * amount_calc * plan_amount
                one_period_amount = plan_amount * amount_calc
                db.execute('''INSERT INTO balance_info(user_id,due_amount,customer_status,due_start_date, pending_intervals,one_interval_amount,paid_amount)
                VALUES(?,?,?,?,?,?,?)
                ''',[user_id,due_amount_total,"Active",billing_date,periods,one_period_amount,0])

                due_amount = due_amount_total - one_period_amount
                if due_amount < 0:
                    due_amount = 0
                invoice_date = next_due_date(plan_cycle,billing_date,0)
                next_invoice_date = next_due_date(plan_cycle,invoice_date,1)

                db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                 VALUES(?,?,?,?,?,?,?)''',[user_id,due_amount,one_period_amount,"Active",invoice_date,next_invoice_date,0])
                conn.commit()

            new_amount = int(db.execute('''select price from plans where plan_id = ?''',[int(request.form['plan'])]).fetchall()[0][0])

            if(user_info[4] == request.form['status'] and user_info[10] != 7 and user_info[9] != int(request.form['plan'])):
                plan_cycle = int(request.form['cycle'])
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
                due_amount_total = amount_calc * new_amount
                db.execute('''UPDATE balance_info SET due_amount = due_amount + ?,pending_intervals = pending_intervals + 1
                ,one_interval_amount = ?
                WHERE user_id = ?
                ''',[due_amount_total,due_amount_total,user_id])

                next_invoice_date = next_due_date(plan_cycle,datetime.datetime.now().date,1)
                previous_due_amount = int(db.execute('''SELECT due_amount FROM balance_info where user_id = ?''',[user_id]).fetchall()[0][0])
                db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                 VALUES(?,?,?,?,?,?,?)''',[user_id,previous_due_amount,due_amount_total,"Active",datetime.datetime.now().date(),next_invoice_date,0])
                conn.commit()

            if (user_info[9] == int(request.form['plan'])):
                new_amount = int(request.form['final_amount'])

            db.execute('''
            UPDATE user SET mobile = ?,status = ?,address = ?,zone=?,
            altMobile=?,rate_plan=?,plan_cycle=?,modified_timestamp=?,modifer=?,sub_status=?,account_status=?
                        ,discount_amount=?
                        WHERE id = ?
            ''',[request.form['mobile'],request.form['status'],request.form['add'],
            int(request.form['zone']),request.form['altmobile'],int(request.form['plan']),int(request.form['cycle']),current_user.username,current_time,
            request.form['sub'],request.form['account']
           ,new_amount,user_id])
            conn.commit()
            return redirect(url_for('home_blueprint.users'))
    zones = db.execute('''SELECT * FROM zones''').fetchall()
    cycles = db.execute('''SELECT * FROM plan_cycles WHERE id IN (1,2,3,4)''').fetchall()
    plans = db.execute('''SELECT * FROM plans WHERE plan_id IN (1,7,15,16,17)''').fetchall()
    conn.close()
    return render_template('update_profile.html', user=user_info,cycles=cycles,zones=zones, plans=plans)
  else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
  if current_user.department != 2:
    issues = None
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    db = conn.cursor()
    zones = db.execute('''select * from zones''').fetchall()
    output = db.execute('''
     SELECT
         user.username as username,
         user.name AS Name,
         balance_info.due_amount as due_amount,
         user.mobile as MobileNumber,
         user.address as Address,
         user.id as user_id,
         due_start_date,
         user.zone
                              FROM balance_info LEFT JOIN user ON user_id = id WHERE due_amount > 0
                              and customer_status = 'Active'
                              order by due_amount desc
                              ''').fetchall()
    if request.method == "POST":
        zone = request.form['zone']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        if start_date == '':
            start_date = datetime.datetime.strptime("1969-01-01","%Y-%m-%d").date()
        else:
            start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
        if end_date == '':
            end_date = datetime.datetime.strptime("2069-01-01","%Y-%m-%d").date()
        else:
            end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
        if zone == '':
            zone = '0'
        zone = int(zone)
        if zone == 0:
            output = db.execute('''
            SELECT
            user.username as username,
            user.name AS Name,
            balance_info.due_amount as due_amount,
            user.mobile as MobileNumber,
            user.address as Address,
            user.id as user_id,
            due_start_date,
            user.zone
            FROM balance_info LEFT JOIN user ON user_id = id
             WHERE due_amount > 0 and customer_status = 'Active'
             and due_start_date between ? and ?
             order by due_amount desc
             ''',[start_date,end_date]).fetchall()
        else:
            output = db.execute('''
                 SELECT
                 user.username as username,
                 user.name AS Name,
                 balance_info.due_amount as due_amount,
                 user.mobile as MobileNumber,
                 user.address as Address,
                 user.id as user_id,
                 due_start_date,
                 user.zone
             FROM balance_info LEFT JOIN user ON user_id = id
              WHERE due_amount > 0 and customer_status = 'Active'
              and zone = ?
              and due_start_date between ? and ?
              order by due_amount desc
              ''',[zone,start_date,end_date]).fetchall()

        return render_template('payments.html', issues=output, zones = zones,processing_place=1)
    conn.close()
    return render_template('payments.html', issues=output,zones = zones,processing_place=1)
  else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/unsettled_amount', methods=['GET', 'POST'])
@login_required
def unsettled_amount():
  if current_user.department == 3 or current_user.department == 1:
    issues = None
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    db = conn.cursor()
    zones = db.execute('''select * from zones''').fetchall()
    output = db.execute('''
     SELECT
         user.username as username,
         user.name AS Name,
         balance_info.due_amount as due_amount,
         user.mobile as MobileNumber,
         user.address as Address,
         user.id as user_id,
         due_start_date,
         user.zone
                              FROM balance_info
                              JOIN unsettled_balance ON balance_info.user_id = unsettled_balance.user_id
                              LEFT JOIN user ON balance_info.user_id = id WHERE balance_info.due_amount > 0
                              order by due_amount desc
                              ''').fetchall()
    if request.method == "POST":
        zone = request.form['zone']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        if start_date == '':
            start_date = datetime.datetime.strptime("1969-01-01","%Y-%m-%d").date()
        else:
            start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
        if end_date == '':
            end_date = datetime.datetime.strptime("2069-01-01","%Y-%m-%d").date()
        else:
            end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
        if zone == '':
            zone = '0'
        zone = int(zone)
        if zone == 0:
            output = db.execute('''
            SELECT
            user.username as username,
            user.name AS Name,
            balance_info.due_amount as due_amount,
            user.mobile as MobileNumber,
            user.address as Address,
            user.id as user_id,
            due_start_date,
            user.zone
            FROM balance_info LEFT JOIN user ON balance_info.user_id = id
            JOIN unsettled_balance ON balance_info.user_id = unsettled_balance.user_id
             WHERE balance_info.due_amount > 0
             and due_start_date between ? and ?
             order by due_amount desc
             ''',[start_date,end_date]).fetchall()
        else:
            output = db.execute('''
                 SELECT
                 user.username as username,
                 user.name AS Name,
                 balance_info.due_amount as due_amount,
                 user.mobile as MobileNumber,
                 user.address as Address,
                 user.id as user_id,
                 due_start_date,
                 user.zone
             FROM balance_info LEFT JOIN user ON balance_info.user_id = id
             JOIN unsettled_balance ON balance_info.user_id = unsettled_balance.user_id
              WHERE balance_info.due_amount > 0
              and zone = ?
              and due_start_date between ? and ?
              order by due_amount desc
              ''',[zone,start_date,end_date]).fetchall()
        return render_template('unsettled_dues.html', issues=output, zones = zones,processing_place = 0)
    conn.close()
    return render_template('unsettled_dues.html', issues=output,zones = zones,processing_place=0)
  else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/generate_invoice/<tid>', methods=['GET','POST'])
@login_required
def generate_invoice(tid):
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    data = db.execute('''SELECT username,address, user.name, plan_name,PRICE,due_amount,current_cycle_amount,
    invoice_date,invoices.id, due_amount + current_cycle_amount as total_amount,plan_cycle,plan_cycles.name,user.mobile,next_invoice_date
    ,actual_amount,discount_amount
     FROM invoices JOIN user
    on user.id = invoices.user_id
    LEFT JOIN plans on rate_plan = plan_id
    LEFT JOIN plan_cycles ON plan_cycles.id = user.plan_cycle
      WHERE invoices.id = ?''',[tid]).fetchall()[0]
    conn.close()
    return render_template('generate_invoice.html', invoice_details=data)

@blueprint.route('/generate_bill/<tid>', methods=['GET','POST'])
@login_required
def generate_bill(tid):
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    transactions = db.execute('''
    SELECT
        username, user.id,amount,
        TIMESTAMP,salesman,billno,
        name,transactions.trasaction_id,address,mobile
     FROM transactions LEFT JOIN user ON user.id = transactions.user_id
     WHERE trasaction_id = ?
     ''',[tid]).fetchall()[0]
    conn.close()
    return render_template('invoice_test.html', trans_details=transactions)

@blueprint.route('/generate_ledger/<user_id>', methods=['GET','POST'])
@login_required
def generate_ledger(user_id):
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    data = db.execute('''SELECT username,amount,TIMESTAMP,name,address FROM transactions JOIN user on user_id = id WHERE user_id = ?''',[user_id]).fetchall()
    total = db.execute('''SELECT sum(amount) FROM transactions WHERE user_id = ?''',[user_id]).fetchall()
    conn.close()
    return render_template('generate_ledger.html', invoice_details=data, total=total)

def invoice_helper(start_date,end_date):
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    if start_date == '' and end_date == '':
        transactions = db.execute('''
            SELECT
                 user.username,user.mobile, user.email,
                 invoices.due_amount,invoices.current_cycle_amount AS amount,
                 invoice_date,invoices.id as invoice_id,
                         zones.name
                 FROM invoices JOIN user on user_id = user.id
                 JOIN zones ON zones.id= user.zone
                 ''').fetchall()
    elif end_date == '':
        start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
        transactions = db.execute('''
            SELECT
                 user.username,user.mobile, user.email,
                 invoices.due_amount,invoices.current_cycle_amount AS amount,
                 invoice_date,invoices.id as invoice_id,
                         zones.name
                 FROM invoices JOIN user on user_id = user.id
                 JOIN zones ON zones.id= user.zone
                 AND invoice_date >= ?
                 ''',[start_date]).fetchall()
    elif start_date == '':
        end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
        transactions = db.execute('''
            SELECT
                 user.username,user.mobile, user.email,
                 invoices.due_amount,invoices.current_cycle_amount AS amount,
                 invoice_date,invoices.id as invoice_id,
                         zones.name
                 FROM invoices JOIN user on user_id = user.id
                 JOIN zones ON zones.id= user.zone
                 AND invoice_date <= ?
                 ''',[end_date]).fetchall()
    else:
        start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
        transactions = db.execute('''
            SELECT
                 user.username,user.mobile, user.email,
                 invoices.due_amount,invoices.current_cycle_amount AS amount,
                 invoice_date,invoices.id as invoice_id,
                         zones.name
                 FROM invoices JOIN user on user_id = user.id
                 JOIN zones ON zones.id= user.zone
                 AND invoice_date BETWEEN ? AND ?
                 ''',[start_date,end_date]).fetchall()
    return transactions
@blueprint.route('/invoice', methods=['GET', 'POST'])
@login_required
def invoice():
  if current_user.department !=2 :
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    transactions = db.execute('''SELECT user.username,user.mobile, user.email, invoices.due_amount,invoices.current_cycle_amount AS amount,
    invoice_date,invoices.id as invoice_id,
                         zones.name
     FROM invoices JOIN user on user_id = user.id
     JOIN zones ON zones.id= user.zone''').fetchall()
    zones = db.execute('''SELECT * FROM zones''').fetchall()
    if request.method == "POST":
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        zone = request.form['zone']
        if zone == '':
            transactions = invoice_helper(start_date,end_date)
        else:
            zone = int(zone)
            if start_date == '' and end_date == '':
                transactions = db.execute('''
                    SELECT
                         user.username,user.mobile, user.email,
                         invoices.due_amount,invoices.current_cycle_amount AS amount,
                         invoice_date,invoices.id as invoice_id,
                         zones.name
                         FROM invoices JOIN user on user_id = user.id
                         JOIN zones ON zones.id= user.zone
                         WHERE user.zone = ?
                         ''',[zone]).fetchall()
            elif end_date == '':
                start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
                transactions = db.execute('''
                    SELECT
                         user.username,user.mobile, user.email,
                         invoices.due_amount,invoices.current_cycle_amount AS amount,
                         invoice_date,invoices.id as invoice_id,
                         zones.name
                         FROM invoices JOIN user on user_id = user.id
                         JOIN zones ON zones.id= user.zone
                         WHERE user.zone = ?
                         AND invoice_date >= ?
                         ''',[zone,start_date]).fetchall()
            elif start_date == '':
                end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
                transactions = db.execute('''
                    SELECT
                         user.username,user.mobile, user.email,
                         invoices.due_amount,invoices.current_cycle_amount AS amount,
                         invoice_date,invoices.id as invoice_id,
                         zones.name
                         FROM invoices JOIN user on user_id = user.id
                         JOIN zones ON zones.id= user.zone
                         WHERE user.zone = ?
                         AND invoice_date <= ?
                         ''',[zone,end_date]).fetchall()
            else:
                start_date = datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
                end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
                transactions = db.execute('''
                    SELECT
                         user.username,user.mobile, user.email,
                         invoices.due_amount,invoices.current_cycle_amount AS amount,
                         invoice_date,invoices.id as invoice_id,
                         zones.name
                         FROM invoices JOIN user on user_id = user.id
                         JOIN zones ON zones.id= user.zone
                         WHERE user.zone = ?
                         AND invoice_date BETWEEN ? AND ?
                         ''',[zone,start_date,end_date]).fetchall()
        transactions = invoice_helper(start_date,end_date)
        return render_template('invoice.html', users=transactions,zones = zones)
    conn.close()
    return render_template('invoice.html', users = transactions,zones = zones)
  else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/update_inventory', methods=['GET', 'POST'])
@login_required
def update_inventory():
  if current_user.department == 3:
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()
    products = db.execute("SELECT * from products").fetchall()
    if request.method == 'POST':
        prod_name = request.form['prod_name']
        quantity = request.form['prod_quantity']

        transaction_allowed = False
        if prod_name not in ['', ' ', None]:
            if quantity not in ['', ' ', None]:
                transaction_allowed = True

        if transaction_allowed:
            try:
                db.execute("INSERT INTO products (name, quantity, used_quanity,available_quantity ) VALUES (?, ?,?,?)", (prod_name, quantity,0,quantity))
                conn.commit()
            except sql.Error as e:
                msg = f"An error occurred: {e.args[0]}"
            else:
                msg = f"{prod_name} added successfully"

            if msg:
                print(msg)

            return redirect(url_for('home_blueprint.update_inventory'))
    conn.close()
    return render_template('inventory.html', products = products)
  else:
      return redirect(url_for('home_blueprint.index'))

@blueprint.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    type_ = request.args.get('type')
    conn = sql.connect('db.sqlite3')
    db = conn.cursor()

    if type_ == 'location' and request.method == 'POST':
        loc_id = request.form['loc_id']
        loc_name = request.form['loc_name']

        if loc_name:
            db.execute("UPDATE location SET loc_name = ? WHERE loc_id == ?", (loc_name, str(loc_id)))
            conn.commit()

        return redirect(url_for('location'))

    elif type_ == 'product' and request.method == 'POST':
        prod_id = request.form['prod_id']
        prod_name = request.form['prod_name']
        prod_quantity = request.form['prod_quantity']

        if prod_name:
            db.execute("UPDATE products SET name = ? WHERE id == ?", (prod_name, prod_id))
        if prod_quantity:
            db.execute("SELECT quantity FROM products WHERE id = ?", (prod_id,))
            old_prod_quantity = db.fetchone()[0]
            db.execute("UPDATE products SET quantity = ? + ?, available_quantity =  available_quantity + ?"
                           "WHERE id == ?", (prod_quantity, old_prod_quantity, prod_quantity, prod_id))
        conn.commit()

        return redirect(url_for('home_blueprint.update_inventory'))
    conn.close()
    return render(url_for(home_blueprint.update_inventory))

@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith( '.html' ):
            template += '.html'

        # Detect the current page
        segment = get_segment( request )

        # Serve the file (if exists) from app/templates/FILE.html
        return render_template( template, segment=segment )

    except TemplateNotFound:
        return render_template('page-404.html'), 404

    except:
        return render_template('page-500.html'), 500

# Helper - Extract current page name from request
def get_segment( request ):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
