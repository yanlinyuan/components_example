import streamlit as st
from Bio import Phylo
import matplotlib.pyplot as plt
from io import BytesIO
import tempfile

st.title("进化树可视化工具")

# 文件上传组件
uploaded_file = st.file_uploader("请上传进化树文件", type=["treefile"])

def convert_to_newick(treefile_content):
    """将treefile转换为标准Newick格式"""
    try:
        # 尝试直接解析为Newick格式
        temp_tree = Phylo.read(BytesIO(treefile_content), "newick")
        return treefile_content  # 如果解析成功直接返回原内容
    except:
        # 转换处理流程
        decoded_content = treefile_content.decode()
        
        # 移除注释（示例处理）
        cleaned_content = decoded_content.split(';')[0] + ';'
        
        # 处理特殊字符（可根据需要扩展）
        cleaned_content = cleaned_content.replace(' ', '_')  # 空格替换为下划线
        
        return cleaned_content.encode()

if uploaded_file is not None:
    # 显示文件基本信息
    file_details = {
        "文件名": uploaded_file.name,
        "文件类型": "Newick格式进化树",
        "文件大小": f"{uploaded_file.size / 1024:.1f} KB"
    }
    st.json(file_details)
    
    # 添加运行按钮控制流程
    if st.button("🚀 开始分析", type="primary"):
        with st.spinner("正在解析进化树..."):
            try:
                # 读取并转换文件
                raw_content = uploaded_file.getvalue()
                newick_content = convert_to_newick(raw_content)
                
                # 使用临时文件进行解析
                with tempfile.NamedTemporaryFile() as tmp:
                    tmp.write(newick_content)
                    tmp.seek(0)
                    
                    # 解析Newick格式进化树
                    tree = Phylo.read(tmp.name, "newick")
                
                # 创建绘图区域
                fig = plt.figure(figsize=(20, len(tree.get_terminals()) * 0.5))
                ax = fig.add_subplot(111)
                
                # 配置绘图参数
                plt.rcParams.update({
                    'font.size': 8,
                    'font.family': 'sans-serif',
                    'axes.linewidth': 0.5
                })

                # 进度条更新
                st.spinner("正在生成可视化...")
                
                # 绘制进化树
                Phylo.draw(
                    tree,
                    axes=ax,
                    orientation="right",
                    branch_labels=None,
                    label_colors=lambda x: "black",
                    label_params={
                        'rotation': 0,
                        'va': 'center',
                        'ha': 'left',
                        'fontstyle': 'normal'
                    }
                )

                # 布局优化
                plt.subplots_adjust(left=0.2, right=0.8)
                ax.yaxis.set_ticks_position('none')
                ax.xaxis.set_tick_params(pad=5)

                # 生成SVG文件
                svg_buffer = BytesIO()
                plt.savefig(
                    svg_buffer,
                    format="svg",
                    dpi=300,
                    bbox_inches="tight",
                    pad_inches=0.2
                )
                svg_buffer.seek(0)

                # 显示结果
                st.success("分析完成！")
                st.pyplot(fig)
                
                # 添加下载组件
                st.download_button(
                    label="⬇️ 下载SVG矢量图",
                    data=svg_buffer,
                    file_name="phylogenetic_tree.svg",
                    mime="image/svg+xml",
                    help="点击下载高质量矢量图文件"
                )
                
                plt.close()
                
            except Exception as e:
                st.error(f"分析失败：{str(e)}")
                st.exception(e)