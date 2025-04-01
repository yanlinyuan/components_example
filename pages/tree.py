import streamlit as st
from Bio import Phylo
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import os

st.title('智能进化树可视化工具')

DEFAULT_TREE = "3_species.pep.muscle.treefile"

def load_tree(source):
    """通用树加载函数"""
    try:
        if isinstance(source, str):  # 本地文件路径
            with open(source, 'r') as f:
                return Phylo.read(f, 'newick')
        else:  # 上传文件对象
            return Phylo.read(source, 'newick')
    except Exception as e:
        st.error(f"文件加载失败: {str(e)}")
        return None

def plot_tree(tree):
    """通用绘图函数"""
    try:
        # 读取进化树文件
        tree = Phylo.read(uploaded_file, 'newick')
        
        # 计算树的深度和叶子节点
        max_depth = max(tree.depths().values())
        leaves = list(tree.get_terminals())
        n_leaves = len(leaves)
        
        # 为叶子节点分配角度
        angles = np.linspace(0, 2 * np.pi, n_leaves, endpoint=False)
        for leaf, angle in zip(leaves, angles):
            leaf.angle = angle
            leaf.radius = max_depth - tree.depths()[leaf]
        
        # 后序遍历计算非叶子节点的位置
        for clade in tree.get_nonterminals(order='postorder'):
            children = clade.clades
            clade.angle = np.mean([child.angle for child in children])
            clade.radius = max_depth - tree.depths()[clade]
        
        # 创建极坐标图
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)
        
        # 绘制连接线
        for clade in tree.find_clades():
            if clade == tree.root:
                continue
            path = tree.get_path(clade)
            parent = path[-2] if len(path) >= 2 else tree.root
            r1, theta1 = parent.radius, parent.angle
            r2, theta2 = clade.radius, clade.angle
            ax.plot([theta1, theta2], [r1, r2], color='black', lw=1)
        
        # 添加叶子标签
        for leaf in leaves:
            x = leaf.angle
            y = leaf.radius
            ax.text(
                x, y, leaf.name,
                ha='center', va='center',
                rotation=np.degrees(x) - 90,
                fontsize=8
            )
        
        # 美化图形
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['polar'].set_visible(False)
        
        # 创建SVG缓冲区
        svg_buffer = BytesIO()
        plt.savefig(svg_buffer, format='svg', bbox_inches='tight')
        plt.close()
        
        # 显示预览图（PNG格式）
        png_buffer = BytesIO()
        plt.savefig(png_buffer, format='png', bbox_inches='tight', dpi=300)
        plt.close()
        st.image(png_buffer)
        
        # 添加SVG下载按钮
        st.download_button(
            label="下载SVG矢量图",
            data=svg_buffer.getvalue(),
            file_name="circular_tree.svg",
            mime="image/svg+xml"
        )
    
    except Exception as e:
        st.error(f"处理过程中发生错误: {e}")

# 文件上传组件
uploaded_file = st.file_uploader("上传进化树文件（可选）", type=["treefile", "nwk"])

# 自动检测文件来源
if uploaded_file:
    st.success("检测到上传文件，正在处理...")
    tree_source = uploaded_file
elif os.path.exists(DEFAULT_TREE):
    st.info(f"自动加载默认文件: {DEFAULT_TREE}")
    tree_source = DEFAULT_TREE
else:
    st.warning("请上传文件或确保默认文件存在")
    st.stop()

# 执行绘图流程
if tree := load_tree(tree_source):
    try:
        # 执行绘图逻辑（保持之前的绘图代码）
        # 创建双缓冲区（SVG+PNG）
        
        # 显示预览图
        st.image(png_buffer)
        
        # 添加下载按钮
        st.download_button(...)
        
    except Exception as e:
        st.error(f"绘图错误: {str(e)}")