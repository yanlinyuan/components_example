import streamlit as st
import psutil
import pandas as pd
import time

def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            processes.append({
                'PID': proc.info['pid'],
                'Name': proc.info['name'],
                'User': proc.info['username'],
                'CPU%': proc.info['cpu_percent'],
                'MEM%': proc.info['memory_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return pd.DataFrame(processes).sort_values('CPU%', ascending=False)

def main():
    st.set_page_config(page_title="Streamlit htop", layout="wide")
    st.title("🖥️ Streamlit System Monitor (htop-like)")

    # 自定义刷新频率
    refresh_interval = st.sidebar.slider("刷新间隔(秒)", 1, 10, 2)

    # 创建占位符用于动态更新
    metrics_placeholder = st.empty()
    process_placeholder = st.empty()

    while True:
        # 获取系统信息
        cpu_percent = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        
        # 构建指标显示
        with metrics_placeholder.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("CPU使用率", f"{cpu_percent}%")
                st.progress(cpu_percent / 100)
            
            with col2:
                st.metric("内存使用率", f"{mem.percent}%")
                st.progress(mem.percent / 100)
            
            with col3:
                st.metric("总内存", f"{mem.total // (1024**3)}GB")
                st.metric("可用内存", f"{mem.available // (1024**3)}GB")

        # 获取并显示进程信息
        with process_placeholder.container():
            df = get_processes()
            st.dataframe(
                df,
                column_config={
                    "CPU%": st.column_config.ProgressColumn(
                        "CPU%",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "MEM%": st.column_config.ProgressColumn(
                        "MEM%",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    )
                },
                hide_index=True,
                use_container_width=True,
                height=600
            )

        time.sleep(refresh_interval)

if __name__ == "__main__":
    main()
