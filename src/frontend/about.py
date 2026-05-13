import streamlit as st


def show_about_page():
    st.markdown("### 行迹 PaceTrace")
    st.markdown("校园跑管理工具")
    st.divider()
    st.markdown(
        """
**授权协议**

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

**合理使用声明**

1. 本软件仅供个人学习、研究使用
2. 使用者应遵守所在学校的校园跑相关规定
3. 开发者不对因使用本软件产生的任何后果承担责任
4. 本软件不收集、上传任何用户个人信息
5. 所有数据仅存储在用户本地设备

[GitHub](https://github.com/csy214-beep/PaceTrace) · [ISSUE](https://github.com/csy214-beep/PaceTrace/issues) · [PR](https://github.com/csy214-beep/PaceTrace/pulls)
    """
    )
