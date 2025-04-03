import streamlit as st
import subprocess
import sys
import re
from pathlib import Path

# 安全配置
ALLOWED_COMMANDS = {'pip install', 'pip list'}
USER_INSTALL_DIR = Path.home() / "user_env"
MAX_OUTPUT_LINES = 200

def sanitize_command(cmd):
    """安全校验命令输入"""
    # 提取基础命令
    base_cmd = cmd.split(' ', 2)[0:2]
    if ' '.join(base_cmd) not in ALLOWED_COMMANDS:
        return None
    
    # 过滤危险字符
    sanitized = re.sub(r"[;&|$`]", "", cmd)
    
    # 添加安全参数
    if base_cmd[1] == 'install':
        return f"{sanitized} --user --target {USER_INSTALL_DIR}"
    return sanitized

def execute_command(cmd):
    """执行安全命令"""
    try:
        proc = subprocess.run(
            [sys.executable, "-m"] + cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30
        )
        return proc.stdout.strip()[:5000]
    except Exception as e:
        return str(e)

# 初始化环境
USER_INSTALL_DIR.mkdir(exist_ok=True)
if str(USER_INSTALL_DIR) not in sys.path:
    sys.path.append(str(USER_INSTALL_DIR))

# 页面配置
st.set_page_config(
    page_title="安全包管理器",
    page_icon="🔒",
    layout="centered"
)

# 主界面
st.title("🔒 沙箱式Python包管理")
with st.expander("使用指南", expanded=True):
    st.markdown("""
    ### 安全命令行模式
    支持以下命令：
    - `pip install <package>` - 安装指定包
    - `pip list` - 查看已安装包

    示例：
    ```bash
    pip install requests==2.28.2
    pip install numpy~=1.23.0
    pip list
    ```
    """)

# 命令行接口
with st.form("cli-form"):
    cmd_input = st.text_input(
        "输入命令：",
        placeholder="pip install package",
        help="支持标准pip语法，自动添加安全参数"
    )
    submitted = st.form_submit_button("执行")

if submitted:
    if not cmd_input:
        st.error("请输入有效命令")
    else:
        safe_cmd = sanitize_command(cmd_input)
        if not safe_cmd:
            st.error("禁止执行该命令")
            st.stop()
        
        with st.spinner("执行中..."):
            output = execute_command(safe_cmd)
            
            st.markdown("### 执行结果")
            st.code(output)
            
            if "Successfully installed" in output:
                st.balloons()

# 环境状态显示
st.markdown("### 环境信息")
col1, col2 = st.columns(2)
with col1:
    st.metric("安装目录", str(USER_INSTALL_DIR))
with col2:
    st.metric("已安装包数", len(list(USER_INSTALL_DIR.glob("*.dist-info"))))

# 安全提示
st.markdown("""
---
**安全机制说明**：
1. 命令白名单验证
2. 自动过滤危险字符
3. 用户空间隔离安装
4. 30秒执行超时
5. 输出内容限制
""")