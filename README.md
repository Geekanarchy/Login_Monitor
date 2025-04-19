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

### Clone the Repository

To get started, clone the repository from GitHub:

```bash
git clone https://github.com/Geekanarchy/Login_Monitor.git
cd Login_Monitor
```

### 1. Configure

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

### Build and Run with Docker

To build and run the Docker container, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/Geekanarchy/Login_Monitor.git
cd Login_Monitor
```

2. Build and run the Docker container:

```bash
docker-compose up --build
```

---

## 🐳 Run with Docker

### Build and Run

To build and run the Docker container, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/Geekanarchy/Login_Monitor.git
cd Login_Monitor
```

2. Build and run the Docker container:

```bash
docker-compose up --build
```

The container will use values from `.env` and check the login endpoint at runtime.

### Optimized Dockerfile

The `Dockerfile` has been optimized using a multi-stage build to reduce the final image size and improve security. Key improvements include:

1. **Multi-Stage Build**:
   - Dependencies are installed in a separate builder stage, and only the necessary files are copied to the final image.

2. **Minimized Layers**:
   - Commands are combined to reduce the number of layers in the image.

3. **Non-Root User**:
   - The application runs as a non-root user for improved security.

### Build and Run with Optimized Dockerfile

To build and run the Docker container with the optimized `Dockerfile`, use the following commands:

```bash
docker build -t login-monitor .
docker run --rm -it login-monitor
```

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

4. **Docker Build Failures**
   - **Problem**: The Docker container fails to build or run.
   - **Solution**:
     - Ensure Docker is installed and running on your system.
     - Run `docker-compose up --build` to rebuild the container.
     - Check the Dockerfile and `docker-compose.yml` for syntax errors or misconfigurations.

5. **Log File Issues**
   - **Problem**: The `login_monitor.log` file is not being updated or is missing.
   - **Solution**:
     - Ensure the script has write permissions for the log file.
     - Check the `LOG_FILE` path in the script and ensure it points to a valid location.
     - If running in Docker, ensure the volume mapping for logs is correctly configured in `docker-compose.yml`.

6. **Webex Alert Issues**
   - **Problem**: Webex alerts are not being sent.
   - **Solution**:
     - Verify the `WEBEX_WEBHOOK` URL is correct and active.
     - Check Webex API permissions and ensure the webhook is configured to accept incoming messages.
     - Look for error messages in the logs to identify the issue.

7. **Permission Errors**
   - **Problem**: The script fails due to permission issues.
   - **Solution**:
     - Ensure the script and its dependencies have the necessary permissions to execute.
     - If running in Docker, ensure the container has access to required files and directories.

8. **Throttled Alerts**
   - **Problem**: Alerts are not being sent even though the status has changed.
   - **Solution**:
     - Check the `ALERT_THROTTLE_PERIOD` value in the `.env` file.
     - Ensure sufficient time has passed since the last alert.

If you encounter an issue not listed here, check the logs in `login_monitor.log` for more details or raise an issue in the repository.

---

## 🧾 License

MIT – Open use in commercial or personal projects.
