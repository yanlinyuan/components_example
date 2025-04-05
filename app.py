import streamlit as st
import subprocess

st.set_page_config(page_title="云端命令行工具", page_icon="💻")

def run_command(command):
    try:
        process = subprocess.run(
            command,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            check=True
        )
        return process.stdout, None
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr

# 界面布局
st.title("云端命令行终端")
st.markdown("""
⚠️ **使用须知**  
1. 支持基础Linux命令和Conda环境管理
2. 环境变动仅在当前会话有效
3. 禁止执行危险操作（rm -rf、格式化等）
""")

with st.expander("常用Conda命令示例"):
    st.code("""
# 创建环境
conda create -n myenv python=3.8 -y
# 激活环境（需在后续命令前添加）
conda activate myenv
# 安装包
conda install numpy pandas -y
# 或使用pip
pip install requests
""")

# 命令行输入
command = st.text_input("输入命令", key="cmd_input",
                        placeholder="输入要执行的命令...")

if st.button("执行") or command:
    if not command:
        st.warning("请输入命令")
        st.stop()
    
    st.divider()
    st.subheader("执行结果")
    
    with st.status("执行中...", expanded=True) as status:
        stdout, stderr = run_command(command)
        
        if stderr:
            status.update(label="执行失败 ❌", state="error")
            st.error(stderr)
        else:
            status.update(label="执行成功 ✅", state="complete")
        
        if stdout:
            st.code(stdout, line_numbers=True)

    if "conda activate" in command:
        st.info("激活环境后，需在后续命令前添加 'conda run -n 环境名'")
    