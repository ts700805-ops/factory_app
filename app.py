import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd
import requests

# 設定網頁
st.set_page_config(page_title="生產工時管理系統", layout="wide")

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

# --- 2. 資料功能 ---
def get_users():
    u = db.reference('users').get()
    return u if u else {"管理員": "8888"}

# --- 3. 登入系統 ---
if "user" not in st.session_state:
    st.title("🏭 生產管理系統登入")
    user_list = get_users()
    name = st.selectbox("選擇姓名", list(user_list.keys()))
    code = st.text_input("輸入代碼", type="password")
    if st.button("登入"):
        if user_list[name] == code:
            st.session_state.user = name
            st.rerun()
        else: st.error("代碼錯誤")
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("登出"):
        del st.session_state.user
        st.rerun()

    # --- 功能 A：生產回報 (仿 Excel 欄位) ---
    st.header("📝 生產日報回報")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            status = st.selectbox("狀態", ["作業中", "完工", "暫停", "下班"])
        with c2:
            order_no = st.text_input("製令單號 (B)", placeholder="例如: 25M0497-03")
        with c3:
            process_name = st.text_input("工段名稱 (E)", placeholder="例如: 配電/模組")
        
        c4, c5 = st.columns(2)
        with c4:
            part_no = st.text_input("P/N (C)")
        with c5:
            work_hours = st.number_input("當前投入工時", min_value=0.0, step=0.5, value=1.0)

        remark = st.text_area("備註 (J)")

        if st.button("✅ 提交紀錄 (寫入雲端)", use_container_width=True):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.reference('production_logs').push({
                "狀態": status, "姓名": st.session_state.user, "製令": order_no,
                "PN": part_no, "工段": process_name, "工時": work_hours,
                "備註": remark, "日期時間": now
            })
            st.success("紀錄已成功存檔！")
            st.balloons()

    # --- 功能 B：管理員後台 (建立帳號 + 完整表單) ---
    if st.session_state.user == "管理員":
        st.divider()
        st.header("⚙️ 管理員後台")
        t1, t2 = st.tabs(["👥 帳號管理", "📊 完整生產報表"])
        
        with t1:
            st.subheader("建立新員工")
            n_name = st.text_input("員工姓名")
            n_code = st.text_input("設定代碼")
            if st.button("建立"):
                if n_name and n_code:
                    db.reference(f'users/{n_name}').set(n_code)
                    st.rerun()
            
            st.write("目前名單：", list(get_users().keys()))

        with t2:
            all_data = db.reference('production_logs').get()
            if all_data:
                df = pd.DataFrame.from_dict(all_data, orient='index')
                # 重新排序列，對應你的 Excel
                cols = ["日期時間", "狀態", "製令", "工段", "姓名", "工時", "備註"]
                df = df[cols]
                st.dataframe(df, use_container_width=True)
                
                # 下載按鈕
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載完整報表 (Excel可用)", data=csv, file_name="production_report.csv")
            else:
                st.info("尚無紀錄")
