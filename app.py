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
        "all_leaders": ["管理員", "組長A", "組長B"],
        "all_staff": ["徐梓翔", "陳德文", "人員C"], import streamlit as st
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
        "all_leaders": ["管理員", "組長A", "組長B"],
        "all_staff": ["徐梓翔", "陳德文", "人員C"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                for key in ["all_leaders", "all_staff", "processes", "order_list"]:
                    if key not in data or not data[key]:
                        data[key] = default_settings[key]
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 ---
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .order-card {
        background: #ffffff;
        border-radius: 8px;
        border: 2px solid #1e40af;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        overflow: hidden;
    }
    .order-title {
        background-color: #1e40af;
        color: white;
        padding: 10px 15px;
        font-size: 16px;
        font-weight: 900;
        border-bottom: 2px solid #1e3a8a;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .power-date {
        background: #fbbf24;
        color: #1e40af;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 900;
    }
    .table-row {
        display: flex;
        border-bottom: 1px solid #dee2e6;
        min-height: 40px;
        align-items: center;
    }
    .table-row:last-child { border-bottom: none; }
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
    .cell-staff {
        flex-grow: 1;
        padding: 5px 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    /* 標籤樣式 */
    .badge-leader { background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 13px; font-weight: 900; }
    .badge-main { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 13px; font-weight: 900; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600; border: 1px solid #cbd5e1; }
    
    .search-panel { background: white; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯 ---
settings = get_settings()
all_leaders = settings["all_leaders"]
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]

if "user" not in st.session_state:
    st.title("⚓ 超慧科技公佈欄 - 登入")
    u = st.selectbox("👤 請選擇您的姓名", all_leaders + all_staff)
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
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📋 超慧科技公佈欄</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-panel">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
            s_staff = c2.selectbox("👤 篩選人員/組長", ["全部"] + sorted(all_leaders + all_staff))
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
                    p_date = o_df.sort_values("提交時間", ascending=False).iloc[0].get("通電日期", "未設定")

                    if s_staff != "全部":
                        check_cols = ["組長"] + [f"人員{i}" for i in range(1, 6) if f"人員{i}" in o_df.columns]
                        if not o_df[check_cols].apply(lambda x: s_staff in x.values, axis=1).any(): continue

                    with cols[idx % 3]:
                        st.markdown(f'''
                            <div class="order-card">
                                <div class="order-title">
                                    <span>📦 製令：{o_id}</span>
                                    <span class="power-date">⚡ 通電：{p_date}</span>
                                </div>
                        ''', unsafe_allow_html=True)
                        
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            if not match.empty:
                                row = match.iloc[0]
                                leader = row.get("組長", "-")
                                # 恢復：人員1 為主要藍色標籤
                                w1 = row.get("人員1", "NA")
                                # 其餘人員 2-5 為灰色次要標籤
                                others = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", None, ""]]
                                
                                staff_html = f'<div class="badge-leader">L: {leader}</div>'
                                if w1 != "NA":
                                    staff_html += f'<div class="badge-main">{w1}</div>'
                                staff_html += "".join([f'<div class="badge-sub">{s}</div>' for s in others])
                            else:
                                staff_html = '<div style="color:#cbd5e1; font-size:11px;">未派工</div>'
                            
                            st.markdown(f'<div class="table-row"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.info("目前尚無派工紀錄")

    # --- 📝 任務派發 (自動覆蓋/編輯) ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 任務派發 / 內容修正</h2>', unsafe_allow_html=True)
        with st.form("dispatch_form"):
            c1, c2, c3, c4 = st.columns(4)
            target_o = c1.selectbox("1. 製令編號", order_list)
            target_p = c2.selectbox("2. 製造工序", process_list)
            target_l = c3.selectbox("3. 指派組長", all_leaders)
            target_d = c4.date_input("4. 通電日期", datetime.date.today())
            
            st.write("---")
            st.write("🔧 分派組員 (人員 1 將顯示為藍色主要標籤)")
            pc = st.columns(5)
            workers = [pc[i].selectbox(f"人員 {i+1}", ["NA"] + all_staff, key=f"ws_{i}") for i in range(5)]
            
            if st.form_submit_button("🚀 發布並更新公佈欄"):
                try:
                    r = requests.get(f"{DB_URL}.json", timeout=5)
                    db_data = r.json()
                    target_key = None
                    if db_data:
                        for key, val in db_data.items():
                            if val.get("製令") == target_o and val.get("製造工序") == target_p:
                                target_key = key
                                break
                    
                    payload = {
                        "製令": target_o, "製造工序": target_p, "組長": target_l,
                        "通電日期": str(target_d),
                        "人員1": workers[0], "人員2": workers[1], "人員3": workers[2], "人員4": workers[3], "人員5": workers[4],
                        "提交時間": get_now_str()
                    }

                    if target_key:
                        requests.put(f"{DB_BASE_URL}/work_logs/{target_key}.json", data=json.dumps(payload))
                        st.success(f"🔄 已更新製令 {target_o} 資料")
                    else:
                        requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                        st.success(f"✅ 已新增製令 {target_o} 派工")
                    st.rerun()
                except:
                    st.error("連線失敗")

    # --- ⚙️ 設定管理 ---
    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統資料後台管理</h2>', unsafe_allow_html=True)
        with st.form("admin_settings"):
            edit_o = st.text_area("製令編號設定", value=",".join(order_list))
            edit_l = st.text_area("組長名單設定", value=",".join(all_leaders))
            edit_s = st.text_area("一般人員名單設定", value=",".join(all_staff))
            edit_p = st.text_area("工序流程設定", value=",".join(process_list))
            
            if st.form_submit_button("💾 儲存並更新"):
                updated_cfg = {
                    "order_list": [x.strip() for x in edit_o.split(",") if x.strip()],
                    "all_leaders": [x.strip() for x in edit_l.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in edit_s.split(",") if x.strip()],
                    "processes": [x.strip() for x in edit_p.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(updated_cfg))
                st.success("✅ 設定已更新")
                st.rerun()
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                for key in ["all_leaders", "all_staff", "processes", "order_list"]:
                    if key not in data or not data[key]:
                        data[key] = default_settings[key]
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 ---
st.set_page_config(page_title="超慧科技公佈欄", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .order-card {
        background: #ffffff;
        border-radius: 8px;
        border: 2px solid #1e40af;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        overflow: hidden;
    }
    .order-title {
        background-color: #1e40af;
        color: white;
        padding: 10px 15px;
        font-size: 16px;
        font-weight: 900;
        border-bottom: 2px solid #1e3a8a;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .power-date {
        background: #fbbf24;
        color: #1e40af;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 900;
    }
    .table-row {
        display: flex;
        border-bottom: 1px solid #dee2e6;
        min-height: 40px;
        align-items: center;
    }
    .table-row:last-child { border-bottom: none; }
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
    .cell-staff {
        flex-grow: 1;
        padding: 5px 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
    }
    .badge-leader { background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 13px; font-weight: 900; }
    .badge-staff { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: 600; border: 1px solid #cbd5e1; }
    .search-panel { background: white; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯 ---
settings = get_settings()
all_leaders = settings["all_leaders"]
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]

if "user" not in st.session_state:
    st.title("⚓ 超慧科技公佈欄 - 登入")
    u = st.selectbox("👤 請選擇您的姓名", all_leaders + all_staff)
    if st.button("確認進入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 超慧科技公佈欄", "📝 任務派發", "⚙️ 設定管理"])
    
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 公佈欄 ---
    if menu == "📊 超慧科技公佈欄":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📋 超慧科技公佈欄</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-panel">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
            s_staff = c2.selectbox("👤 篩選人員/組長", ["全部"] + sorted(all_leaders + all_staff))
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
                    # 抓取該製令最新的通電日期
                    p_date = o_df.sort_values("提交時間", ascending=False).iloc[0].get("通電日期", "未設定")

                    if s_staff != "全部":
                        check_cols = ["組長"] + [f"人員{i}" for i in range(1, 6) if f"人員{i}" in o_df.columns]
                        if not o_df[check_cols].apply(lambda x: s_staff in x.values, axis=1).any(): continue

                    with cols[idx % 3]:
                        st.markdown(f'''
                            <div class="order-card">
                                <div class="order-title">
                                    <span>📦 製令：{o_id}</span>
                                    <span class="power-date">⚡ 通電：{p_date}</span>
                                </div>
                        ''', unsafe_allow_html=True)
                        
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            if not match.empty:
                                row = match.iloc[0]
                                leader = row.get("組長", "-")
                                staff_members = [row.get(f"人員{i}") for i in range(1, 6) if row.get(f"人員{i}") not in ["NA", None, ""]]
                                staff_html = f'<div class="badge-leader">L: {leader}</div>'
                                staff_html += "".join([f'<div class="badge-staff">{s}</div>' for s in staff_members])
                            else:
                                staff_html = '<div style="color:#cbd5e1; font-size:11px;">未派工</div>'
                            
                            st.markdown(f'<div class="table-row"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.info("目前尚無派工紀錄")

    # --- 📝 任務派發 (具備自動覆蓋/編輯功能) ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 任務派發 / 內容修正</h2>', unsafe_allow_html=True)
        st.caption("提示：若「製令」與「工序」相同，重新發布將自動「覆蓋舊內容」，達到編輯效果。")
        
        with st.form("dispatch_form"):
            c1, c2, c3, c4 = st.columns(4)
            target_o = c1.selectbox("1. 製令編號", order_list)
            target_p = c2.selectbox("2. 製造工序", process_list)
            target_l = c3.selectbox("3. 指派組長", all_leaders)
            target_d = c4.date_input("4. 通電日期", datetime.date.today())
            
            st.write("---")
            st.write("🔧 分派組員 (最多5位)")
            pc = st.columns(5)
            workers = [pc[i].selectbox(f"人員 {i+1}", ["NA"] + all_staff, key=f"ws_{i}") for i in range(5)]
            
            if st.form_submit_button("🚀 發布並更新公佈欄"):
                # 1. 先抓取舊資料，尋找是否有相同的 (製令 + 工序)
                try:
                    r = requests.get(f"{DB_URL}.json", timeout=5)
                    db_data = r.json()
                    target_key = None
                    if db_data:
                        for key, val in db_data.items():
                            if val.get("製令") == target_o and val.get("製造工序") == target_p:
                                target_key = key # 找到舊資料的 ID
                                break
                    
                    payload = {
                        "製令": target_o, "製造工序": target_p, "組長": target_l,
                        "通電日期": str(target_d),
                        "人員1": workers[0], "人員2": workers[1], "人員3": workers[2], "人員4": workers[3], "人員5": workers[4],
                        "提交時間": get_now_str()
                    }

                    if target_key:
                        # 2. 如果有舊資料，用 PUT (覆蓋)
                        requests.put(f"{DB_BASE_URL}/work_logs/{target_key}.json", data=json.dumps(payload))
                        st.success(f"🔄 已更新製令 {target_o} 的 {target_p} 資料")
                    else:
                        # 3. 如果沒舊資料，用 POST (新增)
                        requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                        st.success(f"✅ 已新增製令 {target_o} 派工")
                    
                    st.rerun()
                except:
                    st.error("連線失敗，請檢查網路")

    # --- ⚙️ 設定管理 ---
    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統資料後台管理</h2>', unsafe_allow_html=True)
        with st.form("admin_settings"):
            edit_o = st.text_area("製令編號設定 (逗號隔開)", value=",".join(order_list))
            edit_l = st.text_area("組長名單設定 (逗號隔開)", value=",".join(all_leaders))
            edit_s = st.text_area("一般人員名單設定 (逗號隔開)", value=",".join(all_staff))
            edit_p = st.text_area("工序流程設定 (逗號隔開)", value=",".join(process_list))
            
            if st.form_submit_button("💾 儲存並更新系統選單"):
                updated_cfg = {
                    "order_list": [x.strip() for x in edit_o.split(",") if x.strip()],
                    "all_leaders": [x.strip() for x in edit_l.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in edit_s.split(",") if x.strip()],
                    "processes": [x.strip() for x in edit_p.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(updated_cfg))
                st.success("✅ 所有設定已同步更新！")
                st.rerun()
