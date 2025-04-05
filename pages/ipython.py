import streamlit as st
import subprocess
import sys

def install_ipython():
    with st.spinner("Installing IPython..."):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ipython"])
            st.success("IPython installed successfully!")
        except subprocess.CalledProcessError as e:
            st.error(f"Installation failed: {e}")

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True,
                                capture_output=True, text=True, timeout=30)
        return result.stdout, None
    except subprocess.CalledProcessError as e:
        return e.stdout + e.stderr, e
    except Exception as e:
        return None, e

# 应用界面
st.title("🖥️ 命令行终端模拟器")
st.warning("⚠️ 注意：本程序可以执行任意系统命令，请谨慎使用！")

# 侧边栏安装IPython
with st.sidebar:
    if st.button("安装 IPython"):
        install_ipython()

# 主界面
command = st.text_input("输入命令（支持所有系统命令）：", "ls -la")

if st.button("执行命令"):
    if not command:
        st.warning("请输入要执行的命令")
    else:
        st.write(f"**执行命令：** `{command}`")
        st.write("**输出结果：**")
        
        with st.spinner("执行中..."):
            output, error = execute_command(command)
        
        if output:
            st.code(output)
        if error:
            st.error(f"发生错误：{str(error)}")

st.markdown("---")
st.info("使用说明：\n"
        "1. 在输入框输入命令（如：`ping google.com`）\n"
        "2. 点击'执行命令'按钮\n"
        "3. 侧边栏可以安装IPython\n"
        "4. 支持所有系统命令（Linux命令）")
