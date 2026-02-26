import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定區 (維持無金鑰與台灣時區) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

def get_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

# --- 2. 核心功能 ---
def get_db(path):
    try:
        response = requests.get(f"{DB_URL}{path}.json")
        return response.json()
    except: return None

def save_db(path, data, method="post"):
    try:
        if method == "post": requests.post(f"{DB_URL}{path}.json", json=data)
        else: requests.put(f"{DB_URL}{path}.json", json=data)
    except: pass

# --- 3. 頁面配置 ---
st.set_page_config(page_title="數位戰情室", layout="wide")

raw_users = get_db("users")
STAFF_DATA = {"管理員": "8888"}
if raw_users: STAFF_DATA.update(raw_users)

# --- 4. 登入系統 ---
if "user" not in st.session_state:
    st.title("🔐 員工系統登入")
    with st.form("login"):
        input_name = st.selectbox("請選擇姓名", list(STAFF_DATA.keys()))
        input_code = st.text_input("輸入代碼", type="password")
        if st.form_submit_button("進入系統", use_container_width=True):
            if str(STAFF_DATA.get(input_name)) == input_code:
                st.session_state.user = input_name
                st.rerun()
            else: st.error("❌ 代碼錯誤")
else:
    # --- 5. 左側選單 ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    options = ["🏗️ 工時回報", "📝 個人提交紀錄"]
    if st.session_state.user == "管理員":
        options += ["⚙️ 系統帳號管理", "📊 完整工時報表"]
    menu = st.sidebar.radio("功能選單", options)
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 登出系統", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    # --- 6. 頁面內容 ---

    # A. 工時回報頁面
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        with st.expander("⏱️ 工時計時器", expanded=True):
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.work_start = get_now()
                st.rerun() 
            
            if col_b.button("⏹️ 結束計時", use_container_width=True):
                if 'work_start' in st.session_state:
                    st.session_state.work_end = get_now()
                    duration = st.session_state.work_end - st.session_state.work_start
                    total_seconds = int(duration.total_seconds())
                    h = total_seconds // 3600
                    m = (total_seconds % 3600) // 60
                    st.session_state.display_hours = f"{h}小時 {m}分鐘"
                    st.rerun()
                else: st.warning("請先按下『開始計時』")

            if col_c.button("🧹 清除時間", use_container_width=True):
                for k in ['work_start', 'work_end', 'display_hours']:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

            t1, t2 = st.columns(2)
            s_time = st.session_state.get('work_start')
            e_time = st.session_state.get('work_end')
            
            with t1:
                st.markdown("**🔔 記錄開始時間**")
                if s_time: st.info(f"🕒 {s_time.strftime('%H:%M:%S')}")
                else: st.write("---")
            
            with t2:
                st.markdown("**🔔 記錄結束時間**")
                if e_time: st.success(f"⌛ {e_time.strftime('%H:%M:%S')}")
                else: st.write("---")

        with st.form("work_form"):
            user_code = STAFF_DATA.get(st.session_state.user, "N/A")
            c1, c2, c3 = st.columns(3)
            status = c1.selectbox("狀態", ["作業中", "暫停", "下班", "完工"])
            order_no = c2.text_input("製令")
            pn = c3.text_input("P/N")
            
            c4, c5, c6 = st.columns(3)
            prod_type = c4.text_input("Type")
            stage = c5.text_input("工段名稱")
            current_hours = st.session_state.get('display_hours', "0小時 0分鐘")
            hours_text = c6.text_input("累計工時", value=current_hours)

            st.write(f"📌 **工號：** {user_code} | **姓名：** {st.session_state.user}")
            
            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                f_start = s_time.strftime('%Y-%m-%d %H:%M:%S') if s_time else "N/A"
                f_end = get_now().strftime("%Y-%m-%d %H:%M:%S")
                log_data = {
                    "狀態": status, "製令": order_no, "P/N": pn, "Type": prod_type, "工段名稱": stage,
                    "工號": user_code, "姓名": st.session_state.user,
                    "開始時間": f_start, "結束時間": f_end, "累計工時": hours_text
                }
                save_db("work_logs", log_data)
                st.success("✅ 紀錄已成功提交！")
                for k in ['work_start', 'work_end', 'display_hours']:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

    # B. 個人提交紀錄 (顯示：開始 + 結束 + 累計工時)
    elif menu == "📝 個人提交紀錄":
        st.header(f"📝 {st.session_state.user} 的提交紀錄")
        raw_logs = get_db("work_logs")
        if raw_logs:
            df = pd.DataFrame.from_dict(raw_logs, orient='index').reset_index(drop=True)
            name_key = next((k for k in ["姓名", "name"] if k in df.columns), None)
            
            if name_key:
                df_personal = df[df[name_key].astype(str) == str(st.session_state.user)]
                if not df_personal.empty:
                    # 依需求排定顯示欄位
                    cols = ["狀態", "製令", "P/N", "Type", "工段名稱", "開始時間", "結束時間", "累計工時"]
                    existing = [c for c in cols if c in df_personal.columns]
                    st.dataframe(df_personal[existing].sort_values(by="結束時間", ascending=False), use_container_width=True)
                else: st.info("查無您的提交紀錄。")
            else: st.warning("資料庫格式不符。")
        else: st.info("目前尚無任何報工數據。")

    # C. 帳號管理 (其餘功能均不改動)
    elif menu == "⚙️ 系統帳號管理":
        st.header("👤 系統帳號管理")
        new_n = st.text_input("新員工姓名")
        new_c = st.text_input("設定員工工號")
        if st.button("➕ 建立帳號並同步"):
            if new_n and new_c:
                save_db(f"users/{new_n}", new_c, method="put")
                st.success("✅ 帳號已建立！")
                st.rerun()

    # D. 完整報表
    elif menu == "📊 完整工時報表":
        st.header("📊 完整工時報表")
        raw_logs = get_db("work_logs")
        if raw_logs:
            df = pd.DataFrame.from_dict(raw_logs, orient='index').reset_index(drop=True)
            st.dataframe(df, use_container_width=True)
