import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime

# 設定網頁標題
st.set_page_config(page_title="工時紀錄系統", layout="centered")
st.title("🏗️ 工時紀錄系統")

# --- 1. Firebase 連線設定 (修正讀取邏輯) ---
if not firebase_admin._apps:
    try:
        # 讀取剛剛下載並上傳的 key.json 檔案
        cred = credentials.Certificate("key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/" 
        })
        st.toast("雲端連線成功！", icon="☁️")
    except Exception as e:
        st.error(f"❌ 初始化失敗：{e}")
        st.info("💡 提示：請確保 GitHub 上的 key.json 檔案內容完整，且檔案名稱正確。")

# --- 2. 製作輸入介面 ---
st.subheader("新增工時紀錄")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("員工姓名", placeholder="例如：賴智文")
with col2:
    hours = st.number_input("工時 (小時)", min_value=0.5, max_value=24.0, step=0.5, value=8.0)

if st.button("點我存檔到雲端", use_container_width=True):
    if name:
        new_data = {
            "name": name,
            "hours": hours,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            db.reference('work_logs').push(new_data)
            st.success(f"✅ 成功存入：{name} {hours} 小時")
            st.balloons()
        except Exception as e:
            st.error(f"❌ 存檔失敗：{e}")
    else:
        st.warning("⚠️ 請先輸入姓名喔！")

# --- 3. 顯示最近的紀錄 ---
st.divider()
st.subheader("📋 最近的存檔紀錄")
try:
    logs = db.reference('work_logs').order_by_key().limit_to_last(5).get()
    if logs:
        for key, value in reversed(logs.items()):
            st.write(f"🕒 {value['time']} - **{value['name']}**: {value['hours']} 小時")
    else:
        st.write("目前尚無紀錄")
except:
    pass
