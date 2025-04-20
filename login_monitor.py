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
- debug_with_curl: Uses curl for debugging login requests.
- extract_csrf_token: Extracts CSRF token from response.
- log_event: Structured JSON logging.
- check_http_status: Check HTTP status code.
- create_alert_message: Create detailed alert messages.
"""

import requests
import smtplib
import os
import time
import logging
import json
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from dotenv import load_dotenv
import subprocess
import urllib3
import traceback

# Load environment variables
load_dotenv()

# Disable SSL verification warnings if verification is disabled
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Support both single URL and multiple URLs
LOGIN_URL = os.getenv("LOGIN_URL")
LOGIN_URLS = os.getenv("LOGIN_URLS", "").split(",")

if LOGIN_URL:
    LOGIN_URLS = [LOGIN_URL]  # If single URL is provided, use it as a list

# Authentication settings
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
FAILED_KEYWORD = os.getenv("FAILED_KEYWORD", "Invalid credentials")

# Email settings
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Webex settings
WEBEX_WEBHOOK = os.getenv("WEBEX_WEBHOOK", "")

# HTTP settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 10))
SUCCESS_STATUS_CODES = list(map(int, os.getenv("SUCCESS_STATUS_CODES", "200,201,202,204").split(",")))

# File paths
LOG_FILE = "logs/login_monitor.log"
STATE_FILE = "last_status.txt"

# Ensure the logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Retry settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

# Alert throttle timers
last_alert_time = None
ALERT_THROTTLE_PERIOD = timedelta(minutes=int(os.getenv("ALERT_THROTTLE_PERIOD", 10)))

# Load log rotation settings from .env
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))  # Default: 5 MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 3))  # Default: 3 backups

# Environment metadata
HOSTNAME = os.getenv("HOSTNAME", "unknown")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Configure logging with RotatingFileHandler
logging.basicConfig(level=logging.INFO, handlers=[
    RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT),
    logging.StreamHandler()
])
logger = logging.getLogger("LoginMonitor")

# Validate environment variables
def validate_env_vars():
    required_vars = ["USERNAME", "PASSWORD", "EMAIL_FROM", "EMAIL_TO", "SMTP_SERVER", "SMTP_USERNAME", "SMTP_PASSWORD"]
    
    # Ensure at least one login URL is defined
    if not LOGIN_URL and not any(url.strip() for url in LOGIN_URLS):
        logger.error("No login URLs defined. Set either LOGIN_URL or LOGIN_URLS environment variable.")
        exit(1)
        
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)

# Structured JSON logging
def log_event(event_type, data):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "hostname": HOSTNAME,
        "environment": ENVIRONMENT,
        "event": event_type,
        **data
    }
    logger.info(json.dumps(log_entry))

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

        log_event("email_sent", {"subject": subject})
    except smtplib.SMTPException as e:
        logger.error(f"Email error: {e}")
        raise

# Make Webex alerts optional
if WEBEX_WEBHOOK:
    def send_webex_alert(body):
        try:
            response = requests.post(WEBEX_WEBHOOK, json={"text": body}, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                log_event("webex_sent", {"status_code": response.status_code})
            else:
                logger.error(f"Webex alert failed with status code {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Webex error: {e}")
else:
    def send_webex_alert(body):
        logger.info("Webex alert skipped as WEBEX_WEBHOOK is not configured.")

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

def debug_with_curl(url, payload, headers):
    try:
        # Construct the curl command
        curl_command = [
            "curl", "-X", "POST", url,
            "-d", f"username={payload['username']}&password={payload['password']}"
        ]

        # Add headers to the curl command
        for key, value in headers.items():
            curl_command.extend(["-H", f"{key}: {value}"])
            
        # Add SSL verification flag
        if not VERIFY_SSL:
            curl_command.append("-k")

        # Execute the curl command and capture the output
        result = subprocess.run(curl_command, capture_output=True, text=True)
        logger.debug(f"Curl command: {' '.join(curl_command)}")
        logger.debug(f"Curl response: {result.stdout}")
        logger.debug(f"Curl error (if any): {result.stderr}")
        
        log_event("curl_debug", {
            "url": url,
            "exit_code": result.returncode,
            "stdout_length": len(result.stdout),
            "stderr_length": len(result.stderr)
        })
    except Exception as e:
        logger.error(f"Curl debugging failed: {e}")

def extract_csrf_token(session, response):
    # Try from cookies first
    csrf_token = session.cookies.get("XSRF-TOKEN")
    
    # If not in cookies, try to extract from HTML content
    if not csrf_token and "text/html" in response.headers.get("Content-Type", ""):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for common CSRF token input fields
            csrf_input = soup.find('input', {'name': ['csrf_token', '_token', 'csrf', 'CSRF']})
            if csrf_input and csrf_input.get('value'):
                csrf_token = csrf_input.get('value')
                logger.info(f"Extracted CSRF token from HTML form: {csrf_token[:5]}...")
        except ImportError:
            logger.warning("BeautifulSoup not installed, skipping HTML CSRF extraction")
    
    if csrf_token:
        log_event("csrf_token_found", {"method": "cookies" if session.cookies.get("XSRF-TOKEN") else "html"})
    else:
        logger.debug("No CSRF token found")
    
    return csrf_token

def check_http_status(url):
    try:
        response = requests.head(url, timeout=REQUEST_TIMEOUT, verify=VERIFY_SSL)
        log_event("http_status_check", {"url": url, "status_code": response.status_code})
        return response.status_code
    except Exception as e:
        logger.error(f"HTTP status check failed: {e}")
        log_event("http_status_failed", {"url": url, "error": str(e)})
        return None

def check_login(url):
    start_time = time.time()
    session = requests.Session()
    session.verify = VERIFY_SSL  # Use configurable SSL verification
    
    try:
        # Step 1: Fetch the CSRF token if available
        initial_response = session.get(url, timeout=REQUEST_TIMEOUT)
        csrf_token = extract_csrf_token(session, initial_response)

        # Step 2: Prepare the login payload and headers
        payload = {
            "username": USERNAME,
            "password": PASSWORD,
        }
        headers = {}

        # Include CSRF token in headers if available
        if csrf_token:
            headers["X-XSRF-TOKEN"] = csrf_token

        # Step 3: Determine content type (JSON or form data)
        if "application/json" in initial_response.headers.get("Content-Type", ""):
            headers["Content-Type"] = "application/json"
            payload = {
                "username": USERNAME,
                "password": PASSWORD,
            }
            # Include CSRF token in JSON payload if required
            if csrf_token:
                payload["csrf_token"] = csrf_token
                
            response = session.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        else:
            response = session.post(url, data=payload, headers=headers, timeout=REQUEST_TIMEOUT)

        # Calculate response time
        end_time = time.time()
        response_time = end_time - start_time
        
        # Step 4: Check the response for success or failure
        if FAILED_KEYWORD in response.text or response.status_code not in SUCCESS_STATUS_CODES:
            logger.debug(f"Response content: {response.text[:500]}...")  # Log first 500 chars only
            debug_with_curl(url, payload, headers)  # Add curl debugging here
            
            log_event("login_check_failed", {
                "url": url,
                "status_code": response.status_code,
                "response_time": round(response_time, 2),
                "failed_keyword_found": FAILED_KEYWORD in response.text
            })
            
            return "login_failed", f"Status {response.status_code}", response_time
            
        log_event("login_check_success", {
            "url": url,
            "status_code": response.status_code,
            "response_time": round(response_time, 2)
        })
        
        return "success", "Login OK", response_time
        
    except requests.exceptions.Timeout:
        end_time = time.time()
        response_time = end_time - start_time
        logger.error("Request timed out")
        log_event("login_check_timeout", {"url": url, "timeout": REQUEST_TIMEOUT})
        return "unreachable", "Request timed out", response_time
        
    except requests.exceptions.ConnectionError:
        end_time = time.time()
        response_time = end_time - start_time
        logger.error("Connection error")
        log_event("login_check_connection_error", {"url": url})
        return "unreachable", "Connection error", response_time
        
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        response_time = end_time - start_time
        logger.error(f"Request exception: {e}")
        log_event("login_check_request_exception", {"url": url, "error": str(e)})
        return "unreachable", str(e), response_time

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
            
def create_alert_message(status, url, detail, response_time=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add response time information if available
    performance_info = ""
    if response_time is not None:
        performance_info = f"Response Time: {response_time:.2f} seconds\n"
    
    return f"""
🚨 Login Monitor Alert
Status: {status}
URL: {url}
Environment: {ENVIRONMENT}
Host: {HOSTNAME}
Time: {timestamp}
{performance_info}Details: {detail}

This alert was generated by the automated login monitoring system.
"""

if __name__ == "__main__":
    try:
        # Validate environment variables first
        validate_env_vars()
        
        log_event("monitor_started", {
            "version": "1.1.0",
            "urls_count": len(LOGIN_URLS)
        })
        
        for url in LOGIN_URLS:
            if not url.strip():  # Skip empty URLs
                continue
                
            url = url.strip()  # Remove whitespace
            log_event("checking_url", {"url": url})
            
            # First check if site is accessible at all
            http_status = check_http_status(url)
            if http_status is None or http_status >= 500:
                logger.warning(f"Site at {url} appears to be down with status {http_status}")
                
            current_status = None
            detail = ""
            response_time = None
            
            for attempt in range(MAX_RETRIES):
                current_status, detail, response_time = check_login(url)
                if current_status == "success":
                    break
                delay = exponential_backoff(attempt)
                logger.warning(f"Attempt {attempt + 1} for {url} failed. Retrying in {delay} seconds...")
                time.sleep(delay)

            previous_status = read_last_status()
            write_log(current_status, detail)

            if current_status != previous_status and should_send_alert():
                alert_msg = create_alert_message(current_status, url, detail, response_time)
                
                if current_status == "login_failed":
                    retry_alert(send_email, "Login Failed Alert", alert_msg)
                    retry_alert(send_webex_alert, alert_msg)

                elif current_status == "unreachable":
                    retry_alert(send_email, "Site Unreachable Alert", alert_msg)
                    retry_alert(send_webex_alert, alert_msg)

                elif current_status == "success":
                    if os.getenv("SEND_RECOVERY_ALERTS", "false").lower() == "true":
                        retry_alert(send_email, "Login Monitor Recovery", alert_msg)
                        retry_alert(send_webex_alert, alert_msg)
                    logger.info("Login restored.")
            else:
                logger.info(f"No status change or alert throttled for {url}.")

            write_last_status(current_status)
            
    except Exception as e:
        error_details = traceback.format_exc()
        logger.critical(f"Unhandled exception in main process: {e}\n{error_details}")
        
        # Send alert about critical failure
        critical_alert = f"""
🚨 CRITICAL: Login Monitor Failed
Error: {e}
Environment: {ENVIRONMENT}
Host: {HOSTNAME}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Stack Trace:
{error_details}

The login monitor has encountered a critical error and may not be functioning properly.
"""
        retry_alert(send_email, "CRITICAL: Login Monitor Failed", critical_alert)
        retry_alert(send_webex_alert, critical_alert)
    