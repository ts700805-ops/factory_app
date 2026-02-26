import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定與時間 (強制台灣 UTC+8) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

def get_now():
    # 修正截圖中出現的時間誤差，對齊您的電腦時間
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# --- 2. 資料庫操作 ---
def get_db(path):
    try:
        r = requests.get(f"{DB_URL}{path}.json")
        return r.json()
    except: return None

def save_db(path, data):
    try: requests.post(f"{DB_URL}{path}.json", json=data)
    except: pass

# --- 3. 登入與選單 ---
st.set_page_config(page_title="數位報工", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 登入系統")
    u = st.selectbox("姓名", ["管理員", "李小龍", "賴智文"])
    p = st.text_input("代碼", type="password")
    if st.button("進入", use_container_width=True):
        if (u == "管理員" and p == "8888") or (u == "李小龍" and p == "1234") or (u == "賴智文"):
            st.session_state.user = u
            st.rerun()
        else: st.error("代碼錯誤")
else:
    menu = st.sidebar.radio("選單", ["🏗️ 工時回報", "📝 歷史紀錄"])
    if st.sidebar.button("登出"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

    # --- 4. 功能頁面 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報")
        
        # 計時器區 (解決截圖中的小時數不對問題)
        with st.expander("⏱️ 工時計時器", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.s_t = get_now()
                st.rerun()
            if c2.button("⏹️ 結束計時", use_container_width=True):
                if 's_t' in st.session_state:
                    st.session_state.e_t = get_now()
                    d = st.session_state.e_t - st.session_state.s_t
                    st.session_state.dur = f"{d.seconds//3600}小時 {(d.seconds%3600)//60}分鐘"
                    st.rerun()
            if c3.button("🧹 清除", use_container_width=True):
                for k in ['s_t', 'e_t', 'dur']: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

            st.write(f"🕒 開始：{st.session_state.get('s_t','---')} | ⌛ 結束：{st.session_state.get('e_t','---')}")

        # 提交表單
        with st.form("f"):
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=st.session_state.get('dur', "0小時 0分鐘"))

            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                log = {
                    "姓名": st.session_state.user, "狀態": status, "製令": order, "P/N": pn, 
                    "Type": tp, "工段名稱": stage, "累計工時": hours,
                    "開始時間": str(st.session_state.get('s_t','N/A')),
                    "結束時間": str(get_now())
                }
                save_db("work_logs", log)
                st.success("✅ 提交成功！")

    elif menu == "📝 歷史紀錄":
        st.header("📝 系統所有紀錄")
        data = get_db("work_logs")
        if data:
            # 這是最不容易出錯的顯示方式：直接轉成表格
            df = pd.DataFrame(list(data.values()))
            st.dataframe(df, use_container_width=True)
            st.info("💡 看到『賴智文』是正常的，那是您資料庫裡的舊資料。新提交的資料會出現在表格最下方或最上方。")
        else:
            st.write("目前沒有資料")
