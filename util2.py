# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
 
import hashlib, binascii, os

# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/

def hash_pass( password ):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash) # return bytes

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
password = hash_pass('0205')
username = 'rnaik'
db.execute('''UPDATE users SET password = %s where username = %s''',[password,username])
conn.commit()
# db.execute('''INSERT INTO users(username,password,name,department) values(?,?,?,?)''',['suhasini',password,'Suhasini',4])
# usernames = ['nsanju',
# 'chinni',
# 'nagaraju',
# 'venkatesh',
# 'shyam',
# 'vprasad',
# 'shok',
# 'mahesh',
# 'dmahesh',
# 'mmadhu',
# 'kravi',
# 'dpeter',
# 'cereddy',
# 'anaik',
# 'hbasha',
# 'raja',
# 'rsekhar',
# 'bnaik',
# 'ramu',
# 'rnaik',
# 'ajay']
# names = ['N.Sanju.',
# 'Chinni',
# 'Nagaraju',
# 'Venkatesh',
# 'Shyam',
# 'Vara Prasad',
# 'Ashok',
# 'Mahesh',
# 'D Mahesh Reddy',
# 'M.Madhu',
# 'K.Ravi',
# 'D.Petar',
# 'C.Eswar Reddy',
# 'Arjun Naik',
# 'Hussain Basha',
# 'Raja',
# 'Raja Sekhar',
# 'Badri Naik',
# 'Ramu',
# 'Raju Naik',
# 'Ajay']
#
# passwords = ['8341090949',
# '8801436230',
# '9000721709',
# '9010494224',
# '9133597770',
# '8978223489',
# '9032747469',
# '8008815743',
# '9502241391',
# '9160726102',
# '9912898567',
# '9154199898',
# '7893888261',
# '6300374797',
# '9160066950',
# '9704850963',
# '7032645762',
# '8008523105',
# '9133597774',
# '9133597772',
# '9515581287']
#
# mobiles = [8341090949    ,
# 8801436230    ,
# 9000721709    ,
# 9010494224    ,
# 9133597770    ,
# 8978223489    ,
# 9032747469    ,
# 8008815743    ,
# 9502241391    ,
# 9160726102    ,
# 9912898567    ,
# 9154199898    ,
# 7893888261    ,
# 6300374797    ,
# 9160066950    ,
# 9704850963    ,
# 7032645762    ,
# 8008523105    ,
# 9133597774    ,
# 9133597772    ,
# 9515581287    ]
# for i in range(len(passwords)):
#     password = hash_pass(passwords[i])
#     db.execute('''INSERT INTO users(username,password,name,mobile) values(?,?,?,?)''',[usernames[i],password,names[i],mobiles[i]])
# password = hash_pass("pass")
