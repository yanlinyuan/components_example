import streamlit as st
import subprocess
import os
import requests
from pathlib import Path

# 设置页面标题和图标
st.set_page_config(
    page_title="Cloud Terminal",
    page_icon="🖥️",
    layout="centered"
)

def install_miniforge():
    """安装Miniforge3到用户目录"""
    home = Path.home()
    miniforge_path = home / "miniforge3"
    conda_exec = miniforge_path / "bin" / "conda"
    
    if not conda_exec.exists():
        try:
            # 下载Miniforge安装脚本
            st.info("🚀 开始下载Miniforge3...")
            url = "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
            response = requests.get(url)
            response.raise_for_status()
            
            with open("miniforge_installer.sh", "wb") as f:
                f.write(response.content)
            os.chmod("miniforge_installer.sh", 0o755)
            
            # 静默安装到用户目录
            st.info("🛠️ 正在安装Miniforge3...（这可能需要几分钟）")
            install_cmd = f"bash miniforge_installer.sh -b -p {miniforge_path}"
            process = subprocess.run(install_cmd, 
                                   shell=True, 
                                   capture_output=True, 
                                   text=True,
                                   env=os.environ)
            
            # 更新PATH环境变量
            conda_bin = str(miniforge_path / "bin")
            os.environ["PATH"] = f"{conda_bin}:{os.environ['PATH']}"
            
            # 初始化conda
            subprocess.run(f"{conda_bin}/conda init bash", 
                          shell=True, 
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)
            
            st.success("✅ Miniforge3安装完成！")
            
        except Exception as e:
            st.error(f"安装失败: {str(e)}")
            st.stop()
    else:
        st.session_state.conda_installed = True

def execute_command(command):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(command,
                              shell=True,
                              capture_output=True,
                              text=True,
                              env=os.environ)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}

# 主程序
def main():
    st.title("☁️ Cloud Terminal")
    st.markdown("在浏览器中执行Linux命令（支持conda环境）")
    
    # 初始化session状态
    if "history" not in st.session_state:
        st.session_state.history = []
    
    # 安装Miniforge3
    with st.status("检查系统环境...", expanded=True) as status:
        install_miniforge()
        status.update(label="环境准备就绪", state="complete", expanded=False)
    
    # 命令输入框
    command = st.chat_input("输入Linux命令（例如：conda list）", key="cmd_input")
    
    if command:
        # 执行命令
        with st.spinner("执行中..."):
            output = execute_command(command)
        
        # 记录历史
        st.session_state.history.append({
            "command": command,
            "output": output
        })
        
        # 显示最新结果
        latest = st.session_state.history[-1]
        
        with st.expander(f"命令: `{latest['command']}`", expanded=True):
            if latest['output'].get("error"):
                st.error(latest['output']["error"])
            
            if latest['output']["stdout"]:
                st.subheader("输出")
                st.code(latest['output']["stdout"])
            
            if latest['output']["stderr"]:
                st.subheader("错误")
                st.error(latest['output']["stderr"])
            
            st.caption(f"返回代码: {latest['output']['returncode']}")

if __name__ == "__main__":
    main()
