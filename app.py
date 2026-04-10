import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心連線設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
DONE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/completed_logs"
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

# --- 2. 介面樣式優化 (縮小字體以符合顯示多筆資料需求) ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    /* 縮小全網頁基礎字體 */
    html, body, [class*="st-"] { font-size: 14px; }
    
    /* 待辦事項卡片：緊湊設計，方便顯示更多筆 */
    .task-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-left: 5px solid #1E3A8A;
        border-radius: 5px;
        padding: 6px 10px;
        margin-bottom: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .task-main-text {
        font-size: 15px !important;
        font-weight: bold;
        color: #1E3A8A;
    }
    .task-sub-text {
        font-size: 12px !important;
        color: #666;
    }
    /* 完工按鈕樣式優化 */
    .stButton>button {
        padding: 2px 12px !important;
        font-size: 13px !important;
        height: 32px !important;
    }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

# --- 3. 登入邏輯 ---
if "user" not in st.session_state:
    st.title("⚓ 系統登入")
    u = st.selectbox("請選擇姓名", settings.get("assigners", ["管理員"]))
    if st.button("登入系統"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "📝 現場派工作業", "📜 完工紀錄查詢", "⚙️ 系統內容管理"])
    
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 4. 📊 經營者看板 ---
    if menu == "📊 經營者看板 (首頁)":
        st.subheader("📊 派工執行實況看板")
        
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            
            if data:
                all_logs = []
                for k, v in data.items():
                    v['id'] = k
                    all_logs.append(v)
                df = pd.DataFrame(all_logs)

                c1, c2 = st.columns(2)
                c1.metric("總派件數", f"{len(df)} 件")
                c2.metric("動員人力", f"{df['作業人員'].nunique()} 人")

                with st.expander("🔍 快速篩選資料", expanded=False):
                    f1, f2, f3, f4 = st.columns(4)
                    s_order = f1.selectbox("製令", ["全部"] + sorted(df["製令"].unique().tolist()))
                    s_proc = f2.selectbox("工序", ["全部"] + sorted(df["製造工序"].unique().tolist()))
                    s_worker = f3.selectbox("作業員", ["全部"] + sorted(df["作業人員"].unique().tolist()))
                    s_assign = f4.selectbox("派工員", ["全部"] + sorted(df["派工人員"].unique().tolist()))

                f_df = df.copy()
                if s_order != "全部": f_df = f_df[f_df["製令"] == s_order]
                if s_proc != "全部": f_df = f_df[f_df["製造工序"] == s_proc]
                if s_worker != "全部": f_df = f_df[f_df["作業人員"] == s_worker]
                if s_assign != "全部": f_df = f_df[f_df["派工人員"] == s_assign]

                st.markdown("---")
                st.markdown("### 📋 待辦派工明細 (點擊按鈕結案)")

                for _, row in f_df.iterrows():
                    col_content, col_btn = st.columns([8.5, 1.5])
                    with col_content:
                        st.markdown(f"""
                        <div class="task-container">
                            <div>
                                <div class="task-main-text">📦 {row['製令']} | 👷 {row['作業人員']}</div>
                                <div class="task-sub-text">⚙️ 工序：{row['製造工序']} | ⏳ 期限：{row['作業期限']} | 🚩 派工：{row['派工人員']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_btn:
                        st.write("") # 垂直微調對齊
                        if st.button("✅ 完工", key=f"done_{row['id']}"):
                            try:
                                done_item = row.to_dict()
                                done_item['實際完工時間'] = get_now_str()
                                # 修正語法：確保 Requests 括號正確閉合
                                resp = requests.post(f"{DONE_URL}.json", json=done_item)
                                if resp.status_code == 200:
                                    requests.delete(f"{DB_URL}/{row['id']}.json")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"連線失敗: {e}")
            else:
                st.info("目前沒有待辦任務。")
        except:
            st.error("連線資料庫失敗，請確認 Firebase URL 設定正確。")

    # --- 5. 📝 現場派工作業 ---
    elif menu == "📝 現場派工作業":
        st.subheader("📝 建立新派工")
        with st.form("new_task"):
            f_order = st.selectbox("選擇製令", settings.get("orders", []))
            f_proc = st.selectbox("選擇工序", settings.get("processes", []))
            f_worker = st.selectbox("作業人員", settings.get("workers", []))
            f_date = st.date_input("作業期限", datetime.date.today())
            if st.form_submit_button("發布任務"):
                new_task = {"製令": f_order, "製造工序": f_proc, "作業人員": f_worker, "派工人員": st.session_state.user, "作業期限": str(f_date), "派工時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=new_task)
                st.success("發布成功")
                st.rerun()

    # --- 6. 📜 完工紀錄查詢 ---
    elif menu == "📜 完工紀錄查詢":
        st.subheader("📜 已完工歷史紀錄")
        try:
            r = requests.get(f"{DONE_URL}.json")
            done_data = r.json()
            if done_data:
                df_done = pd.DataFrame([v for k, v in done_data.items()])
                # 修正第 190 行：補齊 st.dataframe 的括號
                st.dataframe(df_done, use_container_width=True, hide_index=True)
            else:
                st.write("尚無完工紀錄。")
        except:
            st.write("讀取資料失敗。")

    # --- 7. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.subheader("⚙️ 選單設定")
        with st.form("sys_config"):
            c_orders = st.text_area("製令清單", ",".join(settings.get("orders", [])))
            c_workers = st.text_area("人員清單", ",".join(settings.get("workers", [])))
            c_procs = st.text_area("工序清單", ",".join(settings.get("processes", [])))
            if st.form_submit_button("儲存"):
                new_conf = {
                    "orders": [x.strip() for x in c_orders.split(",") if x.strip()],
                    "assigners": settings.get("assigners", ["管理員"]),
                    "workers": [x.strip() for x in c_workers.split(",") if x.strip()],
                    "processes": [x.strip() for x in c_procs.split(",") if x.strip()]
                }
                requests.patch(f"{SETTING_URL}.json", json=new_conf)
                st.success("設定更新")
                st.rerun()
