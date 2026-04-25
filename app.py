import streamlit as st
import pandas as pd
import datetime
import requests
import json
import time

# --- 1. 資料庫路徑設定 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

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

# --- 2. 介面樣式設定 ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    .order-card { 
        background: white; 
        border-radius: 16px; 
        border: 2px solid #ff4d4d; 
        margin-bottom: 25px; 
        overflow: hidden; 
        box-shadow: 0 0 15px rgba(255, 77, 77, 0.3);
    }
    html, body, [data-testid="stMarkdownContainer"] p {
        font-size: 1.15rem !important;
        font-weight: 500;
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
    }
    .proc-row-container {
        padding: 12px 20px;
        border-bottom: 2px solid #f1f5f9;
    }
    .proc-name { 
        font-weight: 900; 
        color: #1e293b; 
        font-size: 17px;
        border-left: 5px solid #ff4d4d;
        padding-left: 12px;
    }
    .badge-staff { 
        background: #eff6ff; 
        color: #1d4ed8; 
        padding: 4px 12px; 
        border-radius: 6px; 
        font-size: 15px; 
        font-weight: 700;
        border: 1px solid #bfdbfe;
        margin-right: 5px;
    }
    .status-done { 
        color: #ffffff; 
        font-weight: 800; 
        font-size: 16px; 
        background: #10b981;
        padding: 6px 14px;
        border-radius: 8px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 初始化資料 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
process_map = settings.get("process_map", {})
staff_map = settings.get("staff_map", {}) 

if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"

# --- 4. 登入邏輯 ---
if "user" not in st.session_state:
    st.markdown('<div style="height:100px;"></div>', unsafe_allow_html=True)
    st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-size:3rem;">⚓ 超慧科技</h1>', unsafe_allow_html=True)
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
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📋 製造部派工進度看板</h1>', unsafe_allow_html=True)

        @st.dialog("👥 編輯施工人員", width="medium")
        def edit_staff_dialog(order_id, proc_name, current_data):
            st.subheader(f"🛠️ {proc_name}")
            # 編輯對話框也同步使用綁定人員
            my_team = staff_map.get(st.session_state.user, all_staff)
            options = ["NA"] + sorted(list(set(my_team)))
            with st.form("staff_edit_form"):
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
                    requests.put(f"{DB_URL}/{db_id}.json", data=json.dumps(new_payload))
                    st.success("✅ 人員更新成功！")
                    time.sleep(0.5); st.rerun()

        @st.dialog("📅 修改預計通電日期", width="small")
        def edit_power_date_dialog(order_id, current_date_str, related_records):
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

        # --- 篩選列：將人員清單改為該組長綁定的人員 ---
        my_team = staff_map.get(st.session_state.user, all_staff)
        f_cols = st.columns([1, 1])
        with f_cols[0]: s_order = st.selectbox("🔍 篩選製令", ["全部"] + sorted(list(set(order_list))))
        with f_cols[1]: s_staff = st.selectbox("👤 篩選人員 (僅顯示您的組員)", ["全部"] + sorted(my_team))
        
        try:
            r_work = requests.get(f"{DB_URL}.json").json() or {}
            df_work = pd.DataFrame([dict(v, db_id=k) for k, v in r_work.items()]).fillna("NA") if r_work else pd.DataFrame()
            r_finish = requests.get(f"{FINISH_URL}.json").json() or {}
            df_finish = pd.DataFrame([v for k, v in r_finish.items()]).fillna("NA") if r_finish else pd.DataFrame()

            # 決定目前要顯示的製令
            display_orders = [str(o) for o in order_list]
            if s_order != "全部": display_orders = [str(s_order)]

            main_cols = st.columns(3) 
            for idx, o_id in enumerate(display_orders):
                o_df = df_work[df_work["製令"] == str(o_id)]
                f_df_order = df_finish[df_finish["製令"] == str(o_id)]
                
                # 人員篩選邏輯
                if s_staff != "全部":
                    staff_match = False
                    for df in [o_df, f_df_order]:
                        if not df.empty:
                            for i in range(1, 6):
                                if (df[f"人員{i}"] == s_staff).any():
                                    staff_match = True; break
                    if not staff_match: continue

                p_date = "未設定"
                if not o_df.empty: p_date = str(o_df.iloc[0].get("通電日期", "未設定"))
                elif not f_df_order.empty: p_date = str(f_df_order.iloc[0].get("通電日期", "未設定"))

                with main_cols[idx % 3]:
                    st.markdown(f'<div class="order-card"><div class="order-header"><span>📦 {o_id}</span><span class="power-date-tag">⚡ {p_date}</span></div>', unsafe_allow_html=True)
                    
                    # 修改日期小按鈕
                    c1, c2 = st.columns([0.85, 0.15])
                    with c2:
                        if st.button("📅", key=f"dt_{o_id}"):
                            related = {k: v for k, v in r_work.items() if v.get("製令") == str(o_id)}
                            edit_power_date_dialog(o_id, p_date, related)

                    my_procs = process_map.get(st.session_state.user, process_list)
                    for p_idx, proc in enumerate(my_procs):
                        m_w = o_df[o_df["製造工序"] == proc]
                        m_f = f_df_order[f_df_order["製造工序"] == proc]
                        is_done = not m_f.empty
                        target_row = m_w.iloc[0] if not m_w.empty else (m_f.iloc[0] if not m_f.empty else None)
                        
                        st.markdown('<div class="proc-row-container">', unsafe_allow_html=True)
                        r_ui = st.columns([3, 4, 1, 2.5])
                        with r_ui[0]: st.markdown(f'<div class="proc-name">{proc}</div>', unsafe_allow_html=True)
                        with r_ui[1]:
                            staff_html = ""
                            if target_row is not None:
                                for i in range(1, 6):
                                    p = target_row.get(f"人員{i}")
                                    if p and p != "NA": staff_html += f'<span class="badge-staff">{p}</span>'
                            st.markdown(f'<div>{staff_html if staff_html else "<i>尚未派工</i>"}</div>', unsafe_allow_html=True)
                        with r_ui[2]:
                            if not is_done and st.button("✏️", key=f"ed_{o_id}_{p_idx}"):
                                if m_w.empty:
                                    init = {"製令": str(o_id), "製造工序": proc, "組長": st.session_state.user, "通電日期": p_date, "人員1": "NA", "人員2": "NA", "人員3": "NA", "人員4": "NA", "人員5": "NA"}
                                    res = requests.post(f"{DB_URL}.json", data=json.dumps(init))
                                    init["db_id"] = res.json().get("name"); edit_staff_dialog(o_id, proc, init)
                                else: edit_staff_dialog(o_id, proc, m_w.iloc[0].to_dict())
                        with r_ui[3]:
                            if is_done: st.markdown('<div class="status-done">✅ 已完工</div>', unsafe_allow_html=True)
                            elif not m_w.empty and any(m_w.iloc[0].get(f"人員{i}") != "NA" for i in range(1,6)):
                                if st.button("完工", key=f"fsh_{o_id}_{p_idx}", type="primary"):
                                    dat = m_w.iloc[0].to_dict(); db_id = dat.pop('db_id')
                                    dat["完工時間"] = get_now_str(); dat["完工人員"] = st.session_state.user
                                    requests.post(f"{FINISH_URL}.json", data=json.dumps(dat))
                                    requests.delete(f"{DB_URL}/{db_id}.json"); st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e: st.error(f"連線或資料錯誤: {e}")

    # --- 📜 完工紀錄查詢 ---
    elif st.session_state.menu_selection == "📜 完工紀錄查詢":
        st.title("📜 歷史完工紀錄")
        try:
            r = requests.get(f"{FINISH_URL}.json").json()
            if r:
                f_df = pd.DataFrame([dict(v, db_id=k) for k, v in r.items() if v]).fillna("NA")
                f_df = f_df.sort_values("完工時間", ascending=False)
                kw = st.text_input("🔍 搜尋製令、工序或人員")
                display_df = f_df if not kw else f_df[f_df.astype(str).apply(lambda x: x.str.contains(kw, case=False)).any(axis=1)]
                for o_id in display_df["製令"].unique():
                    with st.expander(f"📦 製令：{o_id}"):
                        st.dataframe(display_df[display_df["製令"] == o_id].drop(columns=['db_id']), use_container_width=True)
            else: st.info("目前無完工紀錄")
        except: st.error("連線失敗")

    # --- 📝 任務派發 ---
    elif st.session_state.menu_selection == "📝 任務派發":
        st.title("📝 任務指派")
        my_team = staff_map.get(st.session_state.user, all_staff)
        with st.form("dispatch_form"):
            t_o = st.selectbox("1. 選擇製令", order_list)
            t_p = st.selectbox("2. 選擇工序", process_list)
            t_d = st.date_input("3. 預計通電日期")
            wk = [st.selectbox(f"人員 {i+1}", ["NA"] + sorted(my_team), key=f"new_st_{i}") for i in range(5)]
            if st.form_submit_button("🚀 發布任務"):
                payload = {"製令": str(t_o), "製造工序": t_p, "組長": st.session_state.user, "通電日期": str(t_d), "最後更新": get_now_str()}
                for i, w in enumerate(wk): payload[f"人員{i+1}"] = w
                requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                st.success("任務指派成功！"); time.sleep(0.5); st.rerun()

    # --- ⚙️ 設定管理 ---
    elif st.session_state.menu_selection == "⚙️ 設定管理":
        st.title("⚙️ 系統設定")
        with st.form("config_form"):
            so = st.text_area("製令清單 (逗號隔開)", ",".join(order_list))
            sl = st.text_area("組長清單", ",".join(all_leaders))
            ss = st.text_area("人員清單", ",".join(all_staff))
            sp = st.text_area("工序清單", ",".join(process_list))
            sm = st.text_area("組長:工序綁定 (格式 組長:工序1,工序2)", "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()]))
            staff_in = st.text_area("組長:人員綁定 (格式 組長:人員1,人員2)", "\n".join([f"{k}:{','.join(v)}" for k, v in staff_map.items()]))
            
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
                st.success("設定更新成功！"); time.sleep(0.8); st.rerun()
