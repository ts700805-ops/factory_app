import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd
import requests

# 設定
st.set_page_config(page_title="自主管理工時系統", layout="wide")

# --- 1. Firebase 連線 (用來儲存帳號名單與工時，確保不遺失) ---
if not firebase_admin._apps:
    try:
        firebase_key = {
            "type": "service_account",
            "project_id": "my-factory-system",
            "private_key_id": "c57de9a722e669103746d6fe9c185a9682227944",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQC+TW76EuAmGqxR\n9hUmQ7dWvUSJx8qOlLsm47FM6VrzMNreaBnCKaK7VySL8iXLfiuvcfCu/9doXsG0\nuz95UN3EyK6Wh1O9DQvIHUIPC7v0P7hmdjTYBISbmcqmttbgJX62v3LLgsbEP+sN\nQcetmhpzGG+OkvDQlsE+cB1BMLRGqT9PhqrIV4zQw4Iz/ITyljfzumXfwpei9YFJ\nGw3Ndeu7WJHV3qg6UiwPCTpG0nu3t80KdaeKaZfpGD5iMd3WyoEhkvTitD83mx+s\nxjGilGygZX5+SdfKwRyi1baOmtS6A8T2lLRTxfsncoNffrH//zoQOuwXYCJyMN8F\nCVMnOWp1AgMBAAECgf9cc8LXJvimglu8h5V0vE9inbxJABfAr5yGvB4TNDm66pCF\nwA1a5kGWWxg8ZC3OjQFz1WfVDB9IQALACc3stmMnbDQwXE+fnccINDazSN5Maphy\nTWvcZ+TMVHCIKhHMwDcEdIvf6/FV+pKPn22OOgJ8IgWWEWlHJX9AenLdy243K/0C\nGM1CENv11SOT3465GHd7048A9pZn0WDFQQeiXYvqnniW1aHjOfcSiwcNE0sjmRUA\nMhBn8xor965wUPDer+qnyOQPBvgZiShJ3PQrq+FOJ8V6eGqQn/9LAHIeheGtmuVP\nUqMVGlYzQa6K8etTZ6bG0YUxxSDjsoxGe6NxEc0CgYEA5KouCwffJBjLnyU668FA\nCtnfcKJY2nvXUlMCPYAzP2KbECIsRnz3Z5DFr9bNhx8GHGD/+vT3nURnTLGbJ7zT\n3nDsPT86hSB+J/5ti5H/UPVD2rfPq339c6woY5IWGyq4+bwORFxGlRVHrx04DYbs\n1Ojut+C8CZyC1b9rIIBzKcMCgYEA1Q1A9lBMBeO80Z3y2aoYeZu+dIjPDR9sGH5R\nR31AgGylfAfFa/65EafLxOGMRBgsTycfBmRhAnwKbcq+b9Mw/mdfTFFf5RSPKZk9\n2Cjm7HpRbroiYqngAYZ3YvvyzMwXz4vdqGrIez9egUax3YK8PKX8xEw+xGETBKDz\nVmuHH2cCgYBi5DKLdLkNTGfriNdllCsVRkp61Mtmmf5yTRH/9Qy00flLzeumBG+e\n656DQHucf09OQKkUKJNaAXZHVdxLID/kyKNyjYDKiFXnCALqRJbNtXTGB46ZlSBi\nwUaqYUiMMTrUTn9BE0M3QH/C/Pj76KlOHvr2rQvFgFmZBXLYGJU1rwKBgCR82JtW\ntS5tCnF785ODph1tpvieVZeRwhmPyKvNr7ZO5SiQzCbqwRdc/XECj9s5qJ0FvjKC\nDns2czLKfkL4kHOBkLipVxsMolglfon+t03YxQmJ0nufgbE2L2DGNoqOgm5koS9\nhQhWmgDZ8qxVL5fTda7IwBcx6OfqCMLMN6ARAoGBAI/cljGsbWos3vpljC58T/PW\nEcLHY13XEDqZyRJIAFH/BFjhe7R1Npj/5YKr+u+or1TCE4oit7JqXuTQG/UF1wGW\nEdwli7ADexZRA03ufrQm9SiLrfLiSsjNyDFgVPIoICAvccc1g9ST/NiduXuTpLG/\n2mkFDS9X6cKbVT2HwU04\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-fbsvc@my-factory-system.iam.gserviceaccount.com",
            "client_id": "101286242423091218106",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40my-factory-system.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred, {'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/"})
    except: pass

# --- 2. 核心功能庫 ---
def get_users():
    users = db.reference('users').get()
    return users if users else {"管理員": "8888"} # 預設管理員

def send_line(msg):
    # 如果你有 Token 再填入即可
    token = "這裡填入你的LineToken"
    if token != "這裡填入你的LineToken":
        requests.post("https://notify-bot.line.me/api/notify", headers={"Authorization": f"Bearer {token}"}, data={"message": msg})

# --- 3. 登入介面 ---
if "user" not in st.session_state:
    st.title("🔐 系統登入")
    user_list = get_users()
    name = st.selectbox("請選擇姓名", list(user_list.keys()))
    code = st.text_input("請輸入代碼", type="password")
    if st.button("進入系統", use_container_width=True):
        if user_list[name] == code:
            st.session_state.user = name
            st.rerun()
        else:
            st.error("❌ 代碼錯誤")
else:
    # --- 4. 登入後的畫面 ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("切換帳號/登出"):
        del st.session_state.user
        st.rerun()

    # --- 功能 A：員工報工區 ---
    st.header("🏗️ 工時回報")
    with st.container(border=True):
        hours = st.number_input("今日時數", min_value=0.5, max_value=24.0, step=0.5, value=8.0)
        if st.button("🚀 提交紀錄", use_container_width=True):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.reference('work_logs').push({"name": st.session_state.user, "hours": hours, "time": now})
            send_line(f"\n📢 工時回報：{st.session_state.user}\n時數：{hours}\n時間：{now}")
            st.success("紀錄已存檔！")
            st.balloons()

    # --- 功能 B：管理員專區 (只有「管理員」可以看到帳號管理) ---
    if st.session_state.user == "管理員":
        st.divider()
        st.header("⚙️ 管理員後台")
        
        tab1, tab2 = st.tabs(["👤 帳號管理", "📊 工時報表"])
        
        with tab1:
            st.subheader("建立新帳號")
            new_name = st.text_input("新員工姓名")
            new_code = st.text_input("設定新代碼 (數字)")
            if st.button("➕ 建立帳號"):
                if new_name and new_code:
                    db.reference(f'users/{new_name}').set(new_code)
                    st.success(f"帳號 {new_name} 建立成功！")
                    st.rerun()
            
            st.subheader("目前員工名單")
            current_users = get_users()
            for u_name, u_code in current_users.items():
                col_u1, col_u2 = st.columns([3, 1])
                col_u1.write(f"員工：{u_name} (代碼：{u_code})")
                if u_name != "管理員": # 不讓自己刪除自己
                    if col_u2.button("刪除", key=f"del_{u_name}"):
                        db.reference(f'users/{u_name}').delete()
                        st.rerun()

        with tab2:
            all_logs = db.reference('work_logs').get()
            if all_logs:
                df = pd.DataFrame.from_dict(all_logs, orient='index')[['time', 'name', 'hours']]
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載 Excel", data=csv, file_name="report.csv")
