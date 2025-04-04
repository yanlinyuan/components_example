import streamlit as st
import subprocess
import platform
import sys
import re
import requests
import socket
import os
import time
from pathlib import Path
from typing import Dict, List, Union
from functools import lru_cache

# 配置常量
MAX_DIR_DEPTH = 3
PAGE_SIZE = 25
IP_API_ENDPOINTS = [
    'https://api.ipify.org?format=json',
    'https://ipinfo.io/json',
    'https://ifconfig.me/all.json'
]

def get_local_ips() -> List[str]:
    """获取所有本地IP地址"""
    ips = []
    try:
        for interface in socket.getaddrinfo(socket.gethostname(), None):
            ip = interface[4][0]
            if ip not in ips and not ip.startswith('127.'):
                ips.append(ip)
    except:
        pass
    return ips or ['无法获取']

@st.cache_data(ttl=60)
def get_public_ip() -> str:
    """获取公网IP地址，带重试机制"""
    for endpoint in IP_API_ENDPOINTS:
        try:
            response = requests.get(endpoint, timeout=3)
            if response.status_code == 200:
                return response.json().get('ip', '格式错误')
        except Exception as e:
            continue
    return '获取失败'

@st.cache_data(ttl=3600)
def get_system_info() -> Dict:
    """获取增强版系统信息"""
    try:
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "hostname": socket.gethostname(),
            "local_ips": get_local_ips(),
            "public_ip": get_public_ip(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
    except Exception as e:
        return {"error": str(e)}

def format_size(size_bytes: float) -> str:
    """智能格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f}TB"

def scan_directory(path: Path, depth: int = 0) -> Dict:
    """安全扫描目录结构"""
    structure = {}
    if depth > MAX_DIR_DEPTH:
        return structure
    
    try:
        for entry in path.iterdir():
            try:
                if entry.is_dir():
                    structure[f"📁 {entry.name}"] = scan_directory(entry, depth+1)
                else:
                    structure[f"📄 {entry.name}"] = {
                        "size": format_size(entry.stat().st_size),
                        "modified": entry.stat().st_mtime
                    }
            except Exception as e:
                structure[f"⚠️ {entry.name}"] = str(e)
    except PermissionError:
        structure["权限不足"] = {}
    except Exception as e:
        structure[f"扫描失败: {str(e)}"] = {}
    
    return structure

@st.cache_data(ttl=10)
def get_filesystem_info() -> Dict:
    """获取增强版文件系统信息"""
    try:
        current_path = Path.cwd()
        return {
            "current_path": str(current_path),
            "structure": scan_directory(current_path),
            "total_space": format_size(os.statvfs(current_path).f_blocks * os.statvfs(current_path).f_frsize),
            "free_space": format_size(os.statvfs(current_path).f_bavail * os.statvfs(current_path).f_frsize)
        }
    except Exception as e:
        return {"error": f"文件系统错误: {str(e)}"}

def display_directory_tree(tree: Dict, parent: str = "") -> None:
    """递归显示目录树形结构"""
    for name, contents in tree.items():
        if isinstance(contents, dict) and "size" not in contents:
            with st.expander(f"🗂️ {name}", expanded=depth<1):
                display_directory_tree(contents, name)
        else:
            st.markdown(f"""
            <div style="margin-left: {20*depth}px">
                🔸 {name}  
                <span style="color: #666; font-size: 0.8em">
                    {contents.get('size', '')} | 
                    {time.strftime('%Y-%m-%d', time.localtime(contents.get('modified')))}
                </span>
            </div>
            """, unsafe_allow_html=True)

def display_system_panel() -> None:
    """显示系统信息面板"""
    with st.expander("🖥️ 系统概览", expanded=True):
        cols = st.columns([1,1,2])
        sys_info = get_system_info()
        fs_info = get_filesystem_info()
        
        with cols[0]:
            st.subheader("系统信息")
            st.metric("操作系统", f"{sys_info.get('system', '')} {sys_info.get('release', '')}")
            st.metric("Python版本", sys_info.get('python_version', '未知'))
            
        with cols[1]:
            st.subheader("网络信息")
            st.metric("公网IP", sys_info.get('public_ip', '未知'))
            st.metric("内网IP", ", ".join(sys_info.get('local_ips', [])))
            
        with cols[2]:
            st.subheader("存储信息")
            if not fs_info.get("error"):
                st.write(f"**当前路径:** `{fs_info['current_path']}`")
                st.progress(1 - (os.statvfs(fs_info['current_path']).f_bavail / 
                           os.statvfs(fs_info['current_path']).f_blocks))
                cols = st.columns(2)
                cols[0].metric("总空间", fs_info["total_space"])
                cols[1].metric("可用空间", fs_info["free_space"])

def get_system_packages() -> Dict:
    """跨平台获取系统软件包"""
    system = platform.system()
    try:
        if system == "Linux":
            return parse_dpkg_packages()
        elif system == "Darwin":
            return parse_brew_packages()
        elif system == "Windows":
            return parse_winget_packages()
        return {"error": f"不支持的系统: {system}"}
    except Exception as e:
        return {"error": str(e)}

def parse_dpkg_packages() -> Dict:
    """解析Debian系软件包"""
    result = subprocess.run(["dpkg", "-l"], capture_output=True, text=True)
    return {
        parts[1]: parts[2] 
        for line in result.stdout.splitlines() 
        if line.startswith('ii ') and (parts := re.split(r'\s+', line, 4))
    }

def parse_brew_packages() -> Dict:
    """解析Homebrew软件包"""
    result = subprocess.run(["brew", "list", "--versions"], capture_output=True, text=True)
    return {
        parts[0]: ' '.join(parts[1:])
        for line in result.stdout.splitlines()
        if line and (parts := line.split())
    }

def parse_winget_packages() -> Dict:
    """解析Windows软件包"""
    ps_command = """
    Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* |
    Select-Object DisplayName, DisplayVersion |
    Where-Object { $_.DisplayName -ne $null }
    """
    result = subprocess.run(
        ["powershell", "-Command", ps_command],
        capture_output=True, 
        text=True,
        shell=True
    )
    packages = {}
    for line in result.stdout.splitlines()[3:-3]:
        if line.strip() and (parts := re.split(r'\s{2,}', line, 1)):
            packages[parts[0]] = parts[1].strip() if len(parts) > 1 else '未知版本'
    return packages

@st.cache_data
def get_python_packages() -> Dict:
    """获取Python包信息"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=freeze"],
            capture_output=True,
            text=True
        )
        return dict(
            tuple(pkg.split('==')) 
            for line in result.stdout.splitlines() 
            if '==' in (pkg := line.strip())
        )
    except Exception as e:
        return {"error": str(e)}

def display_package_table(packages: Dict, title: str) -> None:
    """交互式表格显示"""
    if "error" in packages:
        st.error(packages["error"])
        return
    
    search_term = st.text_input(
        f"搜索{title}包", 
        placeholder="输入包名关键词...",
        key=f"search_{title}"
    )
    
    filtered = {
        k:v for k,v in packages.items()
        if search_term.lower() in k.lower()
    }
    
    if not filtered:
        st.warning("未找到匹配的软件包")
        return
    
    st.dataframe(
        pd.DataFrame.from_dict(filtered, orient='index', columns=["版本"]),
        use_container_width=True,
        height=600
    )

def main():
    st.set_page_config(
        page_title="服务器监控仪表盘",
        page_icon="🖥️",
        layout="wide"
    )
    st.title("服务器全景监控仪表盘")
    
    display_system_panel()
    
    st.header("📦 软件仓库")
    tab1, tab2 = st.tabs(["系统软件", "Python包"])
    
    with tab1:
        if st.button("扫描系统软件", key="scan_system"):
            with st.spinner("正在扫描系统软件..."):
                st.session_state.system_packages = get_system_packages()
        if "system_packages" in st.session_state:
            display_package_table(st.session_state.system_packages, "系统")
    
    with tab2:
        if st.button("扫描Python包", key="scan_python"):
            with st.spinner("正在扫描Python环境..."):
                st.session_state.python_packages = get_python_packages()
        if "python_packages" in st.session_state:
            display_package_table(st.session_state.python_packages, "Python")
    
    st.sidebar.markdown("### 操作说明")
    st.sidebar.info("""
    1. 点击各区域的扫描按钮获取最新数据
    2. 使用搜索框快速定位软件包
    3. 表格支持点击列标题排序
    4. 数据自动缓存60秒
    """)

if __name__ == "__main__":
    main()
