import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
DONE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/completed_logs" # 新增完工資料庫路徑
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json")
        data = r.json()
        if not data: 
            return {"orders": [], "assigners": ["管理員"], "workers": ["人員"], "processes": ["預設工序"]}
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "workers": ["人員"], "processes": ["預設工序"]}

# --- 2. 頁面配置 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 表格明細區字體放大 */
    div[data-testid="stDataFrame"] div[role="gridcell"] > div {
        font-size: 80px !important;
        line-height: 1.2 !important;
        font-weight: bold !important;
    }
    .main-title { font-size: 48px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 25px; }
    .stButton>button { height: 75px; font-size: 32px !important; font-weight: bold !important; }
    /* 完工按鈕專用樣式 */
    .done-btn button { background-color: #28a745 !important; color: white !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    if st.button("啟航"):
        st.balloons()
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    # 修改導航選單，加入「✅ 完工資料專區」
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "✅ 完工資料專區", "📝 現場派工作業", "📋 歷史紀錄查詢", "⚙️ 系統內容管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (首頁 - 加入完工按鈕) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 派工執行實況看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = []
                for k, v in data.items():
                    v['id'] = k
                    all_logs.append(v)
                df = pd.DataFrame(all_logs)

                # 顯示統計圖表 (略...)
                
                st.subheader("📑 待辦派工明細 (點擊完工可移出)")
                # 遍歷資料顯示，並在每一行加上完工按鈕
                for index, row in df.iterrows():
                    with st.container():
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            # 使用大字體顯示資訊
                            st.markdown(f"### 📦 製令：{row.get('製令')} | 👷 人員：{row.get('作業人員')}")
                            st.write(f"工序：{row.get('製造工序')} | 期限：{row.get('作業期限')}")
                        with col2:
                            # 完工按鈕
                            if st.button(f"✅ 完工", key=f"done_{row['id']}"):
                                # 1. 搬移到完工區
                                row_data = row.to_dict()
                                row_data['完工時間'] = get_now_str()
                                requests.post(f"{DONE_URL}.json", json=row_data)
                                # 2. 從待辦區刪除
                                requests.delete(f"{DB_URL}/{row['id']}.json")
                                st.balloons() # 🎈 特效
                                st.success(f"{row.get('製令')} 已完工！")
                                st.rerun()
                        st.divider()
            else:
                st.info("目前尚無待辦派工資料。")
        except:
            st.error("連線資料庫失敗")

    # --- 4. ✅ 完工資料專區 (新功能) ---
    elif menu == "✅ 完工資料專區":
        st.markdown('<p class="main-title">✅ 已完工歷史存檔</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DONE_URL}.json")
            done_data = r.json()
            if done_data:
                done_list = [v for k, v in done_data.items()]
                df_done = pd.DataFrame(done_list)
                st.dataframe(df_done[["製令", "製造工序", "作業人員", "完工時間"]], use_container_width=True, height=600)
            else:
                st.info("尚無完工紀錄。")
        except:
            st.error("讀取完工資料失敗")

    # --- 5. 📝 現場派工作業 --- (維持原樣)
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        with st.form("dispatch_form"):
            order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
            process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
            worker = st.selectbox("👷 作業人員", settings.get("workers", []))
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            if st.form_submit_button("🚀 發布任務"):
                log = {"製令": order_no, "製造工序": process_name, "派工人員": st.session_state.user, "作業人員": worker, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.balloons()
                st.success("任務已發布！")

    # --- 6. 📋 歷史紀錄查詢 --- (維持原樣)
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 歷史紀錄維護")
        # ... (維持您原本修正過後的編輯與刪除邏輯，並確保儲存修改有 st.balloons())
        # (此處程式碼同前一版本，包含容錯處理)

    # --- 7. ⚙️ 系統內容管理 --- (維持原樣)
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("settings_form"):
            # ... (管理清單內容)
            if st.form_submit_button("✅ 儲存並更新所有設定"):
                # (儲存邏輯...)
                st.balloons()
                st.rerun()
