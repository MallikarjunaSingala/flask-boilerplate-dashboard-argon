def update_user_profile(user_id):
  if current_user.department == 3:
    errors = []
    conn = mysql.connector.connect(**config)
    db = conn.cursor()
    current_time = datetime.datetime.now()
    db.execute('''
    SELECT
    id, username, email ,
    mobile , status , address ,
    zone ,name ,    altMobile ,
    rate_plan ,    plan_cycle ,    modifer ,
    modified_timestamp,    sub_status ,account_status,
    discount_amount,billing_date  FROM User_data user WHERE id = %s''',[user_id])
    user_info = list(db.fetchall()[0])
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
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
            ''',[user_id,user_info[1],user_info[2],request.form['mobile'],request.form['status'],request.form['add'],
            'NA',request.form['zone'],user_info[5],request.form['altmobile'],request.form['plan'],request.form['cycle'],current_user.username,current_time,
            request.form['sub'],request.form['account'],int(request.form['final_amount'])])

            if(user_info[4]=='Active' and request.form['status'] == 'Inactive' and user_info[10] != 7):
                
                db.execute('''SELECT due_amount FROM balance_info WHERE user_id = %s''',[user_id])
                due_amount = int(db.fetchall()[0][0])
                if due_amount != 0 :
                    db.execute('''SELECT * FROM unsettled_balance WHERE user_id = %s''',[user_id])
                    check = db.fetchall()
                    if(len(check) == 0):
                        db.execute('''INSERT INTO unsettled_balance VALUES(%s,%s,1)''',[user_id,due_amount])
                        conn.commit()
                    else:
                        db.execute('''UPDATE unsettled_balance SET due_amount = due_amount + %s,no_of_times = no_of_times+1 WHERE user_id = %s''',due_amount,user_id)
                        conn.commit()
                db.execute('''INSERT INTO recent_inactives(user_id,username,inactive_date,updated_portal)
                VALUES(%s,%s,%s,%s)''',[user_id,user_info[1],datetime.datetime.now().date(),0])
                db.execute('''UPDATE balance_info SET customer_status = "Inactive" WHERE user_id = %s''',[user_id])
                conn.commit()

            if(user_info[4]=='Active' and request.form['status'] == 'Inactive' and user_info[10] == 7):
                db.execute('''INSERT INTO balance_info VALUES(%s,%s,%s,%s,%s,"Inactive",%s,%s)''',[user_id,0,0,None,None,0,0])
                db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                VALUES(%s,%s,%s,"Inactive",%s,%s,%s)''',[user_id,0,0,None,None,0])
                conn.commit()

            if(user_info[4]=='Inactive' and request.form['status'] == 'Active'):
                db.execute('''SELECT due_amount FROM balance_info where user_id = %s''',[user_id])
                previous_due_amount = int(db.fetchall()[0][0])
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

                db.execute('''SELECT price FROM plans where plan_id = %s''',[int(request.form['plan'])])
                plan_amount = int(db.fetchall()[0][0])
                new_amount = plan_amount * amount_calc

                db.execute('''UPDATE balance_info SET due_amount = due_amount + %s,due_start_date = %s,customer_status="Active",
                one_interval_amount = %s,pending_intervals = pending_intervals + 1 WHERE user_id = %s
                ''',[new_amount,datetime.datetime.now().date(),new_amount,user_id])
                next_invoice_date = next_due_date(plan_cycle,datetime.datetime.now().date(),1)
                db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                VALUES(%s,%s,%s,"Active",%s,%s,%s)
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
                VALUES(%s,%s,%s,%s,%s,%s,%s)
                ''',[user_id,due_amount_total,"Active",billing_date,periods,one_period_amount,0])

                due_amount = due_amount_total - one_period_amount
                if due_amount < 0:
                    due_amount = 0
                invoice_date = next_due_date(plan_cycle,billing_date,0)
                next_invoice_date = next_due_date(plan_cycle,invoice_date,1)

                db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                 VALUES(%s,%s,%s,%s,%s,%s,%s)''',[user_id,due_amount,one_period_amount,"Active",invoice_date,next_invoice_date,0])
                conn.commit()

            db.execute('''select price from plans where plan_id = %s''',[int(request.form['plan'])])
            new_amount = int(db.fetchall()[0][0])

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
                db.execute('''UPDATE balance_info SET due_amount = due_amount + %s,pending_intervals = pending_intervals + 1
                ,one_interval_amount = %s
                WHERE user_id = %s
                ''',[due_amount_total,due_amount_total,user_id])

                next_invoice_date = next_due_date(plan_cycle,datetime.datetime.now().date,1)
                db.execute('''SELECT due_amount FROM balance_info where user_id = %s''',[user_id])
                previous_due_amount = int(db.fetchall()[0][0])
                db.execute('''INSERT INTO invoices(user_id,due_amount,current_cycle_amount,user_status,invoice_date,next_invoice_date,processed)
                 VALUES(%s,%s,%s,%s,%s,%s,%s)''',[user_id,previous_due_amount,due_amount_total,"Active",datetime.datetime.now().date(),next_invoice_date,0])
                 
                conn.commit()

            if (user_info[9] == int(request.form['plan'])):
                new_amount = int(request.form['final_amount'])

            db.execute('''
            UPDATE User_data SET mobile = %s,status = %s,address = %s,zone= %s,
            altMobile= %s,rate_plan= %s,plan_cycle= %s,modified_timestamp= %s,modifer= %s,sub_status= %s,account_status= %s
                        ,discount_amount= %s
                        WHERE id = %s
            ''',[request.form['mobile'],request.form['status'],request.form['add'],
            int(request.form['zone']),request.form['altmobile'],int(request.form['plan']),int(request.form['cycle']),current_user.username,current_time,
            request.form['sub'],request.form['account']
           ,new_amount,user_id])
            conn.commit()
            return redirect(url_for('home_blueprint.users'))
    db.execute('''SELECT * FROM zones''')
    zones = db.fetchall()
    db.execute('''SELECT * FROM plan_cycles''')
    cycles = db.fetchall()
    db.execute('''SELECT * FROM plans''')
    plans = db.fetchall()
    conn.close()
    return render_template('update_profile.html', user=user_info,cycles=cycles,zones=zones, plans=plans)
  else:
      return redirect(url_for('home_blueprint.index'))