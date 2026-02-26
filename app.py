import streamlit as st
import pandas as pd
import datetime
import firebase_admin
from firebase_admin import credentials, db
import requests

# --- 1. Firebase 初始化 (解決資料不可被清除的問題) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # 請確保這裡使用的是你之前提到的 3bae875 新金鑰內容
        firebase_key = {
            "type": "service_account",
            "project_id": "my-factory-system",
            "private_key_id": "3bae8750275ed86061094ed09cfb12dcb500802f",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDE28hhl2Z0HJui\nvYImARy3BxkSmLXWyuJWSiyAKUJTHGqWKf4n0O+QQFOtboqD4Tm4jPH1I6eSVV8q\nCmXfk8XMXCKlmWr5rVfu6FMjj/V4wBBR61NA4xoMIGVwuXxTsdp/mW9JWrvFOFJ1\nKCGx1DhoEdfog1uh647wryh5UTMs2vxMFxswfz4QNSayz5Y4jD9pKFST1gcjPfzi\nzE0gqP5/mYZ6RbhFWKL2DRnqJ43xXmdeiz+uARG2MRjLNacb7PIwhPZB31auMFM/\n2kXqHJxDyMh1MPA7mO+6MVPvbKVI48T+oH1kUGoffB0itYjCJX9pmZf8gJoE97CN\nu6a/vK+9AgMBAAECggEADZUDDfCt30RQsflp7wipRtt/gwVJmSiQVdcc8OQShmdx\n1ysjNPNjw/Zxj4gOmIDD7xQSZuZvMQJ2OWaplrO8Xu2FxRqBA075aoCu/nIimT0v\nIxJzFl6qNRH7IxGOdBEo+8rF9IVaaoYInRAIGxvYSciJYVUcJQolPOfo3qNCk6KS\nhePekkbOpkW6uveYTqfdOItoKhvcyCINghqK2arPwAZckwn3BOH5QaSmOK2KEaSu\na6K/2Gx7ALliBNLMazgkAnBrft8MhpEL/nqpgrJEJq+7jRNrLp0XKZuz4oQY9bMw\nLJil0Rx/tW6LVLS3pXvAQwPp464Cn5xmFQ7o9dJqpQKBgQDx8d0HC6KW0DHKs9YD\QL8n1nztfQmwU4pumYCNikDLzEUAZD1R+EGAIsNwvDPwyxqjdsAlmClRd16d9cuf\n3kV3AQjpn6vHwmN+2CjS0dhV7h/79twpjAXkhlscq0lrrMKAlmAofD664OqiY7U7\nkdaxkIibCTubRN29hXsgLAb+1wKBgQDQS2ivfacPjTde5o4LUeyw4rVTt0j1L6zl\nOKED37AKFAFvChgPZ1xZ2/STAVBT9ADqq25H0kzKWWj2K4Tem7MwFFdPH1SP3hqz\ntSnpKD7A/K8bhZRqxuKG3plhz3PR1/verhG7YHSHJSbw6LSuERIlDNw++BGW19wt\n8aTKxu0XiwKBgCX917pKfm52JMtyr9F08k9cI+Pa9ZGFnMA/RGt1YTVfTxp/ow1j\nEU4Ap3XlZ7aQ/g7bD9MXcK2FNAtT1HS3H2tPc0nUM9I7WQpLASYRo4niyYz0N6Ai\nh65Z1qbK0s2gpC4y7siMsgEAXne/dm7zOKZLTtghfAWmq7cd5baokzSjAoGAZ8II\npdKL051exbFHdLAcnYhxFwCoISrcj1qEKq/Uu1B33l5C2fl88W42CLyQzSExC7TV\nvIUvp2SeenH3QASDYCHh1BIhR4E1/+rws6pOiEfW2njSE9Z6pQBhm22BnjheyPAg\n+Rv1MBT7runchxEN3tLnK57a9C8XCPPkSPaKyD0CgYEAu24+aG2kyix8EfOxqbGu\nwXQXiPC5wYgE3v2fY40mkjxCBk0SOZ3ZvTFLAYCQpHgQIQsv/8S2SrJk+DEE6RfA\nF+zDnCSdtpZ02bHRJGNtBUOIfTpc4wdv7gZZ+puzHY6pQc+Am/9yTzxR9UhnVRST\nWzwfe2GCmiwKKXP15szlgFE=\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-fbsvc@my-factory-system.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/"
        })

init_firebase()

# --- 2. 核心功能：從 Firebase 讀取與儲存 ---
def load_staff_data():
    try:
        users = db.reference('users').get()
        return users if users else {"管理員": "8888"}
    except:
        return {"管理員": "8888"}

def load_work_logs():
    try:
        logs = db.reference('work_logs').get()
        if logs:
            return pd.DataFrame.from_dict(logs, orient='index')
        return pd.DataFrame(columns=["紀錄時間", "姓名", "工時(hr)"])
    except:
        return pd.DataFrame(columns=["紀錄時間", "姓名", "工時(hr)"])

def save_work_log(name, hours):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.reference('work_logs').push({
        "紀錄時間": now,
        "姓名": name,
        "工時(hr)": hours
    })
    return now

# --- 3. 頁面配置 ---
st.set_page_config(page_title="員工工時管理系統", layout="centered")
STAFF_DATA = load_staff_data()

# --- 4. 登入系統 ---
if "user" not in st.session_state:
    st.title("🔐 員工系統登入")
    with st.form("login_form"):
        input_name = st.selectbox("請選擇您的姓名", list(STAFF_DATA.keys()))
        input_code = st.text_input("請輸入員工代碼", type="password")
        if st.form_submit_button("登入系統", use_container_width=True):
            if STAFF_DATA.get(input_name) == input_code:
                st.session_state.user = input_name
                st.rerun()
            else:
                st.error("❌ 代碼錯誤")
else:
    # --- 5. 已登入介面 ---
    st.sidebar.write(f"👤 當前使用者：{st.session_state.user}")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    st.title(f"🏗️ {st.session_state.user} - 工時回報")
