import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- إعدادات الصفحة واللغة ---
st.set_page_config(page_title=Z.M Real Estate, layout=wide, page_icon=🏢)

st.markdown(
    style
    @import url('httpsfonts.googleapis.comcss2family=Tajawalwght@400;700&display=swap');
    html, body, [class=css] { font-family 'Tajawal', sans-serif; direction RTL; text-align right; }
    .stMetric { text-align center; border 1px solid #f0f2f6; padding 10px; border-radius 10px; }
    style
    , unsafe_allow_html=True)

# --- الربط بقاعدة البيانات (Google Sheets) ---
conn = st.connection(gsheets, type=GSheetsConnection)

def get_data(sheet_name)
    try
        return conn.read(worksheet=sheet_name, ttl=0)
    except
        return pd.DataFrame()

# --- نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state
    st.session_state.logged_in = False

if not st.session_state.logged_in
    st.title(🔐 دخول نظام عقارات Z.M)
    user = st.text_input(اسم المستخدم)
    pwd = st.text_input(كلمة المرور, type=password)
    if st.button(دخول)
        if user == admin and pwd == Z123
            st.session_state.logged_in = True
            st.rerun()
        else
            st.error(بيانات الدخول خاطئة)
else
    # --- القائمة الجانبية ---
    st.sidebar.title(f🏢 Z.M Real Estate)
    st.sidebar.write(f👤 {user}  🕒 {datetime.now().strftime('%H%M')})
    menu = st.sidebar.radio(القائمة الرئيسية, 
        [📊 لوحة التحكم, 🏠 إدارة العقارات, 📄 إدارة العقود, 💰 الدفعات والسندات, 📑 تقارير الضريبة VAT])

    # --- 1. لوحة التحكم ---
    if menu == 📊 لوحة التحكم
        st.title(الخلاصة المالية والإشغال)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(إجمالي العقارات, 15)
        c2.metric(الوحدات المؤجرة, 42)
        c3.metric(دفعات قادمة, 8)
        c4.metric(إجمالي التحصيل, 125,000 ر.س)
        
        st.divider()
        df_demo = pd.DataFrame({'الشهر' ['يناير', 'فبراير', 'مارس', 'أبريل'], 'الإيراد' [30000, 45000, 38000, 52000]})
        fig = px.line(df_demo, x='الشهر', y='الإيراد', title=حركة الإيرادات الشهرية)
        st.plotly_chart(fig, use_container_width=True)

    # --- 2. إدارة العقارات ---
    elif menu == 🏠 إدارة العقارات
        st.title(إضافة وتعديل العقارات)
        with st.form(prop_form)
            col1, col2 = st.columns(2)
            p_name = col1.text_input(اسم العقار)
            p_type = col2.selectbox(النوع, [سكني, تجاري, إداري, فيلا])
            p_loc = st.text_input(رابط خريطة جوجل)
            p_address = st.text_area(العنوان الوطني التفصيلي)
            if st.form_submit_button(حفظ العقار)
                st.success(fتم حفظ عقار {p_name} في قاعدة البيانات)

    # --- 3. إدارة العقود ---
    elif menu == 📄 إدارة العقود
        st.title(إدارة عقود الإيجار)
        st.info(هنا يمكنك ربط المستأجرين بالوحدات وحساب الضريبة آلياً)
        # نموذج العقد
        with st.expander(📝 إنشاء عقد جديد)
            st.text_input(اسم المستأجر)
            st.date_input(تاريخ بدء العقد)
            st.number_input(قيمة العقد السنوية)
            st.checkbox(عقد تجاري (تطبق ضريبة 15%))
            st.button(إصدار العقد)

    # --- 4. الدفعات والسندات ---
    elif menu == 💰 الدفعات والسندات
        st.title(متابعة التحصيل وسندات القبض)
        # جدول دفعات وهمي للتوضيح
        payments = pd.DataFrame({
            'المستأجر' ['أحمد محمد', 'شركة الحلول'],
            'العقار' ['عمارة 1', 'مجمع 5'],
            'المبلغ' [5000, 15000],
            'الحالة' ['متأخر', 'مدفوع']
        })
        st.table(payments)
        if st.button(🖨️ طباعة سند قبض لآخر دفعة)
            st.success(تم توليد السند بصيغة PDF)

    # --- 5. تقارير الضريبة ---
    elif menu == 📑 تقارير الضريبة VAT
        st.title(إقرارات ضريبة القيمة المضافة)
        quarter = st.selectbox(اختر الربع السنوي, [الربع الأول, الربع الثاني, الربع الثالث, الربع الرابع])
        st.write(fتقرير {quarter} لعام 2026)
        st.button(📥 تصدير التقرير لملف Excel)

    if st.sidebar.button(تسجيل الخروج)
        st.session_state.logged_in = False
        st.rerun()
