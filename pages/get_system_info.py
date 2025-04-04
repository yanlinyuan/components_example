import streamlit as st
import subprocess
import platform
import sys
import re

def get_system_info():
    """获取系统级软件信息"""
    try:
        os_info = {
            "System": platform.system(),
            "Release": platform.release(),
            "Version": platform.version(),
            "Machine": platform.machine()
        }
        return os_info
    except Exception as e:
        return {"Error": str(e)}

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

def display_package_table(packages, title):
    """通用包信息显示组件"""
    if "Error" in packages:
        st.error(f"{title}获取失败: {packages['Error']}")
        return

    st.success(f"检测到 {len(packages)} 个{title}")
    
    # 创建搜索框
    search_term = st.text_input(f"搜索{title}：", key=f"search_{title}")
    
    # 过滤结果
    filtered_pkgs = {
        k: v for k, v in packages.items() 
        if search_term.lower() in k.lower()
    }
    
    # 分页控制
    PAGE_SIZE = 20
    if filtered_pkgs:
        page = st.number_input(
            "页码",
            min_value=1,
            max_value=(len(filtered_pkgs)-1)//PAGE_SIZE + 1,
            value=1,
            key=f"page_{title}"
        )
        start = (page-1)*PAGE_SIZE
        end = start + PAGE_SIZE
        
        # 显示表格
        st.table(
            list(filtered_pkgs.items())[start:end]
        )
    else:
        st.warning("没有找到匹配的软件包")

# 页面配置
st.set_page_config(
    page_title="服务器软件信息",
    page_icon="🖥️",
    layout="centered"
)

# 主界面
st.title("🖥️ 服务器环境信息")

# 系统信息部分
st.markdown("### 系统基本信息")
with st.expander("查看系统信息", expanded=True):
    sys_info = get_system_info()
    st.json(sys_info)

# 系统软件部分
st.markdown("### 系统级软件包")
if st.button("刷新系统软件列表"):
    with st.spinner("正在扫描系统软件..."):
        system_packages = get_system_packages()
        display_package_table(system_packages, "系统软件")

# Python包部分
st.markdown("### Python软件包")
if st.button("刷新Python包列表"):
    with st.spinner("正在扫描Python包..."):
        python_packages = get_python_packages()
        display_package_table(python_packages, "Python软件包")

# 注意事项
st.markdown("""
---
**注意**：  
1. 系统软件检测支持：Linux (dpkg)、macOS (Homebrew)、Windows
2. 实际显示内容取决于系统环境和权限设置
3. 信息仅在应用运行时有效
""")