"""
This script monitors the login functionality of a website. It checks the login endpoint, sends alerts via email and Webex Teams, and logs the status.

Functions:
- validate_env_vars: Validates required environment variables.
- exponential_backoff: Implements retry logic with exponential backoff.
- send_email: Sends email alerts.
- send_webex_alert: Sends Webex Teams alerts.
- write_log: Logs status changes.
- read_last_status: Reads the last known status from a file.
- write_last_status: Writes the current status to a file.
- check_login: Checks the login endpoint for success or failure.
"""

import requests
import smtplib
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Load config from .env
LOGIN_URLS = os.getenv("LOGIN_URLS", "").split(",")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
FAILED_KEYWORD = os.getenv("FAILED_KEYWORD", "Invalid credentials")

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
WEBEX_WEBHOOK = os.getenv("WEBEX_WEBHOOK", "")

LOG_FILE = "/app/logs/login_monitor.log"

# Ensure the logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

STATE_FILE = "last_status.txt"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

# Alert throttle timers
last_alert_time = None
ALERT_THROTTLE_PERIOD = timedelta(minutes=int(os.getenv("ALERT_THROTTLE_PERIOD", 10)))

# Load log rotation settings from .env
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))  # Default: 5 MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 3))  # Default: 3 backups

# Configure logging with RotatingFileHandler
logging.basicConfig(level=logging.INFO, handlers=[
    RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT),
    logging.StreamHandler()
])
logger = logging.getLogger("LoginMonitor")

# Validate environment variables
def validate_env_vars():
    required_vars = ["LOGIN_URLS", "USERNAME", "PASSWORD", "EMAIL_FROM", "EMAIL_TO", "SMTP_SERVER", "SMTP_USERNAME", "SMTP_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)

validate_env_vars()

# Exponential backoff retry logic
def exponential_backoff(attempt):
    return min(2 ** attempt, 60)  # Cap delay at 60 seconds

def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email alert sent.")
    except smtplib.SMTPException as e:
        logger.error(f"Email error: {e}")
        raise

def send_webex_alert(body):
    if not WEBEX_WEBHOOK:
        return
    try:
        response = requests.post(WEBEX_WEBHOOK, json={"text": body})
        if response.status_code == 200:
            logger.info("Webex alert sent.")
        else:
            logger.error(f"Webex alert failed with status code {response.status_code}: {response.text}")
            raise Exception(f"Webex alert failed with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Webex error: {e}")
        raise

def write_log(status, detail=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {status} - {detail}\n")

def read_last_status():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return "success"

def write_last_status(status):
    with open(STATE_FILE, "w") as f:
        f.write(status)

def check_login(url):
    session = requests.Session()
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
    }
    try:
        response = session.post(url, data=payload, timeout=10)
        if FAILED_KEYWORD in response.text or response.status_code != 200:
            return "login_failed", f"Status {response.status_code}"
        return "success", "Login OK"
    except requests.exceptions.Timeout:
        return "unreachable", "Request timed out"
    except requests.exceptions.ConnectionError:
        return "unreachable", "Connection error"
    except requests.exceptions.RequestException as e:
        return "unreachable", str(e)

def should_send_alert():
    global last_alert_time
    now = datetime.now()
    if last_alert_time is None or now - last_alert_time > ALERT_THROTTLE_PERIOD:
        last_alert_time = now
        return True
    return False

def retry_alert(func, *args, max_retries=3):
    for attempt in range(max_retries):
        try:
            func(*args)
            return
        except Exception as e:
            logger.error(f"Alert attempt {attempt + 1} failed: {e}")
            time.sleep(exponential_backoff(attempt))

if __name__ == "__main__":
    for url in LOGIN_URLS:
        current_status = None
        detail = ""
        for attempt in range(MAX_RETRIES):
            current_status, detail = check_login(url)
            if current_status == "success":
                break
            delay = exponential_backoff(attempt)
            logger.warning(f"Attempt {attempt + 1} for {url} failed. Retrying in {delay} seconds...")
            time.sleep(delay)

        previous_status = read_last_status()
        write_log(current_status, detail)

        if current_status != previous_status and should_send_alert():
            if current_status == "login_failed":
                msg = f"🚨 Login to {url} failed: credentials rejected.\nDetails: {detail}"
                retry_alert(send_email, "Login Failed Alert", msg)
                retry_alert(send_webex_alert, msg)

            elif current_status == "unreachable":
                msg = f"🚨 Site unreachable during login check at {url}.\nDetails: {detail}"
                retry_alert(send_email, "Site Unreachable Alert", msg)
                retry_alert(send_webex_alert, msg)

            elif current_status == "success":
                msg = f"✅ Login check successful again at {url}."
                if os.getenv("SEND_RECOVERY_ALERTS", "false").lower() == "true":
                    retry_alert(send_email, "Login Monitor Recovery", msg)
                    retry_alert(send_webex_alert, msg)
                logger.info("Login restored.")
        else:
            logger.info(f"No status change or alert throttled for {url}.")

        write_last_status(current_status)
