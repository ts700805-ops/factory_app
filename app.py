import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime

# 設定網頁標題
st.set_page_config(page_title="工時紀錄系統", layout="centered")
st.title("🏗️ 工時紀錄系統")

# --- 1. 資料庫初始化 (只會執行一次) ---
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/" 
        })
    except Exception as e:
        st.error(f"❌ 連線失敗：{e}")

# --- 2. 製作輸入介面 ---
st.subheader("新增工時紀錄")

# 建立兩個輸入框
name = st.text_input("員工姓名")
hours = st.number_input("工時 (小時)", min_value=0.5, max_value=24.0, step=0.5)

# 建立一個提交按鈕
if st.button("點我存檔到雲端"):
    if name:
        # 準備要存的資料
        new_data = {
            "name": name,
            "hours": hours,
            "time": str(datetime.datetime.now())
        }
        
        # 存入 Firebase 的 'work_logs' 資料夾下
        try:
            db.reference('work_logs').push(new_data)
            st.success(f"✅ 成功！已存入：{name} {hours} 小時")
        except Exception as e:
            st.error(f"❌ 存檔失敗：{e}")
    else:
        st.warning("⚠️ 請先輸入姓名喔！")
