#02_hmmsearch.py
import streamlit as st
import os
import subprocess
import time
import shutil
import logging
from datetime import datetime
from pathlib import Path  # 新增Pathlib处理路径

class Args:
    def __init__(self, domain, protein, species, gene, hmm_exp1, hmm_exp2):
        self.domain = str(domain).replace("\\", "/")  # 统一使用Linux路径格式
        self.protein = str(protein).replace("\\", "/")
        self.species = species
        self.gene = gene
        self.hmm_exp1 = hmm_exp1
        self.hmm_exp2 = hmm_exp2

def log_step_start(step_name):
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"开始步骤：{step_name} [{start_time}]"
    st.write(message)
    logging.info(message)

def log_step_end(step_name, success=True):
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "成功" if success else "失败"
    message = f"结束步骤：{step_name} [{status}] [{end_time}]"
    st.write(message)
    logging.info(message)

def check_files(file_list, step_name):
    missing = [f for f in file_list if not Path(f).exists()]
    if missing:
        error_msg = f"{step_name} 缺失文件：{missing}"
        logging.error(error_msg)
        st.error(error_msg)
        raise FileNotFoundError(error_msg)
    st.write(f"{step_name} 文件检查通过")
    logging.info(f"{step_name} 文件检查通过")

def run_command(cmd_info, work_dir):
    step_name = cmd_info["step"]
    command = cmd_info["cmd"]
    inputs = cmd_info.get("inputs", [])
    outputs = cmd_info["outputs"]

    log_step_start(step_name)
    
    if inputs:
        check_files(inputs, f"{step_name} 输入文件")

    try:
        # 显示完整路径信息
        st.write(f"当前工作目录：{Path(work_dir).resolve()}")
        st.write(f"输入文件路径验证：{[Path(f).resolve() for f in inputs]}")
        
        st.write(f"执行命令：{command}")
        start_time = time.time()
        
        # 使用绝对路径执行命令
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 显示命令输出
        st.write("命令输出：")
        st.code(process.stdout)
        if process.stderr:
            st.write("命令错误输出：")
            st.code(process.stderr)
        
        cost_time = round(time.time() - start_time, 2)
        st.write(f"命令执行耗时：{cost_time}秒")
        logging.info(f"命令执行耗时：{cost_time}秒")
    except subprocess.CalledProcessError as e:
        log_step_end(step_name, False)
        st.error(f"命令执行失败详情：\n{e.stderr}")
        raise

    check_files(outputs, f"{step_name} 输出文件")
    
    time.sleep(1)
    log_step_end(step_name)

def main_streamlit(args):
    logging.basicConfig(filename='run.log', level=logging.INFO,
                      format='%(asctime)s - %(message)s', encoding='utf-8')
    
    base_dir = Path.cwd()
    work_dir = base_dir / "2.hmmsearch"
    database_dir = base_dir / "1.database"

    try:
        # 初始化工作目录
        st.write("初始化工作环境...")
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(exist_ok=True)

        # 处理输入文件
        st.write("处理输入文件...")
        required_files = {
            "HMM模型文件": (Path(args.domain), work_dir / Path(args.domain).name),
            "蛋白序列文件": (Path(args.protein), work_dir / Path(args.protein).name)
        }

        for file_type, (src, dest) in required_files.items():
            if not src.exists():
                raise FileNotFoundError(f"{file_type} {src} 不存在！")
            shutil.copy(src, dest)
            st.write(f"已拷贝 {file_type}: {dest.resolve()}")  # 显示完整路径

        # 定义中间文件路径（使用绝对路径）
        intermediate_files = {
            "initial_domtbl": work_dir / f"{args.species}.{args.gene}.domtblout",
            "initial_hmmout": work_dir / f"{args.species}.{args.gene}.hmmout",
            "first_filter": work_dir / f"{args.species}.{args.gene}.filter.1st",
            "new_hmm": work_dir / f"new_{args.gene}.hmm",
            "second_domtbl": work_dir / f"{args.species}.new_{args.gene}.domtblout",
            "second_hmmout": work_dir / f"{args.species}.new_{args.gene}.hmmout",
            "second_filter": work_dir / f"{args.species}.new_{args.gene}.filter.2st"
        }

        # 构建命令（使用绝对路径）
        commands = [
            {
                "step": "初始HMM搜索筛选",
                "cmd": f"hmmsearch --cut_tc --domtblout {intermediate_files['initial_domtbl']} "
                       f"-o {intermediate_files['initial_hmmout']} "
                       f'"{work_dir / Path(args.domain).name}" '
                       f'"{work_dir / Path(args.protein).name}"',
                "inputs": [work_dir / Path(args.domain).name, work_dir / Path(args.protein).name],
                "outputs": [intermediate_files['initial_domtbl'], intermediate_files['initial_hmmout']]
            },
            # ...其他命令配置
        ]

        # 执行所有命令
        for cmd_info in commands:
            run_command(cmd_info, work_dir)

        # 显示结果
        result_file = work_dir / "2st_id.fa"
        if result_file.exists():
            with open(result_file, "r") as f:
                st.subheader("结果文件前5行内容：")
                st.code(''.join(f.readlines()[:5]))
            
            with open(result_file, "rb") as f:
                st.download_button("下载结果文件", f, file_name="2st_id.fa")

    except Exception as e:
        st.error(f"错误详情：\n{str(e)}\n"
                f"当前工作目录：{Path.cwd()}\n"
                f"文件存在性验证：\n"
                f"- HMM文件：{Path(args.domain).exists()}\n"
                f"- 蛋白文件：{Path(args.protein).exists()}")
        raise

# Streamlit界面配置
st.title("HMM基因家族分析平台（Windows优化版）")

# 文件上传处理
def handle_upload(uploaded_file, default_path):
    if uploaded_file is not None:
        save_dir = Path("1.database")
        save_dir.mkdir(exist_ok=True)
        target_path = save_dir / uploaded_file.name
        with target_path.open("wb") as f:
            f.write(uploaded_file.getbuffer())
        return target_path
    return Path(default_path)

uploaded_domain = st.file_uploader("上传HMM模型文件", type=["hmm"], 
                                 help="默认使用 ./1.database/PF08392.hmm")
domain_path = handle_upload(uploaded_domain, "./1.database/PF08392.hmm")

uploaded_protein = st.file_uploader("上传蛋白序列文件", type=["fa", "fasta"], 
                                  help="默认使用 ./1.database/Brassica_napus.ZS11.v0.protein.fa")
protein_path = handle_upload(uploaded_protein, "./1.database/Brassica_napus.ZS11.v0.protein.fa")

# 参数输入组件
species = st.text_input("物种标识符", value="BN").upper()
gene = st.text_input("基因家族名称", value="KCS").upper()

# 数值输入处理
hmm_exp1 = st.number_input("首次筛选E值", value=0.00001, format="%.5f")
hmm_exp2 = st.number_input("二次筛选E值", value=0.00001, format="%.5f")

if st.button("开始分析"):
    with st.spinner("分析进行中..."):
        args = Args(
            domain=domain_path,
            protein=protein_path,
            species=species,
            gene=gene,
            hmm_exp1=str(hmm_exp1),
            hmm_exp2=str(hmm_exp2)
        )
        
        try:
            main_streamlit(args)
            st.success("分析成功完成！")
        except Exception as e:
            st.error(f"分析失败，请检查：\n1. 文件路径是否包含特殊字符\n2. 必要组件是否安装\n3. 日志信息：{str(e)}")
            st.write("常见问题解决方案：")
            st.markdown("""
            1. **路径问题**：确保文件路径不包含中文或特殊字符
            2. **文件权限**：以管理员身份运行命令行
            3. **依赖安装**：确认已安装：
               - HMMER (hmmsearch)
               - seqkit
               - clustalw
            4. **日志查看**：检查当前目录下的run.log文件
            """)