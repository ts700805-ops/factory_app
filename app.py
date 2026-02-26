import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 依照截圖設定路徑 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"
LOG_PATH = "work_logs" # 確保與截圖完全一致

def get_now():
    # 強制對齊台灣時間，修正 07:12 偏差
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# --- 2. 登入系統 (維持管理員 8888 權限) ---
st.set_page_config(page_title="數位報工-修復版", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 系統登入")
    u = st.selectbox("人員姓名", ["管理員", "李小龍", "賴智文"])
    p = st.text_input("輸入代碼", type="password")
    if st.button("進入系統", use_container_width=True):
        if (u == "管理員" and p == "8888") or (u == "李小龍" and p == "1234") or (u == "賴智文"):
            st.session_state.user = u
            st.rerun()
        else: st.error("代碼錯誤")
else:
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📋 歷史紀錄查詢"])
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 工時回報 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        # 計時器區塊
        with st.expander("⏱️ 計時器工具", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時"):
                st.session_state.start = get_now()
                st.rerun()
            if c2.button("⏹️ 結束計時"):
                if 'start' in st.session_state:
                    st.session_state.end = get_now()
                    diff = st.session_state.end - st.session_state.start
                    st.session_state.dur = f"{diff.seconds//3600}小時 {(diff.seconds%3600)//60}分鐘"
                    st.rerun()
            if c3.button("🧹 清除"):
                for k in ['start','end','dur']: st.session_state.pop(k, None)
                st.rerun()
            st.write(f"🕒 開始：{st.session_state.get('start','--')} | ⌛ 結束：{st.session_state.get('end','--')}")

        # 依照您的要求填寫 10 個欄位
        with st.form("my_form"):
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=st.session_state.get('dur', "0小時 0分鐘"))

            if st.form_submit_button("🚀 提交紀錄"):
                new_record = {
                    "name": st.session_state.user, # 對齊截圖中的欄位名
                    "status": status, "order": order, "pn": pn, "type": tp, "stage": stage,
                    "hours": hours,
                    "startTime": str(st.session_state.get('start', 'N/A')),
                    "time": str(get_now()) # 對齊截圖中的 time 欄位
                }
                # 存入 work_logs 資料夾
                requests.post(f"{DB_BASE_URL}{LOG_PATH}.json", json=new_record)
                st.success("✅ 資料已同步至 Firebase 'work_logs' 資料夾！")

    # --- 4. 紀錄查詢 ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 歷史紀錄清單")
        r = requests.get(f"{DB_BASE_URL}{LOG_PATH}.json")
        data = r.json()
        
        if data:
            # 這是最保險的寫法：直接轉表格，不處理複雜篩選
            df = pd.DataFrame(list(data.values()))
            st.dataframe(df, use_container_width=True)
            st.write("👆 以上為資料庫中的原始紀錄，包含您在 Firebase 看到的舊資料。")
        else:
            st.info("目前資料庫是空的，或路徑連接失敗。")
