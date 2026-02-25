import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# 1. 檢查是否已經初始化過，避免重複連線
if not firebase_admin._apps:
    # 請確保 key.json 與 app.py 都在 Desktop/factory_app 資料夾內
    try:
        cred = credentials.Certificate("key.json")
        firebase_admin.initialize_app(cred, {
            # 修正點：網址兩端必須加上引號 ""
            'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/" 
        })
        st.success("☁️ 雲端資料庫連線成功！")
    except Exception as e:
        st.error(f"❌ 連線失敗，請檢查 key.json 檔案是否存在：{e}")

# 這裡之後接著你原本的介面程式碼...
