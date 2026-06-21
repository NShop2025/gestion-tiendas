import streamlit as st

from app.services.auth import requerir_login
from app.services.config import cargar_config

cargar_config()

st.set_page_config(page_title="Gestión Tiendas", page_icon="🛍️", layout="wide")

usuario = requerir_login()

st.sidebar.success(f"Conectado como {usuario}")
if st.sidebar.button("Cerrar sesión"):
    del st.session_state["usuario"]
    st.rerun()

st.title("Gestión Tiendas")
st.write(
    "Usá el menú de la izquierda para cargar ventas, compras, gastos, retiros y envíos, "
    "o para ver los reportes (Resumen, Resumen mensual, Stock)."
)
