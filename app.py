import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心設定與資料庫 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_staff": ["管理員", "徐梓翔", "陳德文"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01"],
        "assigners": ["管理員"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data: return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式修正 (鎖死標題專用) ---
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    /* 全局背景 */
    .stApp { background-color: #f1f5f9; }

    /* 每個製令的獨立卡片外框 */
    .order-card-container {
        background: #ffffff;
        border-radius: 12px;
        border: 2px solid #cbd5e1;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        margin-bottom: 25px;
        height: 650px;           /* 固定整個卡片高度 */
        display: flex;
        flex-direction: column;  /* 垂直排列標題與內容 */
        overflow: hidden;        /* 外框禁止捲動 */
    }

    /* 🔵 絕對固定的藍色標題列 */
    .sticky-header {
        background-color: #1e40af;
        color: white;
        padding: 15px 20px;
        font-size: 22px;
        font-weight: 900;
        height: 65px;            /* 固定高度 */
        flex-shrink: 0;          /* 強制不准被擠壓 */
        display: flex;
        align-items: center;
        border-bottom: 4px solid #1e3a8a;
        z-index: 99;
    }

    /* 🟢 唯一允許捲動的內容區 */
    .scrollable-body {
        flex-grow: 1;            /* 自動佔滿剩餘空間 */
        overflow-y: auto !important; /* 強制垂直捲動 */
        padding: 15px;
        background: #ffffff;
    }

    /* 工序小方塊 */
    .process-item {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 12px;
        text-align: center;
    }
    .process-title {
        color: #1e40af;
        font-weight: 800;
        font-size: 14px;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 8px;
        padding-bottom: 4px;
    }
    .main-name {
        font-size: 20px !important;
        font-weight: 900;
        color: #000;
        margin-bottom: 5px;
    }
    .sub-name-tag {
        display: inline-block;
        background: #e2e8f0;
        color: #475569;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin: 2px;
        font-weight: 600;
    }

    /* 搜尋列樣式 */
    .search-bar {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #1e40af;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 邏輯處理 ---
settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]

if "user" not in st.session_state:
    st.title("🔐 超慧科技 - 系統登入")
    u = st.selectbox("請選擇您的姓名", all_staff)
    if st.button("確認進入公佈欄"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 超慧科技公佈欄", "📝 任務派發", "⚙️ 基礎設定"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 超慧科技公佈欄 ---
    if menu == "📊 超慧科技公佈欄":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📢 超慧科技公佈欄</h1>', unsafe_allow_html=True)
        
        # 搜尋功能
        with st.container():
            st.markdown('<div class="search-bar">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            s_order = col1.selectbox("🔍 搜尋製令", ["全部"] + sorted(order_list))
            s_staff = col2.selectbox("👤 搜尋人員", ["全部"] + sorted(all_staff))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, id=k) for k, v in data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs)
                
                # 過濾邏輯
                unique_orders = df["製令"].unique()
                filtered = []
                for o in unique_orders:
                    if s_order != "全部" and s_order != o: continue
                    o_df = df[df["製令"] == o]
                    if s_staff != "全部":
                        cols_check = [f"人員{i}" for i in range(1, 6)]
                        if not o_df[cols_check].apply(lambda x: s_staff in x.values, axis=1).any(): continue
                    filtered.append(o)

                # 顯示三欄佈局
                cols = st.columns(3)
                for idx, o_id in enumerate(filtered):
                    o_df = df[df["製令"] == o_id]
                    with cols[idx % 3]:
                        # 🟢 核心修正結構：Header 與 Scrollable-Body 分離
                        st.markdown(f'''
                            <div class="order-card-container">
                                <div class="sticky-header">📦 製令：{o_id}</div>
                                <div class="scrollable-body">
                        ''', unsafe_allow_html=True)
                        
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            if not match.empty:
                                row = match.iloc[0]
                                main_w = row.get("人員1", "-")
                                sub_ws = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", None, ""]]
                                
                                sub_tags = "".join([f'<span class="sub-name-tag">{s}</span>' for s in sub_ws])
                                content_html = f'<div class="main-name"><span style="color:#1e40af;font-size:12px;">主</span> {main_w}</div>{sub_tags}'
                            else:
                                content_html = '<div style="color:#cbd5e1; font-size:13px; margin-top:5px;">(未派工)</div>'
                            
                            st.markdown(f'''
                                <div class="process-item">
                                    <div class="process-title">{proc}</div>
                                    {content_html}
                                </div>
                            ''', unsafe_allow_html=True)
                        
                        st.markdown('</div></div>', unsafe_allow_html=True)
        except:
            st.error("連線資料庫失敗")

    # --- 📝 任務派發 ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 新增派工任務</h2>', unsafe_allow_html=True)
        with st.form("dispatch_form"):
            c1, c2 = st.columns(2)
            target_o = c1.selectbox("製令編號", order_list)
            target_p = c2.selectbox("作業工序", process_list)
            st.write("---")
            pc = st.columns(5)
            ws = [pc[i].selectbox(f"人員 {i+1}", all_staff, key=f"ws{i}") for i in range(5)]
            if st.form_submit_button("🚀 發布至公佈欄"):
                log = {"製令": target_o, "製造工序": target_p, "人員1": ws[0], "人員2": ws[1], "人員3": ws[2], "人員4": ws[3], "人員5": ws[4], "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", data=json.dumps(log))
                st.success("任務已同步至看板！")
                st.rerun()

    # --- ⚙️ 基礎設定 ---
    elif menu == "⚙️ 基礎設定":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統基礎資料管理</h2>', unsafe_allow_html=True)
        with st.form("sys_setting"):
            o_input = st.text_area("製令清單 (逗號隔開)：", value=",".join(order_list))
            s_input = st.text_area("人員清單：", value=",".join(all_staff))
            p_input = st.text_area("工序流程：", value=",".join(process_list))
            if st.form_submit_button("💾 儲存設定"):
                new_data = {
                    "order_list": [x.strip() for x in o_input.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in s_input.split(",") if x.strip()],
                    "processes": [x.strip() for x in p_input.split(",") if x.strip()],
                    "assigners": settings.get("assigners", ["管理員"])
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("設定已更新至資料庫")
                st.rerun()
