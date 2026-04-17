import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- 1. 核心設定 (絕對不動) ---
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/work_logs"
DONE_URL = "https://my-factory-system-default-rtdb.firebaseio.com/completed_logs"
SETTING_URL = "https://my-factory-system-default-rtdb.firebaseio.com/settings"

def get_now_str():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_settings():
    try:
        r = requests.get(f"{SETTING_URL}.json", timeout=5)
        data = r.json()
        if not data: 
            return {"all_staff": ["管理員"], "processes": ["工序A", "工序B"]}
        # 確保必要欄位存在
        if "all_staff" not in data: data["all_staff"] = ["管理員"]
        if "processes" not in data: data["processes"] = ["預設工序"]
        return data
    except:
        return {"all_staff": ["管理員"], "processes": ["預設工序"]}

# --- 2. 頁面配置 ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-title { font-size: 32px !important; font-weight: bold; color: #1E3A8A; border-bottom: 4px solid #1E3A8A; margin-bottom: 20px; }
    
    /* 製令看板卡片 */
    .order-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-top: 10px solid #1E3A8A;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .order-title { font-size: 24px; font-weight: bold; color: #1e293b; margin-bottom: 15px; }
    
    /* 工序網格佈局 */
    .process-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 12px;
    }
    .process-box {
        background: #f8fafc;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .process-name { font-size: 14px; color: #64748b; margin-bottom: 5px; }
    .worker-name { font-size: 16px; font-weight: bold; color: #1e40af; }
    .na-tag { color: #cbd5e1; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()
all_staff = settings.get("all_staff", ["管理員"])
process_list = settings.get("processes", ["預設工序"])

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", all_staff)
    if st.button("啟航"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 控制塔台 (首頁進度)", "📝 愛的派工中心", "📝 編輯派工紀錄", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 控制塔台 (首頁) ---
    if menu == "📊 控制塔台 (首頁進度)":
        st.markdown('<p class="main-title">📊 超慧科技●神鬼奇航●控制塔台</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                all_logs = [dict(v, db_key=k) for k, v in data.items() if v]
                df = pd.DataFrame(all_logs)
                
                # 按製令編號分組
                unique_orders = df["製令"].unique()
                
                for order in unique_orders:
                    order_df = df[df["製令"] == order]
                    
                    st.markdown(f'''
                    <div class="order-container">
                        <div class="order-title">📦 製令單：{order}</div>
                        <div class="process-grid">
                    ''', unsafe_allow_html=True)
                    
                    # 顯示系統中所有的工序進度
                    for proc in process_list:
                        matched = order_df[order_df["製造工序"] == proc]
                        if not matched.empty:
                            # 顯示主要人員1 (代表負責人)
                            worker_display = matched.iloc[0].get("人員1", "未知")
                            html_worker = f'<span class="worker-name">{worker_display}</span>'
                        else:
                            html_worker = '<span class="na-tag">NA</span>'
                        
                        st.markdown(f'''
                            <div class="process-box">
                                <div class="process-name">{proc}</div>
                                {html_worker}
                            </div>
                        ''', unsafe_allow_html=True)
                    
                    st.markdown('</div></div>', unsafe_allow_html=True)
            else:
                st.info("目前無任何派工紀錄。")
        except Exception as e:
            st.error(f"系統錯誤：{e}")

    # --- 4. 📝 愛的派工中心 ---
    elif menu == "📝 愛的派工中心":
        st.markdown('<p class="main-title">📝 愛的派工中心 (新任務)</p>', unsafe_allow_html=True)
        
        with st.form("new_dispatch"):
            c1, c2 = st.columns(2)
            order_no = c1.text_input("📦 輸入製令編號", placeholder="例如: DAL-2026001")
            proc_name = c2.selectbox("⚙️ 選擇工序", process_list)
            
            st.markdown("---")
            st.subheader("👥 主要人員與派工人員配置 (共5位)")
            pc1, pc2, pc3, pc4, pc5 = st.columns(5)
            w1 = pc1.selectbox("人員 1 (主)", all_staff, key="w1")
            w2 = pc2.selectbox("人員 2", all_staff, key="w2")
            w3 = pc3.selectbox("人員 3", all_staff, key="w3")
            w4 = pc4.selectbox("人員 4", all_staff, key="w4")
            w5 = pc5.selectbox("人員 5", all_staff, key="w5")
            
            assigner = st.selectbox("🚩 指定派工人員", all_staff, index=all_staff.index(st.session_state.user) if st.session_state.user in all_staff else 0)
            
            if st.form_submit_button("🚀 發布任務"):
                if not order_no:
                    st.error("請輸入製令編號！")
                else:
                    log = {
                        "製令": order_no,
                        "製造工序": proc_name,
                        "人員1": w1, "人員2": w2, "人員3": w3, "人員4": w4, "人員5": w5,
                        "派工人員": assigner,
                        "提交時間": get_now_str()
                    }
                    requests.post(f"{DB_URL}.json", json=log)
                    st.success(f"製令 {order_no} 已同步至控制塔台！")
                    st.balloons()

    # --- 5. 📝 編輯派工紀錄 (含下拉式選單改人員) ---
    elif menu == "📝 編輯派工紀錄":
        st.header("📝 派工紀錄管理")
        try:
            r = requests.get(f"{DB_URL}.json")
            db_data = r.json()
            if db_data:
                all_logs = [dict(v, id=k) for k, v in db_data.items() if v]
                log_options = {log['id']: f"[{log.get('製令')}] {log.get('製造工序')} - {log.get('人員1')}" for log in all_logs}
                target_id = st.selectbox("選擇修改項目", options=list(log_options.keys()), format_func=lambda x: log_options[x])
                curr = next((i for i in all_logs if i["id"] == target_id), None)
                
                if curr:
                    with st.expander("📝 編輯人員與資訊", expanded=True):
                        edit_proc = st.selectbox("修改工序", process_list, index=process_list.index(curr.get('製造工序')) if curr.get('製造工序') in process_list else 0)
                        
                        st.write("修改主要人員清單：")
                        ec1, ec2, ec3, ec4, ec5 = st.columns(5)
                        # 將原本的文字輸入全部改為下拉選單
                        nw1 = ec1.selectbox("人員1", all_staff, index=all_staff.index(curr.get('人員1')) if curr.get('人員1') in all_staff else 0)
                        nw2 = ec2.selectbox("人員2", all_staff, index=all_staff.index(curr.get('人員2')) if curr.get('人員2') in all_staff else 0)
                        nw3 = ec3.selectbox("人員3", all_staff, index=all_staff.index(curr.get('人員3')) if curr.get('人員3') in all_staff else 0)
                        nw4 = ec4.selectbox("人員4", all_staff, index=all_staff.index(curr.get('人員4')) if curr.get('人員4') in all_staff else 0)
                        nw5 = ec5.selectbox("人員5", all_staff, index=all_staff.index(curr.get('人員5')) if curr.get('人員5') in all_staff else 0)
                        
                        if st.button("💾 儲存修改"):
                            update_data = {
                                "製造工序": edit_proc,
                                "人員1": nw1, "人員2": nw2, "人員3": nw3, "人員4": nw4, "人員5": nw5
                            }
                            requests.patch(f"{DB_URL}/{target_id}.json", json=update_data)
                            st.success("已更新！"); st.rerun()
                    
                    if st.button("🗑️ 刪除此筆紀錄", type="primary"):
                        requests.delete(f"{DB_URL}/{target_id}.json"); st.rerun()
            else:
                st.info("無待辦紀錄。")
        except:
            st.error("讀取錯誤")

    # --- 6. ⚙️ 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 系統名單設定")
        with st.form("sys_config"):
            st.write("⚠️ 注意：所有人員與工序請以英文逗號 `,` 分隔")
            # 新增人員名單管理，作為所有下拉選單的源頭
            all_staff_str = st.text_area("👥 全體人員名單 (控制下拉選單內容)", value=",".join(all_staff))
            new_processes = st.text_area("⚙️ 編輯工序清單 (首頁看板顯示順序)", value=",".join(process_list))
            
            if st.form_submit_button("💾 儲存配置"):
                new_data = {
                    "all_staff": [x.strip() for x in all_staff_str.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_processes.split(",") if x.strip()]
                }
                requests.patch(f"{SETTING_URL}.json", json=new_data)
                st.success("設定已更新！")
                st.rerun()
