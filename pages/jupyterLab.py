import streamlit as st
import subprocess
import sys
import os
from io import StringIO
from contextlib import redirect_stdout

# 初始化session状态
if 'cwd' not in st.session_state:
    st.session_state.cwd = os.getcwd()
if 'history' not in st.session_state:
    st.session_state.history = []
if 'files' not in st.session_state:
    st.session_state.files = []

# 安全警告
st.sidebar.warning("""
**安全警告**: 此应用允许执行任意代码和命令，存在严重安全风险！
请勿在公共环境中部署，仅限受信任的本地环境使用。
""")

# 功能选择
function = st.sidebar.selectbox(
    "功能模块",
    ("命令终端", "Python编辑器", "文件管理", "Markdown笔记本")
)

# 命令终端模块
if function == "命令终端":
    st.header("系统终端模拟")
    command = st.text_input("输入命令（当前目录：{}）".format(st.session_state.cwd))
    
    if st.button("执行命令"):
        try:
            process = subprocess.run(
                command.split(),
                cwd=st.session_state.cwd,
                capture_output=True,
                text=True
            )
            output = f"STDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
        except Exception as e:
            output = str(e)
        
        st.session_state.history.append(f"$ {command}\n{output}")
        st.code(output)
    
    with st.expander("命令历史"):
        st.code("\n\n".join(st.session_state.history[-5:]))

# Python编辑器模块
elif function == "Python编辑器":
    st.header("Python代码编辑器")
    code = st.text_area("输入Python代码", height=200)
    
    if st.button("执行代码"):
        stdout = StringIO()
        try:
            with redirect_stdout(stdout):
                exec(code)
            output = stdout.getvalue()
        except Exception as e:
            output = str(e)
        
        st.session_state.history.append(f"In []: {code}\nOut[]: {output}")
        st.code(output)

# 文件管理模块
elif function == "文件管理":
    st.header("文件浏览器")
    
    # 显示当前目录内容
    files = os.listdir(st.session_state.cwd)
    selected_file = st.selectbox("当前目录文件", files)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("刷新文件列表"):
            files = os.listdir(st.session_state.cwd)
    
    with col2:
        new_dir = st.text_input("切换目录")
        if st.button("切换"):
            if os.path.isdir(new_dir):
                st.session_state.cwd = new_dir
                files = os.listdir(new_dir)
    
    # 文件上传下载
    uploaded_file = st.file_uploader("上传文件")
    if uploaded_file:
        with open(os.path.join(st.session_state.cwd, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"文件 {uploaded_file.name} 上传成功")

    if selected_file:
        if st.button("下载文件"):
            with open(os.path.join(st.session_state.cwd, selected_file), "rb") as f:
                st.download_button(
                    label="下载选中文件",
                    data=f,
                    file_name=selected_file
                )

# Markdown笔记本模块
elif function == "Markdown笔记本":
    st.header("Markdown笔记本")
    md_content = st.text_area("输入Markdown内容", height=300)
    st.markdown("---")
    st.markdown(md_content)

# 运行说明
st.sidebar.markdown("""
### 使用说明
1. 命令终端：执行系统命令（支持Linux命令）
2. Python编辑器：执行Python代码
3. 文件管理：浏览/上传/下载文件
4. Markdown笔记本：编写格式化的文档

**依赖安装**（在requirements.txt中添加）：
