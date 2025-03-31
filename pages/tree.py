import streamlit as st
from Bio import Phylo
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import os

st.title('智能进化树可视化工具')

DEFAULT_TREE = "3_species.pep.muscle.treefile"

def load_default_tree():
    """加载本地默认树文件"""
    if os.path.exists(DEFAULT_TREE):
        try:
            with open(DEFAULT_TREE, 'r') as f:
                return Phylo.read(f, 'newick')
        except Exception as e:
            st.error(f"默认文件加载失败: {str(e)}")
            return None
    return None

def plot_circular_tree(tree):
    """核心绘图函数"""
    # 计算树结构参数
    max_depth = max(tree.depths().values())
    leaves = list(tree.get_terminals())
    n_leaves = len(leaves)
    
    # 分配节点坐标
    angles = np.linspace(0, 2 * np.pi, n_leaves, endpoint=False)
    for leaf, angle in zip(leaves, angles):
        leaf.angle = angle
        leaf.radius = max_depth - tree.depths()[leaf]
    
    # 计算非叶节点位置
    for clade in tree.get_nonterminals(order='postorder'):
        clade.angle = np.mean([c.angle for c in clade.clades])
        clade.radius = max_depth - tree.depths()[clade]
    
    # 创建绘图对象
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, polar=True)
    
    # 绘制分支
    for clade in tree.find_clades():
        if clade != tree.root:
            parent = tree.get_path(clade)[-2]
            ax.plot([parent.angle, clade.angle], 
                    [parent.radius, clade.radius], 
                    color='steelblue', lw=1.5)
    
    # 添加标签
    for leaf in leaves:
        ax.text(leaf.angle, leaf.radius, leaf.name,
                rotation=np.degrees(leaf.angle)-90,
                ha='center', va='center',
                fontsize=10, fontfamily='sans-serif')
    
    # 美化图形
    ax.set_xticks([])
    ax.set_yticks([])
    [spine.set_visible(False) for spine in ax.spines.values()]
    
    return fig

# 文件上传组件
uploaded_file = st.file_uploader("上传进化树文件（可选）", type=["treefile", "nwk"])

# 智能选择数据源
tree_data = None
if uploaded_file:
    try:
        tree_data = Phylo.read(uploaded_file, 'newick')
        st.success("上传文件解析成功！")
    except Exception as e:
        st.error(f"上传文件解析失败: {str(e)}")
        st.stop()
else:
    tree_data = load_default_tree()
    if tree_data:
        st.info(f"已自动加载本地默认文件: {DEFAULT_TREE}")
    else:
        st.warning("请上传文件或确保本地存在默认文件")
        st.stop()

# 执行绘图流程
with st.spinner('生成树图中...'):
    try:
        fig = plot_circular_tree(tree_data)
        
        # 生成SVG
        svg_buffer = BytesIO()
        fig.savefig(svg_buffer, format='svg', bbox_inches='tight')
        
        # 生成预览图
        png_buffer = BytesIO()
        fig.savefig(png_buffer, format='png', dpi=150)
        
        # 显示结果
        st.image(png_buffer)
        st.download_button(
            label="下载SVG矢量图",
            data=svg_buffer.getvalue(),
            file_name="phylogenetic_tree.svg",
            mime="image/svg+xml"
        )
        
    except Exception as e:
        st.error(f"绘图失败: {str(e)}")
    finally:
        plt.close('all')
