import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定與時間 (對齊下午 03:14) ---
# 改用統一的 logs 分類，避免資料橫向散開
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/all_logs"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# --- 2. 資料庫功能 ---
def save_data(data):
    try: requests.post(f"{DB_URL}.json", json=data)
    except: pass

def get_data():
    try:
        r = requests.get(f"{DB_URL}.json")
        return r.json()
    except: return None

# --- 3. 介面與登入 ---
st.set_page_config(page_title="數位工單", layout="wide")

if "user" not in st.session_state:
    st.title("🔐 系統登入")
    u = st.selectbox("人員", ["管理員", "李小龍", "賴智文"])
    p = st.text_input("密碼", type="password")
    if st.button("進入"):
        if (u == "管理員" and p == "8888") or (u == "李小龍" and p == "1234") or (u == "賴智文"):
            st.session_state.user = u
            st.rerun()
else:
    menu = st.sidebar.radio("功能", ["🏗️ 報工回報", "📋 紀錄查詢"])
    
    # --- 4. 報工頁面 ---
    if menu == "🏗️ 報工回報":
        st.header("🏗️ 生產日報回報")
        
        # 計時器 (解決小時數不對的問題)
        with st.expander("⏱️ 計時器", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("開始"): st.session_state.st = get_now()
            if c2.button("結束"): 
                if 'st' in st.session_state:
                    st.session_state.en = get_now()
                    diff = st.session_state.en - st.session_state.st
                    st.session_state.df = f"{diff.seconds//3600}時 {(diff.seconds%3600)//60}分"
            if c3.button("清除"):
                for k in ['st','en','df']: st.session_state.pop(k, None)

            st.write(f"🕒 開始：{st.session_state.get('st','--')} | ⌛ 結束：{st.session_state.get('en','--')}")

        with st.form("work"):
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=st.session_state.get('df', "0小時 0分"))

            if st.form_submit_button("🚀 提交紀錄"):
                log = {
                    "姓名": st.session_state.user, "狀態": status, "製令": order,
                    "P/N": pn, "Type": tp, "工段名稱": stage, "累計工時": hours,
                    "開始時間": str(st.session_state.get('st','N/A')),
                    "提交時間": str(get_now())
                }
                save_data(log)
                st.success("✅ 已存檔")

    # --- 5. 查詢頁面 ---
    elif menu == "📋 紀錄查詢":
        st.header("📋 歷史紀錄清單")
        res = get_data()
        if res:
            # 將雜亂的 Firebase 資料轉成整齊表格
            df = pd.DataFrame(list(res.values()))
            if "提交時間" in df.columns:
                df = df.sort_values(by="提交時間", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("目前尚無資料")
