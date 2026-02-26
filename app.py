import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd

# --- 1. 初始化網頁配置 ---
st.set_page_config(page_title="數位生產戰情室", layout="wide")

# --- 2. Firebase 連線 (核心修復：解決第 28 行語法錯誤與金鑰驗證失敗) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # 使用你提供的新金鑰，解決 Invalid JWT Signature 錯誤
        firebase_key = {
            "type": "service_account",
            "project_id": "my-factory-system",
            "private_key_id": "3bae8750275ed86061094ed09cfb12dcb500802f",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDE28hhl2Z0HJui\nvYImARy3BxkSmLXWyuJWSiyAKUJTHGqWKf4n0O+QQFOtboqD4Tm4jPH1I6eSVV8q\nCmXfk8XMXCKlmWr5rVfu6FMjj/V4wBBR61NA4xoMIGVwuXxTsdp/mW9JWrvFOFJ1\nKCGx1DhoEdfog1uh647wryh5UTMs2vxMFxswfz4QNSayz5Y4jD9pKFST1gcjPfzi\nzE0gqP5/mYZ6RbhFWKL2DRnqJ43xXmdeiz+uARG2MRjLNacb7PIwhPZB31auMFM/\n2kXqHJxDyMh1MPA7mO+6MVPvbKVI48T+oH1kUGoffB0itYjCJX9pmZf8gJoE97CN\nu6a/vK+9AgMBAAECggEADZUDDfCt30RQsflp7wipRtt/gwVJmSiQVdcc8OQShmdx\n1ysjNPNjw/Zxj4gOmIDD7xQSZuZvMQJ2OWaplrO8Xu2FxRqBA075aoCu/nIimT0v\nIxJzFl6qNRH7IxGOdBEo+8rF9IVaaoYInRAIGxvYSciJYVUcJQolPOfo3qNCk6KS\nhePekkbOpkW6uveYTqfdOItoKhvcyCINghqK2arPwAZckwn3BOH5QaSmOK2KEaSu\na6K/2Gx7ALliBNLMazgkAnBrft8MhpEL/nqpgrJEJq+7jRNrLp0XKZuz4oQY9bMw\nLJil0Rx/tW6LVLS3pXvAQwPp464Cn5xmFQ7o9dJqpQKBgQDx8d0HC6KW0DHKs9YD\QL8n1nztfQmwU4pumYCNikDLzEUAZD1R+EGAIsNwvDPwyxqjdsAlmClRd16d9cuf\n3kV3AQjpn6vHwmN+2CjS0dhV7h/79twpjAXkhlscq0lrrMKAlmAofD664OqiY7U7\nkdaxkIibCTubRN29hXsgLAb+1wKBgQDQS2ivfacPjTde5o4LUeyw4rVTt0j1L6zl\nOKED37AKFAFvChgPZ1xZ2/STAVBT9ADqq25H0kzKWWj2K4Tem7MwFFdPH1SP3hqz\ntSnpKD7A/K8bhZRqxuKG3plhz3PR1/verhG7YHSHJSbw6LSuERIlDNw++BGW19wt\n8aTKxu0XiwKBgCX917pKfm52JMtyr9F08k9cI+Pa9ZGFnMA/RGt1YTVfTxp/ow1j\nEU4Ap3XlZ7aQ/g7bD9MXcK2FNAtT1HS3H2tPc0nUM9I7WQpLASYRo4niyYz0N6Ai\nh65Z1qbK0s2gpC4y7siMsgEAXne/dm7zOKZLTtghfAWmq7cd5baokzSjAoGAZ8II\npdKL051exbFHdLAcnYhxFwCoISrcj1qEKq/Uu1B33l5C2fl88W42CLyQzSExC7TV\nvIUvp2SeenH3QASDYCHh1BIhR4E1/+rws6pOiEfW2njSE9Z6pQBhm22BnjheyPAg\n+Rv1MBT7runchxEN3tLnK57a9C8XCPPkSPaKyD0CgYEAu24+aG2kyix8EfOxqbGu\nwXQXiPC5wYgE3v2fY40mkjxCBk0SOZ3ZvTFLAYCQpHgQIQsv/8S2SrJk+DEE6RfA\nF+zDnCSdtpZ02bHRJGNtBUOIfTpc4wdv7gZZ+puzHY6pQc+Am/9yTzxR9UhnVRST\nWzwfe2GCmiwKKXP15szlgFE=\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-fbsvc@my-factory-system.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        cred = credentials.Certificate(firebase_key)
        # 修正第 28 行：確保引號完整閉合以消除 SyntaxError
        firebase_admin.initialize_app(cred, {'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/"})

init_firebase()

# --- 3. 穩定讀取帳號 ---
def get_user_list():
    try:
        u = db.reference('users').get()
        return u if u else {"管理員": "8888"}
    except: return {"管理員": "8888"}

# --- 4. 登入介面 ---
user_list = get_user_list()

if "user" not in st.session_state:
    st.title("🏭 生產管理系統 - 登入入口")
    with st.container(border=True):
        st.subheader("👤 員工報工入口")
        # 整合帳號清單
        name = st.selectbox("請選擇姓名", list(user_list.keys()))
        code = st.text_input("輸入代碼", type="password")
        if st.button("員工登入", use_container_width=True):
            if user_list.get(name) == code:
                st.session_state.user = name
                st.rerun()
            else: st.error("❌ 代碼錯誤")
else:
    # --- 5. 系統主畫面 ---
    st.sidebar.write(f"當前使用者: **{st.session_state.user}**")
    if st.sidebar.button("登出系統"):
        del st.session_state.user
        st.rerun()

    # --- 管理員戰情看板 (保留截圖中的統計功能) ---
    if st.session_state.user == "管理員":
        st.header("📊 數位戰情室儀表板")
        logs = db.reference('production_logs').get()
        if logs:
            df = pd.DataFrame.from_dict(logs, orient='index')
            m1, m2, m3 = st.columns(3)
            # 統計彩色大數字看板
            m1.metric("🔥 現場作業中", f"{len(df[df['狀態'] == '作業中']['姓名'].unique())} 人")
            m2.metric("🏗️ 進行中製令", f"{len(df[df['狀態'] == '作業中']['製令'].unique())} 案")
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            m3.metric("✅ 今日完工", f"{len(df[(df['日期'] == today_str) & (df['狀態'] == '完工')])} 筆")
            st.dataframe(df.tail(10), use_container_width=True)
        
        st.divider()
        st.subheader("👤 帳號管理 (新增人員)")
        with st.container(border=True):
            ca, cb = st.columns(2)
            new_n = ca.text_input("新員工姓名")
            new_c = cb.text_input("設定員工代碼")
            if st.button("✨ 建立新帳號並同步"):
                if new_n and new_c:
                    try:
                        db.reference(f'users/{new_n}').set(new_c)
                        st.success(f"✅ 「{new_n}」帳號同步成功！")
                    except Exception as e: st.error(f"寫入失敗：{e}")
        st.divider()

    # --- 報工填寫區 (修復第 111 行語法錯誤) ---
    st.header("📝 生產日報回報")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st_val = st.selectbox("狀態 (A)", ["作業中", "完工", "暫停", "下班"])
            order = st.text_input("製令單號 (B)", placeholder="例如: 25M0497-03")
            proc = st.text_input("工段名稱 (E)")
        with c2:
            pn = st.text_input("P/N (C)")
            tp = st.text_input("Type (D)")
            wid = st.text_input("工號 (F)")
        
        if st.button("🚀 提交紀錄", use_container_width=True):
            try:
                now = datetime.datetime.now()
                db.reference('production_logs').push({
                    "狀態": st_val, "姓名": st.session_state.user, "製令": order,
                    "PN": pn, "工段": proc, "工號": wid, "Type": tp,
                    "日期": now.strftime("%Y-%m-%d"), "時間": now.strftime("%H:%M:%S")
                })
                st.success("✅ 提交紀錄成功！")
            except Exception as e: st.error(f"連線異常：{e}")
