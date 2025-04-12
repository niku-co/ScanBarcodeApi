# استفاده از تصویر پایه پایتون
FROM python:3.10-slim

# نصب وابستگی‌های سیستم عامل و ابزارهای مورد نیاز
RUN apt-get update && apt-get install -y \
    gnupg2 \
    curl \
    unixodbc \
    unixodbc-dev \
    libpq-dev \
    apt-transport-https \
    debconf-utils \
    wget \
    && apt-get clean

# نصب Microsoft ODBC Driver 17
WORKDIR /opt

RUN wget https://packages.microsoft.com/ubuntu/18.04/prod/pool/main/m/msodbcsql17/msodbcsql17_17.10.1.1-1_amd64.deb && \
    ACCEPT_EULA=Y dpkg -i msodbcsql17_17.10.1.1-1_amd64.deb || apt-get -f install -y && \
    dpkg -i msodbcsql17_17.10.1.1-1_amd64.deb && \
    rm msodbcsql17_17.10.1.1-1_amd64.deb

# تنظیم مسیر پروژه
WORKDIR /app

# کپی فایل‌های پروژه
COPY . .

# نصب کتابخانه‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# اجرای Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
