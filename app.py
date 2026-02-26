import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd

# --- 網頁配置 ---
st.set_page_config(page_title="數位生產戰情室", layout="wide")

# --- 1. Firebase 連線 (已修正語法引號問題) ---
if not firebase_admin._apps:
    try:
        # 請確保這裡的資訊與你的 Firebase 金鑰完全一致
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
        # 注意：URL 最後必須有引號結尾
        firebase_admin.initialize_app(cred, {'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/"})
    except Exception as e:
        st.error(f"連線失敗，請檢查金鑰：{e}")

# --- 2. 核心功能 ---
def get_users():
    try:
        u = db.reference('users').get()
        return u if u else {"管理員": "8888"}
    except: return {"管理員": "8888"}

# --- 3. 登入介面 ---
if "role" not in st.session_state:
    st.title("🏭 生產管理系統 - 登入入口")
    col_emp, col_adm = st.columns(2)
    
    with col_emp:
        with st.container(border=True):
            st.header("👷 員工報工入口")
            user_list = get_users()
            emp_name = st.selectbox("請選擇姓名", list(user_list.keys()))
            emp_code = st.text_input("輸入代碼", type="password", key="e_code")
            if st.button("員工登入", use_container_width=True):
                if user_list.get(emp_name) == emp_code:
                    st.session_state.role, st.session_state.user = "emp", emp_name
                    st.rerun()
                else: st.error("❌ 代碼錯誤")

    with col_adm:
        with st.container(border=True):
            st.header("📊 管理員戰情室")
            adm_code = st.text_input("最高權限代碼", type="password", key="a_code")
            if st.button("管理員登入", use_container_width=True):
                if adm_code == "8888":
                    st.session_state.role, st.session_state.user = "admin", "管理員"
                    st.rerun()
                else: st.error("❌ 密碼錯誤")
else:
    # --- 4. 登入後 ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("登出系統"):
        del st.session_state.role
        st.rerun()

    if st.session_state.role == "admin":
        st.title("📊 即時生產戰情看板")
        # 儀表板 logic... (大數字指標)
        all_logs = db.reference('production_logs').get()
        if all_logs:
            df = pd.DataFrame.from_dict(all_logs, orient='index')
            c1, c2, c3 = st.columns(3)
            c1.metric("🔥 目前作業人數", f"{len(df[df['狀態'] == '作業中']['姓名'].unique())} 人")
            c2.metric("🏗️ 運行中製令", f"{len(df[df['狀態'] == '作業中']['製令'].unique())} 案")
            c3.metric("✅ 今日完工", f"{len(df[df['日期'] == datetime.date.today().strftime('%Y-%m-%d')][df['狀態'] == '完工'])} 筆")
            st.subheader("💡 現場最新動態表格")
            st.dataframe(df.tail(10), use_container_width=True)
            
            with st.expander("👤 帳號管理員"):
                n_name = st.text_input("新員工姓名")
                n_code = st.text_input("員工代碼")
                if st.button("確認建立"):
                    db.reference(f'users/{n_name}').set(n_code)
                    st.success("成功！")
        else: st.info("尚無資料")
    else:
        # 員工填表介面 (對應 Excel 欄位)
        st.header("📝 日報填寫")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st_val = st.selectbox("狀態 (A)", ["作業中", "完工", "暫停", "下班"])
                order = st.text_input("製令單號 (B)", placeholder="例如: 25M0497-03")
                proc = st.text_input("工段名稱 (E)")
            with col2:
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
                st.success("紀錄已提交！")
