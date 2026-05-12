import streamlit as st

from api import run
from frontend.utils import api_call
from api import ctx


def show_profile_page():
    st.markdown(f"**{ctx.user.studentName}**")
    st.caption(f"{ctx.user.schoolName} | {ctx.user.className} | 学号 {ctx.user.registerCode}")
    st.divider()
    st.markdown("#### 运动统计")
    if st.button("刷新", use_container_width=True, key="ref_stats"):
        st.session_state.run_info = api_call(run.get_run_info)
        st.rerun()
    ri3 = st.session_state.run_info
    rd3 = ri3.get("response") if ri3 else {}
    if rd3:
        c1, c2, c3 = st.columns(3)
        c1.metric("有效天数", rd3.get("runValidDay", 0))
        c2.metric("总距离(米)", rd3.get("runValidDistance", 0))
        c3.metric("配速", rd3.get("showSpeed", "-"))
