#02_hmmsearch.py
import subprocess
import time
import sys
import os
import argparse
import shutil
import logging
from datetime import datetime

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="HMM搜索脚本",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--domain", default="PF08392", help="目标蛋白Pfam结构域编号")
    parser.add_argument("--fa", default="Brassica_napus.ZS11.v0.protein", help="目标物种全基因组蛋白序列")
    parser.add_argument("--species", default="BN", help="目标物种标识符(大写)")
    parser.add_argument("--gene", default="KCS", help="目标基因家族名称")
    parser.add_argument("--hmm_exp1", default="1e-5", help="首次HMM筛选E值")
    parser.add_argument("--hmm_exp2", default="1e-5", help="二次HMM筛选E值")
    return parser.parse_args()

def log_step_start(step_name):
    """记录步骤开始"""
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"开始步骤：{step_name} [{start_time}]"
    print(message)
    logging.info(message)

def log_step_end(step_name, success=True):
    """记录步骤结束"""
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "成功" if success else "失败"
    message = f"结束步骤：{step_name} [{status}] [{end_time}]"
    print(message)
    logging.info(message)

def check_files(file_list, step_name):
    """文件存在性检查"""
    missing = [f for f in file_list if not os.path.exists(f)]
    if missing:
        error_msg = f"{step_name} 缺失文件：{missing}"
        logging.error(error_msg)
        print(f"错误：{error_msg}")
        sys.exit(1)
    print(f"{step_name} 文件检查通过")
    logging.info(f"{step_name} 文件检查通过")

def run_command(cmd_info, work_dir):
    """执行命令并处理相关操作"""
    step_name = cmd_info["step"]
    command = cmd_info["cmd"]
    inputs = cmd_info.get("inputs", [])
    outputs = cmd_info["outputs"]

    log_step_start(step_name)
    
    # 输入文件检查
    if inputs:
        check_files(inputs, f"{step_name} 输入文件")

    # 执行命令
    try:
        print(f"执行命令：{command}")
        start_time = time.time()
        subprocess.run(command, shell=True, check=True, executable='/bin/bash', cwd=work_dir)
        cost_time = round(time.time() - start_time, 2)
        print(f"命令执行耗时：{cost_time}秒")
        logging.info(f"命令执行耗时：{cost_time}秒")
    except subprocess.CalledProcessError as e:
        log_step_end(step_name, False)
        print(f"命令执行失败：{str(e)}")
        sys.exit(1)

    # 输出文件检查
    check_files(outputs, f"{step_name} 输出文件")
    
    # 强制延时
    time.sleep(3)
    log_step_end(step_name)

def main():
    # 初始化日志配置
    logging.basicConfig(filename='run.log', level=logging.INFO,
                      format='%(asctime)s - %(message)s', encoding='utf-8')

    args = parse_arguments()
    base_dir = os.path.expanduser("~/jupyterLab/genefamily/Genefamily_Analysis")
    work_dir = os.path.join(base_dir, "2.hmmsearch")
    database_dir = os.path.join(base_dir, "1.database")

    # 初始化工作目录
    print("\n初始化工作环境...")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)
    os.chdir(work_dir)

    # 检查并拷贝输入文件
    print("\n检查输入文件...")
    required_files = {
        "HMM模型文件": f"{args.domain}.hmm",
        "蛋白序列文件": f"{args.fa}.fa"
    }
    for file_type, filename in required_files.items():
        src = os.path.join(database_dir, filename)
        if not os.path.exists(src):
            print(f"错误：{file_type} {src} 不存在！")
            sys.exit(1)
        shutil.copy(src, work_dir)
        print(f"已拷贝 {file_type}: {filename}")

    # 定义执行流程
    intermediate_files = {
        "initial_domtbl": f"{args.species}.{args.gene}.domtblout",
        "initial_hmmout": f"{args.species}.{args.gene}.hmmout",
        "first_filter": f"{args.species}.{args.gene}.filter.1st",
        "new_hmm": f"new_{args.gene}.hmm",
        "second_domtbl": f"{args.species}.new_{args.gene}.domtblout",
        "second_hmmout": f"{args.species}.new_{args.gene}.hmmout",
        "second_filter": f"{args.species}.new_{args.gene}.filter.2st"
    }

    commands = [
        {
            "step": "初始HMM搜索筛选",
            "cmd": f"conda run -n genefamily hmmsearch --cut_tc --domtblout {intermediate_files['initial_domtbl']} -o {intermediate_files['initial_hmmout']} {args.domain}.hmm {args.fa}.fa",
            "inputs": [f"{args.domain}.hmm", f"{args.fa}.fa"],
            "outputs": [intermediate_files['initial_domtbl'], intermediate_files['initial_hmmout']]
        },
        {
            "step": "第一次筛选过滤",
            "cmd": f"""awk '$7<{args.hmm_exp1} && $1 !~ /^#/ {{print $0}}' {intermediate_files['initial_domtbl']} | awk '{{print $1}}' | sort -u > {intermediate_files['first_filter']}""",
            "inputs": [intermediate_files['initial_domtbl']],
            "outputs": [intermediate_files['first_filter']]
        },
        {
            "step": "提取候选蛋白序列",
            "cmd": f"conda run -n genefamily seqkit grep -r -f {intermediate_files['first_filter']} {args.fa}.fa -o 1st_id.fa",
            "inputs": [f"{args.fa}.fa", intermediate_files['first_filter']],
            "outputs": ["1st_id.fa"]
        },
        {
            "step": "多序列比对",
            "cmd": f"conda run -n genefamily clustalw -infile=1st_id.fa -output=clustal -type=PROTEIN -outfile=1st_id.aln",
            "inputs": ["1st_id.fa"],
            "outputs": ["1st_id.aln"]
        },
        {
            "step": "构建新HMM模型",
            "cmd": f"conda run -n genefamily hmmbuild {intermediate_files['new_hmm']} 1st_id.aln",
            "inputs": ["1st_id.aln"],
            "outputs": [intermediate_files['new_hmm']]
        },
        {
            "step": "二次HMM搜索筛选",
            "cmd": f"conda run -n genefamily hmmsearch --domtblout {intermediate_files['second_domtbl']} -o {intermediate_files['second_hmmout']} {intermediate_files['new_hmm']} {args.fa}.fa",
            "inputs": [intermediate_files['new_hmm'], f"{args.fa}.fa"],
            "outputs": [intermediate_files['second_domtbl'], intermediate_files['second_hmmout']]
        },
        {
            "step": "第二次筛选过滤",
            "cmd": f"""awk '$7<{args.hmm_exp2} && $1 !~ /^#/ {{print $0}}' {intermediate_files['second_domtbl']} | awk '{{print $1}}' | sort -u > {intermediate_files['second_filter']}""",
            "inputs": [intermediate_files['second_domtbl']],
            "outputs": [intermediate_files['second_filter']]
        },
        {
            "step": "提取最终蛋白序列",
            "cmd": f"conda run -n genefamily seqkit grep -r -f {intermediate_files['second_filter']} {args.fa}.fa -o 2st_id.fa",
            "inputs": [f"{args.fa}.fa", intermediate_files['second_filter']],
            "outputs": ["2st_id.fa"]
        }
    ]

    # 执行所有命令
    for cmd_info in commands:
        run_command(cmd_info, work_dir)

    # 返回上级目录
    os.chdir("..")
    print("\n脚本执行完成，已返回上级目录")

if __name__ == "__main__":
    main()