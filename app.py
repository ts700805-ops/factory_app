import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pandas as pd  # 新增：用來處理表格數據

# 設定網頁標題
st.set_page_config(page_title="工時紀錄系統", layout="wide") # 改成寬版比較好收納表格
st.title("🏗️ 工時紀錄系統")

# --- 1. Firebase 連線設定 (使用你昨天的正確金鑰) ---
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
    except Exception as e:
        st.error(f"連線失敗：{e}")

# --- 2. 輸入介面 (維持原功能) ---
st.subheader("📝 新增工時紀錄")
with st.container(border=True): # 加個框框比較好看
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("員工姓名", placeholder="例如：賴智文")
    with col2:
        hours = st.number_input("工時 (小時)", min_value=0.5, max_value=24.0, step=0.5, value=8.0)

    if st.button("🚀 點我存檔到雲端", use_container_width=True):
        if name:
            new_data = {
                "name": name,
                "hours": hours,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            db.reference('work_logs').push(new_data)
            st.success(f"✅ 成功存入：{name}")
            st.balloons()
        else:
            st.warning("⚠️ 請輸入姓名")

# --- 3. 數據管理區 (新增功能) ---
st.divider()
st.subheader("📊 完整工時報表")

try:
    # 從 Firebase 抓取所有資料
    all_logs = db.reference('work_logs').get()
    
    if all_logs:
        # 將 JSON 轉成表格格式 (DataFrame)
        df = pd.DataFrame.from_dict(all_logs, orient='index')
        # 整理表格欄位名稱
        df = df[['time', 'name', 'hours']]
        df.columns = ['紀錄時間', '姓名', '工時(hr)']
        # 按時間排序 (最新在上面)
        df = df.sort_values(by='紀錄時間', ascending=False)

        # 顯示表格
        st.dataframe(df, use_container_width=True, hide_index=True)

        # 下載 Excel 按鈕
        csv = df.to_csv(index=False).encode('utf-8-sig') # 加上 sig 解決中文亂碼
        st.download_button(
            label="📥 下載完整紀錄 (Excel檔)",
            data=csv,
            file_name=f"工時紀錄_{datetime.date.today()}.csv",
            mime="text/csv",
        )
    else:
        st.info("目前雲端資料庫還沒有紀錄喔。")
except Exception as e:
    st.write("讀取報表時發生錯誤。")
