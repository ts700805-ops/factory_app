import streamlit as st
import pandas as pd
import datetime
import requests

# ==============================
# 設定
# ==============================
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"


# ==============================
# Firebase
# ==============================
def get_db(path):
    try:
        r = requests.get(f"{DB_URL}{path}.json")
        return r.json()
    except:
        return None


def save_db(path, data, method="post"):
    try:
        if method == "post":
            requests.post(f"{DB_URL}{path}.json", json=data)
        else:
            requests.put(f"{DB_URL}{path}.json", json=data)
    except:
        pass


# ==============================
# ⭐ 工時格式轉換 (新增)
# ==============================
def format_hours_to_hm(hours_float):
    total_minutes = int(hours_float * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}小時 {m}分鐘"


# ==============================
# 頁面
# ==============================
st.set_page_config(page_title="數位戰情室", layout="wide")

raw_users = get_db("users")
STAFF_DATA = {"管理員": "8888"}
if raw_users:
    STAFF_DATA.update(raw_users)


# ==============================
# 登入
# ==============================
if "user" not in st.session_state:

    st.title("🔐 員工系統登入")

    with st.form("login"):
        name = st.selectbox("請選擇姓名", list(STAFF_DATA.keys()))
        code = st.text_input("輸入代碼", type="password")

        if st.form_submit_button("進入系統"):
            if str(STAFF_DATA.get(name)) == code:
                st.session_state.user = name
                st.rerun()
            else:
                st.error("❌ 代碼錯誤")

else:

    st.sidebar.title(f"👤 {st.session_state.user}")

    options = ["🏗️ 工時回報"]
    if st.session_state.user == "管理員":
        options += ["⚙️ 系統帳號管理", "📊 完整工時報表"]

    menu = st.sidebar.radio("功能選單", options)

    if st.sidebar.button("🚪 登出系統"):
        st.session_state.clear()
        st.rerun()

    # =====================================================
    # 工時回報
    # =====================================================
    if menu == "🏗️ 工時回報":

        st.header("🏗️ 生產日報回報")

        if "calc_hours" not in st.session_state:
            st.session_state.calc_hours = 0.0

        # --------------------------
        # 工時計時器
        # --------------------------
        with st.expander("⏱️ 工時計時器", expanded=True):

            c1, c2 = st.columns(2)

            if c1.button("⏱️ 開始計時"):
                st.session_state.work_start = datetime.datetime.now()

            if c2.button("⏹️ 結束計時"):
                if "work_start" in st.session_state:
                    end = datetime.datetime.now()
                    diff = end - st.session_state.work_start
                    st.session_state.calc_hours = round(diff.total_seconds()/3600, 2)

        # ⭐⭐⭐ 保留綠色顯示 + 時分格式
        if st.session_state.calc_hours > 0:
            st.success(
                f"計時結束！自動計算工時：{format_hours_to_hm(st.session_state.calc_hours)}"
            )

        # --------------------------
        # 表單
        # --------------------------
        with st.form("work_form"):

            user_code = STAFF_DATA.get(st.session_state.user, "N/A")

            c1, c2, c3 = st.columns(3)
            status = c1.selectbox("狀態", ["作業中", "暫停", "下班", "完工"])
            order_no = c2.text_input("製令")
            pn = c3.text_input("P/N")

            c4, c5, c6 = st.columns(3)
            prod_type = c4.text_input("Type")
            stage = c5.text_input("工段名稱")

            hours = c6.number_input(
                "累計工時 (hr)",
                min_value=0.0,
                step=0.01,
                key="calc_hours"
            )

            start_str = st.session_state.get(
                "work_start",
                datetime.datetime.now()
            ).strftime("%Y-%m-%d %H:%M:%S")

            st.write(f"📌 工號：{user_code} | 姓名：{st.session_state.user}")
            st.write(f"⏰ 開始時間：{start_str}")

            if st.form_submit_button("🚀 提交紀錄"):

                log_data = {
                    "狀態": status,
                    "製令": order_no,
                    "P/N": pn,
                    "Type": prod_type,
                    "工段名稱": stage,
                    "工號": user_code,
                    "姓名": st.session_state.user,
                    "開始時間": start_str,
                    "結束時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "累計工時": hours,
                }

                save_db("work_logs", log_data)

                st.success("✅ 紀錄已成功提交！")
                st.session_state.calc_hours = 0.0

    # =====================================================
    # 報表
    # =====================================================
    elif menu == "📊 完整工時報表":

        raw_logs = get_db("work_logs")

        if raw_logs:
            df = pd.DataFrame.from_dict(raw_logs, orient="index")
            st.dataframe(df, use_container_width=True)
