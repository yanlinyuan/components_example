import streamlit as st
import subprocess
import platform
import sys
import re
import requests
from socket import gethostname, gethostbyname
import os
import time
from pathlib import Path

def get_system_info():
    """获取系统级信息，包含IP地址"""
    try:
        # 获取基础系统信息
        os_info = {
            "System": platform.system(),
            "Release": platform.release(),
            "Version": platform.version(),
            "Machine": platform.machine(),
            "Hostname": gethostname()
        }

        # 获取IP地址信息
        try:
            # 获取内网IP
            os_info["Internal IP"] = gethostbyname(gethostname())
            
            # 获取公网IP
            ip_response = requests.get('https://api.ipify.org?format=json', timeout=3)
            if ip_response.status_code == 200:
                os_info["Public IP"] = ip_response.json()["ip"]
            else:
                os_info["Public IP"] = "获取失败"
        except Exception as ip_error:
            os_info["Public IP"] = f"获取错误: {str(ip_error)}"

        return os_info
    except Exception as e:
        return {"Error": str(e)}

def get_filesystem_info():
    """获取文件系统结构信息"""
    try:
        # 获取当前工作目录
        current_path = Path.cwd()
        
        # 获取文件系统结构（限制3层深度）
        fs_structure = {}
        def scan_directory(path, depth=0):
            if depth > 2:  # 控制扫描深度
                return {}
            structure = {}
            try:
                for entry in path.iterdir():
                    if entry.is_dir():
                        structure[entry.name + '/'] = scan_directory(entry, depth+1)
                    else:
                        structure[entry.name] = "file"
            except Exception as e:
                structure[f"⚠️访问错误({str(e)})"] = {}
            return structure
        
        # 获取文件列表详细信息
        file_list = []
        for item in current_path.iterdir():
            try:
                stat = item.stat()
                file_list.append({
                    "name": item.name + ('/' if item.is_dir() else ''),
                    "size": f"{stat.st_size/1024:.1f}KB",
                    "modified": time.strftime('%Y-%m-%d %H:%M', 
                                   time.localtime(stat.st_mtime)),
                    "type": "目录" if item.is_dir() else "文件"
                })
            except Exception as e:
                file_list.append({
                    "name": f"⚠️{item.name}",
                    "size": "N/A",
                    "modified": "访问错误",
                    "type": str(e)
                })
        
        return {
            "current_path": str(current_path),
            "structure": scan_directory(current_path.parent),  # 显示上级目录结构
            "files": file_list
        }
    except Exception as e:
        return {"Error": f"文件系统扫描失败: {str(e)}"}

def display_filesystem_info(fs_info):
    """显示文件系统信息"""
    if "Error" in fs_info:
        st.error(fs_info["Error"])
        return
    
    cols = st.columns([2, 3])
    
    with cols[0]:
        st.markdown("**目录结构**")
        with st.container(height=300):
            def print_structure(structure, indent=0):
                for name, contents in structure.items():
                    st.markdown(f"{'&nbsp;'*indent*4}📁 {name}" if name.endswith('/') else 
                               f"{'&nbsp;'*indent*4}📄 {name}")
                    if isinstance(contents, dict):
                        print_structure(contents, indent+1)
            
            print_structure(fs_info["structure"])
    
    with cols[1]:
        st.markdown(f"**当前路径：** `{fs_info['current_path']}`")
        st.markdown("**文件列表**")
        st.dataframe(
            fs_info["files"],
            column_config={
                "name": "文件名",
                "size": "大小",
                "modified": "修改时间",
                "type": "类型"
            },
            use_container_width=True,
            height=300
        )

# 修改后的系统信息展示部分
def display_system_info():
    """显示增强后的系统信息"""
    with st.expander("📋 系统基本信息", expanded=True):
        sys_info = get_system_info()
        fs_info = get_filesystem_info()
        
        # 三栏布局
        info_cols = st.columns([2, 2, 3])
        
        with info_cols[0]:
            st.markdown("**操作系统信息**")
            st.json({
                "系统类型": sys_info.get("System", "N/A"),
                "发行版本": sys_info.get("Release", "N/A"),
                "系统版本": sys_info.get("Version", "N/A")
            })
        
        with info_cols[1]:
            st.markdown("**网络信息**")
            st.json({
                "主机名": sys_info.get("Hostname", "N/A"),
                "内网IP": sys_info.get("Internal IP", "N/A"),
                "公网IP": sys_info.get("Public IP", "N/A")
            })
        
        with info_cols[2]:
            st.markdown("**文件系统**")
            display_filesystem_info(fs_info)

# 其他函数保持原有实现不变（get_system_packages, get_python_packages, display_combined_packages等）
def get_system_packages():
    """获取系统级安装的软件包"""
    try:
        system = platform.system()
        packages = {}

        if system == "Linux":
            # 尝试获取Debian/Ubuntu系软件包
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True,
                check=True
            )
            # 解析dpkg输出
            for line in result.stdout.split('\n'):
                if line.startswith('ii '):
                    parts = re.split(r'\s+', line.strip(), maxsplit=4)
                    if len(parts) >= 4:
                        packages[parts[1]] = parts[2]

        elif system == "Darwin":
            # 尝试获取Homebrew安装的软件
            result = subprocess.run(
                ["brew", "list", "--versions"],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        packages[parts[0]] = ' '.join(parts[1:])

        elif system == "Windows":
            # 获取Windows已安装程序
            result = subprocess.run(
                ["powershell", "Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion"],
                capture_output=True,
                text=True,
                check=True,
                shell=True
            )
            for line in result.stdout.split('\n')[3:-3]:
                if line.strip():
                    parts = line.split(maxsplit=1)
                    if len(parts) >= 2:
                        name = re.sub(r'\s{2,}', ' ', parts[0])
                        version = parts[1].strip()
                        packages[name] = version

        else:
            return {"Error": f"Unsupported OS: {system}"}

        return packages

    except subprocess.CalledProcessError as e:
        return {"Error": f"命令执行失败: {e.stderr}"}
    except FileNotFoundError:
        return {"Error": "包管理器未找到"}
    except Exception as e:
        return {"Error": str(e)}

def get_python_packages():
    """获取Python安装包信息"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        packages = {}
        for line in result.stdout.split('\n'):
            if '==' in line:
                pkg, ver = line.split('==')
                packages[pkg.strip()] = ver.strip()
        return packages
    except subprocess.CalledProcessError as e:
        return {"Error": f"命令执行失败: {e.stderr}"}
    except Exception as e:
        return {"Error": str(e)}

def display_combined_packages(system_pkgs, python_pkgs):
    """显示合并后的软件包信息"""
    tab1, tab2 = st.tabs(["系统软件", "Python包"])
    
    with tab1:
        if "Error" in system_pkgs:
            st.error(system_pkgs["Error"])
        else:
            st.subheader(f"系统软件包 ({len(system_pkgs)}个)")
            display_package_table(system_pkgs, "system")
    
    with tab2:
        if "Error" in python_pkgs:
            st.error(python_pkgs["Error"])
        else:
            st.subheader(f"Python包 ({len(python_pkgs)}个)")
            display_package_table(python_pkgs, "python")

def display_package_table(packages, pkg_type):
    """通用包信息显示组件（增强版）"""
    if not packages:
        st.warning("没有找到软件包信息")
        return
    
    # 创建搜索框
    search_term = st.text_input(
        "输入名称过滤：", 
        key=f"search_{pkg_type}",
        placeholder="支持模糊搜索"
    )
    
    # 过滤结果
    filtered = {k:v for k,v in packages.items() if search_term.lower() in k.lower()}
    
    # 分页控制
    if filtered:
        PAGE_SIZE = 25
        total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
        
        cols = st.columns([2,1,3])
        with cols[1]:
            page = st.number_input(
                "页码",
                min_value=1,
                max_value=total_pages,
                value=1,
                key=f"page_{pkg_type}"
            )
        
        # 显示分页信息
        start = (page-1)*PAGE_SIZE
        end = start + PAGE_SIZE
        st.caption(f"显示第 {start+1}-{min(end, len(filtered))} 条，共 {len(filtered)} 条")
        
        # 显示表格
        st.table(
            list(filtered.items())[start:end]
        )
    else:
        st.warning("没有找到匹配的软件包")

# 页面配置
st.set_page_config(
    page_title="服务器软件全景",
    page_icon="🖥️",
    layout="wide"
)

# 主界面
st.title("🖥️ 服务器环境全景视图")

# 系统信息展示
with st.expander("📋 系统基本信息", expanded=True):
    sys_info = get_system_info()
    
    # 美化显示
    info_cols = st.columns(2)
    with info_cols[0]:
        st.markdown("**操作系统信息**")
        st.json({
            "系统类型": sys_info.get("System", "N/A"),
            "发行版本": sys_info.get("Release", "N/A"),
            "系统版本": sys_info.get("Version", "N/A")
        })
    
    with info_cols[1]:
        st.markdown("**网络信息**")
        st.json({
            "主机名": sys_info.get("Hostname", "N/A"),
            "内网IP": sys_info.get("Internal IP", "N/A"),
            "公网IP": sys_info.get("Public IP", "N/A")
        })

# 软件信息展示
st.markdown("## 📦 已安装软件清单")

if st.button("🔄 一键刷新所有软件信息", type="primary"):
    with st.spinner("正在全面扫描系统，可能需要较长时间..."):
        system_pkgs = get_system_packages()
        python_pkgs = get_python_packages()
        
        # 使用session_state保存结果
        st.session_state.system_pkgs = system_pkgs
        st.session_state.python_pkgs = python_pkgs

# 显示存储的结果
if 'system_pkgs' in st.session_state and 'python_pkgs' in st.session_state:
    display_combined_packages(
        st.session_state.system_pkgs,
        st.session_state.python_pkgs
    )

# 注意事项
st.markdown("""
---
**注意事项**：
1. 系统软件检测支持：Linux (dpkg)、macOS (Homebrew)、Windows (注册表)
2. 公网IP通过第三方API获取，可能受网络环境影响
3. 数据仅反映当前运行环境状态
4. 首次加载可能需要30秒左右完成扫描
""")

# 样式调整
st.markdown("""
<style>
div[data-baseweb="input"] > input {
    max-width: 300px;
}
div.stSpinner > div {
    margin: auto;
}
</style>
""", unsafe_allow_html=True)

# 修改主界面调用
def main():
    st.set_page_config(
        page_title="服务器全景监控",
        page_icon="🖥️",
        layout="wide"
    )
    st.title("🖥️ 服务器环境全景监控")
    
    # 显示系统信息（包含文件系统）
    display_system_info()
    
    # 软件信息部分保持不变
    st.markdown("## 📦 已安装软件清单")
    # ... 原有软件信息显示代码

if __name__ == "__main__":
    main()