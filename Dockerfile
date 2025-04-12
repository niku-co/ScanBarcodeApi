# استفاده از تصویر پایه پایتون
FROM python:3.10-slim

# نصب وابستگی‌های سیستم عامل و ابزارهای مورد نیاز
RUN apt-get update && apt-get install -y \
    libpq-dev \
    odbcinst \
    unixodbc \
    unixodbc-dev \
    curl \
    wget \
    apt-transport-https \
    debconf-utils \
    dialog \
    debconf-utils && \
    apt --fix-broken install && \
    apt-get clean

# تنظیم ورودی غیر تعاملی برای debconf
RUN echo 'debconf debconf/priority select critical' | debconf-set-selections

# تنظیم دایرکتوری کاری به /opt
WORKDIR /opt

# دانلود و نصب Microsoft ODBC Driver 17
RUN wget https://packages.microsoft.com/ubuntu/18.04/prod/pool/main/m/msodbcsql17/msodbcsql17_17.10.1.1-1_amd64.deb
RUN ACCEPT_EULA=Y dpkg --force-all -i msodbcsql17_17.10.1.1-1_amd64.deb
RUN apt --fix-broken install  -y
RUN ACCEPT_EULA=Y dpkg --force-all -i msodbcsql17_17.10.1.1-1_amd64.deb
RUN rm msodbcsql17_17.10.1.1-1_amd64.deb
RUN ln -s /opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.so.1.1 /opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.so 
RUN echo "export LD_LIBRARY_PATH=/opt/microsoft/msodbcsql17/lib64:\$LD_LIBRARY_PATH" >> /etc/environment

# تنظیم دایرکتوری کاری به /app برای پروژه
WORKDIR /app

# کپی کردن فایل‌های پروژه به داخل تصویر
COPY . .

# نصب وابستگی‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# اجرای برنامه
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
