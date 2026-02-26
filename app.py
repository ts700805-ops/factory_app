import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd
import requests

# --- 網頁配置 ---
st.set_page_config(page_title="數位戰情日報系統", layout="wide")

# --- 1. Firebase 連線 (自動偵測與修復模式) ---
# 這裡我幫你把金鑰直接封裝，並修正了之前可能導致 SyntaxError 的引號問題
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
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://my-factory-system-default-rtdb.firebaseio.com/"
        })
    except Exception as e:
        st.error(f"連線異常，請聯繫管理員: {e}")

# --- 2. 資料庫操作函式 ---
def get_users():
    u = db.reference('users').get()
    return u if u else {"管理員": "8888"}

def get_latest_orders():
    # 抓取最近製令單號供選取，實現防呆功能
    logs = db.reference('production_logs').order_by_key().limit_to_last(100).get()
    if logs:
        return sorted(list(set([v['製令'] for v in logs.values() if '製令' in v])))
    return []

# --- 3. 登入邏輯 ---
if "user" not in st.session_state:
    st.title("🏗️ 現場生產管理系統")
    user_list = get_users()
    name = st.selectbox("請選擇您的姓名", list(user_list.keys()))
    code = st.text_input("請輸入員工代碼", type="password")
    if st.button("登入系統", use_container_width=True):
        if user_list[name] == code:
            st.session_state.user = name
            st.rerun()
        else: st.error("代碼錯誤，請重新輸入")
else:
    # --- 4. 系統主畫面 ---
    st.sidebar.markdown(f"### 👤 使用者: {st.session_state.user}")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 戰情室儀表板 (管理員限定) ---
    if st.session_state.user == "管理員":
        st.title("📊 生產戰情看板")
        all_logs = db.reference('production_logs').get()
        if all_logs:
            df = pd.DataFrame.from_dict(all_logs, orient='index')
            today = datetime.date.today().strftime("%Y-%m-%d")
            df_today = df[df['日期'] == today]
            
            # 彩色儀表板卡片
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🔥 現場作業中", f"{len(df[df['狀態'] == '作業中']['姓名'].unique())} 人")
            m2.metric("📋 今日總筆數", f"{len(df_today)} 筆")
            m3.metric("🏗️ 運行中製令", f"{len(df[df['狀態'] == '作業中']['製令'].unique())} 案")
            m4.metric("✅ 今日完工", f"{len(df_today[df_today['狀態'] == '完工'])} 筆")
            
            # 即時動態表格
            st.subheader("💡 現場人員最新動態")
            latest_df = df.sort_values('時間').groupby('姓名').tail(1)
            st.dataframe(latest_df[['姓名', '狀態', '製令', '工段', '時間']], use_container_width=True)
        st.divider()

    # --- 員工回報區 (對應 Excel 欄位) ---
    st.header("📝 生產日報回報")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            status = st.selectbox("狀態 (A)", ["作業中", "完工", "暫停", "下班"])
        with col2:
            recent = get_latest_orders()
            order_no = st.selectbox("製令單號 (B)", ["手動輸入"] + recent)
            if order_no == "手動輸入":
                order_no = st.text_input("請輸入製令單號", placeholder="25M0497-03")
        with col3:
            process = st.text_input("工段名稱 (E)", placeholder="配電 / 模組 / 包裝")

        col4, col5, col6 = st.columns(3)
        with col4:
            part_no = st.text_input("P/N (C)", placeholder="4TRSC151-EB4L-39")
        with col5:
            type_name = st.text_input("Type (D)", placeholder="RSC151-EB4L")
        with col6:
            work_id = st.text_input("工號 (F)", placeholder="B126")

        remark = st.text_area("備註 (J)")

        if st.button("🚀 按下「開始 / 提交」紀錄", use_container_width=True):
            now = datetime.datetime.now()
            db.reference('production_logs').push({
                "狀態": status, "姓名": st.session_state.user, "製令": order_no,
                "PN": part_no, "工段": process, "工號": work_id, "Type": type_name,
                "備註": remark, "日期": now.strftime("%Y-%m-%d"), "時間": now.strftime("%H:%M:%S")
            })
            st.success(f"紀錄成功：{st.session_state.user} - {order_no} ({status})")
            st.balloons()

    # --- 帳號管理 (管理員限定) ---
    if st.session_state.user == "管理員":
        with st.expander("👤 帳號密碼快速設定"):
            new_n = st.text_input("新員工姓名")
            new_c = st.text_input("新員工代碼 (數字)")
            if st.button("建立帳號"):
                if new_n and new_c:
                    db.reference(f'users/{new_n}').set(new_c)
                    st.success("建立成功！")
                    st.rerun()
