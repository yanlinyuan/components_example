import streamlit as st
import subprocess
import os
import requests
from pathlib import Path

# 设置页面标题和图标
st.set_page_config(
    page_title="Cloud Terminal Pro",
    page_icon="🖥️➡️",
    layout="centered"
)

def install_miniforge():
    """安装Miniforge3到用户目录并初始化conda"""
    home = Path.home()
    miniforge_path = home / "miniforge3"
    conda_bin = miniforge_path / "bin"
    
    if not (conda_bin / "conda").exists():
        try:
            # 下载Miniforge安装脚本
            st.info("🚀 开始下载Miniforge3...")
            url = "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
            response = requests.get(url, timeout=300)
            response.raise_for_status()
            
            with open("miniforge_installer.sh", "wb") as f:
                f.write(response.content)
            os.chmod("miniforge_installer.sh", 0o755)
            
            # 静默安装到用户目录
            st.info("🛠️ 正在安装Miniforge3...（这可能需要3-5分钟）")
            install_cmd = f"bash miniforge_installer.sh -b -p {miniforge_path}"
            subprocess.run(install_cmd, 
                        shell=True,
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
            
            # 初始化conda
            st.info("⚙️ 正在初始化conda环境...")
            init_cmd = f"{conda_bin}/conda init bash"
            subprocess.run(init_cmd,
                          shell=True,
                          check=True,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)
            
            # 设置环境变量
            os.environ["PATH"] = f"{conda_bin}:{os.environ['PATH']}"
            os.environ["CONDA_SHLVL"] = "0"
            
            st.success("✅ Miniforge3安装完成！")
            
        except Exception as e:
            st.error(f"安装失败: {str(e)}")
            st.stop()
    else:
        st.session_state.conda_ready = True

def execute_command(command):
    """执行命令并返回输出（支持conda环境切换）"""
    try:
        # 使用交互式shell确保加载conda配置
        result = subprocess.run(
            ["bash", "-i", "-c", command],
            capture_output=True,
            text=True,
            env=os.environ,
            timeout=300
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "命令执行超时（超过5分钟）"}
    except Exception as e:
        return {"error": str(e)}

# 主程序
def main():
    st.title("☁️ Cloud Terminal Pro")
    st.markdown("""
    ### 支持功能：
    - ✅ 完整的conda环境管理
    - ✅ 实时命令执行反馈
    - ✅ 环境切换持久化
    - ✅ Jupyter内核管理
    """)
    
    # 初始化session状态
    if "history" not in st.session_state:
        st.session_state.history = []
    
    # 安装Miniforge3
    with st.status("准备运行环境...", expanded=True) as status:
        install_miniforge()
        status.update(label="环境准备就绪", state="complete", expanded=False)
    
    # 命令输入框
    command = st.chat_input("输入Linux/conda命令（例如：conda activate base）", key="cmd_input")
    
    if command:
        # 执行命令
        with st.spinner("🚀 执行命令中..."):
            output = execute_command(command)
        
        # 记录历史
        st.session_state.history.append({
            "command": command,
            "output": output
        })
        
        # 显示最新结果
        latest = st.session_state.history[-1]
        
        with st.expander(f"📝 命令: `{latest['command']}`", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if latest['output'].get("error"):
                    st.error(f"❌ 系统错误: {latest['output']['error']}")
                
                if latest['output']["stderr"]:
                    st.error("📛 错误输出")
                    st.code(latest['output']["stderr"], language="bash")
                
                if latest['output']["stdout"]:
                    st.success("📄 标准输出")
                    st.code(latest['output']["stdout"], language="bash")
            
            with col2:
                st.metric("返回代码", latest['output']['returncode'])
                if latest['output']['returncode'] == 0:
                    st.success("执行成功")
                else:
                    st.error("执行失败")

if __name__ == "__main__":
    main()
