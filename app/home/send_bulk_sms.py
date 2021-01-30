import requests
import mysql.connector
from mysql.connector.constants import ClientFlag

config = {
    'user': 'krpcommu_admin',
    'password': 'Vikram@123',
    'host': '172.105.56.108',
    'database': 'krpcommu_fibernet',
    'use_pure': True
}
url = "https://www.smsgatewayhub.com/api/mt/SendSMS"
apikey = "zlK4AxVdjEW230uUT6FVaQ"
senderid = "SMSTST"

conn = mysql.connector.connect(**config)
db = conn.cursor()

db.execute('''SELECT mobile,name FROM User_data WHERE id = 3045''')
details = db.fetchall()
for info in details:
    name = info[1]
    mobile = info[0]
    message="Hello " + str(name) + "\nWe have server down from Hyderabad, we regret for inconvienience. Please hope to get the line back 2 - 3 hours.\n --Team KRP Broadband"
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
    except Exception:
        print("Message not delivered")
        # pass
