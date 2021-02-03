import schedule
import time
def scheduledTask():
    print("Ran")
# schedule.every(5).seconds.do(scheduledTask)
schedule.every().day.at("12:21").do(scheduledTask)
while True:
    schedule.run_pending()
    time.sleep(1)