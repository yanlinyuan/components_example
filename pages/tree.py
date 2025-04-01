import streamlit as st
from Bio import Phylo
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import os

# 应用标题设置
st.set_page_config(page_title="进化树可视化工具", layout="centered")
st.title("🌿 进化树可视化分析系统")

# 默认文件配置
DEFAULT_TREE = "3_species.pep.muscle.treefile"

def load_tree_data(uploaded_file):
    """加载并验证树形数据"""
    try:
        if uploaded_file is not None:
            return Phylo.read(uploaded_file, 'newick'), "uploaded"
        elif os.path.exists(DEFAULT_TREE):
            with open(DEFAULT_TREE, 'r') as f:
                return Phylo.read(f, 'newick'), "default"
        return None, "missing"
    except Exception as e:
        st.error(f"文件解析错误: {str(e)}")
        return None, "error"

def plot_circular_tree(tree):
    """绘制进化树圈图"""
    # 计算树形结构参数
    max_depth = max(tree.depths().values())
    leaves = list(tree.get_terminals())
    n_leaves = len(leaves)
    
    # 创建极坐标画布
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, polar=True)
    
    # 分配叶子节点角度
    angles = np.linspace(0, 2 * np.pi, n_leaves, endpoint=False)
    for leaf, angle in zip(leaves, angles):
        leaf.angle = angle
        leaf.radius = max_depth - tree.depths()[leaf]
    
    # 计算内部节点位置
    for clade in tree.get_nonterminals(order='postorder'):
        clade.angle = np.mean([c.angle for c in clade.clades])
        clade.radius = max_depth - tree.depths()[clade]
    
    # 绘制分支连线
    for clade in tree.find_clades():
        if clade != tree.root:
            parent = tree.get_path(clade)[-2]
            ax.plot([parent.angle, clade.angle],
                    [parent.radius, clade.radius],
                    color='#2E86C1',
                    lw=1.5,
                    solid_capstyle='round')
    
    # 添加叶子标签
    for leaf in leaves:
        ax.text(leaf.angle, leaf.radius, leaf.name,
                rotation=np.degrees(leaf.angle)-90,
                ha='center', va='center',
                fontsize=10,
                fontfamily='Arial')
    
    # 美化图形
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)
    
    return fig

# 文件上传组件
uploaded_file = st.file_uploader(
    "📤 上传Newick格式进化树文件 (.treefile/.nwk)",
    type=["treefile", "nwk"],
    help="可上传自定义文件或使用默认样本"
)

# 加载数据
tree_data, status = load_tree_data(uploaded_file)

# 状态提示
if status == "default":
    st.info(f"ℹ️ 已自动加载默认文件: {DEFAULT_TREE}")
elif status == "missing":
    st.warning("⚠️ 未找到默认文件，请上传分析文件")
    st.stop()
elif status == "error":
    st.stop()

# 生成可视化
if tree_data:
    with st.spinner('🖌️ 正在生成进化树可视化...'):
        try:
            fig = plot_circular_tree(tree_data)
            
            # 生成SVG缓冲区
            svg_buffer = BytesIO()
            fig.savefig(svg_buffer, format="svg", bbox_inches="tight")
            plt.close(fig)
            
            # 显示预览
            st.image(svg_buffer.getvalue(), use_column_width=True)
            
            # 添加下载按钮
            st.download_button(
                label="💾 下载SVG矢量图",
                data=svg_buffer.getvalue(),
                file_name="phylogenetic_tree.svg",
                mime="image/svg+xml",
                help="矢量格式支持无损缩放和后期编辑"
            )
            
        except Exception as e:
            st.error(f"可视化生成失败: {str(e)}")