import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# 設定網頁標題（增加這個，你才不會看到空白）
st.title("工時紀錄系統")

# 1. 檢查是否已經初始化過
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/" 
        })
    except Exception as e:
        st.error(f"❌ 連線失敗：{e}")

# 將成功訊息放在外面，這樣每次重新整理都會顯示
if firebase_admin._apps:
    st.success("☁️ 雲端資料庫狀態：連線中")
    
# 測試區：隨便打個字，確認網頁不是死的
st.write("系統目前運作正常，請開始輸入資料。")
