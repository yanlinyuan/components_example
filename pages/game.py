import streamlit as st
import random

# 应用配置
st.set_page_config(
    page_title="数字猜猜乐",
    page_icon="🎮",
    layout="centered"
)

# 初始化游戏状态
def init_game():
    st.session_state.answer = random.randint(1, 100)
    st.session_state.attempts = 0
    st.session_state.guesses = []
    st.session_state.game_over = False

if 'answer' not in st.session_state:
    init_game()

# 页面布局
st.title("🎮 数字猜猜乐")
st.markdown("""
### 游戏规则
1. 我已经想好了1-100之间的一个数字
2. 在下方输入你的猜测
3. 我会告诉你猜大了还是小了
4. 用最少的次数猜中吧！
""")

# 游戏控制面板
with st.container(border=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        guess = st.number_input("输入你的猜测 (1-100)：", 
                              min_value=1, 
                              max_value=100,
                              key="input_guess")
    with col2:
        st.write("")
        st.write("")
        if st.button("提交", use_container_width=True):
            if guess == st.session_state.answer:
                st.session_state.game_over = True
            st.session_state.attempts += 1
            st.session_state.guesses.append(guess)
    
    if st.button("新游戏", use_container_width=True):
        init_game()
        st.rerun()

# 显示游戏进度
with st.container(border=True):
    if st.session_state.game_over:
        st.balloons()
        st.success(f"🎉 恭喜！你在 {st.session_state.attempts} 次尝试后猜中了！")
        st.markdown(f"**正确答案：** `{st.session_state.answer}`")
    else:
        st.markdown(f"**已尝试次数：** {st.session_state.attempts}")

    if st.session_state.guesses:
        st.markdown("### 猜测历史")
        for g in st.session_state.guesses:
            if g < st.session_state.answer:
                st.markdown(f"🔼 {g} （太小了）")
            elif g > st.session_state.answer:
                st.markdown(f"🔽 {g} （太大了）")

# 侧边栏彩蛋
with st.sidebar:
    st.markdown("## 游戏统计")
    st.markdown(f"**历史最佳成绩：**\n\n`{min(st.session_state.guesses + [999], key=lambda x: abs(x - st.session_state.answer))}`")
    st.divider()
    st.markdown("**开发信息**")
    st.code("版本：1.0.0\n开发者：AI助手")