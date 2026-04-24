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
    .order-card { background: white; border-radius: 8px; border: 2px solid #1e40af; margin-bottom: 25px; overflow: hidden; }
    .order-title { background: #1e40af; color: white; padding: 10px 15px; font-weight: 900; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #1e40af; }
    .power-date { background: #fbbf24; color: #1e40af; padding: 2px 10px; border-radius: 4px; font-size: 13px; font-weight: bold; }
    .table-row-container { border-bottom: 1px solid #dee2e6; display: flex; align-items: stretch; }
    .cell-proc { width: 100px; min-width: 100px; background: #f1f5f9; color: #1e40af; font-weight: 800; padding: 10px; display: flex; align-items: center; border-right: 1px solid #dee2e6; font-size: 14px; }
    .cell-staff { flex-grow: 1; padding: 10px; display: flex; align-items: center; flex-wrap: wrap; gap: 6px; background: white; }
    .badge-leader { background: #f59e0b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge-main { background: #1e40af; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 5px; border-radius: 4px; font-size: 10px; border: 1px solid #cbd5e1; }
    .search-panel { background: white; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; }
    .history-header { background: #f1f5f9; font-weight: bold; border-bottom: 2px solid #cbd5e1; padding: 10px 5px; text-align: left; }
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

    # --- 📊 製造部派工專區 ---
    if menu == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📋 超慧科技製造部派工進度</h1>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="search-panel">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
            s_staff = c2.selectbox("👤 篩選人員/組長", ["全部"] + sorted(list(set(all_leaders + all_staff))))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=10)
            db_data = r.json()
            if db_data and isinstance(db_data, dict):
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs).fillna("NA")
                unique_orders = df["製令"].unique()
                filtered_orders = [o for o in unique_orders if (s_order == "全部" or str(o) == str(s_order))]
                
                cols = st.columns(3)
                display_count = 0
                for o_id in filtered_orders:
                    o_df = df[df["製令"] == o_id]
                    if s_staff != "全部":
                        check_cols = ["組長", "人員1", "人員2", "人員3", "人員4", "人員5"]
                        if not o_df[[c for c in check_cols if c in o_df.columns]].apply(lambda x: s_staff in x.values, axis=1).any(): continue

                    p_date = str(o_df.iloc[0].get("通電日期", "未設定"))
                    with cols[display_count % 3]:
                        st.markdown(f'<div class="order-card"><div class="order-title"><span>📦 製令：{o_id}</span><span class="power-date">⚡ 通電：{p_date}</span></div>', unsafe_allow_html=True)
                        for proc in process_list:
                            match = o_df[o_df["製造工序"] == proc]
                            if not match.empty:
                                row = match.iloc[0]
                                row_cols = st.columns([0.85, 0.15]) 
                                staff_html = f'<div class="badge-leader">L: {row.get("組長","")}</div>'
                                for i in range(1, 6):
                                    p_val = row.get(f"人員{i}")
                                    if p_val not in ["NA", ""]:
                                        badge_class = "badge-main" if i == 1 else "badge-sub"
                                        staff_html += f'<div class="{badge_class}">{p_val}</div>'
                                
                                with row_cols[0]: 
                                    st.markdown(f'<div class="table-row-container"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                                with row_cols[1]:
                                    if st.button("✅", key=f"fin_{row['id']}"):
                                        clean_data = {k: (v if not (isinstance(v, float) and math.isnan(v)) else "NA") for k, v in row.to_dict().items()}
                                        clean_data["完工時間"] = get_now_str()
                                        clean_data["完工人員"] = st.session_state.user
                                        if requests.post(f"{FINISH_URL}.json", data=json.dumps(clean_data)).status_code == 200:
                                            requests.delete(f"{DB_URL}/{row['id']}.json")
                                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    display_count += 1
            else: st.info("💡 目前資料庫為空，尚無派工紀錄")
        except: st.warning("💡 系統提示：目前無可顯示之派工資料。")

    # --- 📜 完工紀錄查詢 ---
    elif menu == "📜 完工紀錄查詢":
        st.markdown('<h2 style="color:#1e40af;">📜 歷史完工紀錄查詢</h2>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{FINISH_URL}.json", timeout=10)
            f_data = r.json()
            if f_data and isinstance(f_data, dict):
                all_finish_logs = [dict(v, id=k) for k, v in f_data.items() if v]
                f_df = pd.DataFrame(all_finish_logs).fillna("NA")
                st.markdown('<div class="search-panel">', unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                f_order_input = sc1.text_input("🔍 搜尋製令 (關鍵字過濾)", key="search_box")
                f_staff_s = sc2.selectbox("👤 搜尋人員", ["全部"] + sorted(all_staff))
                st.markdown('</div>', unsafe_allow_html=True)

                filtered_df = f_df.copy()
                if f_order_input:
                    filtered_df = filtered_df[filtered_df["製令"].astype(str).str.contains(f_order_input, case=False, na=False)]
                if f_staff_s != "全部":
                    staff_cols = ["人員1", "人員2", "人員3", "人員4", "人員5"]
                    mask = filtered_df[staff_cols].apply(lambda row: f_staff_s in row.values, axis=1)
                    filtered_df = filtered_df[mask]

                if not filtered_df.empty:
                    filtered_df = filtered_df.sort_values("完工時間", ascending=False)
                    # 修正 st.dataframe 括號問題
                    st.dataframe(filtered_df, use_container_width=True)
                else: st.warning("⚠️ 查無資料")
            else: st.info("💡 目前歷史紀錄為空")
        except Exception as e: st.error(f"讀取失敗：{e}")

    # --- 📝 任務派發 ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 任務派發 / 內容修正</h2>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        t_o = c1.selectbox("1. 製令編號", order_list)
        t_l = c3.selectbox("3. 指派組長", all_leaders)

        my_processes = process_map.get(t_l, [])
        display_processes = my_processes if my_processes else process_list
        t_p = c2.selectbox("2. 製造工序", display_processes)
        t_d = c4.date_input("4. 通電日期")
        st.write("---")
        
        my_team = leader_map.get(t_l, [])
        display_staff = my_team if my_team else all_staff
        st.caption(f"💡 目前 {t_l} 的組員名單：{', '.join(display_staff) if display_staff else '未綁定'} | 負責工序：{', '.join(my_processes) if my_processes else '全部'}")
        
        pc = st.columns(5)
        workers = []
        for i in range(5):
            w = pc[i].selectbox(f"人員 {i+1}", ["NA"] + display_staff, key=f"w{i}")
            workers.append(w)
            
        if st.button("🚀 準備發布", type="primary", use_container_width=True):
            payload = {"製令": str(t_o), "製造工序": t_p, "組長": t_l, "通電日期": str(t_d), "提交時間": get_now_str()}
            for i in range(5): payload[f"人員{i+1}"] = workers[i]
            try:
                r = requests.get(f"{DB_URL}.json")
                r_check = r.json()
                target_key = None
                if r_check and isinstance(r_check, dict):
                    target_key = next((k for k, v in r_check.items() if v and v.get("製令")==str(t_o) and v.get("製造工序")==t_p), None)
                
                if target_key: requests.put(f"{DB_URL}/{target_key}.json", data=json.dumps(payload))
                else: requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                
                st.balloons()
                st.success(f"✅ 製令 {t_o} 發布完成！")
                time.sleep(1.5)
                st.rerun()
            except Exception as e: st.error(f"發布失敗：{str(e)}")

    # --- ⚙️ 設定管理 ---
    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統資料後台管理</h2>', unsafe_allow_html=True)
        
        # 1. 基本名單設定
        with st.expander("📌 基本名單設定", expanded=True):
            with st.form("admin_settings"):
                e_o = st.text_area("製令編號 (逗號隔開)", value=",".join(order_list))
                e_l = st.text_area("組長名單 (逗號隔開)", value=",".join(all_leaders))
                e_s = st.text_area("一般人員 (逗號隔開)", value=",".join(all_staff))
                e_p = st.text_area("工序流程 (逗號隔開)", value=",".join(process_list))
                if st.form_submit_button("💾 儲存基本名單"):
                    new_cfg = settings.copy()
                    new_cfg.update({
                        "order_list": [x.strip() for x in e_o.replace("，", ",").split(",") if x.strip()],
                        "all_leaders": [x.strip() for x in e_l.replace("，", ",").split(",") if x.strip()],
                        "all_staff": [x.strip() for x in e_s.replace("，", ",").split(",") if x.strip()],
                        "processes": [x.strip() for x in e_p.replace("，", ",").split(",") if x.strip()]
                    })
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                    st.success("基本名單更新成功")
                    time.sleep(1)
                    st.rerun()

        st.markdown("---")
        
        # 2. 組長與工序對應綁定
        st.markdown("### 🛠️ 組長與工序對應綁定")
        p_map_text_list = [f"{leader}:{','.join(procs)}" for leader, procs in process_map.items()]
        current_p_map_str = "\n".join(p_map_text_list)
        with st.form("process_binding_form"):
            st.info("💡 格式：組長姓名:工序1,工序2 (支援全形符號)")
            new_p_map_str = st.text_area("工序綁定清單區", value=current_p_map_str, height=150)
            if st.form_submit_button("🔗 儲存工序綁定"):
                new_p_map = {}
                try:
                    lines = [l.strip() for l in new_p_map_str.split("\n") if l.strip()]
                    for line in lines:
                        line = line.replace("：", ":")
                        if ":" in line:
                            l_part, p_part = line.split(":", 1)
                            new_p_map[l_part.strip()] = [x.strip() for x in p_part.replace("，", ",").split(",") if x.strip()]
                    new_cfg = settings.copy()
                    new_cfg["process_map"] = new_p_map
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                    st.success("✅ 工序連動已更新！")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("格式錯誤，請檢查冒號與逗號")

        st.markdown("---")
        
        # 3. 組長與人員對應綁定
        st.markdown("### 👥 組長與人員對應綁定")
        map_text_list = [f"{leader}:{','.join(staff_list)}" for leader, staff_list in leader_map.items()]
        current_map_str = "\n".join(map_text_list)
        with st.form("leader_binding_quick_form"):
            st.info("💡 格式：組長姓名:人員1,人員2")
            new_map_str = st.text_area("組員綁定清單區", value=current_map_str, height=200)
            if st.form_submit_button("🔗 儲存人員綁定"):
                new_map = {}
                try:
                    lines = [l.strip() for l in new_map_str.split("\n") if l.strip()]
                    for line in lines:
                        line = line.replace("：", ":")
                        if ":" in line:
                            leader_part, staff_part = line.split(":", 1)
                            new_map[leader_part.strip()] = [x.strip() for x in staff_part.replace("，", ",").split(",") if x.strip()]
                    new_cfg = settings.copy()
                    new_cfg["leader_map"] = new_map
                    requests.put(f"{SETTING_URL}.json", data=json.dumps(new_cfg))
                    st.success("✅ 人員綁定已更新！")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("格式錯誤，請檢查冒號與逗號")
