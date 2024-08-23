import os
import subprocess
from automation import run_daily_automation
import schedule
import time

def job():
    daily_post, audio_file = run_daily_automation()
    print(f"Daily compilation completed. Audio file saved as {audio_file}")

# Schedule the job to run daily at midnight
schedule.every().day.at("00:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)