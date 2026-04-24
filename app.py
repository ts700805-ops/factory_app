import streamlit as st
import pandas as pd
import datetime
import requests
import json
import time

# --- 1. 核心資料與設定 (Firebase URL) ---
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
        "leader_map": {},
        "process_map": {}
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                for key in ["all_leaders", "all_staff", "processes", "order_list"]:
                    if key not in data or not data[key]: data[key] = default_settings[key]
                return data
        return default_settings
    except:
        return default_settings

# --- 2. 介面設定 ---
st.set_page_config(page_title="超慧科技管理系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .order-card { background: white; border-radius: 8px; border: 2px solid #1e40af; margin-bottom: 20px; width: 100%; overflow: hidden; }
    .order-title { background: #1e40af; color: white; padding: 10px 15px; font-weight: 900; display: flex; justify-content: space-between; align-items: center; }
    .power-date { background: #fbbf24; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .table-row-container { border-bottom: 1px solid #dee2e6; display: flex; align-items: center; min-height: 50px; }
    .row-finished { background-color: #f0fdf4; } /* 完工列的背景色 */
    .cell-proc { width: 140px; min-width: 140px; color: #1e40af; font-weight: 800; padding-left: 10px; font-size: 14px; }
    .cell-staff { flex-grow: 1; display: flex; flex-wrap: wrap; gap: 4px; padding: 5px; }
    .badge-staff { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .badge-done-tag { background: #22c55e; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-left: 5px; }
    .no-data { color: #94a3b8; font-size: 12px; font-style: italic; padding-left: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心數據讀取 ---
settings = get_settings()
all_leaders = settings.get("all_leaders", [])
all_staff = settings.get("all_staff", [])
process_list = settings.get("processes", [])
order_list = settings.get("order_list", [])
leader_map = settings.get("leader_map", {})
process_map = settings.get("process_map", {})

if "user" not in st.session_state:
    st.markdown('<h1 style="text-align:center; color:#1e3a8a;">⚓ 超慧科技管理系統</h1>', unsafe_allow_html=True)
    with st.columns([1,2,1])[1]:
        with st.container(border=True):
            u = st.selectbox("👤 請選擇組長登入", sorted(all_leaders))
            if st.button("確認進入", use_container_width=True, type="primary"):
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
        st.markdown('<h2 style="text-align:center; color:#1e40af; font-weight:900;">📋 製造部派工進度</h2>', unsafe_allow_html=True)
        
        current_user = st.session_state.user
        my_staff_list = leader_map.get(current_user, all_staff) 

        filter_c1, filter_c2 = st.columns(2)
        sel_order = filter_c1.selectbox("📦 篩選製令", ["全部"] + order_list)
        sel_staff = filter_c2.selectbox("👤 篩選人員", ["全部"] + sorted(my_staff_list))
        st.divider()

        my_procs = process_map.get(current_user, process_list) 

        try:
            db_res = requests.get(f"{DB_URL}.json", timeout=10).json() or {}
            fn_res = requests.get(f"{FINISH_URL}.json", timeout=10).json() or {}
            
            all_df = pd.DataFrame([dict(v, id=k) for k, v in db_res.items()]) if db_res else pd.DataFrame()
            done_df = pd.DataFrame([dict(v, id=k) for k, v in fn_res.items()]) if fn_res else pd.DataFrame()

            display_orders = [sel_order] if sel_order != "全部" else order_list
            display_cols = st.columns(2)
            card_idx = 0
            
            for o_id in display_orders:
                o_match = all_df[all_df["製令"] == str(o_id)] if not all_df.empty else pd.DataFrame()
                o_done = done_df[done_df["製令"] == str(o_id)] if not done_df.empty else pd.DataFrame()

                if sel_staff != "全部":
                    staff_cols = [f"人員{i}" for i in range(1, 6)]
                    in_progress = not o_match.empty and o_match[staff_cols].apply(lambda x: sel_staff in x.values, axis=1).any()
                    in_done = not o_done.empty and o_done[staff_cols].apply(lambda x: sel_staff in x.values, axis=1).any()
                    if not (in_progress or in_done): continue

                with display_cols[card_idx % 2]:
                    # 優先從進行中取得通電日期，若無則從完工紀錄取
                    p_date = "未設定"
                    if not o_match.empty: p_date = str(o_match.iloc[0].get("通電日期", "未設定"))
                    elif not o_done.empty: p_date = str(o_done.iloc[0].get("通電日期", "未設定"))
                    
                    st.markdown(f'<div class="order-card"><div class="order-title"><span>📦 製令：{o_id}</span><span class="power-date">⚡ 通電：{p_date}</span></div>', unsafe_allow_html=True)

                    for proc in my_procs:
                        proc_match = o_match[o_match["製造工序"] == proc] if not o_match.empty else pd.DataFrame()
                        proc_done = o_done[o_done["製造工序"] == proc] if not o_done.empty else pd.DataFrame()
                        
                        # 篩選人員邏輯
                        if sel_staff != "全部":
                            target = proc_match if not proc_match.empty else proc_done
                            if not target.empty:
                                if sel_staff not in target.iloc[0][[f"人員{i}" for i in range(1, 6)]].values: continue
                            else: continue

                        # 判斷背景與資料內容
                        row_class = "table-row-container row-finished" if not proc_done.empty else "table-row-container"
                        active_row = proc_match.iloc[0] if not proc_match.empty else (proc_done.iloc[0] if not proc_done.empty else None)

                        row_c1, row_c2, row_c3 = st.columns([0.7, 0.15, 0.15])
                        
                        with row_c1:
                            if active_row is not None:
                                staff_html = "".join([f'<div class="badge-staff">{active_row.get(f"人員{i}")}</div>' for i in range(1, 6) if active_row.get(f"人員{i}") and active_row.get(f"人員{i}") != "NA"])
                                done_tag = '<div class="badge-done-tag">✅ 完工</div>' if not proc_done.empty else ""
                                st.markdown(f'<div class="{row_class}"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}{done_tag}</div></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="table-row-container"><div class="cell-proc">{proc}</div><div class="no-data">尚未派工</div></div>', unsafe_allow_html=True)
                        
                        with row_c2:
                            # 編輯按鈕：只要有資料（不論完工與否）都能編輯
                            if active_row is not None:
                                with st.popover("✏️"):
                                    try: curr_d = pd.to_datetime(active_row.get("通電日期", "today")).date()
                                    except: curr_d = datetime.date.today()
                                    new_d = st.date_input("日期", value=curr_d, key=f"d_{o_id}_{proc}")
                                    staff_opts = ["NA"] + my_staff_list
                                    new_staff = [st.selectbox(f"人員{i}", staff_opts, index=staff_opts.index(active_row.get(f"人員{i}", "NA")) if active_row.get(f"人員{i}") in staff_opts else 0, key=f"s{i}_{o_id}_{proc}") for i in range(1, 6)]
                                    if st.button("儲存修改", key=f"sv_{o_id}_{proc}", use_container_width=True):
                                        edit_p = active_row.to_dict()
                                        edit_p.update({"通電日期": str(new_d), "最後修改": get_now_str(), **{f"人員{i+1}": new_staff[i] for i in range(5)}})
                                        # 根據原本在哪個資料庫就更新哪邊
                                        target_url = FINISH_URL if not proc_done.empty else DB_URL
                                        requests.put(f"{target_url}/{active_row['id']}.json", data=json.dumps(edit_p))
                                        st.rerun()

                        with row_c3:
                            # 完工/取消完工 按鈕
                            if not proc_match.empty:
                                if st.button("✅", key=f"ok_{o_id}_{proc}", help="標記為完工"):
                                    row = proc_match.iloc[0].to_dict()
                                    row["完工時間"], row["完工人員"] = get_now_str(), current_user
                                    requests.post(f"{FINISH_URL}.json", data=json.dumps(row))
                                    requests.delete(f"{DB_URL}/{row['id']}.json")
                                    st.rerun()
                            elif not proc_done.empty:
                                if st.button("🔄", key=f"undo_{o_id}_{proc}", help="取消完工狀態"):
                                    row = proc_done.iloc[0].to_dict()
                                    if "完工時間" in row: del row["完工時間"]
                                    if "完工人員" in row: del row["完工人員"]
                                    requests.post(f"{DB_URL}.json", data=json.dumps(row))
                                    requests.delete(f"{FINISH_URL}/{row['id']}.json")
                                    st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    card_idx += 1
        except Exception as e: st.error(f"錯誤: {e}")

    # --- 📜 完工紀錄查詢、📝 任務派發、⚙️ 設定管理 保持原有邏輯 ---
    elif menu == "📜 完工紀錄查詢":
        st.markdown('<h2 style="color:#1e40af;">📜 歷史完工紀錄查詢</h2>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{FINISH_URL}.json", timeout=10).json()
            if r:
                f_df = pd.DataFrame([dict(v, id=k) for k, v in r.items() if v]).fillna("NA")
                f_df = f_df.drop(columns=[c for c in ["提交時間", "最後修改時間", "最後修改"] if c in f_df.columns])
                if "製令" in f_df.columns:
                    cols = ["製令"] + [c for c in f_df.columns if c not in ["製令", "id"]]
                    f_df = f_df[cols + ["id"]]
                q1, q2 = st.columns(2)
                sk, sp = q1.text_input("🔍 搜尋製令"), q2.selectbox("👤 搜尋人員", ["全部"] + sorted(all_staff))
                if sk: f_df = f_df[f_df["製令"].astype(str).str.contains(sk)]
                if sp != "全部": f_df = f_df[f_df[[f"人員{i}" for i in range(1, 6)]].apply(lambda x: sp in x.values, axis=1)]
                st.dataframe(f_df.drop(columns=["id"]).sort_values("完工時間", ascending=False), use_container_width=True)
                with st.expander("🗑️ 刪除紀錄管理"):
                    del_id = st.selectbox("選擇要刪除的紀錄 ID", f_df["id"].tolist(), format_func=lambda x: f"{f_df[f_df['id']==x]['製令'].values[0]} - {f_df[f_df['id']==x]['製造工序'].values[0]}")
                    if st.button("確認刪除", type="primary"):
                        requests.delete(f"{FINISH_URL}/{del_id}.json"); st.success("已刪除"); time.sleep(0.5); st.rerun()
            else: st.info("無紀錄")
        except Exception as e: st.error(f"讀取失敗: {e}")

    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 任務指派</h2>', unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            t_o, t_l = c1.selectbox("1. 製令", order_list), c3.selectbox("3. 組長", all_leaders, index=all_leaders.index(st.session_state.user) if st.session_state.user in all_leaders else 0)
            t_p, t_d = c2.selectbox("2. 工序", process_map.get(t_l, process_list)), c4.date_input("4. 通電日期")
            wk = [col.selectbox(f"人員 {i+1}", ["NA"] + leader_map.get(t_l, all_staff), key=f"nw_{i}") for i, col in enumerate(st.columns(5))]
            if st.button("🚀 發布任務", type="primary", use_container_width=True):
                payload = {"製令": str(t_o), "製造工序": t_p, "組長": t_l, "通電日期": str(t_d), "提交時間": get_now_str(), **{f"人員{i+1}": wk[i] for i in range(5)}}
                requests.post(f"{DB_URL}.json", data=json.dumps(payload)); st.success("成功"); time.sleep(0.5); st.rerun()

    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統設定管理</h2>', unsafe_allow_html=True)
        with st.form("sys_config"):
            so, sl, ss, sp = st.text_area("製令清單", ",".join(order_list)), st.text_area("組長名單", ",".join(all_leaders)), st.text_area("所有人員", ",".join(all_staff)), st.text_area("工序清單", ",".join(process_list))
            sm_p = st.text_area("組長:工序綁定", "\n".join([f"{k}:{','.join(v)}" for k, v in process_map.items()]))
            sm_l = st.text_area("組長:組員綁定", "\n".join([f"{k}:{','.join(v)}" for k, v in leader_map.items()]))
            if st.form_submit_button("💾 儲存所有設定"):
                def parse(s, nl=False):
                    if nl: return {x.split(":")[0].strip(): [y.strip() for y in x.split(":")[1].split(",")] for x in s.split("\n") if ":" in x}
                    return [x.strip() for x in s.replace("，", ",").split(",") if x.strip()]
                new_conf = {"order_list": parse(so), "all_leaders": parse(sl), "all_staff": parse(ss), "processes": parse(sp), "process_map": parse(sm_p, True), "leader_map": parse(sm_l, True)}
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_conf)); st.success("設定成功！"); time.sleep(0.5); st.rerun()
