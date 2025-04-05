import streamlit as st
import subprocess
import sys
import os
import signal
from threading import Thread
from queue import Queue, Empty

# 自动安装依赖
def setup_dependencies():
    try:
        import ipython
    except ImportError:
        with st.spinner("正在自动安装IPython..."):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ipython"])
            
# 初始化会话状态
def init_session():
    if 'ipy_proc' not in st.session_state:
        st.session_state.ipy_proc = None
        st.session_state.output_queue = Queue()
        st.session_state.error_queue = Queue()

# 启动IPython进程
def start_ipython():
    if st.session_state.ipy_proc is None:
        try:
            process = subprocess.Popen(
                ["ipython", "--no-autoindent"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                shell=True,
                preexec_fn=os.setsid
            )
            
            st.session_state.ipy_proc = process
            
            # 启动输出捕获线程
            Thread(target=output_reader, args=(process.stdout, st.session_state.output_queue)).start()
            Thread(target=output_reader, args=(process.stderr, st.session_state.error_queue)).start()
            
        except Exception as e:
            st.error(f"启动IPython失败: {str(e)}")

# 输出读取线程
def output_reader(pipe, queue):
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                queue.put(line)
    finally:
        queue.put(None)

# 获取实时输出
def get_output():
    output = []
    while True:
        try:
            line = st.session_state.output_queue.get_nowait()
            if line is None:
                break
            output.append(line)
        except Empty:
            break
    return ''.join(output)

# 安全终止进程
def kill_proc():
    if st.session_state.ipy_proc:
        try:
            os.killpg(os.getpgid(st.session_state.ipy_proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        st.session_state.ipy_proc = None

# 主程序界面
st.set_page_config(page_title="Cloud IPython", layout="wide")
setup_dependencies()
init_session()

# 标题和安全警告
st.title("☁️ Cloud IPython Terminal")
st.markdown("""---""")
st.warning("""
⚠️ **高危操作警告**  
本终端拥有服务器完整权限，可执行：
- 任意Python代码
- 系统命令（使用!前缀）
- 文件系统操作
- 网络访问
""")

# 侧边栏控制面板
with st.sidebar:
    st.subheader("会话控制")
    if st.button("🔄 重启会话"):
        kill_proc()
        start_ipython()
        st.rerun()
        
    if st.button("⏹️ 终止会话"):
        kill_proc()
        st.success("会话已终止")
        
    st.markdown("""---""")
    st.subheader("快捷命令示例")
    st.code("!ls -la\ndf = pd.DataFrame(np.random.rand(5,5))\n%timeit sum(range(1000))")

# 主输入输出界面
start_ipython()  # 自动启动会话

# 输入区域
input_code = st.text_area(
    "输入Python代码或命令（支持多行）：",
    height=150,
    value="print('Hello Cloud IPython!')\nimport platform\nplatform.platform()",
    key="code_input"
)

# 执行按钮
if st.button("▶️ 执行代码"):
    if st.session_state.ipy_proc is None:
        st.error("IPython会话未启动！")
        st.stop()
    
    try:
        # 发送代码到IPython进程
        st.session_state.ipy_proc.stdin.write(input_code + "\n\n")
        st.session_state.ipy_proc.stdin.flush()
    except BrokenPipeError:
        st.error("会话连接已中断，请重启会话")
        st.stop()
    
    # 显示执行结果
    with st.expander("📜 执行结果", expanded=True):
        output = get_output()
        if output:
            st.code(output)
        
        errors = []
        while True:
            try:
                err_line = st.session_state.error_queue.get_nowait()
                if err_line is None:
                    break
                errors.append(err_line)
            except Empty:
                break
        
        if errors:
            st.error("".join(errors))

# 会话信息
with st.expander("ℹ️ 会话状态"):
    if st.session_state.ipy_proc:
        st.success(f"IPython会话运行中 (PID: {st.session_state.ipy_proc.pid})")
        st.code(f"Python版本: {sys.version.split()[0]}\nIPython路径: {sys.executable}")
    else:
        st.error("无活跃会话")

# 使用说明
st.markdown("""---""")
st.info("""
**使用指南：**
1. 输入多行Python代码（自动缩进）
2. 点击执行查看实时输出
3. 使用`!`前缀执行系统命令（例：`!pip list`）
4. 支持IPython魔术命令（例：`%timeit`, `%matplotlib inline`）
5. 侧边栏可重启/终止会话

**示例功能：**
```python
# 数据分析
import pandas as pd
import numpy as np
df = pd.DataFrame(np.random.randn(100, 4), columns=list('ABCD'))
df.describe()

# 系统操作
!ls -la | grep .streamlit

# 性能测试
%timeit [x**2 for x in range(100000)]

# 可视化（需安装matplotlib）
# %pip install matplotlib
import matplotlib.pyplot as plt
plt.plot([1,2,3,4])
plt.ylabel('示例图表')
plt.show()
