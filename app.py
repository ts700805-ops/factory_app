import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定區 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

def get_now():
    # 修正您標示的時間偏差，強制台灣時區
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
st.set_page_config(page_title="生產日報系統", layout="wide")

# 讀取員工名單
raw_users = get_db("users")
STAFF_DATA = {"管理員": "8888"}
if raw_users: STAFF_DATA.update(raw_users)

# --- 4. 登入系統 ---
if "user" not in st.session_state:
    st.title("🔐 員工登入")
    with st.form("login"):
        u = st.selectbox("姓名", list(STAFF_DATA.keys()))
        p = st.text_input("密碼代碼", type="password")
        if st.form_submit_button("進入", use_container_width=True):
            if str(STAFF_DATA.get(u)) == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("代碼錯誤")
else:
    # --- 5. 功能選單 ---
    menu = st.sidebar.radio("功能表", ["🏗️ 工時回報", "📝 歷史紀錄查詢"])
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 6. 頁面內容 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        # 計時器區塊
        with st.expander("⏱️ 計時器工作台", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.start_t = get_now()
                st.rerun()
            if c2.button("⏹️ 結束計時", use_container_width=True):
                if 'start_t' in st.session_state:
                    st.session_state.end_t = get_now()
                    diff = st.session_state.end_t - st.session_state.start_t
                    h, m = diff.seconds // 3600, (diff.seconds % 3600) // 60
                    st.session_state.total_h = f"{h}小時 {m}分鐘"
                    st.rerun()
            if c3.button("🧹 清除", use_container_width=True):
                for k in ['start_t', 'end_t', 'total_h']: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

            # 顯示目前計時狀況
            v1, v2 = st.columns(2)
            st_val = st.session_state.get('start_t')
            en_val = st.session_state.get('end_t')
            v1.info(f"🕒 開始：{st_val.strftime('%H:%M:%S') if st_val else '---'}")
            v2.success(f"⌛ 結束：{en_val.strftime('%H:%M:%S') if en_val else '---'}")

        # 表單提交
        with st.form("work_form"):
            user_code = STAFF_DATA.get(st.session_state.user, "0000")
            hours_val = st.session_state.get('total_h', "0小時 0分鐘")
            
            row1 = st.columns(3)
            status = row1[0].selectbox("狀態", ["作業中", "完工", "暫停"])
            order = row1[1].text_input("製令")
            pn = row1[2].text_input("P/N")
            
            row2 = st.columns(3)
            tp = row2[0].text_input("Type")
            stage = row2[1].text_input("工段名稱")
            hours = row2[2].text_input("累計工時", value=hours_val) # 您要求的累計時間

            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                data = {
                    "姓名": st.session_state.user, "工號": user_code,
                    "狀態": status, "製令": order, "P/N": pn, "Type": tp, "工段名稱": stage,
                    "開始時間": st_val.strftime('%Y-%m-%d %H:%M:%S') if st_val else "N/A",
                    "結束時間": get_now().strftime('%Y-%m-%d %H:%M:%S'),
                    "累計工時": hours
                }
                save_db("work_logs", data)
                st.success("✅ 已提交成功！")

    elif menu == "📝 歷史紀錄查詢":
        st.header("📝 系統紀錄清單")
        res = get_db("work_logs")
        if res:
            # 最暴力簡單的轉換方式，直接轉表格
            df = pd.DataFrame(list(res.values()))
            # 排序：讓最新提交的在最上面
            if "結束時間" in df.columns:
                df = df.sort_values(by="結束時間", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("資料庫目前空空如也，請先去提交一筆資料。")
