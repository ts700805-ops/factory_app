import streamlit as st
import pandas as pd
import datetime
import requests
import json
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
                if "leader_map" not in data: data["leader_map"] = {}
                if "process_map" not in data: data["process_map"] = {}
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面樣式 ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .order-card { 
        background: white; border-radius: 12px; border: 1px solid #e2e8f0; 
        margin-bottom: 20px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .order-header { 
        background: #1e3a8a; color: white; padding: 12px 20px; 
        font-weight: 900; display: flex; justify-content: space-between; align-items: center; 
    }
    .power-date-tag { 
        background: #facc15; color: #1e3a8a; padding: 4px 12px; 
        border-radius: 6px; font-size: 14px; font-weight: bold; 
    }
    .proc-row { 
        display: flex; align-items: center; 
        border-bottom: 1.5px solid #cbd5e1; 
        padding: 10px 15px;
    }
    .proc-row:last-child { border-bottom: none; }
    .proc-name { width: 140px; font-weight: 800; color: #1e3a8a; font-size: 15px; }
    .staff-area { flex-grow: 1; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    .badge-main { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .badge-sub { background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 12px; border: 1px solid #cbd5e1; }
    .status-done { color: #10b981; font-weight: bold; font-size: 14px; }
    .status-empty { color: #cbd5e1; font-style: italic; font-size: 13px; }
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

if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 製造部派工專區"
if "edit_target" not in st.session_state:
    st.session_state.edit_target = None

if "user" not in st.session_state:
    st.title("⚓ 超慧科技管理系統 - 登入")
    u = st.selectbox("👤 請選擇您的姓名", sorted(list(set(all_leaders + all_staff))))
    if st.button("確認進入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    nav = st.sidebar.radio("功能導航", ["📊 製造部派工專區", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if nav != st.session_state.menu_selection:
        st.session_state.menu_selection = nav
        st.rerun()

    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部派工專區 ---
    if st.session_state.menu_selection == "📊 製造部派工專區":
        st.markdown('<h1 style="text-align:center; color:#1e3a8a; font-weight:900;">📋 製造部派工進度專區</h1>', unsafe_allow_html=True)
        
        # 決定目前使用者要看到的工序清單
        current_user = st.session_state.user
        if current_user in process_map:
            # 只顯示該組長綁定的工序
            my_display_procs = process_map[current_user]
        else:
            # 如果是管理員或不在清單中，顯示全部
            my_display_procs = process_list

        c1, c2 = st.columns(2)
        s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
        s_staff = c2.selectbox("👤 篩選人員", ["全部"] + sorted(list(set(all_leaders + all_staff))))

        try:
            r_work = requests.get(f"{DB_URL}.json").json() or {}
            r_finish = requests.get(f"{FINISH_URL}.json").json() or {}
            df_work = pd.DataFrame([dict(v, id=k) for k, v in r_work.items()]).fillna("NA") if r_work else pd.DataFrame()
            df_finish = pd.DataFrame([dict(v, id=k) for k, v in r_finish.items()]).fillna("NA") if r_finish else pd.DataFrame()

            display_orders = [o for o in order_list if (s_order == "全部" or str(o) == str(s_order))]
            cols = st.columns(2)
            for idx, o_id in enumerate(display_orders):
                o_df = df_work[df_work["製令"] == str(o_id)]
                
                # 執行人員篩選邏輯
                if s_staff != "全部" and not o_df.empty:
                    check_cols = ["組長", "人員1", "人員2", "人員3", "人員4", "人員5"]
                    if not o_df[[c for c in check_cols if c in o_df.columns]].apply(lambda x: s_staff in x.values, axis=1).any():
                        continue

                p_date = "未設定"
                if not o_df.empty: p_date = str(o_df.iloc[0].get("通電日期", "未設定"))

                with cols[idx % 2]:
                    st.markdown(f'<div class="order-card"><div class="order-header"><div>📦 製令：{o_id}</div><div class="power-date-tag">⚡ 通電：{p_date}</div></div>', unsafe_allow_html=True)
                    # 僅迴圈顯示該使用者綁定的工序
                    for proc in my_display_procs:
                        m_w = o_df[o_df["製造工序"] == proc]
                        m_f = df_finish[(df_finish["製令"] == str(o_id)) & (df_finish["製造工序"] == proc)] if not df_finish.empty else pd.DataFrame()

                        r_ui = st.columns([0.6, 0.15, 0.25])
                        with r_ui[0]:
                            html = ""
                            if not m_w.empty:
                                row = m_w.iloc[0]
                                for i in range(1, 6):
                                    p = row.get(f"人員{i}")
                                    if p and p != "NA": html += f'<div class="{"badge-main" if i==1 else "badge-sub"}">{p}</div>'
                            elif not m_f.empty: html = '<span class="status-done">✅ 已完工</span>'
                            else: html = '<span class="status-empty">尚未派工</span>'
                            st.markdown(f'<div class="proc-row"><div class="proc-name">{proc}</div><div class="staff-area">{html}</div></div>', unsafe_allow_html=True)
                        
                        with r_ui[1]:
                            if st.button("✏️", key=f"ed_{o_id}_{proc}"):
                                st.session_state.edit_target = {"order": str(o_id), "proc": proc}
                                st.session_state.menu_selection = "📝 任務派發"
                                st.rerun()
                        with r_ui[2]:
                            if not m_w.empty:
                                if st.button("確認完工", key=f"ok_{o_id}_{proc}"):
                                    dat = m_w.iloc[0].to_dict()
                                    dat["完工時間"] = get_now_str()
                                    dat["完工人員"] = st.session_state.user
                                    requests.post(f"{FINISH_URL}.json", data=json.dumps(dat))
                                    requests.delete(f"{DB_URL}/{dat['id']}.json")
                                    st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e: st.error(f"讀取資料失敗: {e}")

    # --- 📜 完工紀錄查詢 ---
    elif st.session_state.menu_selection == "📜 完工紀錄查詢":
        st.markdown('<h2>📜 歷史完工紀錄查詢</h2>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{FINISH_URL}.json").json()
            if r:
                all_logs = [dict(v, id=k) for k, v in r.items() if v]
                f_df = pd.DataFrame(all_logs).fillna("NA")
                
                q1, q2 = st.columns(2)
                sk = q1.text_input("🔍 搜尋製令")
                sp = q2.selectbox("👤 搜尋人員", ["全部"] + sorted(all_staff))
                if sk: f_df = f_df[f_df["製令"].astype(str).str.contains(sk)]
                if sp != "全部": f_df = f_df[f_df[["人員1", "人員2", "人員3", "人員4", "人員5"]].apply(lambda x: sp in x.values, axis=1)]
                
                drop_cols = ["id", "提交時間", "最後修改時間", "通電日期"]
                f_df_display = f_df.drop(columns=[c for c in drop_cols if c in f_df.columns])
                
                cols = f_df_display.columns.tolist()
                if "製令" in cols:
                    cols.insert(0, cols.pop(cols.index("製令")))
                    f_df_display = f_df_display[cols]
                
                st.dataframe(f_df_display.sort_values("完工時間", ascending=False), use_container_width=True)
                
                st.divider()
                with st.expander("🗑️ 刪除紀錄管理"):
                    del_id = st.selectbox("選擇要刪除的紀錄 ID", options=[log['id'] for log in all_logs], 
                                          format_func=lambda x: f"ID: {x} | {next(l['製令'] for l in all_logs if l['id']==x)} - {next(l['製造工序'] for l in all_logs if l['id']==x)}")
                    if st.button("🔴 確認刪除此筆紀錄"):
                        requests.delete(f"{FINISH_URL}/{del_id}.json")
                        st.success("紀錄已刪除"); time.sleep(0.5); st.rerun()
            else: st.info("目前無完工紀錄")
        except: st.error("讀取完工紀錄失敗")

    # --- 📝 任務派發 ---
    elif st.session_state.menu_selection == "📝 任務派發":
        st.markdown('<h2>📝 任務指派與編輯</h2>', unsafe_allow_html=True)
        def_o, def_p = order_list[0], process_list[0]
        if st.session_state.edit_target:
            def_o, def_p = st.session_state.edit_target["order"], st.session_state.edit_target["proc"]
            st.info(f"📍 正在編輯：{def_o} - {def_p}")

        with st.container(border=True):
            v1, v2, v3, v4 = st.columns(4)
            t_o = v1.selectbox("1. 選擇製令", order_list, index=order_list.index(def_o) if def_o in order_list else 0)
            t_l = v3.selectbox("3. 選擇組長", all_leaders)
            my_team = leader_map.get(t_l, all_staff)
            my_procs = process_map.get(t_l, process_list)
            t_p = v2.selectbox("2. 選擇工序", my_procs, index=my_procs.index(def_p) if def_p in my_procs else 0)
            t_d = v4.date_input("4. 設定通電日期")
            
            st.write(f"👥 **{t_l}** 的組員：{', '.join(my_team)}")
            wk = []
            for i, col in enumerate(st.columns(5)):
                wk.append(col.selectbox(f"人員 {i+1}", ["NA"] + my_team, key=f"w_{i}"))
            
            if st.button("🚀 確認發布任務", type="primary", use_container_width=True):
                payload = {"製令": str(t_o), "製造工序": t_p, "組長": t_l, "通電日期": str(t_d), "提交時間": get_now_str(),
                           "人員1": wk[0], "人員2": wk[1], "人員3": wk[2], "人員4": wk[3], "人員5": wk[4]}
                r_c = requests.get(f"{DB_URL}.json").json() or {}
                ek = next((k for k, v in r_c.items() if v.get("製令")==str(t_o) and v.get("製造工序")==t_p), None)
                if ek: requests.put(f"{DB_URL}/{ek}.json", data=json.dumps(payload))
                else: requests.post(f"{DB_URL}.json", data=json.dumps(payload))
                st.session_state.edit_target = None
                st.success("任務指派成功！"); time.sleep(0.5); st.rerun()

    # --- ⚙️ 設定管理 ---
    elif st.session_state.menu_selection == "⚙️ 設定管理":
        st.markdown('<h2>⚙️ 系統設定</h2>', unsafe_allow_html=True)
        with st.form("set_form"):
            so, sl, ss, sp = st.text_area("製令", ",".join(order_list)), st.text_area("組長", ",".join(all_leaders)), st.text_area("人員", ",".join(all_staff)), st.text_area("工序", ",".join(process_list))
            sm_l = st.text_area("組長:組員綁定", "\n".join([f"{k}:{','.join(v)}" for k, v in leader_map.items()]))
            sm_p = st.text_area("組長:工序綁定", "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()]))
            if st.form_submit_button("💾 儲存並更新"):
                def parse(s, nl=False):
                    if nl: return {x.split(":")[0].strip(): [y.strip() for y in x.split(":")[1].split(",")] for x in s.split("\n") if ":" in x}
                    return [x.strip() for x in s.replace("，", ",").split(",") if x.strip()]
                new_s = {"order_list": parse(so), "all_leaders": parse(sl), "all_staff": parse(ss), "processes": parse(sp),
                         "leader_map": parse(sm_l, True), "process_map": parse(sm_p, True)}
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_s))
                st.rerun()
