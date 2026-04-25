import streamlit as st
import pandas as pd
import datetime
import requests
import json
import time

# --- 1. 資料庫路徑設定 (修正變數定義，確保 SETTINGS_URL 正常工作) ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"  # 確保這行變數名稱與 get_settings 一致

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_leaders": ["陳德文", "劉志偉", "吳政昌", "蘇萬紘"],
        "all_staff": ["徐梓翔", "陳德文", "胡瑄芸", "蕭詩瓊"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "12345"],
        "process_map": {
            "陳德文": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢"],
            "吳政昌": ["S.T作業"],
            "劉志偉": ["收機清潔", "包機作業", "PACKING", "前置作業(門板組立)"]
        },
        "staff_map": {} 
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict): return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式設定 (手機版字體與紅色外框) ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    
    /* 製令卡片加上紅色外框與陰影 */
    .order-card { 
        background: white; 
        border-radius: 16px; 
        border: 2px solid #ff4d4d; /* 紅色外框 */
        margin-bottom: 25px; 
        overflow: hidden; 
        box-shadow: 0 0 15px rgba(255, 77, 77, 0.3); /* 紅色發光效果 */
    }
    
    /* 整體字體優化 */
    html, body, [data-testid="stMarkdownContainer"] p {
        font-size: 1.15rem !important;
        font-weight: 500;
    }

    /* 針對手機版 (螢幕小於 768px) 加大字體與清晰度 */
    @media (max-width: 768px) {
        .proc-name { font-size: 1.3rem !important; }
        .badge-staff { font-size: 1.1rem !important; }
        .order-header { font-size: 1.4rem !important; }
        .status-done { font-size: 1.2rem !important; }
        .stButton button { height: 50px !important; font-size: 1.2rem !important; }
    }
    
    .order-header { 
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); 
        color: white; 
        padding: 15px 20px; 
        font-weight: 900; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        font-size: 1.3rem;
    }
    
    .power-date-tag { 
        background: #fbbf24; 
        color: #1e3a8a; 
        padding: 5px 15px; 
        border-radius: 50px; 
        font-size: 15px; 
        font-weight: 800;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .proc-row-container {
        padding: 12px 20px;
        border-bottom: 2px solid #f1f5f9;
        transition: background 0.3s;
    }
    .proc-row-container:hover { background-color: #fff5f5; }
    
    .proc-name { 
        font-weight: 900; 
        color: #1e293b; 
        font-size: 17px;
        border-left: 5px solid #ff4d4d;
        padding-left: 12px;
    }
    
    .staff-area { display: flex; flex-wrap: wrap; gap: 8px; }
    .badge-staff { 
        background: #eff6ff; 
        color: #1d4ed8; 
        padding: 4px 12px; 
        border-radius: 6px; 
        font-size: 15px; 
        font-weight: 700;
        border: 1px solid #bfdbfe;
        display: inline-block;
    }
    
    .status-done { 
        color: #ffffff; 
        font-weight: 800; 
        font-size: 16px; 
        background: #10b981;
        padding: 6px 14px;
        border-radius: 8px;
        display: inline-block;
        text-align: center;
    }
    .status-empty { color: #94a3b8; font-style: italic; font-size: 15px; }
    
    .stButton>button { border-radius: 8px; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 讀取設定 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
process_map = settings.get("process_map", {})
staff_map = settings.get("staff_map", {}) 

if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"
if "edit_target" not in st.session_state:
    st.session_state.edit_target = None

# --- 4. 登入介面 ---
if "user" not in st.session_state:
    st.markdown('<div style="height:100px;"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-size:3rem;">⚓ 超慧科技</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#64748b;">生產管理系統 v2.1 (手機優化版)</p>', unsafe_allow_html=True)
    with st.columns([1,1.5,1])[1]:
        with st.container(border=True):
            u = st.selectbox("👤 請選擇您的組長姓名", sorted(all_leaders))
            if st.button("確認登入系統", use_container_width=True, type="primary"):
                st.session_state.user = u
                st.rerun()
else:
    st.sidebar.markdown(f"### 👤 當前人員：{st.session_state.user}")
    nav = st.sidebar.radio("功能導航", ["📊 製造部派工專區", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    if st.sidebar.button("登出系統", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部派工專區 ---
    if st.session_state.menu_selection == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900; margin-bottom:30px;">📋 製造部派工進度看板</h1>', unsafe_allow_html=True)

        # --- 對話框 1：編輯人員 (此處預設也使用綁定人員) ---
        @st.dialog("👥 編輯施工人員", width="medium")
        def edit_staff_dialog(order_id, proc_name, current_data):
            st.subheader(f"🛠️ {proc_name}")
            current_leader = st.session_state.user
            # 編輯對話框也同步使用綁定人員清單
            my_team = staff_map.get(current_leader, [])
            display_options = my_team if my_team else all_staff
            options = ["NA"] + sorted(list(set(display_options)))

            with st.form("staff_edit_form"):
                st.write(f"📦 製令：{order_id}")
                st.write(f"👤 負責組長：**{current_leader}**")
                
                new_wk = []
                for i in range(5):
                    p_val = current_data.get(f"人員{i+1}", "NA")
                    d_idx = options.index(p_val) if p_val in options else 0
                    sel = st.selectbox(f"人員 {i+1}", options, index=d_idx, key=f"dlg_staff_{i}")
                    new_wk.append(sel)
                
                if st.form_submit_button("💾 儲存修改", use_container_width=True):
                    new_payload = current_data.copy()
                    new_payload.update({
                        "最後更新": get_now_str(),
                        "人員1": new_wk[0], "人員2": new_wk[1], "人員3": new_wk[2], "人員4": new_wk[3], "人員5": new_wk[4]
                    })
                    db_id = new_payload.pop("db_id", None)
                    if db_id and db_id != "NA":
                        requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(new_payload))
                        st.success("✅ 人員更新成功！")
                        time.sleep(0.5); st.rerun()

        # --- 對話框 2：修改通電日期 ---
        @st.dialog("📅 修改預計通電日期", width="small")
        def edit_power_date_dialog(order_id, current_date_str, related_records):
            st.subheader(f"📦 製令：{order_id}")
            try:
                default_date = datetime.datetime.strptime(current_date_str, "%Y-%m-%d") if current_date_str != "未設定" else datetime.date.today()
            except:
                default_date = datetime.date.today()
            new_date = st.date_input("請選擇新的通電日期", value=default_date)
            if st.button("💾 確認修改", use_container_width=True):
                for db_id, data in related_records.items():
                    data["通電日期"] = str(new_date); data["最後更新"] = get_now_str()
                    requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(data))
                st.success("✅ 日期已更新"); time.sleep(0.5); st.rerun()

        # --- 頁面篩選列：修改處：篩選人員改為綁定人員 ---
        current_leader = st.session_state.user
        # 取得當前組長綁定的人員，若無則顯示全部
        my_team = staff_map.get(current_leader, [])
        staff_filter_options = sorted(list(set(my_team))) if my_team else all_staff
        
        my_procs = process_map.get(current_leader, process_list)
        f_cols = st.columns([1, 1, 1])
        with f_cols[0]: s_order = st.selectbox("🔍 篩選製令", ["全部"] + sorted(list(set(order_list))))
        with f_cols[1]: s_staff = st.selectbox("👤 篩選人員 (僅顯示組員)", ["全部"] + staff_filter_options)
        
        try:
            r_work = requests.get(f"{DB_URL}.json").json() or {}
            df_work = pd.DataFrame([dict(v, db_id=k) for k, v in r_work.items()]).fillna("NA") if r_work else pd.DataFrame()
            r_finish = requests.get(f"{FINISH_URL}.json").json() or {}
            df_finish = pd.DataFrame([v for k, v in r_finish.items()]).fillna("NA") if r_finish else pd.DataFrame()

            # --- 篩選邏輯 ---
            base_orders = [str(o) for o in order_list]
            if s_order != "全部":
                base_orders = [str(s_order)]

            final_display_orders = []
            for o_id in base_orders:
                o_df = df_work[df_work["製令"] == str(o_id)]
                f_df_order = df_finish[df_finish["製令"] == str(o_id)]
                if s_staff == "全部":
                    final_display_orders.append(o_id)
                else:
                    found = False
                    for df in [o_df, f_df_order]:
                        if not df.empty:
                            for i in range(1, 6):
                                # 修正原本語法錯誤，加入 contains 判定 (針對 image_0a0bdb.png)
                                if (df[f"人員{i}"].astype(str).str.contains(s_staff)).any():
                                    found = True; break
                        if found: break
                    if found: final_display_orders.append(o_id)

            if not final_display_orders:
                st.info(f"💡 目前篩選條件下無符合的任務項目 (人員: {s_staff})")
            else:
                # 三欄式卡片佈局
                main_cols = st.columns(3) 
                for idx, o_id in enumerate(final_display_orders):
                    o_df = df_work[df_work["製令"] == str(o_id)]
                    f_df_order = df_finish[df_finish["製令"] == str(o_id)]
                    
                    p_date = "未設定"
                    if not o_df.empty: p_date = str(o_df.iloc[0].get("通電日期", "未設定"))
                    elif not f_df_order.empty: p_date = str(f_df_order.iloc[0].get("通電日期", "未設定"))

                    with main_cols[idx % 3]:
                        st.markdown(f'''
                            <div class="order-card">
                                <div class="order-header">
                                    <span>📦 {o_id}</span>
                                    <span class="power-date-tag">⚡ {p_date}</span>
                                </div>
                        ''', unsafe_allow_html=True)
                        
                        # 修改日期按鈕
                        date_edit_col = st.columns([0.8, 0.2])
                        with date_edit_col[1]:
                            if st.button("📅", key=f"date_edit_{o_id}"):
                                related = {k: v for k, v in r_work.items() if v.get("製令") == str(o_id)}
                                edit_power_date_dialog(o_id, p_date, related)

                        # 工序內容列
                        for p_idx, proc in enumerate(my_procs):
                            u_key = f"v21_{str(o_id).replace('-','_')}_{p_idx}"
                            m_w = o_df[o_df["製造工序"] == proc]
                            m_f = f_df_order[f_df_order["製造工序"] == proc]
                            
                            is_assigned = False
                            is_done = not m_f.empty
                            target_row = m_w.iloc[0] if not m_w.empty else (m_f.iloc[0] if not m_f.empty else None)
                            
                            st.markdown('<div class="proc-row-container">', unsafe_allow_html=True)
                            r_ui = st.columns([3.0, 3.5, 0.8, 2.7])
                            
                            with r_ui[0]:
                                st.markdown(f'<div class="proc-name">{proc}</div>', unsafe_allow_html=True)
                            with r_ui[1]:
                                staff_html = ""
                                if target_row is not None:
                                    for i in range(1, 6):
                                        p = target_row.get(f"人員{i}")
                                        if p and p != "NA": staff_html += f'<span class="badge-staff">{p}</span>'; is_assigned = True
                                st.markdown(f'<div>{staff_html if staff_html else "<i>尚未派工</i>"}</div>', unsafe_allow_html=True)
                            with r_ui[2]:
                                if not is_done:
                                    if st.button("✏️", key=f"eb_staff_{u_key}"):
                                        if m_w.empty:
                                            init = {"製令": str(o_id), "製造工序": proc, "組長": st.session_state.user, "通電日期": p_date, "人員1": "NA", "人員2": "NA", "人員3": "NA", "人員4": "NA", "人員5": "NA"}
                                            res = requests.post(f"{DB_URL}.json", data=json.dumps(init))
                                            init["db_id"] = res.json().get("name"); edit_staff_dialog(o_id, proc, init)
                                        else: edit_staff_dialog(o_id, proc, target_row.to_dict())
                            with r_ui[3]:
                                if is_done:
                                    st.markdown('<div class="status-done">✅ 已完工</div>', unsafe_allow_html=True)
                                else:
                                    if not is_assigned: st.warning("⚠️ 請指派")
                                    else:
                                        if st.button("完工", key=f"db_{u_key}", type="primary", use_container_width=True):
                                            dat = m_w.iloc[0].to_dict(); db_id = dat.pop('db_id')
                                            dat["完工時間"] = get_now_str(); dat["完工人員"] = st.session_state.user
                                            requests.post(f"{FINISH_URL}.json", data=json.dumps(dat))
                                            requests.delete(f"{DB_URL}/{db_id}.json"); st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True) 
                        st.markdown('</div>', unsafe_allow_html=True) # 卡片結束
        except Exception as e: st.error(f"連線或資料錯誤: {e}")

    # --- 📜 完工紀錄查詢 ---
    elif st.session_state.menu_selection == "📜 完工紀錄查詢":
        st.title("📜 歷史完工紀錄")
        try:
            r = requests.get(f"{FINISH_URL}.json").json()
            if r:
                f_df = pd.DataFrame([dict(v, db_id=k) for k, v in r.items() if v]).fillna("NA")
                f_df = f_df.sort_values("完工時間", ascending=False)
                keyword = st.text_input("🔍 搜尋", key="instant_search").strip()
                display_df = f_df if not keyword else f_df[f_df.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)]
                for o_id in display_df["製令"].unique():
                    order_records = display_df[display_df["製令"] == o_id]
                    with st.expander(f"📦 製令：{o_id} (已完工 {len(order_records)} 項)"):
                        st.dataframe(order_records.drop(columns=['db_id']), use_container_width=True)
                        for _, row in order_records.iterrows():
                            if st.button(f"🗑️ 刪除 {row['製造工序']}", key=f"del_{row['db_id']}"):
                                requests.delete(f"{FINISH_URL}/{row['db_id']}.json"); st.rerun()
            else: st.info("目前無完工紀錄")
        except: st.error("連線失敗")

    # --- 📝 任務派發 (此處也限制顯示組員) ---
    elif st.session_state.menu_selection == "📝 任務派發":
        st.title("📝 任務指派與編輯")
        current_leader = st.session_state.user
        my_team = staff_map.get(current_leader, all_staff)
        with st.form("dispatch_form"):
            v1, v2 = st.columns(2)
            t_o = v1.selectbox("1. 選擇製令", order_list)
            t_p = v2.selectbox("2. 選擇工序", process_list)
            v3, v4 = st.columns(2)
            t_l = v3.selectbox("3. 負責組長", all_leaders, index=all_leaders.index(current_leader) if current_leader in all_leaders else 0)
            t_d = v4.date_input("4. 預計通電日期")
            # 修正：限制人員選單為當前組長綁定的人員
            wk = [st.selectbox(f"人員 {i+1}", ["NA"] + sorted(list(set(my_team))), key=f"form_staff_{i}") for i in range(5)]
            
            if st.form_submit_button("🚀 確認發布任務", use_container_width=True):
                payload = {"製令": str(t_o), "製造工序": t_p, "組長": t_l, "通電日期": str(t_d), "最後更新": get_now_str()}
                for i, w in enumerate(wk): payload[f"人員{i+1}"] = w
                # 判定是否存在，發布新任務
                requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                st.success("任務指派成功！"); time.sleep(0.5); st.session_state.menu_selection = "📊 製造部派工專區"; st.rerun()

    # --- ⚙️ 設定管理 (回復完整欄位) ---
    elif st.session_state.menu_selection == "⚙️ 設定管理":
        st.title("⚙️ 系統設定")
        with st.form("config_form"):
            so = st.text_area("製令清單", ",".join(order_list))
            sl = st.text_area("組長清單", ",".join(all_leaders))
            ss = st.text_area("人員清單", ",".join(all_staff))
            sp = st.text_area("工序清單", ",".join(process_list))
            sm = st.text_area("組長:工序綁定", "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()]))
            staff_in = st.text_area("組長:人員綁定", "\n".join([f"{k}:{','.join(v)}" for k, v in staff_map.items()]))
            
            if st.form_submit_button("💾 儲存設定"):
                def split_s(s): return [x.strip() for x in s.split(",") if x.strip()]
                new_proc_map = {}
                for line in sm.split("\n"):
                    if ":" in line: k, v = line.split(":", 1); new_proc_map[k.strip()] = split_s(v)
                new_staff_map = {}
                for line in staff_in.split("\n"):
                    if ":" in line: k, v = line.split(":", 1); new_staff_map[k.strip()] = split_s(v)
                
                final_conf = {
                    "order_list": split_s(so), "all_leaders": split_s(sl), "all_staff": split_s(ss),
                    "processes": split_s(sp), "process_map": new_proc_map, "staff_map": new_staff_map
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(final_conf))
                st.success("設定已更新"); time.sleep(0.8); st.rerun()
