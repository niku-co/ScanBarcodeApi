import hashlib
from flask import Blueprint, jsonify, request
from persiantools.jdatetime import JalaliDateTime
from db import get_db_connection

routes = Blueprint("routes", __name__)

def hash_password(password: str) -> bytes:
    """هش کردن پسورد با استفاده از MD5"""
    # تبدیل پسورد به بایت و هش کردن آن
    encoded_password = password.encode('utf-16le')  # استفاده از Unicode همانطور که در توضیحات شما بود
    md5_hash = hashlib.md5(encoded_password)
    return md5_hash.digest()

@routes.route("/users", methods=["GET"])
def get_users():
    """Fetch all users from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT FullName, PassWord, RollID FROM UserManager WHERE RollID = 1")
        users = cursor.fetchall()

        result = []
        for row in users:
            user_data = {
                "FullName": row.FullName
            }
            # دریافت پسورد از پارامتر query
            user_password = request.args.get('password')  # فرض کنیم کاربر پسورد را وارد کرده است
            # اگر پسورد وارد شده توسط کاربر موجود باشد
            if user_password:
                # هش کردن پسورد وارد شده
                entered_password_hash = hash_password(user_password)
                # مقایسه هش پسورد وارد شده با پسورد ذخیره‌شده در دیتابیس
                if entered_password_hash == row.PassWord:
                    user_data['پسورد درست است'] = 'Yes'
                else:
                    user_data['پسورد درس نیست'] = 'No'
            result.append(user_data)
        return jsonify(result)  # بازگرداندن اطلاعات کاربران به فرمت JSON

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():  # اطمینان از بسته شدن اتصال
            conn.close()

@routes.route("/shamsi-date", methods=["GET"])
def get_shamsi_date():
    """برگرداندن تاریخ جاری به شمسی"""
    try:
        shamsi_date = JalaliDateTime.now().strftime('%Y/%m/%d %H:%M:%S')
        return jsonify({"ShamsiDate": shamsi_date})
    except Exception as e:
        return jsonify({"error": f"خطا در دریافت تاریخ شمسی: {str(e)}"}), 500
    
@routes.route("/orders", methods=["GET"])
def get_orders():
    """Fetch orders from the database with specified fields and, if available, add Quantity from Good_Store based on GoodIDs."""
    try:
        # دریافت مقدار OrderDate از query string؛ اگر ارسال نشد، مقدار پیش‌فرض "14031121" استفاده می‌شود.
        order_date = request.args.get("OrderDate", "14031121")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # کوئری برای دریافت سفارش‌ها همراه با GoodIDs (در صورتی که ستون GoodIDs وجود داشته باشد)
        query = """
            SELECT OrderID, OrderNumber, OrderDate, OrderTime, DeliveryTime, GoodIDs 
            FROM Orders 
            WHERE OrderDate = ?
        """
        cursor.execute(query, (order_date,))
        orders = cursor.fetchall()

        result = []
        for row in orders:
            order_dict = {
                "OrderID": row.OrderID,
                "OrderNumber": row.OrderNumber,
                "OrderDate": row.OrderDate,
                "OrderTime": row.OrderTime,
                "DeliveryTime": row.DeliveryTime,
            }
            # بررسی وجود فیلد GoodIDs و داشتن مقدار
            if hasattr(row, "GoodIDs") and row.GoodIDs:
                # فرض می‌کنیم مقدار GoodIDs به صورت "{15}" ذخیره شده است؛
                # پاک کردن براکت‌ها و فاصله‌های اضافی
                good_id = row.GoodIDs.strip("{}").strip()
                # بررسی در جدول Good_Store برای یافتن رکورد مربوط به GoodID استخراج شده
                cursor.execute("SELECT Quantity FROM Good_Store WHERE GoodID = ?", (good_id,))
                good_row = cursor.fetchone()
                if good_row:
                    order_dict["Quantity"] = good_row.Quantity
                else:
                    order_dict["Quantity"] = None
            else:
                order_dict["Quantity"] = None

            result.append(order_dict)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@routes.route("/update-delivery", methods=["GET", "POST"])
def update_delivery():
    """Manually call UpdateDelivery stored procedure with a provided OrderID."""
    try:
        if request.method == "GET":
            # دریافت OrderID از query string
            order_id = request.args.get("OrderID")
            print("Received OrderID (GET):", order_id)
        elif request.method == "POST":
            # دریافت OrderID از JSON body
            data = request.get_json()
            print("Received data (POST):", data)
            order_id = data.get("OrderID")

        if not order_id:
            return jsonify({"error": "OrderID is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # بررسی اینکه آیا OrderID معتبر است (یعنی هنوز DeliveryTime خالی است)
        cursor.execute("""
            SELECT OrderID, DeliveryTime 
            FROM Orders 
            WHERE OrderID = ? AND (DeliveryTime IS NULL OR DeliveryTime = '')
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            # اگر رکوردی یافت نشد، به احتمال زیاد قبلاً بروز شده است
            return jsonify({"error": "!قبلا ثبت شده"}), 404

        print("Order found:", order.OrderID, order.DeliveryTime)

        # فراخوانی استورپروسجر UpdateDelivery
        try:
            print("Calling stored procedure UpdateDelivery with OrderID:", order_id)
            cursor.execute("EXEC UpdateDelivery @OrderID=?, @RecordDate=?", (order_id, 0))
            conn.commit()
            print("Stored procedure executed successfully.")
            return jsonify({"OrderID": str(order_id), "Status": "Updated"}), 200
        except Exception as sp_error:
            print("Error in stored procedure:", sp_error)
            return jsonify({"OrderID": str(order_id), "Status": f"Failed: {str(sp_error)}"}), 500

    except Exception as e:
        print("General error:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@routes.route("/barcod", methods=["GET"])
def process_variable_barcode():
    """Process barcode with variable lengths for OrderTime and OrderNumber, fetch matching order, and retrieve Quantity."""
    try:
        barcode = request.args.get("barcod")
        if not barcode:
            return jsonify({"error": "Barcode is required"}), 400

        if len(barcode) < 9:
            return jsonify({"error": "Invalid barcode length"}), 400

        order_date = barcode[:8]
        remaining = barcode[8:]
        
        if not remaining.isdigit():
            return jsonify({"error": "Invalid barcode format: non-digit characters found in time/number part"}), 400

        possibilities = []
        if len(remaining) >= 4:
            possibilities.append((remaining[:4], remaining[4:]))
        if len(remaining) >= 3:
            possibilities.append((remaining[:3], remaining[3:]))

        conn = get_db_connection()
        cursor = conn.cursor()

        order = None
        chosen_order_time = None
        chosen_order_number = None
        good_id = None  # برای ذخیره GoodID

        for order_time, order_number in possibilities:
            query = """
                SELECT OrderID, DeliveryTime, GoodIDs 
                FROM Orders 
                WHERE OrderDate = ? AND OrderTime = ? AND OrderNumber = ?
            """
            cursor.execute(query, (order_date, order_time, order_number))
            order = cursor.fetchone()
            if order:
                chosen_order_time = order_time
                chosen_order_number = order_number
                # استخراج GoodIDs از جدول Orders
                if hasattr(order, "GoodIDs") and order.GoodIDs:
                    good_id = order.GoodIDs.strip("{}").strip()  # حذف کروشه‌ها
                break

        if not order:
            return jsonify({"error": "No matching order found"}), 404

        # مقدار Quantity را از جدول Good_Store بازیابی کن اگر GoodID وجود داشته باشد
        quantity = None
        if good_id:
            cursor.execute("SELECT Quantity FROM Good_Store WHERE GoodID = ?", (good_id,))
            good_row = cursor.fetchone()
            if good_row:
                quantity = good_row.Quantity

        result = {
            "OrderID": str(order.OrderID),
            "DeliveryTime": order.DeliveryTime if order.DeliveryTime else "NULL",
            "OrderDate": order_date,
            "OrderTime": chosen_order_time,
            "OrderNumber": chosen_order_number,
            "Quantity": quantity  # مقدار Quantity اضافه شد
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()
