FROM python:3.11-slim
WORKDIR /app
COPY . /app

# Add a non-root user for improved security
RUN useradd -m appuser
USER appuser

RUN pip install -r requirements.txt
CMD ["python", "login_monitor.py"]
