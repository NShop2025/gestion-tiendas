import streamlit as st

from app.services.config import cargar_config

cargar_config()

st.set_page_config(page_title="Gestión Tiendas", page_icon="🛍️", layout="wide")

# El login se valida adentro de cada página (requerir_login(), primera línea de cada una en
# pages/), no acá: así el gate corre dentro del contexto de st.navigation y no se duplica.
paginas = [
    st.Page("pages/1_Cargar_Venta.py", title="Cargar Venta", icon="🛒", default=True),
    st.Page("pages/2_Cargar_Compra.py", title="Cargar Compra", icon="📦"),
    st.Page("pages/3_Cargar_Gasto.py", title="Cargar Gasto", icon="💸"),
    st.Page("pages/4_Cargar_Retiro.py", title="Cargar Retiro", icon="💰"),
    st.Page("pages/5_Cargar_Envio.py", title="Cargar Envío", icon="🚚"),
    st.Page("pages/6_Resumen.py", title="Resumen", icon="📊"),
    st.Page("pages/8_Stock.py", title="Stock", icon="📦"),
]
st.navigation(paginas, position="top").run()
