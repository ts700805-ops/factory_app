import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd
import requests

# 設定網頁
st.set_page_config(page_title="2.0 自動化工時系統", layout="wide")

# --- 1. Firebase 連線 (沿用你的正確金鑰) ---
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

# --- 2. 核心功能 ---
def get_users():
    u = db.reference('users').get()
    return u if u else {"管理員": "8888"}

def get_recent_orders():
    # 抓取最近 50 筆紀錄，用來提供製令單號自動建議
    logs = db.reference('production_logs').order_by_key().limit_to_last(50).get()
    if logs:
        return sorted(list(set([v['製令'] for v in logs.values() if '製令' in v])))
    return []

# --- 3. 登入系統 ---
if "user" not in st.session_state:
    st.title("🏭 自動化生產日報系統")
    user_list = get_users()
    name = st.selectbox("請選擇姓名", list(user_list.keys()))
    code = st.text_input("輸入員工代碼", type="password")
    if st.button("登入系統", use_container_width=True):
        if user_list[name] == code:
            st.session_state.user = name
            st.rerun()
        else: st.error("代碼錯誤")
else:
    st.sidebar.subheader(f"👤 當前員工：{st.session_state.user}")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 功能 A：生產回報區 ---
    st.header("🕒 即時生產報工")
    
    # 建立一個簡單的「開始/結束」紀錄邏輯
    with st.container(border=True):
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            status = st.selectbox("目前狀態", ["作業中", "暫停", "完工", "下班"])
        with col_s2:
            # 自動建議功能：從歷史紀錄抓取製令單號
            recent_orders = get_recent_orders()
            order_no = st.selectbox("製令單號 (選取或手動輸入)", ["手動輸入"] + recent_orders)
            if order_no == "手動輸入":
                order_no = st.text_input("請輸入新製令單號", placeholder="例如: 25M0497-03")
        with col_s3:
            process_name = st.text_input("工段名稱 (E)", placeholder="例如: 配電")

        col_s4, col_s5, col_s6 = st.columns(3)
        with col_s4:
            work_id = st.text_input("工號 (F)", placeholder="例如: B126")
        with col_s5:
            part_no = st.text_input("P/N (C)")
        with col_s6:
            type_name = st.text_input("Type (D)")

        remark = st.text_area("備註 (J)")

        if st.button("🚀 提交生產紀錄", use_container_width=True):
            now = datetime.datetime.now()
            db.reference('production_logs').push({
                "狀態": status, "姓名": st.session_state.user, "製令": order_no,
                "PN": part_no, "工段": process_name, "工號": work_id, "Type": type_name,
                "備註": remark, "日期": now.strftime("%Y-%m-%d"), "時間": now.strftime("%H:%M:%S")
            })
            st.success(f"已紀錄：{order_no} ({status})")
            st.balloons()

    # --- 功能 B：管理員後台 ---
    if st.session_state.user == "管理員":
        st.divider()
        st.header("📊 生產數據看板")
        
        # 即時看板：顯示現在誰在「作業中」
        all_logs = db.reference('production_logs').get()
        if all_logs:
            df = pd.DataFrame.from_dict(all_logs, orient='index')
            
            # 看板 1：當前現場狀態
            st.subheader("💡 現場即時動態")
            working_df = df[df['狀態'] == '作業中'].tail(10)
            if not working_df.empty:
                st.table(working_df[['姓名', '製令', '工段', '時間']])
            else:
                st.write("目前現場無人作業中。")

            # 看板 2：完整報表
            st.subheader("📋 歷史日報表")
            st.dataframe(df, use_container_width=True)
            
            # 匯出 Excel
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載 Excel 生產月報", data=csv, file_name=f"生產日報_{datetime.date.today()}.csv")
            
        # 帳號管理
        with st.expander("👤 帳號密碼管理系統"):
            n_name = st.text_input("新員工姓名")
            n_code = st.text_input("設定代碼")
            if st.button("確認建立帳號"):
                if n_name and n_code:
                    db.reference(f'users/{n_name}').set(n_code)
                    st.success("建立成功！")
                    st.rerun()
