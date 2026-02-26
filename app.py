import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定區 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

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

    # A. 工時回報頁面 (保持原功能)
    if menu == "🏗️ 工時回報":
        st.header("🏗️ 生產日報回報")
        
        with st.expander("⏱️ 工時計時器", expanded=True):
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("⏱️ 開始計時", use_container_width=True):
                st.session_state.work_start = datetime.datetime.now()
                st.rerun() 
            
            if col_b.button("⏹️ 結束計時", use_container_width=True):
                if 'work_start' in st.session_state:
                    st.session_state.work_end = datetime.datetime.now()
                    duration = st.session_state.work_end - st.session_state.work_start
                    total_seconds = int(duration.total_seconds())
                    h = total_seconds // 3600
                    m = (total_seconds % 3600) // 60
                    st.session_state.display_hours = f"{h}小時 {m}分鐘"
                    st.rerun()
                else: st.warning("請先按下『開始計時』")

            if col_c.button("🧹 清除時間", use_container_width=True):
                if 'work_start' in st.session_state: del st.session_state['work_start']
                if 'work_end' in st.session_state: del st.session_state['work_end']
                if 'display_hours' in st.session_state: del st.session_state['display_hours']
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
            hours_text = c6.text_input("累計工時", value=st.session_state.get('display_hours', "0小時 0分鐘"))

            st.write(f"📌 **工號：** {user_code} | **姓名：** {st.session_state.user}")
            
            if st.form_submit_button("🚀 提交紀錄", use_container_width=True):
                final_start = s_time.strftime('%Y-%m-%d %H:%M:%S') if s_time else "N/A"
                final_end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_data = {
                    "狀態": status, "製令": order_no, "P/N": pn, "Type": prod_type, "工段名稱": stage,
                    "工號": user_code, "姓名": st.session_state.user,
                    "開始時間": final_start, "結束時間": final_end, "累計工時": hours_text
                }
                save_db("work_logs", log_data)
                st.success("✅ 紀錄已成功提交！")
                if 'work_start' in st.session_state: del st.session_state['work_start']
                if 'work_end' in st.session_state: del st.session_state['work_end']
                if 'display_hours' in st.session_state: del st.session_state['display_hours']
                st.rerun()

    # B. 個人提交紀錄 (強化版：解決看不見資料的問題)
    elif menu == "📝 個人提交紀錄":
        st.header(f"📝 {st.session_state.user} 的提交紀錄")
        raw_logs = get_db("work_logs")
        
        if raw_logs:
            # 將資料字典轉換為 DataFrame，並確保 ID 轉換為欄位
            df = pd.DataFrame.from_dict(raw_logs, orient='index').reset_index(drop=True)
            
            # 自動偵測姓名欄位 (容錯處理)
            name_col = None
            for c in ["姓名", "name", "Name"]:
                if c in df.columns:
                    name_col = c
                    break
            
            if name_col:
                # 執行篩選
                df_personal = df[df[name_col] == st.session_state.user]
                
                if not df_personal.empty:
                    # 定義要顯示的 10 個欄位順序
                    cols = ["狀態", "製令", "P/N", "Type", "工段名稱", "工號", "姓名", "開始時間", "結束時間", "累計工時"]
                    existing = [c for c in cols if c in df_personal.columns]
                    df_display = df_personal[existing]
                    
                    # 排序：結束時間最新的在最上面
                    if "結束時間" in df_display.columns:
                        df_display = df_display.sort_values(by="結束時間", ascending=False)
                    
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.info(f"查無 {st.session_state.user} 的紀錄。請確認您是否已提交報工。")
            else:
                st.warning("資料庫格式異常，請聯絡管理員確認欄位名稱。")
        else:
            st.info("系統目前尚無任何報工數據。")

    # C. 系統帳號管理
    elif menu == "⚙️ 系統帳號管理":
        st.header("👤 系統帳號管理")
        with st.container(border=True):
            new_n = st.text_input("新員工姓名")
            new_c = st.text_input("設定員工工號")
            if st.button("➕ 建立帳號並同步", use_container_width=True):
                if new_n and new_c:
                    save_db(f"users/{new_n}", new_c, method="put")
                    st.success(f"✅ 員工「{new_n}」帳號已建立！")
                    st.rerun()

    # D. 完整報表頁面
    elif menu == "📊 完整工時報表":
        st.header("📊 完整工時報表")
        raw_logs = get_db("work_logs")
        if raw_logs:
            df = pd.DataFrame.from_dict(raw_logs, orient='index').reset_index(drop=True)
            cols = ["狀態", "製令", "P/N", "Type", "工段名稱", "工號", "姓名", "開始時間", "結束時間", "累計工時"]
            existing = [c for c in cols if c in df.columns]
            df_display = df[existing]
            if "結束時間" in df_display.columns:
                df_display = df_display.sort_values(by="結束時間", ascending=False)
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("目前尚無報工紀錄。")
