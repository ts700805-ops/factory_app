import streamlit as st
import pandas as pd
import datetime
import requests

# =====================================
# 基本設定
# =====================================
DB_URL = "https://my-factory-system-default-rtdb.firebaseio.com/"


# =====================================
# Firebase
# =====================================
def get_db(path):
    try:
        r = requests.get(f"{DB_URL}{path}.json")
        return r.json()
    except:
        return None


def save_db(path, data):
    try:
        requests.post(f"{DB_URL}{path}.json", json=data)
    except:
        pass


# =====================================
# ⭐ 時間格式轉換（小時 → 小時+分鐘）
# =====================================
def format_hours_to_hm(hours):
    total_min = int(hours * 60)
    h = total_min // 60
    m = total_min % 60
    return f"{h}小時 {m}分鐘"


# =====================================
# 頁面設定
# =====================================
st.set_page_config(page_title="工時系統", layout="wide")

raw_users = get_db("users")
STAFF_DATA = {"管理員": "8888"}

if raw_users:
    STAFF_DATA.update(raw_users)


# =====================================
# 登入
# =====================================
if "user" not in st.session_state:

    st.title("🔐 員工登入")

    with st.form("login"):
        name = st.selectbox("姓名", list(STAFF_DATA.keys()))
        code = st.text_input("代碼", type="password")

        if st.form_submit_button("登入"):
            if str(STAFF_DATA.get(name)) == code:
                st.session_state.user = name
                st.rerun()
            else:
                st.error("密碼錯誤")


# =====================================
# 主畫面
# =====================================
else:

    st.sidebar.title(f"👤 {st.session_state.user}")
    menu = st.sidebar.radio("功能", ["工時回報", "完整報表"])

    # =====================================================
    # 工時回報
    # =====================================================
    if menu == "工時回報":

        st.header("⏱️ 工時計時")

        if "calc_hours" not in st.session_state:
            st.session_state.calc_hours = 0.0

        if "work_start" not in st.session_state:
            st.session_state.work_start = None

        c1, c2 = st.columns(2)

        # -------------------------
        # 開始
        # -------------------------
        if c1.button("▶️ 開始計時"):
            st.session_state.work_start = datetime.datetime.now()
            st.session_state.calc_hours = 0.0

        # -------------------------
        # 結束（⭐ 核心修正點）
        # -------------------------
        if c2.button("⏹️ 結束計時"):
            if st.session_state.work_start:
                diff = datetime.datetime.now() - st.session_state.work_start
                hours = round(diff.total_seconds() / 3600, 2)

                # ⭐ 只更新 session_state
                st.session_state.calc_hours = hours

        # =============================
        # ⭐ 綠色顯示（保留）
        # =============================
        if st.session_state.calc_hours > 0:
            st.success(
                f"計時結束！自動計算工時：{format_hours_to_hm(st.session_state.calc_hours)}"
            )

        # =================================================
        # ⭐ 表單（關鍵修正：用 value= 不用 key=）
        # =================================================
        with st.form("form"):

            status = st.selectbox("狀態", ["作業中", "暫停", "完工"])

            order_no = st.text_input("製令")
            pn = st.text_input("P/N")
            prod_type = st.text_input("Type")
            stage = st.text_input("工段名稱")

            # ⭐⭐ 重點在這裡 ⭐⭐
            hours = st.number_input(
                "累計工時 (hr)",
                min_value=0.0,
                step=0.01,
                value=st.session_state.calc_hours   # ← 用 value 帶入
            )

            st.write(f"工號：{STAFF_DATA[st.session_state.user]}")
            st.write(f"姓名：{st.session_state.user}")

            if st.form_submit_button("提交"):

                data = {
                    "狀態": status,
                    "製令": order_no,
                    "P/N": pn,
                    "Type": prod_type,
                    "工段名稱": stage,
                    "工號": STAFF_DATA[st.session_state.user],
                    "姓名": st.session_state.user,
                    "累計工時": hours,
                    "時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                save_db("work_logs", data)

                st.success("✅ 已送出")

                # 重置
                st.session_state.calc_hours = 0.0
                st.session_state.work_start = None

    # =====================================================
    # 報表
    # =====================================================
    else:

        logs = get_db("work_logs")

        if logs:
            df = pd.DataFrame.from_dict(logs, orient="index")
            st.dataframe(df, use_container_width=True)
