# 🔐 Website Login Monitor

A Python-based login monitoring script that checks the availability of a website's login endpoint. It supports:

- 🚫 **Login failure detection**
- 🌐 **Site unreachable alerts**
- 🔁 **Retry logic before alerting**
- 🔐 **Environment variable configuration**
- 🐳 **Docker support**
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
- Deployable via **Docker** or traditional cron

---

## 🚀 Quick Start

### 1. Clone the Repo & Configure

```bash
cp .env.example .env
nano .env  # Edit values accordingly
```

### 2. Run with Python (Non-Docker)

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

## 🐳 Run with Docker

### Build and Run

```bash
docker-compose up --build
```

The container will use values from `.env` and check the login endpoint at runtime.

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

### Multiple URLs

The `LOGIN_URLS` environment variable now supports multiple URLs separated by commas. The script will iterate through each URL and perform login checks individually.

Example:

```env
LOGIN_URLS=https://example.com/login,https://anotherexample.com/login
```

---

## 📝 Files Used

| File                | Purpose                          |
|---------------------|----------------------------------|
| `login_monitor.py`  | Main monitoring script           |
| `.env`              | Environment configuration        |
| `login_monitor.log` | Log of login attempts/results    |
| `last_status.txt`   | Tracks previous known state      |
| `Dockerfile`        | Build container                  |
| `docker-compose.yml`| Run service with `.env` support  |

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

- Alert throttle timers
- Prometheus metrics exporter
- Log rotation
- Multi-site login checks
- JSON-formatted webhook alerts

---

## 🔒 Security Tip

Never commit `.env` or credentials to version control. Use `.gitignore` to protect secrets.

---

### Troubleshooting

#### Common Issues

1. **Missing Environment Variables**
   - Ensure all required variables are set in the `.env` file.
   - Use the `env.example` file as a reference.

2. **SMTP Errors**
   - Verify SMTP credentials and server details in the `.env` file.
   - Check if the SMTP server allows connections from your IP.

3. **Webex Alert Issues**
   - Ensure the `WEBEX_WEBHOOK` URL is correct and active.
   - Check Webex API permissions.

4. **Docker Build Failures**
   - Ensure Docker is installed and running.
   - Run `docker-compose up --build` to rebuild the container.

5. **Log File Issues**
   - Ensure the `login_monitor.log` file is writable.
   - Check volume mappings in `docker-compose.yml`.

---

## 🧾 License

MIT – Open use in commercial or personal projects.
