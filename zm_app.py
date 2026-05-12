import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- إعدادات الصفحة (تم تصحيحها هنا) ---
st.set_page_config(page_title="Z.M Real Estate", layout="wide", page_icon="🏢")

# --- تنسيق اللغة العربية ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: RTL; text-align: right; }
    .stMetric { text-align: center; border: 1px solid #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 دخول نظام عقارات Z.M")
    user = st.text_input("اسم المستخدم")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if user == "admin" and pwd == "Z123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("بيانات الدخول خاطئة")
else:
    # --- القائمة الجانبية ---
    st.sidebar.title("🏢 Z.M Real Estate")
    st.sidebar.write(f"👤 مرحباً: {st.session_state.username if 'username' in st.session_state else 'المدير'}")
    menu = st.sidebar.radio("القائمة الرئيسية", 
        ["📊 لوحة التحكم", "🏠 إدارة العقارات", "📄 إدارة العقود", "💰 الدفعات والسندات", "📑 تقارير الضريبة VAT"])

    # --- محتوى القوائم ---
    if menu == "📊 لوحة التحكم":
        st.header("إحصائيات العقارات")
        c1, c2, c3 = st.columns(3)
        c1.metric("العقارات", "10")
        c2.metric("الوحدات", "50")
        c3.metric("التحصيل", "100,000 ر.س")
    
    elif menu == "🏠 إدارة العقارات":
        st.header("إضافة عقار جديد")
        st.text_input("اسم العقار")
        st.selectbox("النوع", ["سكني", "تجاري"])
        st.button("حفظ")

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()
