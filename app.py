import streamlit as st
import pandas as pd
import datetime
import requests  # 改用簡單的 requests 連線，避開 firebase_admin 的金鑰問題

# --- 1. 設定區 (只需填入網址，不需要貼上整段 JSON 金鑰) ---
#
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"

# --- 2. 核心功能：透過 REST API 讀取與儲存 (完全避開認證錯誤) ---
def get_db(path):
    try:
        # 在 Firebase 規則設為公開的情況下，直接讀取 .json 即可
        response = requests.get(f"{DB_URL}{path}.json")
        return response.json()
    except:
        return None

def save_db(path, data, method="post"):
    try:
        if method == "post":
            requests.post(f"{DB_URL}{path}.json", json=data)
        else:
            requests.put(f"{DB_URL}{path}.json", json=data)
    except:
        pass

# --- 3. 頁面配置與登入邏輯 ---
st.set_page_config(page_title="生產管理系統", layout="centered")

# 從 Firebase 獲取員工清單
raw_users = get_db("users")
STAFF_DATA = raw_users if raw_users else {"管理員": "8888"}

if "user" not in st.session_state:
    st.title("🔐 員工系統登入")
    with st.form("login_form"):
        input_name = st.selectbox("請選擇您的姓名", list(STAFF_DATA.keys()))
        input_code = st.text_input("請輸入員工代碼", type="password")
        if st.form_submit_button("登入系統", use_container_width=True):
            if str(STAFF_DATA.get(input_name)) == input_code:
                st.session_state.user = input_name
                st.rerun()
            else:
                st.error("❌ 代碼錯誤")
else:
    # --- 4. 已登入介面 ---
    st.sidebar.write(f"👤 當前使用者：{st.session_state.user}")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 5. 管理員專區：建立使用者 (放在最上方) ---
    if st.session_state.user == "管理員":
        st.header("👤 系統帳號管理")
        with st.container(border=True):
            st.write("在此建立新員工，資料將永久儲存")
            c1, c2 = st.columns(2)
            new_n = c1.text_input("新員工姓名")
            new_c = c2.text_input("設定員工工號/代碼")
            if st.button("➕ 建立帳號並同步", use_container_width=True):
                if new_n and new_c:
                    # 使用 put 直接寫入使用者節點
                    save_db(f"users/{new_n}", new_c, method="put")
                    st.success(f"✅ 員工「{new_n}」建立成功！")
                    st.rerun()
        st.divider()

    # --- 6. 報工功能 ---
    st.title(f"🏗️ {st.session_state.user} - 工時回報")
    with st.container(border=True):
        hours = st.number_input("今日工作時數", min_value=0.5, max_value=24.0, step=0.5, value=8.0)
        if st.button("🚀 提交工時", use_container_width=True):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_data = {"紀錄時間": now, "姓名": st.session_state.user, "工時(hr)": hours}
            save_db("work_logs", log_data)
            st.success("✅ 紀錄已提交！")

    # --- 7. 管理員報表 ---
    if st.session_state.user == "管理員":
        st.divider()
        st.subheader("📊 完整工時報表")
        raw_logs = get_db("work_logs")
        if raw_logs:
            df = pd.DataFrame.from_dict(raw_logs, orient='index')
            st.dataframe(df.sort_values(by="紀錄時間", ascending=False), use_container_width=True)
            
