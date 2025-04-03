import streamlit as st
import subprocess
import platform
import sys

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

# 页面配置
st.set_page_config(
    page_title="服务器软件信息",
    page_icon="🖥️",
    layout="centered"
)

# 主界面
st.title("🖥️ 服务器环境信息")
st.markdown("""
### 系统基本信息
本应用运行环境的系统参数如下：
""")

# 显示系统信息
with st.expander("查看系统信息", expanded=True):
    sys_info = get_system_info()
    st.json(sys_info)

# 显示Python包信息
st.markdown("""
### Python软件包
已安装的Python包及其版本信息：
""")

if st.button("刷新软件列表"):
    with st.spinner("正在扫描已安装软件..."):
        packages = get_python_packages()
        
        if "Error" in packages:
            st.error(packages["Error"])
        else:
            st.success(f"检测到 {len(packages)} 个已安装包")
            
            # 创建可搜索的表格
            search_term = st.text_input("搜索软件包：")
            
            # 过滤显示结果
            filtered_pkgs = {
                k: v for k, v in packages.items() 
                if search_term.lower() in k.lower()
            }
            
            # 分页显示
            PAGE_SIZE = 20
            page = st.number_input("页码", 
                                 min_value=1, 
                                 max_value=len(filtered_pkgs)//PAGE_SIZE+1, 
                                 value=1)
            
            start = (page-1)*PAGE_SIZE
            end = start + PAGE_SIZE
            
            st.table(
                list(filtered_pkgs.items())[start:end]
            )

# 注意事项
st.markdown("""
---
**注意**：  
由于Streamlit Community Cloud的安全限制：
1. 仅能显示Python环境信息
2. 无法获取系统级软件（如apt安装的软件）
3. 信息仅在应用运行时有效
""")