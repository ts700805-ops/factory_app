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
            return {"orders": [], "assigners": ["管理員"], "workers": ["賴智文"], "processes": ["預設工序"]}
        return data
    except:
        return {"orders": [], "assigners": ["管理員"], "workers": ["人員"], "processes": ["預設工序"]}

# --- 2. 頁面配置 (針對綠框與藍框精確調校) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    /* 【藍框框：表格明細區】字體放大 2 倍 (約 32px) */
    div[data-testid="stDataFrame"] div[role="gridcell"] > div {
        font-size: 32px !important;
        line-height: 1.5 !important;
    }
    /* 表格欄位標題同步放大 */
    div[data-testid="stDataFrame"] div[role="columnheader"] span {
        font-size: 28px !important;
        font-weight: bold !important;
    }

    /* 【綠框框：篩選區】符合 1.5 倍的大小與高度 */
    .stSelectbox label {
        font-size: 26px !important;
        font-weight: bold !important;
        margin-bottom: 10px !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        font-size: 24px !important;
        height: 55px !important; /* 增加選單高度符合字體 */
        display: flex;
        align-items: center;
    }

    /* 其他全域優化 */
    .main-title { font-size: 48px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 25px; }
    .stat-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-top: 6px solid #1E3A8A; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
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

    # --- 3. 📊 經營者看板 (首頁) ---
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
                st.subheader("🔍 快速篩選資料") # 這是綠框區塊
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

                st.subheader("📑 派工明細清單") # 這是藍框區塊
                # 這裡顯示篩選後的結果，字體已放大
                st.dataframe(filtered_df[["製令", "製造工序", "派工人員", "作業人員", "作業期限"]], use_container_width=True, height=600, hide_index=True)
            else: st.info("目前尚無派工資料。")
        except: st.error("連線資料庫失敗")

    # --- 4. 📝 現場派工作業 (不亂動) ---
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
                requests.post(f"{DB
