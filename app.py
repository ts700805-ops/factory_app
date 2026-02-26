import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd

# --- 1. 初始化網頁 ---
st.set_page_config(page_title="生產管理系統", layout="wide")

# --- 2. Firebase 連線 (核心除錯：修復 JWT Signature 錯誤) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # 使用原始三引號字串，確保換行符號不被系統竄改
        private_key = """-----BEGIN PRIVATE KEY-----
MIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQC+TW76EuAmGqxR
9hUmQ7dWvUSJx8qOlLsm47FM6VrzMNreaBnCKaK7VySL8iXLfiuvcfCu/9doXsG0
uz95UN3EyK6Wh1O9DQvIHUIPC7v0P7hmdjTYBISbmcqmttbgJX62v3LLgsbEP+sN
QcetmhpzGG+OkvDQlsE+cB1BMLRGqT9PhqrIV4zQw4Iz/ITyljfzumXfwpei9YFJ
Gw3Ndeu7WJHV3qg6UiwPCTpG0nu3t80KdaeKaZfpGD5iMd3WyoEhkvTitD83mx+s
xjGilGygZX5+SdfKwRyi1baOmtS6A8T2lLRTxfsncoNffrH//zoQOuwXYCJyMN8F
CVMnOWp1AgMBAAECgf9cc8LXJvimglu8h5V0vE9inbxJABfAr5yGvB4TNDm66pCF
wA1a5kGWWxg8ZC3OjQFz1WfVDB9IQALACc3stmMnbDQwXE+fnccINDazSN5Maphy
TWvcZ+TMVHCIKhHMwDcEdIvf6/FV+pKPn22OOgJ8IgWWEWlHJX9AenLdy243K/0C
GM1CENv11SOT3465GHd7048A9pZn0WDFQQeiXYvqnniW1aHjOfcSiwcNE0sjmRUA
MhBn8xor965wUPDer+qnyOQPBvgZiShJ3PQrq+FOJ8V6eGqQn/9LAHIeheGtmuVP
UqMVGlYzQa6K8etTZ6bG0YUxxSDjsoxGe6NxEc0CgYEA5KouCwffJBjLnyU668FA
CtnfcKJY2nvXUlMCPYAzP2KbECIsRnz3Z5DFr9bNhx8GHGD/+vT3nURnTLGbJ7zT
3nDsPT86hSB+J/5ti5H/UPVD2rfPq339c6woY5IWGyq4+bwORFxGlRVHrx04DYbs
1Ojut+C8CZyC1b9rIIBzKcMCgYEA1Q1A9lBMBeO80Z3y2aoYeZu+dIjPDR9sGH5R
R31AgGylfAfFa/65EafLxOGMRBgsTycfBmRhAnwKbcq+b9Mw/mdfTFFf5RSPKZk9
2Cjm7HpRbroiYqngAYZ3YvvyzMwXz4vdqGrIez9egUax3YK8PKX8xEw+xGETBKDz
VmuHH2cCgYBi5DKLdLkNTGfriNdllCsVRkp61Mtmmf5yTRH/9Qy00flLzeumBG+e
656DQHucf09OQKkUKJNaAXZHVdxLID/kyKNyjYDKiFXnCALqRJbNtXTGB46ZlSBi
wUaqYUiMMTrUTn9BE0M3QH/C/Pj76KlOHvr2rQvFgFmZBXLYGJU1rwKBgCR82JtW
tS5tCnF785ODph1tpvieVZeRwhmPyKvNr7ZO5SiQzCbqwRdc/XECj9s5qJ0FvjKC
Dns2czLKfkL4kHOBkLipVxsMolglfon+t03YxQmJ0nufgbE2L2DGNoqOgm5koS9
hQhWmgDZ8qxVL5fTda7IwBcx6OfqCMLMN6ARAoGBAI/cljGsbWos3vpljC58T/PW
EcLHY13XEDqZyRJIAFH/BFjhe7R1Npj/5YKr+u+or1TCE4oit7JqXuTQG/UF1wGW
Edwli7ADexZRA03ufrQm9SiLrfLiSsjNyDFgVPIoICAvccc1g9ST/NiduXuTpLG/
2mkFDS9X6cKbVT2HwU04
-----END PRIVATE KEY-----"""
        
        firebase_config = {
            "type": "service_account",
            "project_id": "my-factory-system",
            "private_key": private_key,
            "client_email": "firebase-adminsdk-fbsvc@my-factory-system.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        try:
            cred = credentials.Certificate(firebase_config)
            # 確保資料庫 URL 引用正確，避免截圖中的 SyntaxError
            firebase_admin.initialize_app(cred, {'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/"})
        except Exception as e:
            st.error(f"連線失敗：{e}")

init_firebase()

# --- 3. 獲取資料 ---
def get_users():
    try:
        u = db.reference('users').get()
        return u if u else {"管理員": "8888"}
    except:
        return {"管理員": "8888"}

# --- 4. 登入介面 ---
user_list = get_users()

if "user" not in st.session_state:
    st.title("🏭 生產管理系統 - 登入")
    with st.container(border=True):
        name = st.selectbox("請選擇姓名", list(user_list.keys()))
        code = st.text_input("輸入代碼", type="password")
        if st.button("登入系統", use_container_width=True):
            if user_list.get(name) == code:
                st.session_state.user = name
                st.rerun()
            else:
                st.error("❌ 代碼錯誤")
else:
    # --- 5. 登入後功能 ---
    st.sidebar.write(f"當前使用者: **{st.session_state.user}**")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 管理員專區 ---
    if st.session_state.user == "管理員":
        st.header("📊 數位戰情室看板")
        logs = db.reference('production_logs').get()
        if logs:
            df = pd.DataFrame.from_dict(logs, orient='index')
            m1, m2, m3 = st.columns(3)
            # 對應 Excel 的統計看板需求
            m1.metric("🔥 現場作業中", f"{len(df[df['狀態'] == '作業中']['姓名'].unique())} 人")
            m2.metric("🏗️ 進行中製令", f"{len(df[df['狀態'] == '作業中']['製令'].unique())} 案")
            today = datetime.date.today().strftime("%Y-%m-%d")
            m3.metric("✅ 今日完工", f"{len(df[(df['日期'] == today) & (df['狀態'] == '完工')])} 筆")
            st.dataframe(df.tail(10), use_container_width=True)
        
        st.divider()
        st.subheader("👤 系統帳號管理 (新增人員)")
        with st.container(border=True):
            c_u, c_c = st.columns(2)
            new_n = c_u.text_input("輸入新員工姓名")
            new_c = c_c.text_input("設定員工代碼")
            if st.button("➕ 建立新帳號"):
                if new_n and new_c:
                    try:
                        db.reference(f'users/{new_n}').set(new_c)
                        st.success(f"✅ 「{new_n}」帳號已同步！請登出確認選單。")
                    except Exception as e:
                        st.error(f"寫入失敗：{e}")
        st.divider()

    # --- 報工填寫區 (對應 Excel 欄位) ---
    st.header("📝 生產日報回報")
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
            try:
                now = datetime.datetime.now()
                db.reference('production_logs').push({
                    "狀態": st_val, "姓名": st.session_state.user, "製令": order,
                    "PN": pn, "工段": proc, "工號": wid, "Type": tp,
                    "日期": now.strftime("%Y-%m-%d"), "時間": now.strftime("%H:%M:%S")
                })
                st.success("✅ 紀錄已成功提交！")
            except Exception as e:
                st.error(f"提交失敗：{e}")
