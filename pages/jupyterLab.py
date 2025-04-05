# jupyterLab.py
import streamlit as st
import subprocess

st.title("JupyterLab 管理器")

with st.expander("安装JupyterLab"):
    if st.button("安装"):
        with st.spinner("安装中..."):
            result = subprocess.run(["pip", "install", "jupyterlab"], 
                                 capture_output=True, text=True)
            st.code(result.stdout)

with st.expander("启动JupyterLab（模拟）"):
    st.warning("""
    由于Streamlimt Cloud限制：
    1. 无法绑定非标准端口
    2. 无法保持进程运行
    3. 外部无法访问其他端口
    """)
    st.code("""
    # 本地环境可用的启动命令
    jupyter lab --ip=0.0.0.0 --port=8501 \
    --no-browser --allow-root \
    --NotebookApp.token='' --NotebookApp.password=''
    """)
    