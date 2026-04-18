import streamlit as st
import pandas as pd
import datetime
import requests
import json
import math

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
        "all_staff": ["徐梓翔", "陳德文", "人員C"], 
        "processes": ["骨架作業", "前置作業", "配電作業", "模組作業", "水平調整", "通電作業", "IPQC表單查檢", "S.T作業", "收機清潔", "包機作業", "異常", "欠料", "PACKING", "前置作業(門板組立)"],
        "order_list": ["26M0041-01", "26M0041-02", "26M0051-01", "12345"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=10)
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
st.set_page_config(page_title="大量科技公佈欄", layout="wide")

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
        min-height: 48px;
        align-items: center;
    }
    .table-row:last-child { border-bottom: none; }
    .cell-proc {
        width: 110px;
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
    .badge-leader { background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 900; }
    .badge-main { background: #1e40af; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 900; }
    .badge-sub { background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; border: 1px solid #cbd5e1; }
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
    st.title("⚓ 大量科技公佈欄 - 登入")
    u = st.selectbox("👤 請選擇您的姓名", sorted(all_leaders + all_staff))
    if st.button("確認進入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **目前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 製造部公佈欄", "📜 完工紀錄查詢", "📝 任務派發", "⚙️ 設定管理"])
    
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 製造部公佈欄 ---
    if menu == "📊 製造部公佈欄":
        st.markdown('<h1 style="text-align:center; color:#1e40af; font-weight:900;">📋 大量科技製造部派工進度</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-panel">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            s_order = c1.selectbox("🔍 篩選製令", ["全部"] + sorted(order_list))
            s_staff = c2.selectbox("👤 篩選人員/組長", ["全部"] + sorted(all_leaders + all_staff))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=10)
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs)
                df = df.fillna("NA") 
                
                unique_orders = df["製令"].unique()
                filtered_orders = [o for o in unique_orders if (s_order == "全部" or str(o) == str(s_order))]
                
                cols = st.columns(3)
                for idx, o_id in enumerate(filtered_orders):
                    o_df = df[df["製令"] == o_id]
                    p_date_val = o_df.sort_values("提交時間", ascending=False).iloc[0].get("通電日期", "未設定")
                    p_date = str(p_date_val) if p_date_val != "nan" else "未設定"

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
                            row_cols = st.columns([0.85, 0.15])
                            
                            if not match.empty:
                                row = match.iloc[0]
                                leader = row.get("組長", "-")
                                w1 = row.get("人員1", "NA")
                                others = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", None, ""]]
                                
                                staff_html = f'<div class="badge-leader">L: {leader}</div>'
                                if w1 != "NA": staff_html += f'<div class="badge-main">{w1}</div>'
                                staff_html += "".join([f'<div class="badge-sub">{s}</div>' for s in others])
                                
                                with row_cols[0]:
                                    st.markdown(f'<div class="table-row"><div class="cell-proc">{proc}</div><div class="cell-staff">{staff_html}</div></div>', unsafe_allow_html=True)
                                with row_cols[1]:
                                    if st.button("✅", key=f"fin_{row['id']}"):
                                        finish_data = {k: (v if not (isinstance(v, float) and math.isnan(v)) else "NA") for k, v in row.to_dict().items()}
                                        finish_data["完工時間"] = get_now_str()
                                        finish_data["完工人員"] = st.session_state.user
                                        
                                        try:
                                            res_post = requests.post(f"{FINISH_URL}.json", data=json.dumps(finish_data), timeout=10)
                                            if res_post.status_code == 200:
                                                requests.delete(f"{DB_URL}/{row['id']}.json", timeout=10)
                                                st.success("完工成功！")
                                                st.rerun()
                                            else:
                                                st.error(f"寫入失敗: {res_post.status_code}")
                                        except Exception as e:
                                            st.error(f"連線失敗: {str(e)}")
                            else:
                                with row_cols[0]:
                                    st.markdown(f'<div class="table-row"><div class="cell-proc" style="color:#cbd5e1;">{proc}</div><div class="cell-staff" style="color:#cbd5e1; font-size:11px;">未派工</div></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("💡 目前沒有任何派工紀錄。")
        except Exception as e:
            st.error(f"❌ 讀取資料庫失敗")

    # --- 📜 完工紀錄查詢 (更新部分：顯示人員 1-5，隱藏組長與完工人員) ---
    elif menu == "📜 完工紀錄查詢":
        st.markdown('<h2 style="color:#1e40af;">📜 歷史完工紀錄查詢</h2>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{FINISH_URL}.json", timeout=10)
            f_data = r.json()
            if f_data:
                f_list = [v for k, v in f_data.items() if isinstance(v, dict)]
                f_df = pd.DataFrame(f_list)
                
                # 確保人員 1~5 欄位都存在並處理缺失值
                display_cols = ["完工時間", "製令", "製造工序", "人員1", "人員2", "人員3", "人員4", "人員5"]
                for col in display_cols:
                    if col not in f_df.columns:
                        f_df[col] = "NA"
                
                f_df = f_df.fillna("NA")
                
                # 顯示表格，僅包含指定的 8 個欄位
                st.dataframe(f_df[display_cols].sort_values("完工時間", ascending=False), use_container_width=True)
            else:
                st.info("目前尚無完工紀錄")
        except:
            st.error("無法取得完工紀錄")

    # --- 📝 任務派發 ---
    elif menu == "📝 任務派發":
        st.markdown('<h2 style="color:#1e40af;">📝 任務派發 / 內容修正</h2>', unsafe_allow_html=True)
        if "pending_payload" not in st.session_state:
            st.session_state.pending_payload = None
            st.session_state.pending_key = None

        with st.form("dispatch_form"):
            c1, c2, c3, c4 = st.columns(4)
            target_o = c1.selectbox("1. 製令編號", order_list)
            target_p = c2.selectbox("2. 製造工序", process_list)
            target_l = c3.selectbox("3. 指派組長", all_leaders)
            target_d = c4.date_input("4. 通電日期", datetime.date.today())
            
            st.write("---")
            st.write("🔧 分派組員 (人員 1 為主要標籤)")
            pc = st.columns(5)
            workers = [pc[i].selectbox(f"人員 {i+1}", ["NA"] + all_staff, key=f"ws_{i}") for i in range(5)]
            submit_clicked = st.form_submit_button("🚀 準備發布")
            
            if submit_clicked:
                try:
                    r = requests.get(f"{DB_URL}.json", timeout=10)
                    db_data = r.json()
                    target_key = None
                    if db_data:
                        for key, val in db_data.items():
                            if str(val.get("製令")) == str(target_o) and val.get("製造工序") == target_p:
                                target_key = key
                                break
                    
                    payload = {
                        "製令": str(target_o), 
                        "製造工序": target_p, 
                        "組長": target_l,
                        "通電日期": str(target_d),
                        "人員1": workers[0], "人員2": workers[1], "人員3": workers[2], "人員4": workers[3], "人員5": workers[4],
                        "提交時間": get_now_str()
                    }

                    if target_key:
                        st.session_state.pending_payload = payload
                        st.session_state.pending_key = target_key
                    else:
                        res = requests.post(f"{DB_URL}.json", data=json.dumps(payload), timeout=10)
                        if res.status_code == 200:
                            st.success(f"✅ 已成功新增製令 {target_o} 派工")
                            st.rerun()
                except:
                    st.error(f"❌ 連線異常")

        if st.session_state.pending_payload:
            st.warning(f"⚠️ 是否覆蓋製令【{st.session_state.pending_payload['製令']}】的【{st.session_state.pending_payload['製造工序']}】紀錄？")
            cc1, cc2, _ = st.columns([1, 1, 2])
            if cc1.button("✅ 確認覆蓋", type="primary"):
                res = requests.put(f"{DB_URL}/{st.session_state.pending_key}.json", data=json.dumps(st.session_state.pending_payload))
                if res.status_code == 200:
                    st.session_state.pending_payload = None
                    st.session_state.pending_key = None
                    st.rerun()
            if cc2.button("❌ 取消"):
                st.session_state.pending_payload = None
                st.session_state.pending_key = None
                st.rerun()

    # --- ⚙️ 設定管理 ---
    elif menu == "⚙️ 設定管理":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統資料後台管理</h2>', unsafe_allow_html=True)
        with st.form("admin_settings"):
            edit_o = st.text_area("製令編號設定 (逗號分隔)", value=",".join(order_list))
            edit_l = st.text_area("組長名單設定 (逗號分隔)", value=",".join(all_leaders))
            edit_s = st.text_area("一般人員名單設定 (逗號分隔)", value=",".join(all_staff))
            edit_p = st.text_area("工序流程設定 (逗號分隔)", value=",".join(process_list))
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
