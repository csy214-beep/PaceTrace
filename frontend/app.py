import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def _load_env():
    path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

_load_env()

from api import auth, run as api_run, club as api_club, ctx
from frontend.utils import api_call
from frontend.home import show_home_page
from frontend.run import show_run_page
from frontend.club import show_club_page
from frontend.profile import show_profile_page
from frontend.about import show_about_page

st.set_page_config(page_title="行迹", page_icon=None, layout="centered")

st.markdown("""
<style>
    #MainMenu, footer { display: none; }
    .block-container { padding-top: 3.5rem; max-width: 720px; }
    section[data-testid="stSidebar"] { width: 220px !important; min-width: 220px !important; }
    section[data-testid="stSidebar"] .block-container { padding: 0.8rem; }
    section[data-testid="stSidebar"] hr { margin: 0.4rem 0; }
    .card { background:#fafafa; border-radius:10px; padding:0.8rem; margin-bottom:0.5rem; border:1px solid #eee; }
    .card-sm { font-size:0.85rem; color:#666; }
    .tag-ok { background:#e8f5e9; color:#2e7d32; border-radius:10px; padding:1px 8px; font-size:0.75rem; }
    .tag-full { background:#fbe9e7; color:#c62828; border-radius:10px; padding:1px 8px; font-size:0.75rem; }
    .tag-si { background:#e3f2fd; color:#1565c0; border-radius:10px; padding:1px 8px; font-size:0.75rem; }
    .tag-sb { background:#fff3e0; color:#e65100; border-radius:10px; padding:1px 8px; font-size:0.75rem; }
    div[data-testid="stMetricValue"] { font-size:1.4rem !important; }
    .center-box { max-width:360px; margin:4rem auto; text-align:center; }
</style>
""", unsafe_allow_html=True)


if "page" not in st.session_state:
    st.session_state.page = "首页"
for k in ["run_info", "records", "activities", "my_acts", "club_types", "semester_acts", "log_content"]:
    if k not in st.session_state:
        st.session_state[k] = None

PAGES = ["首页", "跑步", "俱乐部", "我的", "关于"]


if not ctx.user.studentId:
    st.markdown("<div class='center-box'>", unsafe_allow_html=True)
    st.markdown("### 行迹")
    st.markdown("Campus Run Management")
    st.divider()
    with st.form("login_f"):
        st.text_input("手机号", key="login_phone")
        st.text_input("密码", type="password", key="login_pwd")
        if st.form_submit_button("登录", use_container_width=True, type="primary"):
            r = api_call(auth.login, st.session_state.login_phone, st.session_state.login_pwd)
            if r and r.get("code") == 10000:
                st.rerun()
            elif r:
                st.error("账号或密码错误")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


with st.sidebar:
    st.markdown(f"**{ctx.user.studentName}**")
    st.caption(ctx.user.schoolName)
    st.divider()
    for p in PAGES:
        if st.button(p, key=f"nav_{p}", use_container_width=True):
            st.session_state.page = p
            st.rerun()
    st.divider()
    if st.button("退出", use_container_width=True, key="sb_logout"):
        auth.logout()
        st.rerun()


def ensure_cache():
    if st.session_state.run_info is None:
        st.session_state.run_info = api_call(api_run.get_run_info)
        st.session_state.records = api_call(api_run.get_run_records, 1, 10)
        st.session_state.my_acts = api_call(api_club.get_my_activities)
        st.session_state.club_types = api_call(api_club.get_club_projects)
        st.session_state.semester_acts = api_call(api_club.get_semester_activities)

ensure_cache()

page = st.session_state.page

if page == "首页":
    show_home_page()
elif page == "跑步":
    show_run_page()
elif page == "俱乐部":
    show_club_page()
elif page == "我的":
    show_profile_page()
elif page == "关于":
    show_about_page()
