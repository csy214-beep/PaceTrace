import streamlit as st

from api import club
from frontend.utils import api_call


def show_home_page():
    ri = st.session_state.run_info
    rd = ri.get("response") if ri else {}
    if rd:
        c1, c2, c3 = st.columns(3)
        c1.metric("跑步天数", rd.get("runValidDay", 0))
        c2.metric("总距离(米)", rd.get("runValidDistance", 0))
        c3.metric("配速", rd.get("showSpeed", "-"))
    st.divider()
    st.markdown("#### 最近跑步")
    recs = st.session_state.records
    rl = recs.get("response") if recs else []
    if rl:
        for r in rl[:5]:
            st.markdown(
                f"<div class='card'><div><b>{r.get('recordDate')}</b> {r.get('defeatedInfo')}</div>"
                f"<div class='card-sm'>{r.get('runValidDistance')}m | {r.get('runValidTime')}min | {r.get('runSpeed')}m/min</div></div>",
                unsafe_allow_html=True,
            )
    st.divider()
    st.markdown("#### 俱乐部热门")
    hc = api_call(club.get_home_club)
    hl = hc.get("response") if hc else []
    if hl:
        for a in hl:
            full = int(a.get("applyStudentCount", 0)) >= int(a.get("maxStudent", 1))
            tag = '<span class="tag-full">已满</span>' if full else '<span class="tag-ok">可报</span>'
            st.markdown(
                f"<div class='card'><div>{a.get('activityName')} {tag}</div>"
                f"<div class='card-sm'>{a.get('startTime')} | {a.get('addressDetail')} | {a.get('applyStudentCount')}/{a.get('maxStudent')}</div></div>",
                unsafe_allow_html=True,
            )
