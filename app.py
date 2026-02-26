import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定區 (絕對台灣時區) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

def get_now():
    # 強制修正 07:12 與 15:14 的時差
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# --- 2. 核心功能 ---
def get_db(path):
    try:
        r = requests.get(f"{DB_URL}{path}.json")
        return r.json()
    except: return None

def save_db(path, data):
    try: requests.post(f"{DB_URL}{path}.json", json=data)
    except: pass

# --- 3. 頁面配置 ---
st.set_page_config(page_title="生產日報", layout="wide")

raw_users = get_db("users")
STAFF_DATA = {"管理員": "8888"}
if raw_users: STAFF_DATA.update(raw_users)

# --- 4. 登入系統 ---
if "user" not in st.session_state:
    st.title("🔐 員工登入")
    with st.form("login"):
        u = st.selectbox("請選擇姓名", list(STAFF_DATA.keys()))
        p = st.text_input("輸入代碼", type="password")
        if st.form_submit_button("進入", use_container_width=True):
            if str(STAFF_DATA.get(u)) == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("代碼錯誤")
else:
    # --- 5. 功能選單 ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("功能表", ["🏗️ 工時回報", "📝 歷史紀錄查詢"])
    if st.sidebar.button("登出"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

    # --- 6. 頁面內容 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        # 計時器區
        with st.expander("⏱️ 工時計時器", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.start_t = get_now()
                st.rerun()
            if c2.button("⏹️ 結束計時", use_container_width=True):
                if 'start_t' in st.session_state:
                    st.session_state.end_t = get_now()
                    diff = st.session_state.end_t - st.session_state.start_t
                    h, m = diff.seconds // 3600, (diff.seconds % 3600) // 60
                    st.session_state.hours_str = f"{h}小時 {m}分鐘"
                    st.rerun()
            if c3.button("🧹 清除時間", use_container_width=True):
                for k in ['start_t', 'end_t', 'hours_str']:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

            v1, v2 = st.columns(2)
            st_val = st.session_state.get('start_t')
            en_val = st.session_state.get('end_t')
            v1.info(f"🕒 記錄開始時間：{st_val.strftime('%H:%M:%S') if st_val else '---'}")
            v2.success(f"⌛ 記錄結束時間：{en_val.strftime('%H:%M:%S') if en_val else '---'}")

        # 表單提交
        with st.form("work_form"):
            user_code = STAFF_DATA.get(st.session_state.user, "0000")
            h_val = st.session_state.get('hours_str', "0小時 0分鐘")
            
            row1 = st.columns(3)
            status = row1[0].selectbox("狀態", ["作業中", "暫停", "下班", "完工"])
            order = row1[1].text_input("製令")
            pn = row1[2].text_input("P/N")
            
            row2 = st.columns(3)
            tp = row2[0].text_input("Type")
            stage = row2[1].text_input("工段名稱")
            hours = row2[2].text_input("累計工時", value=h_val)

            st.write(f"📌 工號：{user_code} | 姓名：{st.session_state.user}") # 確保姓名顯示李小龍
            
            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                data = {
                    "姓名": st.session_state.user, "工號": user_code,
                    "狀態": status, "製令": order, "P/N": pn, "Type": tp, "工段名稱": stage,
                    "開始時間": st_val.strftime('%Y-%m-%d %H:%M:%S') if st_val else "N/A",
                    "結束時間": get_now().strftime('%Y-%m-%d %H:%M:%S'),
                    "累計工時": hours
                }
                save_db("work_logs", data)
                st.success("✅ 紀錄已成功提交！")
                for k in ['start_t', 'end_t', 'hours_str']:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

    elif menu == "📝 歷史紀錄查詢":
        st.header(f"📝 {st.session_state.user} 的提交紀錄")
        res = get_db("work_logs")
        if res:
            # 轉換並過濾：只顯示目前登入者的資料
            all_data = list(res.values())
            df = pd.DataFrame(all_data)
            
            # 修正李小龍看到賴智文的問題：嚴格篩選姓名
            if "姓名" in df.columns:
                df_me = df[df["姓名"] == st.session_state.user]
                if not df_me.empty:
                    # 依需求排定：開始 + 結束 + 累計時間
                    cols = ["狀態", "製令", "P/N", "Type", "工段名稱", "開始時間", "結束時間", "累計工時"]
                    st.dataframe(df_me[[c for c in cols if c in df_me.columns]].sort_values(by="結束時間", ascending=False), use_container_width=True)
                else: st.info("查無您的紀錄。")
            else: st.warning("資料庫格式異常。")
        else: st.info("目前尚無任何紀錄。")
