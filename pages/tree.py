import streamlit as st
from Bio import Phylo
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import os

# 配置页面
st.set_page_config(page_title="进化树分析仪", layout="wide")
st.title('🌳 交互式进化树可视化分析系统')

# 常量定义
DEFAULT_TREE = "./3_species.pep.muscle.treefile"

def initialize_session():
    """初始化会话状态"""
    if 'analyzed' not in st.session_state:
        st.session_state.analyzed = False

def load_tree_data():
    """加载树形数据源"""
    uploaded_file = st.file_uploader("📤 上传进化树文件（支持.newick/.nwk格式）", 
                                   type=["treefile", "nwk"],
                                   help="点击此处上传自定义文件或使用下方默认样本")
    
    if uploaded_file:
        try:
            return Phylo.read(uploaded_file, 'newick'), "uploaded"
        except Exception as e:
            st.error(f"❌ 文件解析失败: {str(e)}")
            return None, "error"
    
    if os.path.exists(DEFAULT_TREE):
        try:
            with open(DEFAULT_TREE, 'r') as f:
                return Phylo.read(f, 'newick'), "default"
        except Exception as e:
            st.error(f"❌ 默认文件加载失败: {str(e)}")
            return None, "error"
    
    return None, "missing"

def render_control_panel():
    """渲染控制面板"""
    with st.sidebar:
        st.subheader("⚙️ 分析参数设置")
        dpi = st.slider("图像分辨率", 100, 600, 300, 
                       help="高分辨率适合出版，低分辨率适合快速预览")
        branch_width = st.slider("分支线宽", 0.5, 5.0, 1.5)
        font_size = st.slider("标签字号", 6, 20, 10)
        return {"dpi": dpi, "branch_width": branch_width, "font_size": font_size}

def generate_visualization(tree, params):
    """生成可视化结果"""
    with st.spinner('🔍 正在解析树形结构...'):
        max_depth = max(tree.depths().values())
        leaves = list(tree.get_terminals())
        n_leaves = len(leaves)
        
        # 节点坐标计算
        angles = np.linspace(0, 2 * np.pi, n_leaves, endpoint=False)
        for leaf, angle in zip(leaves, angles):
            leaf.angle = angle
            leaf.radius = max_depth - tree.depths()[leaf]

        for clade in tree.get_nonterminals(order='postorder'):
            clade.angle = np.mean([c.angle for c in clade.clades])
            clade.radius = max_depth - tree.depths()[clade]

    with st.spinner('🎨 正在生成可视化...'):
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, polar=True)
        
        # 绘制分支
        for clade in tree.find_clades():
            if clade != tree.root:
                parent = tree.get_path(clade)[-2]
                ax.plot([parent.angle, clade.angle],
                        [parent.radius, clade.radius],
                        color='#2c7bb6', 
                        lw=params['branch_width'])
        
        # 添加标签
        for leaf in leaves:
            ax.text(leaf.angle, leaf.radius, leaf.name,
                    rotation=np.degrees(leaf.angle)-90,
                    ha='center', va='center',
                    fontsize=params['font_size'],
                    fontfamily='Arial')
        
        # 图形美化
        ax.set_xticks([])
        ax.set_yticks([])
        [spine.set_visible(False) for spine in ax.spines.values()]

    return fig

# 初始化会话状态
initialize_session()

# 页面布局
col1, col2 = st.columns([3, 1])

with col1:
    # 数据加载区域
    tree_data, status = load_tree_data()
    
    # 显示数据源状态
    if status == "default":
        st.info(f"ℹ️ 检测到默认文件: {DEFAULT_TREE}，可上传文件覆盖")
    elif status == "missing":
        st.warning("⚠️ 未找到默认文件，请上传分析文件")

    # 运行按钮
    analyze_btn = st.button("🚀 开始分析", 
                           disabled=(tree_data is None),
                           help="点击开始分析流程" if tree_data else "请先提供数据文件")

# 参数设置面板
vis_params = render_control_panel()

# 主分析流程
if analyze_btn and tree_data:
    st.session_state.analyzed = True
    
    try:
        # 执行分析流程
        fig = generate_visualization(tree_data, vis_params)
        
        # 生成输出文件
        with st.spinner('💾 正在准备下载文件...'):
            # SVG缓冲区
            svg_buffer = BytesIO()
            fig.savefig(svg_buffer, format='svg', 
                        bbox_inches='tight', dpi=vis_params['dpi'])
            
            # PNG缓冲区
            png_buffer = BytesIO()
            fig.savefig(png_buffer, format='png',
                        dpi=vis_params['dpi'])
            
            # 释放绘图资源
            plt.close('all')

        # 结果显示区域
        st.success("✅ 分析完成！")
        st.image(png_buffer, use_column_width=True)
        
        # 下载按钮组
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 下载SVG矢量图",
                data=svg_buffer.getvalue(),
                file_name="phylogenetic_tree.svg",
                mime="image/svg+xml",
                help="矢量格式适合进一步编辑"
            )
        with col_d2:
            st.download_button(
                label="📥 下载PNG位图",
                data=png_buffer.getvalue(),
                file_name="phylogenetic_tree.png",
                mime="image/png",
                help="位图格式适合快速查看"
            )

    except Exception as e:
        st.error(f"❌ 分析过程出错: {str(e)}")
        st.session_state.analyzed = False
elif analyze_btn:
    st.warning("⚠️ 请先选择或上传数据文件")

# 显示历史分析状态
if st.session_state.analyzed:
    st.markdown("---")
    st.caption("💡 提示：调整左侧参数后重新点击分析按钮可更新结果")
