import streamlit as st
import subprocess
import sys
import signal
from queue import Queue, Empty
from threading import Thread

def install_ipython():
    with st.spinner("Installing IPython..."):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ipython"])
            st.success("IPython installed successfully!")
        except subprocess.CalledProcessError as e:
            st.error(f"Installation failed: {e}")

def enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def start_ipython():
    if 'ipython_process' not in st.session_state:
        process = subprocess.Popen(["ipython"],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  text=True,
                                  bufsize=1,
                                  universal_newlines=True,
                                  shell=True,
                                  preexec_fn=os.setsid)
        
        st.session_state.ipython_process = process
        st.session_state.output_queue = Queue()
        st.session_state.error_queue = Queue()
        
        Thread(target=enqueue_output, args=(process.stdout, st.session_state.output_queue)).start()
        Thread(target=enqueue_output, args=(process.stderr, st.session_state.error_queue)).start()

def stop_ipython():
    if 'ipython_process' in st.session_state:
        os.killpg(os.getpgid(st.session_state.ipython_process.pid), signal.SIGTERM)
        del st.session_state.ipython_process
        del st.session_state.output_queue
        del st.session_state.error_queue

def read_output():
    output = []
    while True:
        try:
            output.append(st.session_state.output_queue.get_nowait())
        except Empty:
            break
    return ''.join(output)

# 应用界面
st.title("🖥️ IPython 交互式终端")
st.warning("⚠️ 高危操作：本程序可以执行任意Python代码，请谨慎使用！")

# 侧边栏操作
with st.sidebar:
    if st.button("安装 IPython"):
        install_ipython()
    
    if st.button("终止 IPython 会话"):
        stop_ipython()
        st.experimental_rerun()

# IPython会话处理
if 'ipython_process' not in st.session_state:
    start_ipython()

command = st.text_input("输入Python代码（支持多行代码）：", value="print('Hello IPython!')", key="ipython_input")

if st.button("执行代码"):
    if 'ipython_process' not in st.session_state:
        st.error("IPython会话未启动")
        st.stop()
    
    process = st.session_state.ipython_process
    process.stdin.write(command + "\n\n")
    process.stdin.flush()
    
    st.write("**执行代码：**")
    st.code(command)
    
    st.write("**输出结果：**")
    output = read_output()
    if output:
        st.code(output)
    
    error_output = []
    while True:
        try:
            error_output.append(st.session_state.error_queue.get_nowait())
        except Empty:
            break
    if error_output:
        st.error(''.join(error_output))

st.markdown("---")
st.info("使用说明：\n"
        "1. 自动启动IPython会话\n"
        "2. 输入Python代码（支持多行）\n"
        "3. 点击'执行代码'按钮\n"
        "4. 侧边栏可终止会话\n"
        "5. 支持完整的IPython功能（魔术命令、自动补全等）")

# 安全警告
st.error("""
❗ 安全警告：
- 本程序可以执行任意Python代码
- 请勿在生产环境开放此功能
- 所有操作具有最高权限
- 可能造成服务器安全风险
""")
