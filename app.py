import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
# 這裡維持您的資料庫路徑，並新增完工區路徑
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

# --- 2. 頁面配置 (字體維持 80px) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 表格明細區字體放大 */
    div[data-testid="stDataFrame"] div[role="gridcell"] > div {
        font-size: 80px !important;
        line-height: 1.2 !important;
        font-weight: bold !important;
    }
    div[data-testid="stDataFrame"] div[role="columnheader"] span {
        font-size: 50px !important;
        font-weight: bold !important;
    }
    div[data-testid="stDataFrame"] div[role="row"] {
        height: 120px !important;
    }

    /* 篩選區與按鈕樣式 */
    .stSelectbox label { font-size: 26px !important; font-weight: bold !important; }
    .stSelectbox div[data-baseweb="select"] > div { font-size: 24px !important; height: 60px !important; }
    .main-title { font-size: 48px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 25px; }
    .stat-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-top: 6px solid #1E3A8A; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
    .stButton>button { height: 75px; font-size: 32px !important; font-weight: bold !important; }
    
    /* 完工卡片樣式 */
    .done-card {
        padding: 20px;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    p = st.text_input("員工代碼", type="password")
    if st.button("啟航"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 經營者看板 (首頁)", "📝 現場派工作業", "📋 歷史紀錄查詢", "⚙️ 系統內容管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 經營者看板 (首頁) ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 派工執行實況看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = []
                for k, v in data.items():
                    v['db_key'] = k # 紀錄 Firebase 的原始 key 用於刪除
                    all_logs.append(v)
                df = pd.DataFrame(all_logs)

                # 看板統計
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="stat-card">總派件數<br><span style="font-size:65px; font-weight:bold; color:#1E3A8A;">{len(df)}</span> 件</div>', unsafe_allow_html=True)
                with c2:
                    worker_count = df['作業人員'].nunique() if not df.empty else 0
                    st.markdown(f'<div class="stat-card">動員人力<br><span style="font-size:65px; font-weight:bold; color:#1E3A8A;">{worker_count}</span> 人</div>', unsafe_allow_html=True)
                
                # 篩選功能 (維持原樣)
                st.write("")
                st.subheader("🔍 快速篩選資料") 
                with st.expander("點擊展開篩選選單", expanded=True):
                    f1, f2, f3, f4 = st.columns(4)
                    sel_order = f1.selectbox("按製令篩選", ["全部"] + sorted(df["製令"].unique().tolist()))
                    sel_process = f2.selectbox("按工序篩選", ["全部"] + sorted(df["製造工序"].unique().tolist()))
                    sel_assigner = f3.selectbox("按派工員篩選", ["全部"] + sorted(df["派工人員"].unique().tolist()))
                    sel_worker = f4.selectbox("按作業員篩選", ["全部"] + sorted(df["作業人員"].unique().tolist()))

                filtered_df = df.copy()
                if sel_order != "全部": filtered_df = filtered_df[filtered_df["製令"] == sel_order]
                if sel_process != "全部": filtered_df = filtered_df[filtered_df["製造工序"] == sel_process]
                if sel_assigner != "全部": filtered_df = filtered_df[filtered_df["派工人員"] == sel_assigner]
                if sel_worker != "全部": filtered_df = filtered_df[filtered_df["作業人員"] == sel_worker]

                # 顯示大字體表格
                st.subheader("📑 派工明細清單") 
                st.dataframe(filtered_df[["製令", "製造工序", "派工人員", "作業人員", "作業期限"]], use_container_width=True, height=500, hide_index=True)

                # --- 新增：完工按鈕區 ---
                st.markdown("---")
                st.subheader("📦 待辦派工明細 (點擊完工按鈕結案)")
                for index, row in filtered_df.iterrows():
                    with st.container():
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.markdown(f"### 📦 製令：{row['製令']} | 👷 作業員：{row['作業人員']}")
                            st.write(f"工序：{row['製造工序']} | 期限：{row['作業期限']} | 派工：{row['派工人員']}")
                        
                        # 完工按鈕邏輯
                        if col_btn.button(f"✅ 完工", key=f"btn_{row['db_key']}"):
                            done_data = row.to_dict()
                            db_key = done_data.pop('db_key') # 移除暫存 key
                            done_data['實際完工時間'] = get_now_str()
                            
                            # 1. 傳送到完工區
                            requests.post(f"{DONE_URL}.json", json=done_data)
                            # 2. 從待辦區刪除
                            requests.delete(f"{DB_URL}/{db_key}.json")
                            
                            st.balloons()
                            st.success(f"{row['製令']} 已完工！")
                            st.rerun()
            else:
                st.info("目前尚無待辦派工。")
        except:
            st.error("連線資料庫失敗，請檢查網路或 URL。")

    # --- 4. 📝 現場派工作業 (維持原樣) ---
    elif menu == "📝 現場派工作業":
        st.header("📝 建立新派工任務")
        with st.form("dispatch_form"):
            order_no = st.selectbox("📦 選擇製令編號", settings.get("orders", []))
            process_name = st.selectbox("⚙️ 選擇製造工序", settings.get("processes", []))
            c1, c2 = st.columns(2)
            assigner = c1.selectbox("🚩 派工人員", settings.get("assigners", []), index=settings.get("assigners", []).index(st.session_state.user) if st.session_state.user in settings.get("assigners", []) else 0)
            worker = c2.selectbox("👷 作業人員", settings.get("workers", []))
            deadline = st.date_input("⏳ 作業期限", datetime.date.today() + datetime.timedelta(days=1))
            if st.form_submit_button("🚀 發布任務"):
                log = {"製令": order_no, "製造工序": process_name, "派工人員": assigner, "作業人員": worker, "作業期限": str(deadline), "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", json=log)
                st.success("任務已發布！")

    # --- 5. 📋 歷史紀錄查詢 (新增完工資料區) ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 歷史紀錄查詢與維護")
        
        # A. 顯示已完工的歷史資料
        st.subheader("✅ 已完工歷史紀錄")
        try:
            r_done = requests.get(f"{DONE_URL}.json")
            done_db = r_done.json()
            if done_db:
                df_done = pd.DataFrame(list(done_db.values()))
                # 這裡顯示完工紀錄表，您可以根據需要調整顯示欄位
                st.dataframe(df_done[["製令", "製造工序", "作業人員", "實際完工時間"]], use_container_width=True, hide_index=True)
            else:
                st.info("目前尚無完工歷史紀錄。")
        except:
            st.error("讀取完工紀錄失敗")

        st.markdown("---")
        
        # B. 原本的待辦紀錄維護功能 (維持原樣)
        st.subheader("🛠️ 待辦派工修改/刪除")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = []
                for k, v in db_data.items():
                    all_logs.append({"id": k, "製令": v.get("製令", "無"), "製造工序": v.get("製造工序", "無"), "派工人員": v.get("派工人員", "無"), "作業人員": v.get("作業人員", "無"), "作業期限": v.get("作業期限", "無")})
                df = pd.DataFrame(all_logs)
                
                log_options = {log['id']: f"製令：{log['製令']} | 人員：{log['作業人員']}" for log in all_logs}
                target_id = st.selectbox("請選擇要編輯或刪除的紀錄", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                
                curr = next(item for item in all_logs if item["id"] == target_id)
                with st.expander("📝 編輯此筆內容"):
                    ec1, ec2 = st.columns(2)
                    new_order = ec1.selectbox("修改製令", settings.get("orders", []), index=settings.get("orders", []).index(curr['製令']) if curr['製令'] in settings.get("orders", []) else 0)
                    new_proc = ec2.selectbox("修改工序", settings.get("processes", []), index=settings.get("processes", []).index(curr['製造工序']) if curr['製造工序'] in settings.get("processes", []) else 0)
                    if st.button("💾 儲存修改"):
                        requests.patch(f"{DB_URL}/{target_id}.json", json={"製令": new_order, "製造工序": new_proc})
                        st.success("紀錄已更新！")
                        st.rerun()

                if st.button("🗑️ 刪除選定紀錄", type="primary"):
                    requests.delete(f"{DB_URL}/{target_id}.json")
                    st.warning("紀錄已刪除。")
                    st.rerun()
        except:
            st.write("目前沒有待辦紀錄可操作。")

    # --- 6. ⚙️ 系統內容管理 (維持原樣) ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("settings_form"):
            new_orders = st.text_area("📦 編輯製令清單 (請用逗號隔開)", value=",".join(settings.get("orders", [])), height=120)
            new_assigners = st.text_area("🚩 編輯管理人員清單", value=",".join(settings.get("assigners", [])), height=100)
            new_workers = st.text_area("👷 編輯執行人員清單", value=",".join(settings.get("workers", [])), height=100)
            new_procs = st.text_area("⚙️ 編輯工序清單", value=",".join(settings.get("processes", [])), height=100)
            if st.form_submit_button("✅ 儲存並更新所有設定"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "orders": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "workers": [x.strip() for x in new_workers.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_procs.split(",") if x.strip()]
                })
                st.success("設定已更新！")
                st.rerun()
