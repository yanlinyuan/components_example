#02_hmmsearch.py
import streamlit as st
import os
import time
import shutil
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from Bio import SeqIO
from Bio.Align.Applications import ClustalwCommandline
import pyhmmer
from pyhmmer.plan7 import HMMFile, HMMPressed
from pyhmmer.easel import SequenceFile, DigitalSequenceBlock

class Args:
    def __init__(self, domain, protein, species, gene, hmm_exp1, hmm_exp2):
        self.domain = Path(domain)
        self.protein = Path(protein)
        self.species = species
        self.gene = gene
        self.hmm_exp1 = float(hmm_exp1)
        self.hmm_exp2 = float(hmm_exp2)

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
    missing = [f for f in file_list if not f.exists()]
    if missing:
        error_msg = f"{step_name} 缺失文件：{missing}"
        logging.error(error_msg)
        st.error(error_msg)
        raise FileNotFoundError(error_msg)
    st.write(f"{step_name} 文件检查通过")
    logging.info(f"{step_name} 文件检查通过")

def run_hmmsearch(hmm_path, fasta_path, output_prefix, evalue):
    """执行HMM搜索的纯Python实现"""
    with pyhmmer.plan7.HMMFile(hmm_path) as hmm_file:
        hmm = hmm_file.read()
    
    sequences = SequenceFile(fasta_path).read_block()
    press = HMMPressed()
    results = []
    
    for seq in DigitalSequenceBlock(sequences):
        hits = pyhmmer.hmmsearch(hmm, seq, E=evalue)
        for hit in hits:
            results.append({
                "target": hit.name.decode(),
                "evalue": hit.evalue
            })
    
    df = pd.DataFrame(results)
    df.to_csv(f"{output_prefix}.domtblout", sep="\t", index=False)
    return df

def filter_results(input_file, output_file, evalue):
    """过滤结果"""
    df = pd.read_csv(input_file, sep="\t")
    filtered = df[df["evalue"] < evalue]
    filtered["target"].to_csv(output_file, index=False, header=False)
    return filtered

def extract_sequences(fasta_path, id_list, output_path):
    """提取序列"""
    ids = set(pd.read_csv(id_list, header=None)[0])
    records = []
    for record in SeqIO.parse(fasta_path, "fasta"):
        if record.id in ids:
            records.append(record)
    SeqIO.write(records, output_path, "fasta")

def build_hmm(alignment_path, hmm_path):
    """构建HMM模型"""
    with SequenceFile(alignment_path, digital=True) as seqs:
        alphabet = seqs.alphabet
        msa = seqs.read_block()
    
    builder = pyhmmer.plan7.Builder(alphabet)
    background = pyhmmer.plan7.Background(alphabet)
    hmm, _ = builder.build_msa(msa, background)
    with open(hmm_path, "wb") as f:
        hmm.write(f)

def main_pipeline(args):
    """主分析流程"""
    work_dir = Path("2.hmmsearch")
    work_dir.mkdir(exist_ok=True)
    
    # 步骤1: 初始HMM搜索
    log_step_start("初始HMM搜索筛选")
    initial_domtbl = work_dir / f"{args.species}.{args.gene}.domtblout"
    run_hmmsearch(args.domain, args.protein, initial_domtbl.stem, args.hmm_exp1)
    log_step_end("初始HMM搜索筛选")

    # 步骤2: 第一次筛选
    log_step_start("第一次筛选过滤")
    first_filter = work_dir / f"{args.species}.{args.gene}.filter.1st"
    filter_results(initial_domtbl, first_filter, args.hmm_exp1)
    log_step_end("第一次筛选过滤")

    # 步骤3: 提取候选序列
    log_step_start("提取候选蛋白序列")
    first_fasta = work_dir / "1st_id.fa"
    extract_sequences(args.protein, first_filter, first_fasta)
    log_step_end("提取候选蛋白序列")

    # 步骤4: 多序列比对
    log_step_start("多序列比对")
    alignment = work_dir / "1st_id.aln"
    cline = ClustalwCommandline("clustalw2", infile=str(first_fasta), outfile=str(alignment))
    cline()
    log_step_end("多序列比对")

    # 步骤5: 构建新HMM
    log_step_start("构建新HMM模型")
    new_hmm = work_dir / f"new_{args.gene}.hmm"
    build_hmm(alignment, new_hmm)
    log_step_end("构建新HMM模型")

    # 步骤6: 二次HMM搜索
    log_step_start("二次HMM搜索筛选")
    second_domtbl = work_dir / f"{args.species}.new_{args.gene}.domtblout"
    run_hmmsearch(new_hmm, args.protein, second_domtbl.stem, args.hmm_exp2)
    log_step_end("二次HMM搜索筛选")

    # 步骤7: 第二次筛选
    log_step_start("第二次筛选过滤")
    second_filter = work_dir / f"{args.species}.new_{args.gene}.filter.2st"
    filter_results(second_domtbl, second_filter, args.hmm_exp2)
    log_step_end("第二次筛选过滤")

    # 步骤8: 提取最终序列
    log_step_start("提取最终蛋白序列")
    final_fasta = work_dir / "2st_id.fa"
    extract_sequences(args.protein, second_filter, final_fasta)
    log_step_end("提取最终蛋白序列")

    return final_fasta

# Streamlit界面
st.title("HMM基因家族分析平台（纯Python版）")

def handle_upload(uploaded_file, default_path):
    """处理文件上传"""
    if uploaded_file is not None:
        save_dir = Path("1.database")
        save_dir.mkdir(exist_ok=True)
        target_path = save_dir / uploaded_file.name
        with target_path.open("wb") as f:
            f.write(uploaded_file.getbuffer())
        return target_path
    return Path(default_path)

# 文件上传组件
uploaded_domain = st.file_uploader("上传HMM模型文件", type=["hmm"], 
                                 help="默认使用 ./1.database/PF08392.hmm")
domain_path = handle_upload(uploaded_domain, "./1.database/PF08392.hmm")

uploaded_protein = st.file_uploader("上传蛋白序列文件", type=["fa", "fasta"], 
                                  help="默认使用 ./1.database/Brassica_napus.ZS11.v0.protein.fa")
protein_path = handle_upload(uploaded_protein, "./1.database/Brassica_napus.ZS11.v0.protein.fa")

# 参数输入
col1, col2 = st.columns(2)
with col1:
    species = st.text_input("物种标识符", value="BN").upper()
with col2:
    gene = st.text_input("基因家族名称", value="KCS").upper()

hmm_exp1 = st.number_input("首次筛选E值", value=1e-5, format="%.1e")
hmm_exp2 = st.number_input("二次筛选E值", value=1e-5, format="%.1e")

if st.button("开始分析"):
    args = Args(
        domain=domain_path,
        protein=protein_path,
        species=species,
        gene=gene,
        hmm_exp1=hmm_exp1,
        hmm_exp2=hmm_exp2
    )
    
    try:
        with st.spinner("分析进行中..."):
            result_file = main_pipeline(args)
            
            # 显示结果
            with open(result_file, "r") as f:
                st.subheader("结果文件前5行内容：")
                st.code(''.join(f.readlines()[:5]))
            
            with open(result_file, "rb") as f:
                st.download_button("下载结果文件", f, file_name="2st_id.fa")
        
        st.success("分析完成！")
    
    except Exception as e:
        st.error(f"分析失败：{str(e)}")
        st.markdown("""
        **常见问题解决方案：**
        1. 确保上传文件格式正确
        2. 检查输入参数范围
        3. 验证输入文件完整性
        """)