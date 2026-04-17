import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 基礎資料與通訊設定 ---
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
                return data
        return default_settings
    except Exception:
        return default_settings

# --- 2. 介面樣式優化 (看板專屬) ---
st.set_page_config(page_title="超慧科技●製造部●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    
    /* 製令卡片主體：固定高度，不准捲動 */
    .order-card {
        background: white;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 2px solid #cbd5e1;
        height: 600px;
        width: 100%;
        overflow: hidden; 
        display: flex;
        flex-direction: column;
    }

    /* 🟢 標題區：完全獨立於捲動區之外 */
    .order-header {
        background: #1e40af;
        color: #ffffff;
        padding: 15px 20px;
        font-size: 22px;
        font-weight: 900;
        height: 65px;
        display: flex;
        align-items: center;
        flex-shrink: 0; /* 標題絕不縮小 */
        border-bottom: 4px solid #1e3a8a;
    }

    /* 🟢 內容捲動區：只有這裡會動 */
    .scroll-container {
        flex-grow: 1;
        overflow-y: auto !important; /* 強制垂直捲動 */
        padding: 15px;
        background: #ffffff;
    }

    /* 工序區塊樣式 */
    .proc-box {
        background: #ffffff;
        padding: 12px;
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        margin-bottom: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .p-label { 
        font-size: 14px; 
        font-weight: 800; 
        color: #1e40af; 
        margin-bottom: 6px;
        border-bottom: 1px solid #f1f5f9;
        width: 100%;
        text-align: center;
    }

    .main-worker {
        font-size: 19px !important;
        font-weight: 900 !important;
        color: #000000 !important;
    }
    
    .sub-worker-tag {
        font-size: 13px;
        color: #64748b;
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
        margin: 2px;
        display: inline-block;
    }

    .search-panel {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #1e40af;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()
all_staff = settings["all_staff"]
process_list = settings["processes"]
order_list = settings["order_list"]

if "user" not in st.session_state:
    st.title("⚓ 超慧科技 - 系統登入")
    u = st.selectbox("👤 請選擇您的姓名", all_staff)
    if st.button("確認登入"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("功能導航", ["📊 生產看板", "📝 派工錄入", "📝 紀錄編輯", "⚙️ 系統設定"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 📊 生產看板 (獨立捲動修正版) ---
    if menu == "📊 生產看板":
        st.markdown(f'<h1 style="text-align:center; color:#1e40af; font-weight:900;">📊 生產進度看板</h1>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="search-panel">', unsafe_allow_html=True)
            s1, s2 = st.columns(2)
            search_o = s1.selectbox("🔍 搜尋製令", ["全部項目"] + sorted(order_list))
            search_p = s2.selectbox("👤 搜尋參與人員", ["全部人員"] + sorted(all_staff))
            st.markdown('</div>', unsafe_allow_html=True)

        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                all_logs = [dict(v, id=k) for k, v in data.items() if v and isinstance(v, dict)]
                df = pd.DataFrame(all_logs)
                
                unique_orders = df["製令"].unique()
                filtered = []
                for o in unique_orders:
                    if search_o != "全部項目" and search_o != o: continue
                    o_df = df[df["製令"] == o]
                    if search_p != "全部人員":
                        cols_to_check = [f"人員{i}" for i in range(1, 6)]
                        if not o_df[cols_to_check].apply(lambda x: search_p in x.values, axis=1).any(): continue
                    filtered.append(o)

                display_cols = st.columns(3)
                for idx, o_id in enumerate(filtered):
                    o_df = df[df["製令"] == o_id]
                    with display_cols[idx % 3]:
                        # 🟢 物理隔離結構：Header 在外，scroll-container 在內
                        st.markdown(f'''
                            <div class="order-card">
                                <div class="order-header">📦 製令：{o_id}</div>
                                <div class="scroll-container">
                        ''', unsafe_allow_html=True)
                        
                        for p in process_list:
                            match = o_df[o_df["製造工序"] == p]
                            if not match.empty:
                                row = match.iloc[0]
                                w1 = row.get("人員1", "-")
                                subs = [row.get(f"人員{i}") for i in range(2, 6) if row.get(f"人員{i}") not in ["NA", None, ""]]
                                subs_html = "".join([f'<span class="sub-worker-tag">{s}</span>' for s in subs])
                                box_html = f'<div class="main-worker"><span style="color:#1e40af; font-size:12px;">主</span> {w1}</div>' + subs_html
                            else:
                                box_html = '<div style="color:#cbd5e1; font-size:13px; margin-top:10px;">尚未派工</div>'
                            
                            st.markdown(f'''
                                <div class="proc-box">
                                    <div class="p-label">{p}</div>
                                    {box_html}
                                </div>
                            ''', unsafe_allow_html=True)
                        
                        st.markdown('</div></div>', unsafe_allow_html=True)
        except:
            st.error("資料獲取失敗，請檢查網路連線")

    # --- 📝 派工錄入 ---
    elif menu == "📝 派工錄入":
        st.markdown('<h2 style="color:#1e40af;">📝 派發新任務</h2>', unsafe_allow_html=True)
        with st.form("new_task"):
            c1, c2 = st.columns(2)
            o_no = c1.selectbox("📦 選擇製令", order_list)
            p_name = c2.selectbox("⚙️ 選擇工序流程", process_list)
            st.write("---")
            pc = st.columns(5)
            ws = [pc[0].selectbox("主要人員1", all_staff, key="nw0")]
            for i in range(1, 5):
                ws.append(pc[i].selectbox(f"人員 {i+1}", all_staff, key=f"nw{i}"))
            if st.form_submit_button("🚀 發布任務"):
                log = {"製令": o_no, "製造工序": p_name, "人員1": ws[0], "人員2": ws[1], "人員3": ws[2], "人員4": ws[3], "人員5": ws[4], "提交時間": get_now_str()}
                requests.post(f"{DB_URL}.json", data=json.dumps(log))
                st.success(f"✅ 製令 {o_no} 已更新")
                st.rerun()

    # --- 📝 紀錄編輯 ---
    elif menu == "📝 紀錄編輯":
        st.markdown('<h2 style="color:#1e40af;">📝 修改現有紀錄</h2>', unsafe_allow_html=True)
        r = requests.get(f"{DB_URL}.json")
        db_data = r.json()
        if db_data:
            all_logs = [dict(v, id=k) for k, v in db_data.items() if v and isinstance(v, dict)]
            opts = {l['id']: f"[{l.get('製令')}] {l.get('製造工序')}" for l in all_logs}
            tid = st.selectbox("🔍 選擇要修改的紀錄", options=list(opts.keys()), format_func=lambda x: opts[x])
            curr = next((i for i in all_logs if i["id"] == tid), None)
            if curr:
                with st.form("edit_task"):
                    new_p = st.selectbox("工序", process_list, index=process_list.index(curr['製造工序']) if curr['製造工序'] in process_list else 0)
                    ec = st.columns(5)
                    nw = [ec[0].selectbox("主要人員", all_staff, index=all_staff.index(curr.get('人員1')) if curr.get('人員1') in all_staff else 0, key="e0")]
                    for i in range(1, 5):
                        nw.append(ec[i].selectbox(f"人員 {i+1}", all_staff, index=all_staff.index(curr.get(f'人員{i+1}')) if curr.get(f'人員{i+1}') in all_staff else 0, key=f"e{i}"))
                    
                    if st.form_submit_button("💾 儲存修改"):
                        upd = {"製造工序": new_p, "人員1": nw[0], "人員2": nw[1], "人員3": nw[2], "人員4": nw[3], "人員5": nw[4]}
                        requests.patch(f"{DB_URL}/{tid}.json", data=json.dumps(upd))
                        st.success("修改成功")
                        st.rerun()

    # --- ⚙️ 系統設定 ---
    elif menu == "⚙️ 系統設定":
        st.markdown('<h2 style="color:#1e40af;">⚙️ 系統後台設定</h2>', unsafe_allow_html=True)
        with st.form("sys_cfg"):
            new_orders = st.text_area("製令清單 (半形逗號隔開)：", value=",".join(order_list))
            new_staff = st.text_area("人員名單：", value=",".join(all_staff))
            new_procs = st.text_area("工序流程：", value=",".join(process_list))
            if st.form_submit_button("💾 儲存並同步資料庫"):
                new_data = {
                    "order_list": [x.strip() for x in new_orders.split(",") if x.strip()],
                    "all_staff": [x.strip() for x in new_staff.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_procs.split(",") if x.strip()],
                    "assigners": settings.get("assigners", ["管理員"])
                }
                requests.put(f"{SETTING_URL}.json", data=json.dumps(new_data))
                st.success("✅ 資料庫設定已更新")
                st.rerun()
