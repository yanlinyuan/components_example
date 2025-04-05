# 在Streamlit中嵌入Jupyter
from pyodide.http import open_url
from IPython.display import display

def show_jupyter():
    display(IFrame(src="http://172.26.0.246:8870/lab", width="100%", height=800))

st.write("嵌入式Jupyter环境：")
show_jupyter()
