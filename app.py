import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd

# --- 1. 網頁基礎配置 ---
st.set_page_config(page_title="數位生產戰情室", layout="wide")

# --- 2. Firebase 連線 (強化重連機制，防止 RefreshError) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # 修正 image_de0f6e.png 提到的語法與引號問題
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

init_firebase()

# --- 3. 核心功能 ---
def safe_db_get(path):
    """安全抓取資料，防止 RefreshError"""
    try:
        return db.reference(path).get()
    except:
        return None

# --- 4. 登入介面 ---
st.title("🏭 生產管理系統")
user_data = safe_db_get('users')
user_list = user_data if user_data else {"管理員": "8888"}

if "user" not in st.session_state:
    with st.container(border=True):
        st.subheader("👤 系統登入")
        name = st.selectbox("請選擇姓名", list(user_list.keys()))
        code = st.text_input("輸入員工代碼", type="password")
        if st.button("確認進入", use_container_width=True):
            if user_list.get(name) == code:
                st.session_state.user = name
                st.rerun()
            else: st.error("❌ 代碼錯誤")
else:
    # --- 5. 登入後的主畫面 ---
    st.sidebar.write(f"當前使用者: **{st.session_state.user}**")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 管理員區 (戰情看板 + 帳號管理) ---
    if st.session_state.user == "管理員":
        # 1. 戰情室大數字
        st.header("📊 數位戰情看板")
        logs = safe_db_get('production_logs')
        if logs:
            df = pd.DataFrame.from_dict(logs, orient='index')
            m1, m2, m3 = st.columns(3)
            m1.metric("🔥 現場作業中", f"{len(df[df['狀態'] == '作業中']['姓名'].unique())} 人")
            m2.metric("🏗️ 進行中製令", f"{len(df[df['狀態'] == '作業中']['製令'].unique())} 案")
            today = datetime.date.today().strftime("%Y-%m-%d")
            m3.metric("✅ 今日完工", f"{len(df[(df['日期'] == today) & (df['狀態'] == '完工')])} 筆")
            
            st.subheader("💡 現場動態表格")
            latest = df.sort_values('時間').groupby('姓名').tail(1)
            st.dataframe(latest[['姓名', '狀態', '製令', '工段', '時間']], use_container_width=True)
        
        st.divider()
        # 2. 帳號管理區 (解決 image_dd40c0.png 錯誤)
        st.header("👤 系統帳號管理 (新增人員)")
        with st.container(border=True):
            col_u1, col_u2 = st.columns(2)
            new_n = col_u1.text_input("輸入新員工姓名", key="new_name")
            new_c = col_u2.text_input("設定員工代碼", key="new_code")
            if st.button("✨ 建立新帳號並同步"):
                if new_n and new_c:
                    try:
                        db.reference(f'users/{new_n}').set(new_c)
                        st.success(f"✅ 「{new_n}」建立成功！請登出後確認選單。")
                        # 這裡不強迫 rerun，讓使用者看清成功訊息
                    except Exception as e:
                        st.error(f"寫入失敗，請稍後再試：{e}")
                else: st.warning("請完整填寫姓名與代碼")
        st.divider()

    # --- 報工表單 (對應 Excel 欄位) ---
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
            now = datetime.datetime.now()
            db.reference('production_logs').push({
                "狀態": st_val, "姓名": st.session_state.user, "製令": order,
                "PN": pn, "工段": proc, "工號": wid, "Type": tp,
                "日期": now.strftime("%Y-%m-%d"), "時間": now.strftime("%H:%M:%S")
            })
            st.success("✅ 紀錄已同步！")
