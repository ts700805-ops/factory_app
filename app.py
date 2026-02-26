import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定區 (強制台灣時區) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

def get_now():
    # 確保時間跟您電腦右下角一致
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
st.set_page_config(page_title="數位報工系統", layout="wide")

# 讀取員工資料 (包含管理員)
raw_users = get_db("users")
STAFF_DATA = {"管理員": "8888", "李小龍": "1234"} 
if raw_users: STAFF_DATA.update(raw_users)

# --- 4. 登入系統 ---
if "user" not in st.session_state:
    st.title("🔐 系統登入")
    with st.form("login"):
        u = st.selectbox("請選擇姓名", list(STAFF_DATA.keys()))
        p = st.text_input("輸入代碼", type="password")
        if st.form_submit_button("進入系統", use_container_width=True):
            if str(STAFF_DATA.get(u)) == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("❌ 代碼錯誤")
else:
    # --- 5. 功能導覽 ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📊 系統所有紀錄"])
    if st.sidebar.button("登出系統", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

    # --- 6. 頁面內容 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        # 簡易計時器
        with st.expander("⏱️ 計時器 (點擊展開)", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.ts = get_now()
                st.rerun()
            if c2.button("⏹️ 結束計時", use_container_width=True):
                if 'ts' in st.session_state:
                    st.session_state.te = get_now()
                    diff = st.session_state.te - st.session_state.ts
                    st.session_state.td = f"{diff.seconds//3600}小時 {(diff.seconds%3600)//60}分鐘"
                    st.rerun()
            if c3.button("🧹 清除時間", use_container_width=True):
                for k in ['ts', 'te', 'td']: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

            v1, v2 = st.columns(2)
            st_val = st.session_state.get('ts')
            en_val = st.session_state.get('te')
            v1.info(f"🕒 開始：{st_val.strftime('%H:%M:%S') if st_val else '---'}")
            v2.success(f"⌛ 結束：{en_val.strftime('%H:%M:%S') if en_val else '---'}")

        # 提交表單
        with st.form("work_form"):
            h_val = st.session_state.get('td', "0小時 0分鐘")
            
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=h_val)

            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                log = {
                    "姓名": st.session_state.user,
                    "狀態": status, "製令": order, "P/N": pn, "Type": tp, "工段名稱": stage,
                    "開始時間": st_val.strftime('%Y-%m-%d %H:%M:%S') if st_val else "N/A",
                    "結束時間": get_now().strftime('%Y-%m-%d %H:%M:%S'),
                    "累計工時": hours
                }
                save_db("work_logs", log)
                st.success("✅ 提交成功！")
                st.rerun()

    elif menu == "📊 系統所有紀錄":
        st.header("📊 系統所有提交紀錄")
        data = get_db("work_logs")
        if data:
            # 這是最保險的寫法：直接轉表格，不管它有哪些欄位
            df = pd.DataFrame(list(data.values()))
            
            # 排序：最新提交的在最上面
            if "結束時間" in df.columns:
                df = df.sort_values(by="結束時間", ascending=False)
            
            st.dataframe(df, use_container_width=True)
            st.info("💡 提示：您可以使用表格右上角的搜尋功能輸入姓名來篩選資料。")
        else:
            st.info("資料庫目前沒有任何紀錄。")
