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

def display_cpu_cores(cpu_percent):
    st.subheader("CPU核心使用情况")
    num_cores = len(cpu_percent)
    columns_per_row = 4  # 每行显示4个核心
    
    for i in range(0, num_cores, columns_per_row):
        cols = st.columns(columns_per_row)
        for j in range(columns_per_row):
            core_index = i + j
            if core_index < num_cores:
                with cols[j]:
                    label = f"Core {core_index}"
                    value = cpu_percent[core_index]
                    st.metric(label, f"{value:.1f}%")
                    st.progress(value / 100)

def display_memory():
    st.subheader("内存使用详情")
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**物理内存**")
        st.metric("总容量", f"{mem.total / (1024**3):.2f} GB")
        st.metric("使用率", f"{mem.percent}%")
        st.progress(mem.percent / 100)
        st.metric("可用内存", f"{mem.available / (1024**3):.2f} GB")
    
    with col2:
        st.markdown("**交换空间**")
        st.metric("总容量", f"{swap.total / (1024**3):.2f} GB")
        st.metric("使用率", f"{swap.percent}%" if swap.total > 0 else "N/A")
        if swap.total > 0:
            st.progress(swap.percent / 100)
        st.metric("已用交换", f"{swap.used / (1024**3):.2f} GB")

def main():
    st.set_page_config(page_title="Advanced System Monitor", layout="wide")
    st.title("🖥️ 高级系统监控（htop增强版）")

    # 自定义设置
    refresh_interval = st.sidebar.slider("刷新间隔(秒)", 1, 10, 2)
    show_swap = st.sidebar.checkbox("显示交换空间", True)

    # 创建占位符
    cpu_placeholder = st.empty()
    mem_placeholder = st.empty()
    process_placeholder = st.empty()

    while True:
        # 获取CPU数据
        cpu_percent = psutil.cpu_percent(percpu=True)
        
        # 更新CPU显示
        with cpu_placeholder.container():
            display_cpu_cores(cpu_percent)
        
        # 更新内存显示
        with mem_placeholder.container():
            display_memory()
        
        # 更新进程列表
        with process_placeholder.container():
            st.subheader("进程列表")
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
                height=400
            )
        
        time.sleep(refresh_interval)

if __name__ == "__main__":
    main()
