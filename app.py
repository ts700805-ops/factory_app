import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import json

# 設定網頁標題
st.set_page_config(page_title="工時紀錄系統", layout="centered")
st.title("🏗️ 工時紀錄系統")

# --- 1. Firebase 連線設定 (修正簽章與重複連線問題) ---
def init_firebase():
    # 檢查是否已經連線過
    if not firebase_admin._apps:
        try:
            # 讀取 key.json 檔案
            with open("key.json", "r") as f:
                key_data = json.load(f)
            
            # 使用讀取到的資料進行初始化
            cred = credentials.Certificate(key_data)
            firebase_admin.initialize_app(cred, {
                'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/" 
            })
            return True
        except FileNotFoundError:
            st.error("❌ 找不到 key.json 檔案，請確認檔案已上傳到 GitHub。")
            return False
        except Exception as e:
            st.error(f"❌ 連線發生錯誤：{e}")
            return False
    return True

# 執行初始化
if init_firebase():
    st.toast("雲端連線成功！", icon="☁️")

# --- 2. 製作輸入介面 ---
st.subheader("新增工時紀錄")

# 使用 columns 讓介面整齊一點
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("員工姓名", placeholder="例如：賴智文")
with col2:
    hours = st.number_input("工時 (小時)", min_value=0.5, max_value=24.0, step=0.5, value=8.0)

# 建立提交按鈕
if st.button("點我存檔到雲端", use_container_width=True):
    if name:
        # 準備要存的資料
        new_data = {
            "name": name,
            "hours": hours,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # 存入 Firebase 的 'work_logs' 資料夾下
            db.reference('work_logs').push(new_data)
            st.success(f"✅ 成功存入：{name} {hours} 小時")
            st.balloons() # 成功時噴氣球慶祝一下
        except Exception as e:
            st.error(f"❌ 存檔失敗，請檢查資料庫權限：{e}")
    else:
        st.warning("⚠️ 請先輸入姓名喔！")

# --- 3. 顯示最近的紀錄 (讓你知道有沒有存成功) ---
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
    st.write("暫時無法讀取紀錄")
