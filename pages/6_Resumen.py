import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.reportes import saldo_cuenta
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Resumen", page_icon="📊", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Resumen — {tienda_nombre}")

col1, col2 = st.columns(2)
saldo_mp = saldo_cuenta(tienda_id, "mercado_pago")
saldo_santander = saldo_cuenta(tienda_id, "santander")

col1.metric("Saldo Mercado Pago", f"$ {saldo_mp:,.0f}")
col2.metric("Saldo Santander", f"$ {saldo_santander:,.0f}")

st.caption(
    "Saldo = ingresos netos de ventas (incluye envío) − compras − gastos de la cuenta "
    "− retiros − pagos de envíos de la cuenta."
)
