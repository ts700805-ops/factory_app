import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心資料與設定 ---
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

# --- 2. 介面樣式修正 (橫向扁平化) ---
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }

    /* 製令卡片主體 */
    .order-card-fixed {
        background: #ffffff;
        border-radius: 10px;
        border: 2px solid #cbd5e1;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 25px;
        height: 600px;           /* 固定高度 */
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    /* 🔵 固定標題列 */
    .order-header-fixed {
        background-color: #1e40af;
        color: white;
        padding: 12px 18px;
        font-size: 20px;
        font-weight: 900;
        height: 55px;
        flex-shrink: 0;
        border-bottom: 3px solid #1e3a8a;
    }

    /* 🟢 內容捲動區 */
    .order-scroll-body {
        flex-grow: 1;
        overflow-y: auto !important;
        padding: 10px;
        background: #fdfdfd;
    }

    /* 橫向工序條 */
    .proc-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #e2e8f0;
        padding: 8px 0;
        min-height: 50px;
    }
    .proc-row:last-child { border-bottom: none; }

    /* 左側工序名稱：固定寬度 */
    .proc-label {
        width: 120px;
        font-size: 13px;
        font-weight: 700;
        color: #1e40af;
        flex-shrink: 0;
        padding-right: 10px;
        border-right: 2px solid #f1f5f9;
    }

    /* 右側人員名單：橫向排列 */
    .proc-staff-area {
        flex-grow: 1;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding-left: 10px;
        align-items: center;
    }

    .main-tag {
        background: #1e40af;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 15px;
        font-weight: 900;
        border: 1px solid #1e3a8a;
    }

    .sub-tag {
        background: #f1f5f9;
        color: #475569;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #e2e8f0;
    }

    .search-container {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #1e40af;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 邏輯處理 ---
settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]

if "user" not in st.session_state:
    st.title("⚓ 超慧科技 - 系統登入")
    u = st.selectbox("請選擇您的姓名", all_staff)
    if st.button("登入系統"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 超慧科技公佈欄", "📝 任務派發", "⚙️ 基礎資料設定"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 超慧科技公佈欄 (橫向對齊版) ---
    if menu == "📊 超慧科技公佈欄":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📋 超慧科技公佈欄</h1>', unsafe_allow_html=True)
        
        # 搜尋篩選器
        with st.container():
            st.markdown('<div class="search-container">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            s_order = col1.selectbox("🔍 搜尋製令項目", ["全部"] + sorted(order_list))
            s_staff = col2.selectbox("👤 搜尋參與人員", ["全部"] + sorted(all_staff))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, id=k) for k, v in data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs)
                
                unique_orders = df["製令"].unique()
                filtered = []
                for o in unique_orders:
                    if s_order != "全部" and s_order != o: continue
                    o_df = df[df["製令"] == o]
                    if s_staff != "全部":
                        check_cols = [f"人員{i}" for i in range(1, 6)]
                        if not o_df[check_cols].apply(lambda x: s_staff in x.values, axis=1).any(): continue
                    filtered.append(o)

                # 看板顯示 (維持 3 欄，內部改橫向)
                cols = st.columns(3)
                for idx, o_id in enumerate(filtered):
                    o_df = df[df["製令"] == o_id]
                    with cols[idx % 3]:
                        st.markdown(f'''
                            <div class="order-card-fixed">
                                <div class="order-header-fixed">📦 製令：{o_id}</div>
                                <div class="order-scroll-body">
                        ''', unsafe_allow_html=True)
                        
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            if not match.empty:
                                row = match.iloc[0]
                                w1 = row.get("人員1", "-")
                                # 取得其他支援人員
                                others = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", None, "", "管理員"]]
                                
                                w1_html = f'<div class="main-tag">{w1}</div>'
                                others_html = "".join([f'<div class="sub-tag">{s}</div>' for s in others])
                                staff_html = f'<div class="proc-staff-area">{w1_html}{others_html}</div>'
                            else:
                                staff_html = '<div class="proc-staff-area" style="color:#cbd5e1; font-size:12px;">(尚未派工)</div>'
                            
                            st.markdown(f'''
                                <div class="proc-row">
                                    <div class="proc-label">{proc}</div>
                                    {staff_html}
                                </div>
                            ''', unsafe_allow_html=True)
                        
                        st.markdown('</div></div>', unsafe_allow_html=True)
        except Exception:
            st.error("目前看板無資料或網路異常")

    # --- 📝 任務派發 ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 新增派工任務</h2>', unsafe_allow_html=True)
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            o_input = c1.selectbox("製令編號", order_list)
            p_input = c2.selectbox("工序流程", process_list)
            st.write("---")
            pc = st.columns(5)
            ws = [pc[i].selectbox(f"人員 {i+1}", all_staff, key=f"ws{i}") for i in range(5)]
            if st.form_submit_button("🚀 同步至公佈欄"):
                payload = {"製令": o_input, "製造工序": p_input, "人員1": ws[0], "人員2": ws[1], "人員3": ws[2], "人員4": ws[3], "人員5": ws[4], "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                st.success("✅ 任務已發布")
                st.rerun()

    # --- ⚙️ 基礎資料設定 ---
    elif menu == "⚙️ 基礎資料設定":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 基礎資料管理</h2>', unsafe_allow_html=True)
        with st.form("sys_cfg"):
            o_text = st.text_area("製令編號清單 (半形逗號隔開)：", value=",".join(order_list))
            s_text = st.text_area("人員清單：", value=",".join(all_staff))
            p_text = st.text_area("工序流程清單：", value=",".join(process_list))
            if st.form_submit_button("💾 儲存並更新系統"):
                new_cfg = {
                    "order_list": [x.strip() for x in o_text.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in s_text.split(",") if x.strip()],
                    "processes": [x.strip() for x in p_text.split(",") if x.strip()],
                    "assigners": settings.get("assigners", ["管理員"])
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                st.success("✅ 系統設定已更新")
                st.rerun()
