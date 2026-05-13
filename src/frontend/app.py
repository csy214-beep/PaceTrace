import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
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

with open(os.path.join(os.path.dirname(__file__), "style.css"), encoding="utf-8") as f:
    css = f.read()

# detect dark theme and append override
try:
    if st.get_option("theme.base") == "dark":
        css += """
        .card { background:#1e1e1e !important; border-color:#333 !important; }
        .card-sm { color:#999 !important; }
        .tag-ok { background:#1b3d1f !important; color:#66bb6a !important; }
        .tag-full { background:#3d1b1b !important; color:#ef5350 !important; }
        .tag-si { background:#1b2d3d !important; color:#42a5f5 !important; }
        .tag-sb { background:#3d2d1b !important; color:#ffa726 !important; }
        """
except Exception:
    pass

st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


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
