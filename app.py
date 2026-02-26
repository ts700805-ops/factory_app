import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 設定區 (維持無金鑰連線) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

# --- 2. 核心功能：Firebase 讀寫 ---
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
st.set_page_config(page_title="生產管理系統", layout="centered")

raw_users = get_db("users")
STAFF_DATA = raw_users if raw_users else {"管理員": "8888"}

# --- 4. 登入系統 ---
if "user" not in st.session_state:
    st.title("🔐 員工系統登入")
    with st.form("login_form"):
        input_name = st.selectbox("請選擇您的姓名", list(STAFF_DATA.keys()))
        input_code = st.text_input("請輸入員工代碼", type="password")
        if st.form_submit_button("登入系統", use_container_width=True):
            if str(STAFF_DATA.get(input_name)) == input_code:
                st.session_state.user = input_name
                # 當員工登入時，自動記錄「開始時間」在當前階段
                st.session_state.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.rerun()
            else: st.error("❌ 代碼錯誤")
else:
    # --- 5. 已登入介面 ---
    st.sidebar.write(f"👤 使用者：{st.session_state.user}")
    st.sidebar.write(f"⏰ 本次開始時間：{st.session_state.get('start_time', '未記錄')}")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 6. 管理員專區：建立帳號 ---
    if st.session_state.user == "管理員":
        st.header("👤 系統帳號管理")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            new_n = c1.text_input("新員工姓名")
            new_c = c2.text_input("設定員工工號/代碼")
            if st.button("➕ 建立帳號並同步", use_container_width=True):
                if new_n and new_c:
                    save_db(f"users/{new_n}", new_c, method="put")
                    st.success(f"✅ 員工「{new_n}」建立成功！")
                    st.rerun()
        st.divider()

    # --- 7. 報工功能 (補齊所有要求的欄位) ---
    st.title(f"🏗️ {st.session_state.user} - 工時回報")
    with st.container(border=True):
        st.info(f"您的作業開始於：{st.session_state.get('start_time', 'N/A')}")
        hours = st.number_input("今日累計工時 (hr)", min_value=0.5, max_value=24.0, step=0.5, value=8.0)
        
        if st.button("🚀 提交紀錄", use_container_width=True):
            now_end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_code = STAFF_DATA.get(st.session_state.user, "N/A")
            start_t = st.session_state.get('start_time', now_end) # 如果沒抓到就用現在
            
            # 依照你要求的格式建立資料
            log_data = {
                "工號": user_code,
                "姓名": st.session_state.user,
                "開始時間": start_t,
                "結束時間": now_end,
                "累計工時": hours
            }
            save_db("work_logs", log_data)
            st.success("✅ 紀錄已成功提交！")
            st.balloons()

    # --- 8. 管理員報表：嚴格執行指定的格式排序 ---
    if st.session_state.user == "管理員":
        st.divider()
        st.subheader("📊 完整工時報表 (格式校正版)")
        raw_logs = get_db("work_logs")
        if raw_logs:
            df = pd.DataFrame.from_dict(raw_logs, orient='index')
            
            # 定義你要的正確順序
            correct_order = ["工號", "姓名", "開始時間", "結束時間", "累計工時"]
            
            # 檢查資料庫是否具備這些欄位，避免報錯
            existing_cols = [c for c in correct_order if c in df.columns]
            df_display = df[existing_cols]
            
            # 依照結束時間排序（最新的在最上面）
            if "結束時間" in df_display.columns:
                df_display = df_display.sort_values(by="結束時間", ascending=False)
            
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("目前尚無報工紀錄。")
