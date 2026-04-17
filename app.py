import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
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
            return {"assigners": ["管理員"], "worker_map": {}, "processes": ["工序A", "工序B", "工序C", "工序D", "工序E"]}
        return data
    except:
        return {"assigners": ["管理員"], "worker_map": {}, "processes": ["工序A", "工序B", "工序C", "工序D", "工序E"]}

# --- 2. 頁面配置 (全新視覺：緊湊、專業) ---
st.set_page_config(page_title="超慧科技●神鬼奇航●派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f1f5f9; }
    .main-title { font-size: 28px !important; font-weight: 800; color: #0f172a; border-left: 10px solid #1e40af; padding-left: 15px; margin-bottom: 20px; }
    
    /* 看板卡片設計 */
    .order-container {
        background: white; border-radius: 12px; padding: 18px; margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
    }
    .order-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .order-id { font-size: 24px; font-weight: 900; color: #1e40af; }
    
    /* 人員表格樣式 */
    .worker-table { width: 100%; border-collapse: collapse; margin-top: 10px; table-layout: fixed; }
    .worker-table th { background-color: #f8fafc; color: #64748b; padding: 8px; font-size: 14px; border: 1px solid #edf2f7; text-align: center; }
    .worker-table td { padding: 12px; font-size: 16px; border: 1px solid #edf2f7; text-align: center; font-weight: 600; color: #334155; }
    .worker-highlight { color: #1e40af; background-color: #eff6ff; }
    .worker-na { color: #cbd5e1; font-weight: 400 !important; }

    /* 按鈕優化 */
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-size: 16px !important; transition: 0.3s; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 神鬼奇航●控制塔台登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    p = st.text_input("員工代碼", type="password")
    if st.button("我愛德文★志偉愛我"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **當前使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 控制塔台 (首頁)", "💖 愛的派工作業中心", "✅ 歷史紀錄查詢", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出系統"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 控制塔台 (首頁：表格化呈現) ---
    if menu == "📊 控制塔台 (首頁)":
        st.markdown('<p class="main-title">📊 現場生產進度看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json")
            data = r.json()
            if data:
                proc_list = settings.get("processes", [])
                for k, v in data.items():
                    if not v: continue
                    
                    # 開始渲染單張製令卡片
                    st.markdown(f"""
                    <div class="order-container">
                        <div class="order-header">
                            <span class="order-id">📦 製令單：{v['製令']}</span>
                            <div style="text-align: right;">
                                <span style="color:#64748b;">🚩 派工員：{v['派工人員']}</span><br>
                                <span style="color:#e11d48; font-weight:bold;">⏳ 期限：{v['作業期限']}</span>
                            </div>
                        </div>
                        <table class="worker-table">
                            <tr>
                                {" ".join([f"<th>{p}</th>" for p in proc_list])}
                            </tr>
                            <tr>
                                {" ".join([f'<td class="{"worker-highlight" if v.get(p, "NA") != "NA" else "worker-na"}">{v.get(p, "NA")}</td>' for p in proc_list])}
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 完工按鈕
                    if st.button(f"✅ 製令 {v['製令']} 生產報工完成", key=f"fin_{k}"):
                        done_data = v.copy()
                        done_data['實際完工時間'] = get_now_str()
                        requests.post(f"{DONE_URL}.json", json=done_data)
                        requests.delete(f"{DB_URL}/{k}.json")
                        st.balloons()
                        st.rerun()
            else:
                st.info("目前生產線空閒中，尚無派工任務。")
        except Exception as e:
            st.error(f"連線異常：{e}")

    # --- 4. 💖 愛的派工作業中心 ---
    elif menu == "💖 愛的派工作業中心":
        st.markdown('<p class="main-title">💖 愛的派工作業中心</p>', unsafe_allow_html=True)
        
        with st.container():
            c1, c2 = st.columns(2)
            order_input = c1.text_input("1. 請輸入製令編號", placeholder="例如: DAL-20260417")
            assign_list = settings.get("assigners", [])
            selected_assigner = c2.selectbox("2. 確認派工人員", assign_list, index=assign_list.index(st.session_state.user) if st.session_state.user in assign_list else 0)
            
            st.markdown("### 3. 設定各工序負責人")
            # 取得人員名單
            workers = ["NA"] + settings.get("worker_map", {}).get(selected_assigner, [])
            proc_list = settings.get("processes", [])
            
            # 建立多欄位選單
            new_assign_data = {}
            cols = st.columns(len(proc_list) if len(proc_list) <= 5 else 5)
            for i, p_name in enumerate(proc_list):
                with cols[i % len(cols)]:
                    new_assign_data[p_name] = st.selectbox(p_name, workers, key=f"inp_{i}")
            
            st.markdown("---")
            deadline_date = st.date_input("4. 設定作業期限", datetime.date.today() + datetime.timedelta(days=3))
            
            # 發布按鈕 (確保邏輯獨立)
            if st.button("🚀 確認發布此製令單至看板", type="primary"):
                if not order_input:
                    st.warning("⚠️ 請務必填寫『製令編號』後再發布。")
                else:
                    payload = {
                        "製令": order_input,
                        "派工人員": selected_assigner,
                        "作業期限": str(deadline_date),
                        "提交時間": get_now_str(),
                        **new_assign_data
                    }
                    try:
                        resp = requests.post(f"{DB_URL}.json", json=payload)
                        if resp.status_code == 200:
                            st.success(f"✅ 製令 {order_input} 派工成功！已同步至控制塔台。")
                            st.balloons()
                        else:
                            st.error("發送失敗，請檢查資料庫連線。")
                    except Exception as e:
                        st.error(f"系統錯誤：{e}")

    # --- 5. 其餘管理功能 (維持既有逻辑) ---
    elif menu == "✅ 歷史紀錄查詢":
        st.markdown('<p class="main-title">✅ 已完工歷史紀錄</p>', unsafe_allow_html=True)
        r_done = requests.get(f"{DONE_URL}.json")
        if r_done.json():
            df_done = pd.DataFrame([v for k, v in r_done.json().items() if v]).fillna("NA")
            st.dataframe(df_done, use_container_width=True)

    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 系統後台設定")
        with st.expander("編輯基本資料 (人員與工序)", expanded=True):
            new_a = st.text_area("🚩 派工人員名單 (用逗點隔開)", value=",".join(settings.get("assigners", [])))
            new_p = st.text_area("⚙️ 工序名稱定義 (用逗點隔開)", value=",".join(settings.get("processes", [])))
            if st.button("💾 儲存後台定義"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "assigners": [x.strip() for x in new_a.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_p.split(",") if x.strip()]
                })
                st.success("設定已更新"); st.rerun()
        
        target = st.selectbox("配置人員隸屬關係：", settings.get("assigners", []))
        worker_input = st.text_area(f"👷 設定 {target} 的手下成員 (用逗點隔開)", value=",".join(settings.get("worker_map", {}).get(target, [])))
        if st.button(f"💾 儲存 {target} 的人員名單"):
            wm = settings.get("worker_map", {})
            wm[target] = [x.strip() for x in worker_input.split(",") if x.strip()]
            requests.patch(f"{SETTING_URL}.json", json={"worker_map": wm})
            st.success("人員配置已更新"); st.rerun()
