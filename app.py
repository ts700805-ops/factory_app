import streamlit as st
import pandas as pd
import datetime
import requests

# --- 1. 核心設定 ---
# 提醒：請確保這些網址與您的 Firebase 即時資料庫配置一致
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
            return {"assigners": ["管理員"], "worker_map": {}, "processes": ["骨架", "前置", "配電", "模組", "水平"]}
        return data
    except:
        return {"assigners": ["管理員"], "worker_map": {}, "processes": ["骨架", "前置", "配電", "模組", "水平"]}

# --- 2. 頁面配置 (視覺強化：格狀人員看板) ---
st.set_page_config(page_title="超慧科技●生產派工系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-title { font-size: 28px !important; font-weight: 800; color: #1e293b; padding: 10px 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 20px; }
    
    /* 製令大卡片 */
    .order-card {
        background: white; border-radius: 15px; padding: 20px; margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border-top: 5px solid #3b82f6;
    }
    .order-id { font-size: 26px; font-weight: 900; color: #1d4ed8; }
    
    /* 人員網格設計 */
    .worker-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 12px; margin-top: 15px;
    }
    .worker-box {
        background: #f1f5f9; padding: 10px; border-radius: 8px; text-align: center;
        border: 1px solid #e2e8f0;
    }
    .proc-label { font-size: 12px; color: #64748b; margin-bottom: 4px; font-weight: bold; }
    .worker-name { font-size: 16px; color: #0f172a; font-weight: 700; }
    .worker-empty { color: #cbd5e1; font-weight: 400; }
    
    .status-badge { background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 99px; font-size: 14px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

settings = get_settings()

if "user" not in st.session_state:
    st.title("⚓ 系統登入")
    u = st.selectbox("登入者姓名", settings.get("assigners", ["管理員"]))
    if st.button("確認進入系統"):
        st.session_state.user = u
        st.rerun()
else:
    st.sidebar.markdown(f"👤 **使用者：{st.session_state.user}**")
    menu = st.sidebar.radio("導航選單", ["📊 控制塔台 (首頁)", "💖 愛的派工作業中心", "⚙️ 系統內容管理"])
    if st.sidebar.button("登出"):
        st.session_state.clear()
        st.rerun()

    # --- 3. 📊 控制塔台 (首頁：格狀看板) ---
    if menu == "📊 控制塔台 (首頁)":
        st.markdown('<p class="main-title">📊 現場生產派工進度看板</p>', unsafe_allow_html=True)
        try:
            r = requests.get(f"{DB_URL}.json", timeout=5)
            data = r.json()
            if data:
                proc_list = settings.get("processes", [])
                for k, v in data.items():
                    if not v or '製令' not in v: continue
                    
                    st.markdown(f"""
                    <div class="order-card">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <span class="order-id">📦 {v['製令']}</span>
                                <div style="margin-top:5px; color:#64748b;">🚩 派工員：{v.get('派工人員','未註明')} | ⏳ 期限：{v.get('作業期限','-')}</div>
                            </div>
                            <span class="status-badge">生產中</span>
                        </div>
                        <div class="worker-grid">
                    """, unsafe_allow_html=True)
                    
                    # 顯示每個工序的人員
                    for p in proc_list:
                        name = v.get(p, "NA")
                        name_class = "worker-name" if name != "NA" else "worker-empty"
                        st.markdown(f"""
                            <div class="worker-box">
                                <div class="proc-label">{p}</div>
                                <div class="{name_class}">{name}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    if st.button(f"✅ 完成報工 ({v['製令']})", key=f"fin_{k}", use_container_width=True):
                        done_data = v.copy()
                        done_data['實際完工時間'] = get_now_str()
                        requests.post(f"{DONE_URL}.json", json=done_data)
                        requests.delete(f"{DB_URL}/{k}.json")
                        st.balloons()
                        st.rerun()
            else:
                st.info("目前沒有待辦任務。")
        except Exception as e:
            st.error(f"讀取資料失敗：{e}")

    # --- 4. 💖 愛的派工作業中心 (修正連線問題) ---
    elif menu == "💖 愛的派工作業中心":
        st.markdown('<p class="main-title">💖 愛的派工作業中心</p>', unsafe_allow_html=True)
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            order_input = c1.text_input("1. 輸入製令編號", placeholder="例如: 25M0677-01")
            assign_list = settings.get("assigners", [])
            selected_assigner = c2.selectbox("2. 派工人員", assign_list, index=assign_list.index(st.session_state.user) if st.session_state.user in assign_list else 0)
            
            st.markdown("---")
            st.subheader("3. 設定各工序負責人")
            
            # 動態建立工序選擇
            workers = ["NA"] + settings.get("worker_map", {}).get(selected_assigner, [])
            proc_list = settings.get("processes", [])
            
            new_assign_data = {}
            # 使用 4 欄位排版讓介面不擁擠
            rows = [proc_list[i:i+4] for i in range(0, len(proc_list), 4)]
            for row in rows:
                cols = st.columns(4)
                for i, p_name in enumerate(row):
                    with cols[i]:
                        new_assign_data[p_name] = st.selectbox(p_name, workers, key=f"sel_{p_name}")
            
            st.markdown("---")
            deadline_date = st.date_input("4. 作業期限", datetime.date.today() + datetime.timedelta(days=2))
            
            if st.button("🚀 確認發布至看板", type="primary", use_container_width=True):
                if not order_input:
                    st.error("❌ 錯誤：請輸入製令編號！")
                else:
                    payload = {
                        "製令": order_input,
                        "派工人員": selected_assigner,
                        "作業期限": str(deadline_date),
                        "提交時間": get_now_str(),
                        **new_assign_data
                    }
                    try:
                        # 增加 timeout 避免長時間卡住
                        resp = requests.post(f"{DB_URL}.json", json=payload, timeout=10)
                        if resp.status_code == 200:
                            st.success(f"🎉 製令 {order_input} 發布成功！")
                            st.balloons()
                        else:
                            st.error(f"發送失敗，代碼：{resp.status_code}")
                    except Exception as e:
                        st.error(f"連線失敗，請檢查網路或 URL。錯誤訊息：{e}")

    # --- 5. 系統內容管理 ---
    elif menu == "⚙️ 系統內容管理":
        st.header("⚙️ 系統設定")
        with st.expander("編輯工序與派工員名單"):
            new_a = st.text_area("🚩 派工人員名單 (逗點隔開)", value=",".join(settings.get("assigners", [])))
            new_p = st.text_area("⚙️ 工序名稱定義 (逗點隔開)", value=",".join(settings.get("processes", [])))
            if st.button("儲存基本設定"):
                requests.patch(f"{SETTING_URL}.json", json={
                    "assigners": [x.strip() for x in new_a.split(",") if x.strip()],
                    "processes": [x.strip() for x in new_p.split(",") if x.strip()]
                })
                st.success("設定已更新"); st.rerun()
        
        target = st.selectbox("配置人員：", settings.get("assigners", []))
        worker_input = st.text_area(f"👷 {target} 的成員名單 (逗點隔開)", value=",".join(settings.get("worker_map", {}).get(target, [])))
        if st.button(f"儲存 {target} 成員"):
            wm = settings.get("worker_map", {})
            wm[target] = [x.strip() for x in worker_input.split(",") if x.strip()]
            requests.patch(f"{SETTING_URL}.json", json={"worker_map": wm})
            st.success("人員更新成功"); st.rerun()
