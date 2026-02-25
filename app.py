import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime

st.set_page_config(page_title="工時紀錄系統", layout="centered")
st.title("🏗️ 工時紀錄系統")

# --- Firebase 連線 (讀取 Secrets) ---
if not firebase_admin._apps:
    try:
        # 讀取剛才設定的 [firebase_config] 區段
        cred_info = st.secrets["firebase_config"]
        cred = credentials.Certificate(dict(cred_info))
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/" 
        })
        st.toast("雲端連線成功！", icon="☁️")
    except Exception as e:
        st.error(f"❌ 連線失敗：{e}")

# --- 輸入介面 ---
st.subheader("新增工時紀錄")
name = st.text_input("員工姓名", placeholder="例如：賴智文")
hours = st.number_input("工時 (小時)", min_value=0.5, step=0.5, value=8.0)

if st.button("點我存檔到雲端", use_container_width=True):
    if name:
        try:
            db.reference('work_logs').push({
                "name": name,
                "hours": hours,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success(f"✅ 成功存入：{name}")
            st.balloons()
        except Exception as e:
            st.error(f"❌ 存檔失敗：{e}")

# --- 顯示紀錄 ---
st.divider()
st.subheader("📋 最近的存檔紀錄")
try:
    logs = db.reference('work_logs').order_by_key().limit_to_last(5).get()
    if logs:
        for key, value in reversed(logs.items()):
            st.write(f"🕒 {value['time']} - **{value['name']}**: {value['hours']} 小時")
except:
    pass
