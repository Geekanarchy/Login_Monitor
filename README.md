# 🔐 Website Login Monitor

A Python-based login monitoring script that checks the availability of a website's login endpoint. It supports:

- 🚫 **Login failure detection**
- 🌐 **Site unreachable alerts**
- 🔁 **Retry logic before alerting**
- 🔐 **Environment variable configuration**
- 📧 Email & 💬 Webex Teams alerting
- 📝 Log and state tracking

---

## 📦 Features

- Detects **login rejections** (bad credentials, changes in form behavior)
- Detects **site unavailability** (DNS failure, timeouts, refused connections)
- Uses `.env` file to keep credentials/configs outside of source
- Alerts sent via:
  - ✅ Email (SMTP)
  - 💬 Webex Teams (optional)
- Logs all status changes to `login_monitor.log`
- Remembers last status in `last_status.txt`
- Skips duplicate alerts unless status changes
- Built-in **retry logic** before declaring failure

---

## 🚀 Quick Start

### Clone the Repository

To get started, clone the repository from GitHub:

```bash
git clone https://github.com/Geekanarchy/Login_Monitor.git
cd Login_Monitor
```

### 1. Configure

```bash
cp env.example .env
nano .env  # Edit values accordingly
```

### 2. Run with Python

```bash
pip install -r requirements.txt
python login_monitor.py
```

> Or schedule it with `cron` or Windows Task Scheduler.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Tests

```bash
pytest
```

---

### Removed Docker References

Docker references have been removed from this project. Please use the Python-based setup instructions for running the application.

---

## ⚙️ .env Configuration

Example values in `.env.example`:

```env
LOGIN_URLS=https://example.com/login,https://anotherexample.com/login
USERNAME=testuser
PASSWORD=supersecret
FAILED_KEYWORD=Invalid credentials

EMAIL_FROM=monitor@example.com
EMAIL_TO=admin@example.com
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=smtpuser
SMTP_PASSWORD=smtppass

WEBEX_WEBHOOK=https://webexapis.com/v1/webhooks/incoming/yourwebhook

MAX_RETRIES=3
RETRY_DELAY=5
ALERT_THROTTLE_PERIOD=15
```

### Single or Multiple URLs

The script supports monitoring either a single URL or multiple URLs. Configure this in the `.env` file:

- **Single URL**: Use the `LOGIN_URL` variable.
- **Multiple URLs**: Use the `LOGIN_URLS` variable (comma-separated).

If both are set, `LOGIN_URL` will take precedence.

Example for a single URL:

```env
LOGIN_URL=https://example.com/login
```

Example for multiple URLs:

```env
LOGIN_URLS=https://example.com/login,https://anotherexample.com/login
```

### Webex Alerts (Optional)

Webex alerts are now optional. To enable Webex alerts, set the `WEBEX_WEBHOOK` environment variable in your `.env` file. If left empty, Webex alerts will be disabled.

Example:

```env
WEBEX_WEBHOOK=https://webexapis.com/v1/webhooks/incoming/yourwebhook
```

To disable Webex alerts, leave the `WEBEX_WEBHOOK` field empty:

```env
WEBEX_WEBHOOK=
```

---

## 📝 Files Used

| File                | Purpose                          |
|---------------------|----------------------------------|
| `login_monitor.py`  | Main monitoring script           |
| `.env`              | Environment configuration        |
| `login_monitor.log` | Log of login attempts/results    |
| `last_status.txt`   | Tracks previous known state      |

---

### Workspace Structure

The project workspace is structured as follows:

```
Login_Monitor/
├── env.example              # Example .env file for configuration
├── .gitignore               # Git ignore rules
├── LICENSE                  # License file
├── login_monitor.py         # Main monitoring script
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── test_login_monitor.py    # Unit tests for the script
├── logs/                    # Directory for log files
│   └── login_monitor.log    # Log file for monitoring output
├── state/                   # Directory for state files
│   └── last_status.txt      # Tracks the last known status
```

### Required Files and Folders

Ensure the following files and folders exist before running the project:

1. **`logs/` Directory**:
   - Contains `login_monitor.log` for logging output.
   - Ensure this directory is writable by the application.

2. **`state/` Directory**:
   - Contains `last_status.txt` to track the last known status.
   - Ensure this directory is writable by the application.

If these directories or files are missing, create them manually:

```bash
mkdir logs state
New-Item -ItemType File -Path logs\login_monitor.log
New-Item -ItemType File -Path state\last_status.txt
```

### Permissions

Ensure the `logs` and `state` directories have the correct permissions:

```bash
chmod -R 777 logs state
```

---

## 📬 Alert Scenarios

| Status          | Description                     | Triggers Alert |
|-----------------|----------------------------------|----------------|
| success         | Login succeeded                  | Only if recovery |
| login_failed    | Bad credentials / wrong form     | ✅             |
| unreachable     | Site unreachable (DNS/refused)   | ✅             |
| status unchanged| Repeated failure/success         | ❌             |

---

### Alert Throttle Timers

To prevent frequent alerts within a short period, the script includes an alert throttle mechanism. By default, alerts are throttled to one per 10 minutes. You can configure this period using the `ALERT_THROTTLE_PERIOD` environment variable in the `.env` file.

Example:

```env
ALERT_THROTTLE_PERIOD=15  # Throttle alerts to one every 15 minutes
```

---

## 💡 Enhancements Possible

- Prometheus metrics exporter
- JSON-formatted webhook alerts

---

## 🔒 Security Tip

Never commit `.env` or credentials to version control. Use `.gitignore` to protect secrets.

---

### Troubleshooting

#### Common Issues

1. **Network Errors**
   - **Problem**: The script fails to connect to the login URL or Webex webhook.
   - **Solution**:
     - Verify that the URLs in the `LOGIN_URLS` and `WEBEX_WEBHOOK` environment variables are correct.
     - Check your internet connection and ensure the target server is reachable.
     - Use tools like `ping` or `curl` to test connectivity to the URLs.

2. **SMTP Configuration Problems**
   - **Problem**: Email alerts are not being sent.
   - **Solution**:
     - Verify the SMTP server, port, username, and password in the `.env` file.
     - Ensure the `EMAIL_FROM` and `EMAIL_TO` addresses are valid.
     - Check if the SMTP server requires additional configuration, such as enabling "less secure apps" or generating an app-specific password.
     - Test the SMTP connection using a tool like `telnet` or an email client.

3. **Environment Variable Issues**
   - **Problem**: Missing or incorrect environment variables cause the script to fail.
   - **Solution**:
     - Ensure all required variables are set in the `.env` file.
     - Use the `env.example` file as a reference.
     - Double-check for typos or missing values.

4. **Log File Issues**
   - **Problem**: The `login_monitor.log` file is not being updated or is missing.
   - **Solution**:
     - Ensure the script has write permissions for the log file.
     - Check the `LOG_FILE` path in the script and ensure it points to a valid location.

5. **Webex Alert Issues**
   - **Problem**: Webex alerts are not being sent.
   - **Solution**:
     - Verify the `WEBEX_WEBHOOK` URL is correct and active.
     - Check Webex API permissions and ensure the webhook is configured to accept incoming messages.
     - Look for error messages in the logs to identify the issue.

6. **Permission Errors**
   - **Problem**: The script fails due to permission issues.
   - **Solution**:
     - Ensure the script and its dependencies have the necessary permissions to execute.

7. **Throttled Alerts**
   - **Problem**: Alerts are not being sent even though the status has changed.
   - **Solution**:
     - Check the `ALERT_THROTTLE_PERIOD` value in the `.env` file.
     - Ensure sufficient time has passed since the last alert.

If you encounter an issue not listed here, check the logs in `login_monitor.log` for more details or raise an issue in the repository.

---

## 🧾 License

MIT – Open use in commercial or personal projects.
