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
    # 預設保底名單：確保選單不會消失
    default_settings = {
        "all_staff": ["管理員", "徐梓翔", "陳德文"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                # 關鍵修正：檢查必要欄位，缺失則補上預設
                for key in ["all_staff", "processes", "order_list"]:
                    if key not in data or not data[key]:
                        data[key] = default_settings[key]
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 (格線表格版 & 移除紅框空白) ---
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    
    /* 製令卡片主體：移除紅框多餘空白 */
    .order-card {
        background: #ffffff;
        border-radius: 8px;
        border: 2px solid #1e40af;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    /* 🔵 固定藍色標題列 */
    .order-title {
        background-color: #1e40af;
        color: white;
        padding: 10px 15px;
        font-size: 18px;
        font-weight: 900;
        border-bottom: 2px solid #1e3a8a;
    }

    /* 🟢 表格內容區 */
    .table-row {
        display: flex;
        border-bottom: 1px solid #dee2e6;
        min-height: 40px;
        align-items: center;
    }
    .table-row:last-child { border-bottom: none; }

    /* 左側工序格線 */
    .cell-proc {
        width: 120px;
        background-color: #f1f5f9;
        color: #1e40af;
        font-weight: 800;
        font-size: 13px;
        padding: 8px;
        border-right: 1px solid #dee2e6;
        flex-shrink: 0;
    }

    /* 右側人員格線 */
    .cell-staff {
        flex-grow: 1;
        padding: 5px 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }

    .badge-main { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 14px; font-weight: 900; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600; }
    
    .search-panel { background: white; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 資料載入 ---
settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]

if "user" not in st.session_state:
    st.title("⚓ 超慧科技公佈欄 - 登入")
    # 確保登入畫面也能抓到人員名單
    u = st.selectbox("👤 請選擇您的姓名", all_staff)
    if st.button("確認進入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 超慧科技公佈欄", "📝 任務派發", "⚙️ 設定管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 超慧科技公佈欄 ---
    if menu == "📊 超慧科技公佈欄":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📢 超慧科技公佈欄</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-panel">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
            s_staff = c2.selectbox("👤 篩選參與人員", ["全部"] + sorted(all_staff))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs)
                
                unique_orders = df["製令"].unique()
                filtered_orders = [o for o in unique_orders if (s_order == "全部" or o == s_order)]
                
                cols = st.columns(3)
                for idx, o_id in enumerate(filtered_orders):
                    o_df = df[df["製令"] == o_id]
                    # 人員篩選邏輯
                    if s_staff != "全部":
                        check_cols = [f"人員{i}" for i in range(1, 6) if f"人員{i}" in o_df.columns]
                        if not o_df[check_cols].apply(lambda x: s_staff in x.values, axis=1).any(): continue

                    with cols[idx % 3]:
                        st.markdown(f'<div class="order-card"><div class="order-title">📦 製令：{o_id}</div>', unsafe_allow_html=True)
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            if not match.empty:
                                row = match.iloc[0]
                                w1 = row.get("人員1", "-")
                                others = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", None, "", "管理員"]]
                                staff_html = f'<div class="badge-main">{w1}</div>' + "".join([f'<div class="badge-sub">{s}</div>' for s in others])
                            else:
                                staff_html = '<div style="color:#cbd5e1; font-size:12px;">未派工</div>'
                            
                            st.markdown(f'<div class="table-row"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.info("目前尚無資料庫紀錄")

    # --- 📝 任務派發 (找回人員選單) ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 任務派發 (新增紀錄)</h2>', unsafe_allow_html=True)
        with st.form("dispatch_form"):
            c1, c2 = st.columns(2)
            target_o = c1.selectbox("選擇製令", order_list)
            target_p = c2.selectbox("選擇工序", process_list)
            st.write("---")
            st.write("🔧 分派組員 (第 1 位為負責組長)")
            pc = st.columns(5)
            # 使用強制讀取的 all_staff 變數
            workers = [pc[i].selectbox(f"人員 {i+1}", ["NA"] + all_staff, key=f"work_select_{i}") for i in range(5)]
            
            if st.form_submit_button("🚀 發布至公佈欄"):
                payload = {
                    "製令": target_o, "製造工序": target_p,
                    "人員1": workers[0], "人員2": workers[1], "人員3": workers[2], "人員4": workers[3], "人員5": workers[4],
                    "提交時間": get_now_str()
                }
                requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                st.success(f"✅ {target_o} 派工成功！")
                st.rerun()

    # --- ⚙️ 設定管理 (修正儲存後遺失的問題) ---
    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統資料後台管理</h2>', unsafe_allow_html=True)
        with st.form("admin_settings"):
            st.info("請輸入資料並以「半形逗號 , 」隔開")
            edit_o = st.text_area("製令編號設定", value=",".join(order_list))
            edit_s = st.text_area("人員/組長名單設定", value=",".join(all_staff))
            edit_p = st.text_area("工序流程設定", value=",".join(process_list))
            
            if st.form_submit_button("💾 儲存並同步全系統選單"):
                # 重新打包成正確格式
                updated_cfg = {
                    "order_list": [x.strip() for x in edit_o.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in edit_s.split(",") if x.strip()],
                    "processes": [x.strip() for x in edit_p.split(",") if x.strip()]
                }
                # 使用 put 完整覆蓋舊設定，確保 Key 值正確
                requests.put(f"{SETTING_URL}.json", data=json.dumps(updated_cfg))
                st.success("✅ 設定已更新！所有選單已找回並同步。")
                st.rerun()
