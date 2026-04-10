import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
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

# --- 2. 頁面配置 (僅調整 CSS，紅色框框字體放大 2 倍) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 【關鍵修改：紅色框框表格】文字直接放大到 36px (原本的 2 倍以上) */
    div[data-testid="stDataFrame"] div[role="gridcell"] > div {
        font-size: 36px !important;
        line-height: 1.6 !important;
        font-weight: 500 !important;
    }
    /* 表格欄位標題同步放大 */
    div[data-testid="stDataFrame"] div[role="columnheader"] span {
        font-size: 30px !important;
        font-weight: bold !important;
    }

    /* 綠框框與標籤比例調整 */
    .stSelectbox label { font-size: 26px !important; font-weight: bold !important; }
    .stSelectbox div[data-baseweb="select"] > div { font-size: 24px !important; height: 60px !important; }

    /* 其他標題視覺 */
    .main-title { font-size: 48px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; }
    .stat-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-top: 6px solid #1E3A8A; text-align: center; }
    .stButton>button { height: 75px; font-size: 32px !important; font-weight: bold !important; }
    [data-testid="stSidebar"] .stRadio label { font-size: 26px !important; }
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

    # --- 3. 📊 經營者看板 (首頁) [功能完全不變] ---
    if menu == "📊 經營者看板 (首頁)":
        st.markdown('<p class="main-title">📊 派工執行實況看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = []
                for k, v in data.items():
                    all_logs.append({
                        "製令": v.get("製令", "無"),
                        "製造工序": v.get("製造工序", "無"),
                        "派工人員": v.get("派工人員", "無"),
                        "作業人員": v.get("作業人員", "無"),
                        "作業期限": v.get("作業期限", "無")
                    })
                df = pd.DataFrame(all_logs)

                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<div class="stat-card">總派件數<br><span style="font-size:65px; font-weight:bold; color:#1E3A8A;">{len(df)}</span> 件</div>', unsafe_allow_html=True)
                with c2:
                    worker_count = df['作業人員'].nunique() if not df.empty else 0
                    st.markdown(f'<div class="stat-card">動員人力<br><span style="font-size:65px; font-weight:bold; color:#1E3A8A;">{worker_count}</span> 人</div>', unsafe_allow_html=True)
                
                st.write("")
                st.subheader("🔍 快速篩選資料")
                with st.expander("點擊展開篩選選單", expanded=True):
                    f1, f2, f3, f4 = st.columns(4)
                    order_list = ["全部"] + sorted(df["製令"].unique().tolist())
                    process_list = ["全部"] + sorted(df["製造工序"].unique().tolist())
                    assigner_list = ["全部"] + sorted(df["派工人員"].unique().tolist())
                    worker_list = ["全部"] + sorted(df["作業人員"].unique().tolist())
                    
                    sel_order = f1.selectbox("按製令篩選", order_list)
                    sel_process = f2.selectbox("按工序篩選", process_list)
                    sel_assigner = f3.selectbox("按派工員篩選", assigner_list)
                    sel_worker = f4.selectbox("按作業員篩選", worker_list)

                filtered_df = df.copy()
                if sel_order != "全部": filtered_df = filtered_df[filtered_df["製令"] == sel_order]
                if sel_process != "全部": filtered_df = filtered_df[filtered_df["製造工序"] == sel_process]
                if sel_assigner != "全部": filtered_df = filtered_df[filtered_df["派工人員"] == sel_assigner]
                if sel_worker != "全部": filtered_df = filtered_df[filtered_df["作業人員"] == sel_worker]

                st.subheader("📑 派工明細清單")
                # 這部分的顯示字體已經透過 CSS 放大
                st.dataframe(filtered_df[["製令", "製造工序", "派工人員", "作業人員", "作業期限"]], use_container_width=True, height=650, hide_index=True)
            else: st.info("目前尚單資料。")
        except: st.error("連線資料庫失敗")

    # --- 4. 📝 現場派工作業 [功能完全不變] ---
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

    # --- 5. 📋 歷史紀錄查詢 [功能完全不變] ---
    elif menu == "📋 歷史紀錄查詢":
        st.header("📋 歷史紀錄維護")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = []
                for k, v in db_data.items():
                    all_logs.append({
                        "id": k,
                        "製令": v.get("製令", "無"),
                        "製造工序": v.get("製造工序", "無"),
                        "派工人員": v.get("派工人員", "無"),
                        "作業人員": v.get("作業人員", "無"),
                        "作業期限": v.get("作業期限", str(datetime.date.today()))
                    })
                df = pd.DataFrame(all_logs)
                st.dataframe(df[["製令", "製造工序", "派工人員", "作業人員", "作業期限"]], use_container_width=True, hide_index=True)
                st.write("---")
                log_options = {log['id']: f"【{log['製令']}】 人員：{log['作業人員']}" for log in all_logs}
                target_id = st.selectbox("選擇要處理的紀錄", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                if st.button("🗑️ 刪除選定紀錄", type="primary"):
                    requests.delete(f"{DB_URL}/{target_id}.json")
                    st.rerun()
            else: st.info("無紀錄。")
        except: st.error("系統異常")

    # --- 6. ⚙️ 系統內容管理 [功能完全不變] ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 選單內容管理")
        with st.form("settings_form"):
            new_orders = st.text_area("製令清單", value=",".join(settings.get("orders", [])), height=120)
            new_assigners = st.text_area("派工人員", value=",".join(settings.get("assigners", [])), height=120)
            new_workers = st.text_area("作業人員", value=",".join(settings.get("workers", [])), height=120)
            new_procs = st.text_area("工序清單", value=",".join(settings.get("processes", [])), height=120)
            if st.form_submit_button("✅ 儲存更新"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "orders": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigners.split(",") if x.strip()],
                    "workers": [x.strip() for x in new_workers.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_procs.split(",") if x.strip()]
                })
                st.success("設定已更新！")
                st.rerun()
