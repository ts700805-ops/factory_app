import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd

# 設定網頁標題與寬版佈局
st.set_page_config(page_title="專業版工時管理系統", layout="wide")
st.title("🏗️ 專業版工時管理系統")

# --- 1. Firebase 連線 (內含你提供的正確金鑰) ---
if not firebase_admin._apps:
    try:
        firebase_key = {
            "type": "service_account",
            "project_id": "my-factory-system",
            "private_key_id": "c57de9a722e669103746d6fe9c185a9682227944",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQC+TW76EuAmGqxR\n9hUmQ7dWvUSJx8qOlLsm47FM6VrzMNreaBnCKaK7VySL8iXLfiuvcfCu/9doXsG0\nuz95UN3EyK6Wh1O9DQvIHUIPC7v0P7hmdjTYBISbmcqmttbgJX62v3LLgsbEP+sN\nQcetmhpzGG+OkvDQlsE+cB1BMLRGqT9PhqrIV4zQw4Iz/ITyljfzumXfwpei9YFJ\nGw3Ndeu7WJHV3qg6UiwPCTpG0nu3t80KdaeKaZfpGD5iMd3WyoEhkvTitD83mx+s\nxjGilGygZX5+SdfKwRyi1baOmtS6A8T2lLRTxfsncoNffrH//zoQOuwXYCJyMN8F\nCVMnOWp1AgMBAAECgf9cc8LXJvimglu8h5V0vE9inbxJABfAr5yGvB4TNDm66pCF\nwA1a5kGWWxg8ZC3OjQFz1WfVDB9IQALACc3stmMnbDQwXE+fnccINDazSN5Maphy\nTWvcZ+TMVHCIKhHMwDcEdIvf6/FV+pKPn22OOgJ8IgWWEWlHJX9AenLdy243K/0C\nGM1CENv11SOT3465GHd7048A9pZn0WDFQQeiXYvqnniW1aHjOfcSiwcNE0sjmRUA\nMhBn8xor965wUPDer+qnyOQPBvgZiShJ3PQrq+FOJ8V6eGqQn/9LAHIeheGtmuVP\nUqMVGlYzQa6K8etTZ6bG0YUxxSDjsoxGe6NxEc0CgYEA5KouCwffJBjLnyU668FA\nCtnfcKJY2nvXUlMCPYAzP2KbECIsRnz3Z5DFr9bNhx8GHGD/+vT3nURnTLGbJ7zT\n3nDsPT86hSB+J/5ti5H/UPVD2rfPq339c6woY5IWGyq4+bwORFxGlRVHrx04DYbs\n1Ojut+C8CZyC1b9rIIBzKcMCgYEA1Q1A9lBMBeO80Z3y2aoYeZu+dIjPDR9sGH5R\nR31AgGylfAfFa/65EafLxOGMRBgsTycfBmRhAnwKbcq+b9Mw/mdfTFFf5RSPKZk9\n2Cjm7HpRbroiYqngAYZ3YvvyzMwXz4vdqGrIez9egUax3YK8PKX8xEw+xGETBKDz\nVmuHH2cCgYBi5DKLdLkNTGfriNdllCsVRkp61Mtmmf5yTRH/9Qy00flLzeumBG+e\n656DQHucf09OQKkUKJNaAXZHVdxLID/kyKNyjYDKiFXnCALqRJbNtXTGB46ZlSBi\nwUaqYUiMMTrUTn9BE0M3QH/C/Pj76KlOHvr2rQvFgFmZBXLYGJU1rwKBgCR82JtW\ntS5tCnF785ODph1tpvieVZeRwhmPyKvNr7ZO5SiQzCbqwRdc/XECj9s5qJ0FvjKC\nDns2czLKfkL4kHOBkLipVxsMolglfon+t03YxQmJp0nufgbE2L2DGNoqOgm5koS9\nhQhWmgDZ8qxVL5fTda7IwBcx6OfqCMLMN6ARAoGBAI/cljGsbWos3vpljC58T/PW\nEcLHY13XEDqZyRJIAFH/BFjhe7R1Npj/5YKr+u+or1TCE4oit7JqXuTQG/UF1wGW\nEdwli7ADexZRA03ufrQm9SiLrfLiSsjNyDFgVPIoICAvccc1g9ST/NiduXuTpLG/\n2mkFDS9X6cKbVT2HwU04\n-----END PRIVATE KEY-----\n",
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
    except Exception:
        pass

# --- 2. 頂部看板 (今日統計) ---
try:
    all_logs = db.reference('work_logs').get()
    if all_logs:
        df_all = pd.DataFrame.from_dict(all_logs, orient='index')
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        # 篩選今天的資料
        df_today = df_all[df_all['time'].str.contains(today_str)]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("今日累積總工時", f"{df_today['hours'].sum()} 小時")
        m2.metric("今日出勤人數", len(df_today['name'].unique()))
        m3.metric("總歷史筆數", len(df_all))
except:
    pass

# --- 3. 輸入區 ---
st.divider()
with st.expander("➕ 新增今日工時", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("員工姓名")
    with c2:
        hours = st.number_input("工時", min_value=0.5, step=0.5, value=8.0)
    
    if st.button("確認存檔", use_container_width=True):
        if name:
            db.reference('work_logs').push({
                "name": name, "hours": hours,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success(f"已記錄 {name} 的工時")
            st.balloons()
            st.rerun() # 自動重新整理畫面

# --- 4. 管理區 (刪除功能) ---
st.divider()
st.subheader("📋 紀錄管理與刪除")

if all_logs:
    # 這裡顯示一個帶有「刪除」按鈕的清單
    for key, val in reversed(all_logs.items()):
        col_t, col_n, col_h, col_b = st.columns([3, 2, 2, 2])
        col_t.write(f"🕒 {val['time']}")
        col_n.write(f"👤 {val['name']}")
        col_h.write(f"⏳ {val['hours']} hr")
        if col_b.button("🗑️ 刪除", key=key):
            db.reference(f'work_logs/{key}').delete()
            st.warning(f"已刪除 {val['name']} 的紀錄")
            st.rerun()

    # 下載按鈕 (放在最後面)
    df_final = pd.DataFrame.from_dict(all_logs, orient='index')[['time', 'name', 'hours']]
    csv = df_final.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載完整 Excel", data=csv, file_name="工時紀錄.csv", mime="text/csv")
else:
    st.info("尚無紀錄")
