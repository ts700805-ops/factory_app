import streamlit as st
import pandas as pd
import datetime
import requests
import json
import math
import time

# --- 1. 核心資料與設定 ---
DB_BASE_URL = "https://my-factory-system-default-rtdb.firebaseio.com"
DB_URL = f"{DB_BASE_URL}/work_logs"
FINISH_URL = f"{DB_BASE_URL}/completed_logs"
SETTING_URL = f"{DB_BASE_URL}/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    default_settings = {
        "all_leaders": ["管理員", "組長A", "組長B"],
        "all_staff": ["徐梓翔", "陳德文", "胡瑄芸", "蕭詩瓊"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01", "12345"],
        "leader_map": {},
        "process_map": {}
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                for key in ["all_leaders", "all_staff", "processes", "order_list"]:
                    if key not in data or not data[key]:
                        data[key] = default_settings[key]
                if "leader_map" not in data or not isinstance(data["leader_map"], dict): data["leader_map"] = {}
                if "process_map" not in data or not isinstance(data["process_map"], dict): data["process_map"] = {}
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    /* 卡片容器 */
    .order-card { 
        background: white; 
        border-radius: 12px; 
        border: 1px solid #e2e8f0; 
        margin-bottom: 20px; 
        overflow: hidden; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    /* 標題列：深藍色背景 */
    .order-header { 
        background: #1e3a8a; 
        color: white; 
        padding: 12px 20px; 
        font-weight: 900; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
    }
    .header-left { font-size: 18px; display: flex; align-items: center; gap: 8px; }
    /* 通電日期標籤：黃色 */
    .power-date-tag { 
        background: #facc15; 
        color: #1e3a8a; 
        padding: 4px 12px; 
        border-radius: 6px; 
        font-size: 14px; 
        font-weight: bold; 
    }
    /* 工序行 */
    .proc-row { 
        display: flex; 
        align-items: center; 
        border-bottom: 1px solid #f1f5f9; 
        padding: 8px 15px;
    }
    .proc-name { 
        width: 120px; 
        font-weight: 800; 
        color: #1e3a8a; 
        font-size: 15px;
    }
    .staff-area { 
        flex-grow: 1; 
        display: flex; 
        flex-wrap: wrap; 
        gap: 6px; 
        align-items: center;
    }
    /* 標籤樣式 */
    .badge-leader { background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-main { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .badge-sub { background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 12px; border: 1px solid #cbd5e1; }
    .status-done { color: #10b981; font-weight: bold; font-size: 14px; }
    .status-empty { color: #94a3b8; font-style: italic; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心邏輯讀取 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
leader_map = settings.get("leader_map", {})
process_map = settings.get("process_map", {})

if "user" not in st.session_state:
    st.title("⚓ 超慧科技管理系統 - 登入")
    u = st.selectbox("👤 請選擇您的姓名", sorted(list(set(all_leaders + all_staff))))
    if st.button("確認進入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 製造部派工專區", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部派工專區 (一列兩個製令) ---
    if menu == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📋 製造部派工進度專區</h1>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
        s_staff = c2.selectbox("👤 篩選人員", ["全部"] + sorted(list(set(all_leaders + all_staff))))

        try:
            r_work = requests.get(f"{DB_URL}.json", timeout=10).json()
            r_finish = requests.get(f"{FINISH_URL}.json", timeout=10).json()
            
            df_work = pd.DataFrame([dict(v, id=k) for k, v in r_work.items()]).fillna("NA") if r_work else pd.DataFrame()
            df_finish = pd.DataFrame([dict(v, id=k) for k, v in r_finish.items()]).fillna("NA") if r_finish else pd.DataFrame()

            # 找出需要顯示的製令清單
            if not df_work.empty:
                unique_orders = df_work["製令"].unique()
                filtered_orders = [o for o in unique_orders if (s_order == "全部" or str(o) == str(s_order))]
                
                # 設定一列顯示 2 個卡片
                cols = st.columns(2)
                for idx, o_id in enumerate(filtered_orders):
                    o_df = df_work[df_work["製令"] == o_id]
                    
                    # 人員篩選邏輯
                    if s_staff != "全部":
                        check_cols = ["組長", "人員1", "人員2", "人員3", "人員4", "人員5"]
                        if not o_df[[c for c in check_cols if c in o_df.columns]].apply(lambda x: s_staff in x.values, axis=1).any():
                            continue

                    p_date = str(o_df.iloc[0].get("通電日期", "未設定"))
                    
                    with cols[idx % 2]:
                        st.markdown(f"""
                            <div class="order-card">
                                <div class="order-header">
                                    <div class="header-left">📦 製令：{o_id}</div>
                                    <div class="power-date-tag">⚡ 通電：{p_date}</div>
                                </div>
                        """, unsafe_allow_html=True)
                        
                        for proc in process_list:
                            # 檢查進行中
                            m_w = o_df[o_df["製造工序"] == proc]
                            # 檢查已完成
                            m_f = pd.DataFrame()
                            if not df_finish.empty:
                                m_f = df_finish[(df_finish["製令"] == o_id) & (df_finish["製造工序"] == proc)]

                            row_ui = st.columns([0.85, 0.15])
                            
                            with row_ui[0]:
                                staff_html = ""
                                if not m_w.empty:
                                    row = m_w.iloc[0]
                                    staff_html += f'<div class="badge-leader">L: {row.get("組長","")}</div>'
                                    for i in range(1, 6):
                                        p = row.get(f"人員{i}")
                                        if p and p != "NA":
                                            staff_html += f'<div class="{"badge-main" if i==1 else "badge-sub"}">{p}</div>'
                                elif not m_f.empty:
                                    staff_html = '<span class="status-done">✅ 已完工</span>'
                                else:
                                    staff_html = '<span class="status-empty">尚未派工</span>'
                                
                                st.markdown(f'<div class="proc-row"><div class="proc-name">{proc}</div><div class="staff-area">{staff_html}</div></div>', unsafe_allow_html=True)
                            
                            with row_ui[1]:
                                if not m_w.empty:
                                    if st.button("✅", key=f"btn_{m_w.iloc[0]['id']}"):
                                        row_data = m_w.iloc[0].to_dict()
                                        row_data["完工時間"] = get_now_str()
                                        row_data["完工人員"] = st.session_state.user
                                        requests.post(f"{FINISH_URL}.json", data=json.dumps(row_data))
                                        requests.delete(f"{DB_URL}/{row_data['id']}.json")
                                        st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("💡 目前無進行中的派工任務")
        except Exception as e:
            st.error(f"連線錯誤：{e}")

    # --- 📜 完工紀錄查詢 ---
    elif menu == "📜 完工紀錄查詢":
        st.markdown('<h2 style="color:#1e40af;">📜 歷史完工紀錄查詢</h2>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{FINISH_URL}.json", timeout=10)
            f_data = r.json()
            if f_data:
                all_finish_logs = [dict(v, id=k) for k, v in f_data.items() if v]
                f_df = pd.DataFrame(all_finish_logs).fillna("NA")
                
                sc1, sc2 = st.columns(2)
                f_order_input = sc1.text_input("🔍 搜尋製令 (關鍵字)")
                f_staff_s = sc2.selectbox("👤 搜尋人員", ["全部"] + sorted(all_staff))

                filtered_df = f_df.copy()
                if f_order_input:
                    filtered_df = filtered_df[filtered_df["製令"].astype(str).str.contains(f_order_input)]
                if f_staff_s != "全部":
                    mask = filtered_df[["人員1", "人員2", "人員3", "人員4", "人員5"]].apply(lambda x: f_staff_s in x.values, axis=1)
                    filtered_df = filtered_df[mask]

                if not filtered_df.empty:
                    st.dataframe(filtered_df.sort_values("完工時間", ascending=False), use_container_width=True)
                else:
                    st.warning("查無資料")
            else:
                st.info("尚無完工紀錄")
        except:
            st.error("讀取失敗")

    # --- 📝 任務派發 ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 任務指派系統</h2>', unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            t_o = c1.selectbox("1. 選擇製令", order_list)
            t_l = c3.selectbox("3. 指派組長", all_leaders)
            
            my_procs = process_map.get(t_l, process_list)
            t_p = c2.selectbox("2. 選擇工序", my_procs)
            t_d = c4.date_input("4. 通電日期")
            
            my_team = leader_map.get(t_l, all_staff)
            st.write(f"💡 {t_l} 的組員：{', '.join(my_team)}")
            
            pc = st.columns(5)
            workers = []
            for i in range(5):
                w = pc[i].selectbox(f"人員 {i+1}", ["NA"] + my_team, key=f"task_w{i}")
                workers.append(w)
            
            if st.button("🚀 確認發布任務", type="primary", use_container_width=True):
                payload = {
                    "製令": str(t_o), "製造工序": t_p, "組長": t_l, 
                    "通電日期": str(t_d), "提交時間": get_now_str(),
                    "人員1": workers[0], "人員2": workers[1], "人員3": workers[2], "人員4": workers[3], "人員5": workers[4]
                }
                # 覆蓋邏輯：同製令同工序則更新
                r_check = requests.get(f"{DB_URL}.json").json()
                existing_key = None
                if r_check:
                    existing_key = next((k for k, v in r_check.items() if v.get("製令")==str(t_o) and v.get("製造工序")==t_p), None)
                
                if existing_key:
                    requests.put(f"{DB_URL}/{existing_key}.json", data=json.dumps(payload))
                else:
                    requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                
                st.balloons()
                st.success("任務指派成功！")
                time.sleep(1)
                st.rerun()

    # --- ⚙️ 設定管理 ---
    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 後台設定管理</h2>', unsafe_allow_html=True)
        with st.expander("📌 基礎名單維護"):
            with st.form("base_config"):
                e_o = st.text_area("製令編號 (逗號隔開)", value=",".join(order_list))
                e_l = st.text_area("組長名單 (逗號隔開)", value=",".join(all_leaders))
                e_s = st.text_area("一般人員 (逗號隔開)", value=",".join(all_staff))
                e_p = st.text_area("工序流程 (逗號隔開)", value=",".join(process_list))
                if st.form_submit_button("💾 儲存設定"):
                    new_cfg = settings.copy()
                    new_cfg.update({
                        "order_list": [x.strip() for x in e_o.replace("，", ",").split(",") if x.strip()],
                        "all_leaders": [x.strip() for x in e_l.replace("，", ",").split(",") if x.strip()],
                        "all_staff": [x.strip() for x in e_s.replace("，", ",").split(",") if x.strip()],
                        "processes": [x.strip() for x in e_p.replace("，", ",").split(",") if x.strip()]
                    })
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                    st.rerun()
        
        with st.expander("🔗 組長與人員/工序綁定"):
            st.info("格式：組長:項目1,項目2")
            with st.form("binding_config"):
                curr_p = "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()])
                curr_l = "\n".join([f"{k}:{','.join(v)}" for k, v in leader_map.items()])
                new_p_str = st.text_area("工序綁定", value=curr_p)
                new_l_str = st.text_area("人員綁定", value=curr_l)
                if st.form_submit_button("🔗 儲存連結"):
                    def str_to_map(s):
                        res = {}
                        for line in s.split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                res[k.strip()] = [x.strip() for x in v.replace("，", ",").split(",") if x.strip()]
                        return res
                    new_cfg = settings.copy()
                    new_cfg["process_map"] = str_to_map(new_p_str)
                    new_cfg["leader_map"] = str_to_map(new_l_str)
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                    st.rerun()
