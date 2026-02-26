import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="數位生產管理看板", layout="wide")

# --- 2. Firebase 連線 (強制修復 Invalid JWT Signature) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # 強制清理金鑰中的空格與換行錯誤
        raw_key = """-----BEGIN PRIVATE KEY-----
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
            "private_key": raw_key.replace("\\n", "\n"),
            "client_email": "firebase-adminsdk-fbsvc@my-factory-system.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        try:
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred, {'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/"})
        except Exception as e:
            st.error(f"連線失敗：{e}")

init_firebase()

# --- 3. 穩定獲取資料 ---
def get_safe_data(path):
    try:
        return db.reference(path).get()
    except:
        return None

# --- 4. 登入介面 ---
users = get_safe_data('users')
user_list = users if users else {"管理員": "8888"}

if "user" not in st.session_state:
    st.title("🏭 生產管理系統")
    with st.container(border=True):
        st.subheader("👤 系統登入")
        # 人員與管理員合併在同一個下拉選單
        sel_name = st.selectbox("請選擇您的姓名", list(user_list.keys()))
        sel_code = st.text_input("輸入代碼", type="password")
        if st.button("確認進入系統", use_container_width=True):
            if user_list.get(sel_name) == sel_code:
                st.session_state.user = sel_name
                st.rerun()
            else:
                st.error("❌ 代碼不正確")
else:
    # --- 5. 系統主畫面 ---
    st.sidebar.write(f"當前使用者: **{st.session_state.user}**")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 管理員看板 (對應 Excel 需求) ---
    if st.session_state.user == "管理員":
        st.header("📊 數位戰情看板")
        logs = get_safe_data('production_logs')
        if logs:
            df = pd.DataFrame.from_dict(logs, orient='index')
            m1, m2, m3 = st.columns(3)
            # 彩色大數字看板
            m1.metric("🔥 現場作業中", f"{len(df[df['狀態'] == '作業中']['姓名'].unique())} 人")
            m2.metric("🏗️ 進行中製令", f"{len(df[df['狀態'] == '作業中']['製令'].unique())} 案")
            today = datetime.date.today().strftime("%Y-%m-%d")
            m3.metric("✅ 今日完工", f"{len(df[(df['日期'] == today) & (df['狀態'] == '完工')])} 筆")
            st.dataframe(df.tail(5), use_container_width=True)
        
        st.divider()
        # 帳號管理：修正 image_dd3ce0.png 的錯誤
        st.subheader("👤 帳號管理員 (新增人員)")
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            n_name = col_a.text_input("新員工姓名")
            n_code = col_b.text_input("設定員工代碼")
            if st.button("✨ 建立新帳號"):
                if n_name and n_code:
                    try:
                        db.reference(f'users/{n_name}').set(n_code)
                        st.success(f"✅ 「{n_name}」帳號已同步！請點擊登出後確認選單。")
                    except Exception as e:
                        st.error(f"寫入失敗：{e}")
        st.divider()

    # --- 報工表單 ---
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
                st.success("✅ 提交成功！")
            except Exception as e:
                st.error(f"連線異常：{e}")
