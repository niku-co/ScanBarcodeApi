import json
import pyodbc

# بارگذاری تنظیمات از فایل appsettings.json
def load_settings():
    with open('appsettings.json', 'r', encoding='utf-8') as file:
        settings = json.load(file)
        return settings

# تنظیمات را از فایل بارگذاری می‌کنیم
settings = load_settings()

# استخراج connection string از تنظیمات
connection_string = settings['ConnectionStrings']['DefaultConnection']

# تبدیل connection string به فرمت قابل استفاده در pyodbc
def get_db_connection():
    try:
        conn = pyodbc.connect(connection_string)
        print("Connection successful!")
        return conn
    except pyodbc.Error as e:
        print(f"Database connection failed: {str(e)}")
        raise Exception(f"Database connection failed: {str(e)}")

# برای آزمایش اتصال
conn = get_db_connection()
