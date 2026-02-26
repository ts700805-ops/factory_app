import streamlit as st
import pandas as pd
import datetime
import os
import requests

# --- 設定區 ---
# 若有 Line Token 可貼在此處，沒有則維持原樣
LINE_TOKEN = "這裡貼上你的Line權杖"

# 1. 自定義員工名單 (姓名: 代碼)
STAFF_DATA = {
    "管理員": "8888",
    "賴智文": "1234",
    "王小明": "5678",
    "李大華": "0000"
}

# 這是儲存資料的檔案名稱，不需要任何網路授權
LOG_FILE = "work_logs.csv"

# --- 核心功能：讀取與儲存資料 ---
def load_data():
    if os.path.exists(LOG_FILE):
        try:
            return pd.read_csv(LOG_FILE)
        except:
            return pd.DataFrame(columns=["紀錄時間", "姓名", "工時(hr)"])
    return pd.DataFrame(columns=["紀錄時間", "姓名", "工時(hr)"])

def save_data(name, hours):
    df = load_data()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([[now, name, hours]], columns=["紀錄時間", "姓名", "工時(hr)"])
    df = pd.concat([df, new_row], ignore_index=True)
    # 使用 utf-8-sig 確保 Excel 打開不會亂碼
    df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    return now

def send_line(msg):
    if LINE_TOKEN and LINE_TOKEN != "這裡貼上你的Line權杖":
        try:
            headers = {"Authorization": "Bearer " + LINE_TOKEN}
            data = {"message": msg}
            requests.post("https://notify-bot.line.me/api/notify", headers=headers, data=data)
        except: 
            pass

# --- 頁面設定 ---
st.set_page_config(page_title="員工自主管理工時系統", layout="centered")

# --- 2. 登入系統 (使用代碼登入) ---
if "user" not in st.session_state:
    st.title("🔐 員工系統登入")
    # 使用 st.container 讓介面更整齊
    with st.form("login_form"):
        input_name = st.selectbox("請選擇您的姓名", list(STAFF_DATA.keys()))
        input_code = st.text_input("請輸入員工代碼", type="password")
        submit_login = st.form_submit_button("登入系統", use_container_width=True)
        
        if submit_login:
            if STAFF_DATA[input_name] == input_code:
                st.session_state.user = input_name
                st.success(f"歡迎回來，{input_name}！")
                st.rerun()
            else:
                st.error("❌ 代碼錯誤，請重新輸入")
else:
    # --- 3. 已登入介面 ---
    st.sidebar.write(f"👤 當前使用者：{st.session_state.user}")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    st.title(f"🏗️ {st.session_state.user} - 工時回報")

    with st.container(border=True):
        hours = st.number_input("今日工作時數", min_value=0.5, max_value=24.0, step=0.5, value=8.0)
        if st.button("🚀 提交工時並通知老闆", use_container_width=True):
            save_time = save_data(st.session_state.user, hours)
            # 發送 Line 通知
            send_line(f"\n📢 工時回報\n員工：{st.session_state.user}\n工時：{hours}\n時間：{save_time}")
            st.success("✅ 紀錄已成功儲存！")
            st.balloons()

    # --- 4. 管理員報表專區 ---
    if st.session_state.user == "管理員":
        st.divider()
        st.subheader("📊 完整工時報表 (僅管理員可見)")
        df_display = load_data()
        if not df_display.empty:
            # 排序讓最新的紀錄顯示在最上面
            st.dataframe(df_display.sort_values(by="紀錄時間", ascending=False), use_container_width=True)
            
            # 下載按鈕
            csv = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載備份 CSV", data=csv, file_name="work_report.csv", mime="text/csv")
            
            if st.button("🗑️ 刪除最後一筆紀錄"):
                df_display = df_display[:-1]
                df_display.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
                st.warning("最後一筆紀錄已移除")
                st.rerun()
        else:
            st.info("目前尚無任何存檔紀錄。")
