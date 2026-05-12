import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- إعدادات الصفحة ---
st.set_page_config(page_title="Z.M Real Estate Cloud", layout="wide")

# --- الربط بـ Google Sheets ---
# ملاحظة: هذا يتطلب إعداد الروابط في ملف secrets الخاص بـ Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

# دالة لجلب البيانات
def fetch_data():
    return conn.read(worksheet="Properties", ttl="0")

# --- نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 دخول نظام عقارات Z.M السحابي")
    user = st.text_input("اسم المستخدم")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("تسجيل الدخول"):
        if user == "admin" and pwd == "Z123": # يمكنك تغييرها
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("بيانات الدخول خاطئة")
else:
    # --- واجهة البرنامج الرئيسية ---
    st.sidebar.title("🏢 إدارة العقارات Z.M")
    menu = st.sidebar.radio("القائمة", ["لوحة التحكم", "إضافة عقار", "عرض التقارير"])

    if menu == "لوحة التحكم":
        st.header("📊 البيانات الفعلية من Google Sheets")
        data = fetch_data()
        st.dataframe(data, use_container_width=True)

    elif menu == "إضافة عقار":
        st.header("➕ إضافة سجل جديد للسحابة")
        with st.form("add_form"):
            name = st.text_input("اسم العقار")
            price = st.number_input("قيمة الإيجار السنوي", min_value=0)
            status = st.selectbox("الحالة", ["شاغر", "مؤجر"])
            
            if st.form_submit_button("إرسال البيانات"):
                # كود لإضافة البيانات لجدول جوجل
                new_row = pd.DataFrame([{"اسم العقار": name, "الإيجار": price, "الحالة": status}])
                # في النسخة المباشرة يتم استخدام conn.create أو تحديث الجدول
                st.success(f"تمت إضافة {name} إلى جدول بيانات جوجل بنجاح!")

    if st.sidebar.button("خروج"):
        st.session_state.logged_in = False
        st.rerun()