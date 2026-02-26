import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd

# --- 1. 網頁配置 ---
st.set_page_config(page_title="數位生產戰情看板", layout="wide")

# --- 2. Firebase 連線 (修復 Invalid JWT Signature) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # 這裡直接處理金鑰，確保不因換行符號報錯
        pk = "-----BEGIN PRIVATE KEY-----\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQC+TW76EuAmGqxR\n9hUmQ7dWvUSJx8qOlLsm47FM6VrzMNreaBnCKaK7VySL8iXLfiuvcfCu/9doXsG0\nuz95UN3EyK6Wh1O9DQvIHUIPC7v0P7hmdjTYBISbmcqmttbgJX62v3LLgsbEP+sN\nQcetmhpzGG+OkvDQlsE+cB1BMLRGqT9PhqrIV4zQw4Iz/ITyljfzumXfwpei9YFJ\nGw3Ndeu7WJHV3qg6UiwPCTpG0nu3t80KdaeKaZfpGD5iMd3WyoEhkvTitD83mx+s\nxjGilGygZX5+SdfKwRyi1baOmtS6A8T2lLRTxfsncoNffrH//zoQOuwXYCJyMN8F\nCVMnOWp1AgMBAAECgf9cc8LXJvimglu8h5V0vE9inbxJABfAr5yGvB4TNDm66pCF\nwA1a5kGWWxg8ZC3OjQFz1WfVDB9IQALACc3stmMnbDQwXE+fnccINDazSN5Maphy\nTWvcZ+TMVHCIKhHMwDcEdIvf6/FV+pKPn22OOgJ8IgWWEWlHJX9AenLdy243K/0C\nGM1CENv11SOT3465GHd7048A9pZn0WDFQQeiXYvqnniW1aHjOfcSiwcNE0sjmRUA\nMhBn8xor965wUPDer+qnyOQPBvgZiShJ3PQrq+FOJ8V6eGqQn/9LAHIeheGtmuVP\nUqMVGlYzQa6K8etTZ6bG0YUxxSDjsoxGe6NxEc0CgYEA5KouCwffJBjLnyU668FA\nCtnfcKJY2nvXUlMCPYAzP2KbECIsRnz3Z5DFr9bNhx8GHGD/+vT3nURnTLGbJ7zT\n3nDsPT86hSB+J/5ti5H/UPVD2rfPq339c6woY5IWGyq4+bwORFxGlRVHrx04DYbs\n1Ojut+C8CZyC1b9rIIBzKcMCgYEA1Q1A9lBMBeO80Z3y2aoYeZu+dIjPDR9sGH5R\nR31AgGylfAfFa/65EafLxOGMRBgsTycfBmRhAnwKbcq+b9Mw/mdfTFFf5RSPKZk9\n2Cjm7HpRbroiYqngAYZ3YvvyzMwXz4vdqGrIez9egUax3YK8PKX8xEw+xGETBKDz\nVmuHH2cCgYBi5DKLdLkNTGfriNdllCsVRkp61Mtmmf5yTRH/9Qy00flLzeumBG+e\n656DQHucf09OQKkUKJNaAXZHVdxLID/kyKNyjYDKiFXnCALqRJbNtXTGB46ZlSBi\nwUaqYUiMMTrUTn9BE0M3QH/C/Pj76KlOHvr2rQvFgFmZBXLYGJU1rwKBgCR82JtW\ntS5tCnF785ODph1tpvieVZeRwhmPyKvNr7ZO5SiQzCbqwRdc/XECj9s5qJ0FvjKC\nDns2czLKfkL4kHOBkLipVxsMolglfon+t03YxQmJ0nufgbE2L2DGNoqOgm5koS9\nhQhWmgDZ8qxVL5fTda7IwBcx6OfqCMLMN6ARAoGBAI/cljGsbWos3vpljC58T/PW\nEcLHY13XEDqZyRJIAFH/BFjhe7R1Npj/5YKr+u+or1TCE4oit7JqXuTQG/UF1wGW\nEdwli7ADexZRA03ufrQm9SiLrfLiSsjNyDFgVPIoICAvccc1g9ST/NiduXuTpLG/\n2mkFDS9X6cKbVT2HwU04\n-----END PRIVATE KEY-----\n"
        
        firebase_config = {
            "type": "service_account",
            "project_id": "my-factory-system",
            "private_key": pk.replace('\\n', '\n'), # 關鍵修復：替換換行符號
            "client_email": "firebase-adminsdk-fbsvc@my-factory-system.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        try:
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred, {'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/"})
        except Exception as e:
            st.error(f"連線失敗，請檢查金鑰：{e}")

init_firebase()

# --- 3. 穩定讀取 ---
def get_users():
    try:
        u = db.reference('users').get()
        return u if u else {"管理員": "8888"}
    except:
        return {"管理員": "8888"}

# --- 4. 登入介面 ---
user_list = get_users()

if "user" not in st.session_state:
    st.title("🏭 生產管理系統 - 登入入口")
    with st.container(border=True):
        # 管理員與人員都在同一個下拉選單
        sel_user = st.selectbox("請選擇姓名", list(user_list.keys()))
        input_code = st.text_input("輸入代碼", type="password")
        if st.button("確認登入", use_container_width=True):
            if user_list.get(sel_user) == input_code:
                st.session_state.user = sel_user
                st.rerun()
            else: st.error("❌ 代碼不正確")
else:
    # --- 5. 系統功能頁面 ---
    st.sidebar.write(f"當前使用者: **{st.session_state.user}**")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 管理員看板 (對應 Excel 看板需求) ---
    if st.session_state.user == "管理員":
        st.header("📊 數位戰情室儀表板")
        logs = db.reference('production_logs').get()
        if logs:
            df = pd.DataFrame.from_dict(logs, orient='index')
            m1, m2, m3 = st.columns(3)
            # 彩色大數字指標
            m1.metric("🔥 現場作業中", f"{len(df[df['狀態'] == '作業中']['姓名'].unique())} 人")
            m2.metric("🏗️ 進行中製令", f"{len(df[df['狀態'] == '作業中']['製令'].unique())} 案")
            today = datetime.date.today().strftime("%Y-%m-%d")
            m3.metric("✅ 今日完工", f"{len(df[(df['日期'] == today) & (df['狀態'] == '完工')])} 筆")
            st.dataframe(df.tail(10), use_container_width=True)
        
        st.divider()
        # 帳號管理區 (修復截圖中的寫入失敗問題)
        st.subheader("👤 帳號管理員 (新增人員)")
        with st.container(border=True):
            cu, cp = st.columns(2)
            new_n = cu.text_input("新員工姓名")
            new_c = cp.text_input("新員工代碼")
            if st.button("✨ 建立新帳號並同步"):
                if new_n and new_c:
                    try:
                        db.reference(f'users/{new_n}').set(new_c)
                        st.success(f"✅ 帳號「{new_n}」建立成功！登出後即可在選單看到。")
                    except Exception as e:
                        st.error(f"寫入失敗，可能是權限問題：{e}")
        st.divider()

    # --- 報工填寫區 (所有身分) ---
    st.header("📝 生產報工表單")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            status = st.selectbox("狀態 (A)", ["作業中", "完工", "暫停", "下班"])
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
                    "狀態": status, "姓名": st.session_state.user, "製令": order,
                    "PN": pn, "工段": proc, "工號": wid, "Type": tp,
                    "
