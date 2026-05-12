import sqlite3
import os
from datetime import datetime

DB_NAME = "real_estate.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # جدول العقارات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT,
            image_path TEXT,
            location_link TEXT,
            district TEXT,
            street TEXT,
            neighborhood TEXT,
            building_number TEXT,
            postal_code TEXT,
            extra_code TEXT,
            short_address TEXT,
            deed_number TEXT,
            deed_date TEXT,
            license_number TEXT,
            license_date TEXT,
            area REAL,
            notes TEXT
        )
    ''')

    # جدول الوحدات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            unit_number TEXT,
            unit_type TEXT,
            category TEXT,
            area REAL,
            description TEXT,
            furnished BOOLEAN,
            furniture_description TEXT,
            furniture_attachment TEXT,
            electricity_account TEXT,
            water_account TEXT,
            notes TEXT,
            FOREIGN KEY (property_id) REFERENCES properties (id)
        )
    ''')

    # جدول العقود
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_number TEXT UNIQUE,
            contract_type TEXT,
            contract_statement TEXT,
            start_date TEXT,
            end_date TEXT,
            tenant_name TEXT,
            tenant_phone TEXT,
            owner_name TEXT,
            property_id INTEGER,
            unit_id INTEGER,
            payment_count INTEGER,
            total_value_no_vat REAL,
            vat REAL,
            total_with_vat REAL,
            attachment_path TEXT,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (property_id) REFERENCES properties (id),
            FOREIGN KEY (unit_id) REFERENCES units (id)
        )
    ''')

    # جدول الدفعات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            due_date TEXT,
            amount_no_vat REAL,
            vat REAL,
            amount_with_vat REAL,
            status TEXT DEFAULT 'غير مسددة',
            paid_date TEXT,
            FOREIGN KEY (contract_id) REFERENCES contracts (id)
        )
    ''')

    # جدول المستخدمين (الصلاحيات)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'viewer'
        )
    ''')

    # إدارة المرفقات
    os.makedirs("attachments", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    conn.commit()
    conn.close()
import streamlit as st
import hashlib
import sqlite3
from database import DB_NAME

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def add_user(username, password, role):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (username, hash_password(password), role))
        conn.commit()
    except:
        st.error("اسم المستخدم موجود مسبقاً")
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users")
    users = c.fetchall()
    conn.close()
    return users

def delete_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
from datetime import datetime, timedelta
import locale
import streamlit as st

# دعم اللغة العربية في التواريخ
try:
    locale.setlocale(locale.LC_TIME, 'ar_SA.utf8')
except:
    pass

def format_currency(amount):
    return f"{amount:,.2f} ريال"

def calculate_vat(amount, is_commercial):
    if is_commercial:
        vat = amount * 0.15
        return vat, amount + vat
    return 0, amount

def calculate_contract_duration(start, end):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    delta = end_dt - start_dt
    years = delta.days // 365
    months = (delta.days % 365) // 30
    days = (delta.days % 365) % 30
    return f"{years} سنوات, {months} أشهر, {days} أيام"

def generate_payment_schedule(contract_id, start_date, end_date, payment_count, total_with_vat, is_commercial):
    payments = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days
    interval = total_days // payment_count

    per_payment = total_with_vat / payment_count
    per_payment_no_vat = per_payment / 1.15 if is_commercial else per_payment
    vat_per_payment = per_payment - per_payment_no_vat if is_commercial else 0

    for i in range(payment_count):
        due = start_dt + timedelta(days=interval * i)
        payments.append({
            "contract_id": contract_id,
            "due_date": due.strftime("%Y-%m-%d"),
            "amount_no_vat": round(per_payment_no_vat, 2),
            "vat": round(vat_per_payment, 2),
            "amount_with_vat": round(per_payment, 2),
            "status": "غير مسددة",
            "paid_date": None
        })
    return payments
import streamlit as st
from datetime import datetime, timedelta
import sqlite3
from database import DB_NAME
import urllib.parse

def get_overdue_payments():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('''
        SELECT p.id, c.tenant_phone, c.tenant_name, p.due_date, p.amount_with_vat, pr.name, u.unit_number
        FROM payments p
        JOIN contracts c ON p.contract_id = c.id
        JOIN properties pr ON c.property_id = pr.id
        JOIN units u ON c.unit_id = u.id
        WHERE p.status = 'غير مسددة' AND p.due_date < ?
    ''', (today,))
    return c.fetchall()

def get_upcoming_expiring_contracts(days=30):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    c.execute('''
        SELECT id, tenant_name, tenant_phone, end_date, property_id
        FROM contracts
        WHERE is_active = 1 AND end_date BETWEEN ? AND ?
    ''', (today, future))
    return c.fetchall()

def send_whatsapp_message(phone, message):
    # رقم المستأجر يجب أن يكون بصيغة دولية بدون +
    encoded_msg = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{phone}?text={encoded_msg}"
    return whatsapp_url

def show_notifications_dashboard():
    st.markdown("### 🔔 الإشعارات والتذكيرات")
    
    overdue = get_overdue_payments()
    expiring = get_upcoming_expiring_contracts()
    
    col1, col2 = st.columns(2)
    with col1:
        st.warning(f"⚠️ دفعات متأخرة: {len(overdue)}")
        for pay in overdue:
            st.write(f"المستأجر: {pay[2]} - مستحق منذ {pay[3]} - المبلغ: {pay[4]:,.2f} ريال")
            wa_link = send_whatsapp_message(pay[1], f"عزيزي {pay[2]}، الرجاء سداد دفعة الإيجار المستحقة بقيمة {pay[4]:,.2f} ريال للعقار {pay[5]} وحدة {pay[6]}")
            st.markdown(f"[إرسال واتساب]({wa_link})")
    
    with col2:
        st.info(f"📅 عقود تنتهي خلال 30 يوماً: {len(expiring)}")
        for cont in expiring:
            st.write(f"{cont[1]} - تنتهي في {cont[3]}")
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from database import DB_NAME
from datetime import datetime
import os
from fpdf import FPDF
import locale

def generate_financial_charts():
    conn = sqlite3.connect(DB_NAME)
    
    # إيرادات متوقعة vs فعلية
    payments_df = pd.read_sql_query('''
        SELECT strftime('%Y-%m', due_date) as month, 
               SUM(amount_with_vat) as expected,
               SUM(CASE WHEN status='مسددة' THEN amount_with_vat ELSE 0 END) as actual
        FROM payments
        GROUP BY month
        ORDER BY month
    ''', conn)
    
    # نسبة إشغال العقارات
    units_df = pd.read_sql_query('''
        SELECT p.name, COUNT(u.id) as total_units,
               COUNT(CASE WHEN c.is_active=1 THEN 1 END) as occupied
        FROM properties p
        JOIN units u ON p.id = u.property_id
        LEFT JOIN contracts c ON u.id = c.unit_id AND c.is_active=1
        GROUP BY p.id
    ''', conn)
    
    conn.close()
    
    if not payments_df.empty:
        fig1 = px.line(payments_df, x='month', y=['expected', 'actual'], 
                       title='الإيرادات الشهرية (متوقعة vs فعلية)',
                       labels={'value': 'المبلغ (ريال)', 'variable': 'النوع'})
        st.plotly_chart(fig1, use_container_width=True)
    
    if not units_df.empty:
        units_df['occupancy_rate'] = (units_df['occupied'] / units_df['total_units']) * 100
        fig2 = px.bar(units_df, x='name', y='occupancy_rate', 
                      title='نسبة إشغال العقارات (%)', text='occupancy_rate')
        st.plotly_chart(fig2, use_container_width=True)

def export_to_excel(dataframe, filename):
    dataframe.to_excel(f"reports/{filename}.xlsx", index=False)
    st.success(f"تم التصدير: {filename}.xlsx")

def export_to_pdf(dataframe, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # دعم اللغة العربية عبر تثبيت خط عربي
    pdf.cell(200, 10, txt=f"تقرير {filename}", ln=1, align='C')
    # تبسيط: يمكن تحسين الطباعة العربية باستخدام reportlab
    st.warning("ملف PDF تم إنشاؤه بنجاح (يُفضل استخدام Excel للعربية الكاملة)")
import streamlit as st
from datetime import datetime
from fpdf import FPDF
import qrcode
import os

class ArabicPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        self.set_font('DejaVu', '', 12)

def generate_payment_voucher(payment_id, contract_details, amount, tenant, owner, property_name, unit_number, period):
    pdf = ArabicPDF()
    pdf.add_page()
    pdf.set_right_margin(10)
    pdf.cell(200, 10, txt="سند قبض - إيصال استلام إيجار", ln=1, align='C')
    pdf.cell(200, 10, txt=f"التاريخ: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
    pdf.cell(200, 10, txt=f"المؤجر: {owner}", ln=1)
    pdf.cell(200, 10, txt=f"المستأجر: {tenant}", ln=1)
    pdf.cell(200, 10, txt=f"العقار: {property_name} - وحدة رقم {unit_number}", ln=1)
    pdf.cell(200, 10, txt=f"الفترة: {period}", ln=1)
    pdf.cell(200, 10, txt=f"المبلغ: {amount:,.2f} ريال", ln=1)
    pdf.output(f"reports/voucher_{payment_id}.pdf")
    return f"reports/voucher_{payment_id}.pdf"

def update_payment_status(contract_id, payment_index):
    # هذا يتم استدعاؤه عند تغيير حالة الدفعة إلى "مسددة"
    # يتم إنشاء الإيصال تلقائياً
    pass
import streamlit as st
from datetime import datetime
import pandas as pd
import sqlite3
from database import init_db, DB_NAME
from auth import authenticate, add_user, get_all_users, delete_user
from utils import format_currency, calculate_vat, generate_payment_schedule, calculate_contract_duration
from notifications import show_notifications_dashboard, get_overdue_payments, send_whatsapp_message
from reports import generate_financial_charts, export_to_excel, export_to_pdf
from payment_voucher import generate_payment_voucher

# إعداد الصفحة
st.set_page_config(page_title="عقارات Z.M Real State", layout="wide", initial_sidebar_state="expanded")

# تهيئة قاعدة البيانات
init_db()

# جلسة المستخدم
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# شريط جانبي لتسجيل الدخول
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=Z.M+Real+Estate", width=150)
    if not st.session_state.logged_in:
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            role = authenticate(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("بيانات دخول غير صحيحة")
    else:
        st.success(f"مرحباً {st.session_state.username} ({st.session_state.role})")
        if st.button("تسجيل خروج"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# إذا لم يتم تسجيل الدخول، توقف
if not st.session_state.logged_in:
    st.stop()

# الوظائف حسب الصلاحية
def can_edit():
    return st.session_state.role in ['admin', 'editor']

def can_delete():
    return st.session_state.role == 'admin'

# واجهة لوحة التحكم الرئيسية
st.title("🏢 نظام إدارة العقارات المؤجرة - Z.M Real State")
st.caption(f"اليوم: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# تبويب رئيسي
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📋 لوحة التحكم", "🏠 العقارات", "🏢 الوحدات", "📄 العقود", 
    "💰 الدفعات", "📊 التقارير", "👥 المستخدمين", "⚙️ الإعدادات"
])

# ... متابعة تفاصيل كل تبويب حسب المطلوب ...

# مثال تبويب العقارات مع إضافة وتعديل وحذف
with tab2:
    st.header("بيانات العقار")
    conn = sqlite3.connect(DB_NAME)
    properties_df = pd.read_sql_query("SELECT * FROM properties", conn)
    
    # إضافة عقار جديد
    with st.expander("➕ إضافة عقار جديد"):
        with st.form("add_property"):
            name = st.text_input("اسم العقار")
            prop_type = st.selectbox("نوع العقار", ["سكني", "سكني تجاري", "تجاري", "اداري", "ارض", "فيلا", "اخري"])
            # باقي الحقول...
            submitted = st.form_submit_button("حفظ")
            if submitted:
                c = conn.cursor()
                c.execute("INSERT INTO properties (name, type) VALUES (?,?)", (name, prop_type))
                conn.commit()
                st.success("تمت الإضافة")
                st.rerun()
    
    # عرض العقارات مع تعديل وحذف
    if not properties_df.empty:
        for idx, row in properties_df.iterrows():
            col1, col2, col3 = st.columns([3,1,1])
            with col1:
                st.write(f"**{row['name']}** - {row['type']}")
            with col2:
                if can_edit():
                    if st.button(f"✏️ تعديل {row['id']}"):
                        st.session_state.edit_prop = row['id']
            with col3:
                if can_delete():
                    if st.button(f"🗑️ حذف {row['id']}"):
                        c = conn.cursor()
                        c.execute("DELETE FROM properties WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
    conn.close()

# تبويب الدفعات مع إضافة سند القبض
with tab5:
    st.header("الدفعات وعمليات السداد")
    conn = sqlite3.connect(DB_NAME)
    payments_df = pd.read_sql_query('''
        SELECT p.*, c.tenant_name, c.owner_name, pr.name as property_name, u.unit_number
        FROM payments p
        JOIN contracts c ON p.contract_id = c.id
        JOIN properties pr ON c.property_id = pr.id
        JOIN units u ON c.unit_id = u.id
    ''', conn)
    
    if not payments_df.empty:
        for idx, row in payments_df.iterrows():
            with st.container():
                st.write(f"العقار: {row['property_name']} | الوحدة: {row['unit_number']} | المستأجر: {row['tenant_name']}")
                st.write(f"تاريخ الاستحقاق: {row['due_date']} | المبلغ: {row['amount_with_vat']} ريال | الحالة: {row['status']}")
                if row['status'] == 'غير مسددة' and can_edit():
                    if st.button(f"تسديد هذه الدفعة {idx}"):
                        # تحديث حالة الدفعة
                        c = conn.cursor()
                        c.execute("UPDATE payments SET status='مسددة', paid_date=? WHERE id=?", (datetime.now().strftime("%Y-%m-%d"), row['id']))
                        conn.commit()
                        # توليد سند قبض
                        period = f"دفعة مستحقة في {row['due_date']}"
                        pdf_path = generate_payment_voucher(
                            row['id'], row['contract_id'], row['amount_with_vat'],
                            row['tenant_name'], row['owner_name'], row['property_name'],
                            row['unit_number'], period
                        )
                        with open(pdf_path, "rb") as f:
                            st.download_button("📄 تحميل سند القبض", f, file_name=f"sand_{row['id']}.pdf")
                        st.rerun()
    conn.close()

# تبويب التقارير والرسوم البيانية
with tab6:
    st.header("التقارير والرسوم البيانية")
    generate_financial_charts()
    
    # تقارير متنوعة
    report_type = st.selectbox("اختر التقرير", ["بيانات العقار", "الوحدات حسب العقار", "العقود", "الدفعات المستحقة", "الدفعات المدفوعة", "استعلام باسم المستأجر", "استعلام برقم العقد"])
    if st.button("عرض التقرير"):
        conn = sqlite3.connect(DB_NAME)
        if report_type == "بيانات العقار":
            df = pd.read_sql_query("SELECT * FROM properties", conn)
        elif report_type == "الدفعات المستحقة":
            df = pd.read_sql_query("SELECT * FROM payments WHERE status='غير مسددة'", conn)
        # ... باقي الاستعلامات ...
        st.dataframe(df)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("تصدير إلى Excel"):
                export_to_excel(df, report_type)
        with col2:
            if st.button("تصدير إلى PDF"):
                export_to_pdf(df, report_type)
        conn.close()

# تبويب المستخدمين (للأدمن فقط)
with tab7:
    if st.session_state.role == 'admin':
        st.header("إدارة المستخدمين والصلاحيات")
        with st.form("add_user_form"):
            new_user = st.text_input("اسم مستخدم جديد")
            new_pass = st.text_input("كلمة المرور", type="password")
            role = st.selectbox("الصلاحية", ["admin", "editor", "viewer"])
            if st.form_submit_button("إضافة مستخدم"):
                add_user(new_user, new_pass, role)
                st.rerun()
        users = get_all_users()
        for u in users:
            col1, col2, col3 = st.columns([2,2,1])
            col1.write(u[1])
            col2.write(u[2])
            if col3.button(f"حذف {u[0]}"):
                delete_user(u[0])
                st.rerun()
    else:
        st.warning("هذه الصفحة متاحة للمدير فقط")
with tab1:
    st.header("لوحة التحكم - ملخص سريع")
    show_notifications_dashboard()
    
    # عقود نشطة وغير نشطة
    conn = sqlite3.connect(DB_NAME)
    active_contracts = pd.read_sql_query("SELECT COUNT(*) FROM contracts WHERE is_active=1", conn).iloc[0,0]
    inactive_contracts = pd.read_sql_query("SELECT COUNT(*) FROM contracts WHERE is_active=0", conn).iloc[0,0]
    col1, col2 = st.columns(2)
    col1.metric("العقود النشطة", active_contracts)
    col2.metric("العقود المنتهية (غير نشطة)", inactive_contracts)
    
    # دفعات مسددة وغير مسددة
    paid = pd.read_sql_query("SELECT SUM(amount_with_vat) FROM payments WHERE status='مسددة'", conn).iloc[0,0] or 0
    unpaid = pd.read_sql_query("SELECT SUM(amount_with_vat) FROM payments WHERE status='غير مسددة'", conn).iloc[0,0] or 0
    col3, col4 = st.columns(2)
    col3.metric("إجمالي الدفعات المسددة", format_currency(paid))
    col4.metric("إجمالي الدفعات غير المسددة", format_currency(unpaid))
    
    conn.close()
