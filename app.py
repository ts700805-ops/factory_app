import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心設定 ---
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
        "order_list": ["001", "002"],
        "assigners": ["管理員"]
    }
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                return {
                    "all_staff": data.get("all_staff", default_settings["all_staff"]),
                    "processes": data.get("processes", default_settings["processes"]),
                    "order_list": data.get("order_list", default_settings["order_list"]),
                    "assigners": data.get("assigners", default_settings["assigners"])
                }
        return default_settings
    except Exception:
        return default_settings

# --- 2. 頁面配置與「超強固定」CSS ---
st.set_page_config(page_title="超慧科技●生產看板", layout="wide")

st.markdown("""
    <style>
    /* 隱藏 Streamlit 原生多餘邊距 */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    
    /* 1. 頂部搜尋區固定 */
    .fixed-top-header {
        position: sticky;
        top: 0;
        background: #f8fafc;
        z-index: 999;
        padding-bottom: 10px;
        border-bottom: 2px solid #e2e8f0;
    }

    /* 2. 看板主容器：強制不讓網頁出現大捲動條 */
    .board-container {
        display: flex;
        gap: 20px;
        padding: 10px;
        height: 75vh;  /* 鎖定看板高度為視窗的 75% */
        overflow-x: auto; /* 橫向排列製令 */
        align-items: flex-start;
    }

    /* 3. 製令卡片：固定寬度、高度，內部分層 */
    .order-card {
        min-width: 320px;
        max-width: 320px;
        height: 100%; /* 跟隨父容器高度 */
        background: white;
        border-radius: 12px;
        border: 2px solid #1e40af;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    /* 4. [絕對固定] 製令標題藍色區塊 */
    .card-title-fixed {
        background: #1e40af;
        color: white;
        padding: 15px;
        font-size: 20px;
        font-weight: 900;
        flex-shrink: 0; /* 禁止壓縮 */
        text-align: center;
        border-bottom: 2px solid #1e3a8a;
    }

    /* 5. [獨立捲動] 工序內容區塊 */
    .card-body-scroll {
        flex-grow: 1;
        overflow-y: scroll !important; /* 強制開啟垂直捲動 */
        padding: 10px;
        background: #ffffff;
    }

    /* 工序格子設計 */
    .process-item {
        background: #f1f5f9;
        margin-bottom: 8px;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #cbd5e1;
    }
    .process-item.active { border-left: 5px solid #1e40af; background: #eff6ff; }
    
    .proc-name { font-size: 13px; font-weight: 700; color: #475569; margin-bottom: 5px; }
    .staff-main { font-size: 16px; font-weight: 900; color: #1e40af; }
    .staff-sub { font-size: 12px; color: #64748b; background: white; padding: 2px 5px; border-radius: 4px; margin-right: 3px; border: 1px solid #e2e8f0; }
    
    .no-assign { color: #94a3b8; font-style: italic; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]
assigner_list = settings["assigners"]

if "user" not in st.session_state:
    st.title("⚓ 超慧科技系統登入")
    u = st.selectbox("👤 請選擇您的姓名", all_staff)
    if st.button("確認登入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 生產看板", "📝 派工錄入", "📝 紀錄編輯", "⚙️ 系統設定"])

    # --- 3. 📊 生產看板 (全新設計版) ---
    if menu == "📊 生產看板":
        # 標題與搜尋區 (固定在頂部)
        st.markdown('<div class="fixed-top-header">', unsafe_allow_html=True)
        st.markdown(f'<h1 style="text-align:center; color:#1e40af; margin-bottom:15px;">📊 生產進度即時看板</h1>', unsafe_allow_html=True)
        col_s1, col_s2 = st.columns(2)
        search_order = col_s1.selectbox("🔍 搜尋製令", ["全部項目"] + sorted(order_list))
        search_staff = col_s2.selectbox("👤 搜尋參與人員", ["全部人員"] + sorted(all_staff))
        st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, db_key=k) for k, v in data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs)
                unique_orders = df["製令"].unique()
                
                # 過濾邏輯
                display_orders = []
                for order in unique_orders:
                    if search_order != "全部項目" and search_order != order: continue
                    order_df = df[df["製令"] == order]
                    if search_staff != "全部人員":
                        staff_cols = [f"人員{i}" for i in range(1, 6)]
                        if not order_df[staff_cols].apply(lambda row: search_staff in row.values, axis=1).any(): continue
                    display_orders.append(order)

                # 看板 HTML 開始
                board_html = '<div class="board-container">'
                
                for order in display_orders:
                    order_df = df[df["製令"] == order]
                    # 卡片標題區 (固定不動)
                    board_html += f'''
                        <div class="order-card">
                            <div class="card-title-fixed">📦 製令：{order}</div>
                            <div class="card-body-scroll">
                    '''
                    
                    # 卡片內容區 (獨立滾動)
                    for proc in process_list:
                        matched = order_df[order_df["製造工序"] == proc]
                        if not matched.empty:
                            row = matched.iloc[0]
                            main_w = row.get("人員1", "-")
                            subs = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", "管理員", None, ""]]
                            
                            sub_html = "".join([f'<span class="staff-sub">{s}</span>' for s in subs])
                            board_html += f'''
                                <div class="process-item active">
                                    <div class="proc-name">{proc}</div>
                                    <div class="staff-main">👤 {main_w}</div>
                                    <div style="margin-top:5px;">{sub_html}</div>
                                </div>
                            '''
                        else:
                            board_html += f'''
                                <div class="process-item">
                                    <div class="proc-name">{proc}</div>
                                    <div class="no-assign">尚未派工</div>
                                </div>
                            '''
                    
                    board_html += '</div></div>' # 關閉卡片
                
                board_html += '</div>' # 關閉看板容器
                st.markdown(board_html, unsafe_allow_html=True)
                
        except Exception:
            st.error("暫無看板資料或連線異常")

    # --- 派工、編輯與設定 (維持原本功能) ---
    elif menu == "📝 派工錄入":
        st.markdown("## 📝 派發新任務")
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            order_no = c1.selectbox("📦 選擇製令", order_list)
            proc_name = c2.selectbox("⚙️ 選擇工序", process_list)
            st.write("---")
            pc = st.columns(5)
            ws = [pc[i].selectbox(f"人員 {i+1}", all_staff, key=f"nw{i}") for i in range(5)]
            assigner = st.selectbox("🚩 派工負責人", assigner_list)
            if st.form_submit_button("🚀 確認發布"):
                log = {"製令": order_no, "製造工序": proc_name, "人員1": ws[0], "人員2": ws[1], "人員3": ws[2], "人員4": ws[3], "人員5": ws[4], "派工人員": assigner, "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", data=json.dumps(log))
                st.success("✅ 任務已同步")
                st.rerun()

    elif menu == "📝 紀錄編輯":
        st.markdown("## 📝 修改派工紀錄")
        r = requests.get(f"{DB_URL}.json")
        db_data = r.json()
        if db_data:
            all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
            log_opts = {log['id']: f"[{log.get('製令')}] {log.get('製造工序')}" for log in all_logs}
            tid = st.selectbox("🔍 搜尋紀錄", options=list(log_opts.keys()), format_func=lambda x: log_opts[x])
            curr = next((i for i in all_logs if i["id"] == tid), None)
            if curr:
                new_p = st.selectbox("工序", process_list, index=process_list.index(curr['製造工序']) if curr['製造工序'] in process_list else 0)
                ec = st.columns(5)
                nw = [ec[i].selectbox(f"人員 {i+1}", all_staff, index=all_staff.index(curr.get(f'人員{i+1}')) if curr.get(f'人員{i+1}') in all_staff else 0, key=f"e{i}") for i in range(5)]
                if st.button("💾 儲存修改"):
                    upd = {"製造工序": new_p, "人員1": nw[0], "人員2": nw[1], "人員3": nw[2], "人員4": nw[3], "人員5": nw[4]}
                    requests.patch(f"{DB_URL}/{tid}.json", data=json.dumps(upd))
                    st.rerun()
                if st.button("🗑️ 刪除紀錄", type="primary"):
                    requests.delete(f"{DB_URL}/{tid}.json")
                    st.rerun()

    elif menu == "⚙️ 系統設定":
        st.markdown("## ⚙️ 系統設定")
        with st.form("sys_config"):
            new_order_str = st.text_area("製令名單：", value=",".join(order_list))
            new_assigner_str = st.text_area("派工負責人：", value=",".join(assigner_list))
            all_staff_str = st.text_area("人員總名單：", value=",".join(all_staff))
            new_processes = st.text_area("工序名單：", value=",".join(process_list))
            if st.form_submit_button("💾 儲存設定"):
                new_data = {
                    "order_list": [x.strip() for x in new_order_str.split(",") if x.strip()],
                    "assigners": [x.strip() for x in new_assigner_str.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("✅ 設定更新")
                st.rerun()
