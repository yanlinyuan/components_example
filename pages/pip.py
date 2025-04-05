import streamlit as st
import subprocess

def run_command(command):
    try:
        result = subprocess.run(
            command.split(),
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return f"$ {command}\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"$ {command}\nError: {e.stderr}"
    except Exception as e:
        return f"$ {command}\nError: {str(e)}"

st.title("命令行执行工具")
st.warning("注意：此工具仅用于演示目的，请谨慎执行系统命令！")

command = st.text_input("输入命令行指令（例如：pip --version）", 
                       placeholder="输入有效的系统命令")

if st.button("执行"):
    if command.strip():
        with st.spinner("执行中..."):
            output = run_command(command)
            st.code(output, language="bash")
    else:
        st.warning("请输入有效命令")
