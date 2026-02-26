import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定區 (強制台灣時區) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

def get_now():
    # 解決 07:12 與 15:14 的時間偏差問題
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

# 讀取員工資料
raw_users = get_db("users")
STAFF_DATA = {"管理員": "8888", "李小龍": "1234"} # 預設名單
if raw_users: STAFF_DATA.update(raw_users)

# --- 4. 登入系統 ---
if "user" not in st.session_state:
    st.title("🔐 系統登入")
    with st.form("login"):
        u = st.selectbox("請選擇姓名", list(STAFF_DATA.keys()))
        p = st.text_input("輸入代碼", type="password")
        if st.form_submit_button("進入", use_container_width=True):
            if str(STAFF_DATA.get(u)) == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("❌ 代碼錯誤")
else:
    # --- 5. 左側導覽 ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("功能選單", ["🏗️ 工時回報", "📝 歷史紀錄查詢"])
    if st.sidebar.button("登出系統", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

    # --- 6. 頁面內容 ---
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        # 簡單計時器
        with st.expander("⏱️ 工時計時器 (點擊展開)", expanded=True):
            col1, col2, col3 = st.columns(3)
            if col1.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.t_start = get_now()
                st.rerun()
            if col2.button("⏹️ 結束計時", use_container_width=True):
                if 't_start' in st.session_state:
                    st.session_state.t_end = get_now()
                    diff = st.session_state.t_end - st.session_state.t_start
                    st.session_state.t_diff = f"{diff.seconds//3600}小時 {(diff.seconds%3600)//60}分鐘"
                    st.rerun()
            if col3.button("🧹 清除時間", use_container_width=True):
                for k in ['t_start', 't_end', 't_diff']: 
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

            v1, v2 = st.columns(2)
            ts = st.session_state.get('t_start')
            te = st.session_state.get('t_end')
            v1.info(f"🕒 開始：{ts.strftime('%H:%M:%S') if ts else '---'}")
            v2.success(f"⌛ 結束：{te.strftime('%H:%M:%S') if te else '---'}")

        # 回報表單
        with st.form("work_form"):
            h_val = st.session_state.get('t_diff', "0小時 0分鐘")
            
            r1 = st.columns(3)
            status = r1[0].selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
            order = r1[1].text_input("製令")
            pn = r1[2].text_input("P/N")
            
            r2 = st.columns(3)
            tp = r2[0].text_input("Type")
            stage = r2[1].text_input("工段名稱")
            hours = r2[2].text_input("累計工時", value=h_val)

            st.write(f"📌 目前登入：{st.session_state.user} (工號: {STAFF_DATA.get(st.session_state.user)})")
            
            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                # 準備要存入的 10 個欄位
                log = {
                    "姓名": st.session_state.user,
                    "工號": STAFF_DATA.get(st.session_state.user),
                    "狀態": status, "製令": order, "P/N": pn, "Type": tp, "工段名稱": stage,
                    "開始時間": ts.strftime('%Y-%m-%d %H:%M:%S') if ts else "N/A",
                    "結束時間": get_now().strftime('%Y-%m-%d %H:%M:%S'),
                    "累計工時": hours
                }
                save_db("work_logs", log)
                st.success("✅ 紀錄提交成功！")
                st.rerun()

    elif menu == "📝 歷史紀錄查詢":
        st.header("📝 系統所有提交紀錄")
        data = get_db("work_logs")
        if data:
            # 最保險的轉換法：直接抓取所有值，不論欄位叫什麼
            df = pd.DataFrame(list(data.values()))
            
            # 依據結束時間排序 (最新的在上面)
            if "結束時間" in df.columns:
                df = df.sort_values(by="結束時間", ascending=False)
            
            st.dataframe(df, use_container_width=True)
            st.info("💡 提示：若紀錄太多，請使用表格右上角的搜尋功能輸入您的姓名。")
        else:
            st.info("資料庫目前沒有任何紀錄。")
