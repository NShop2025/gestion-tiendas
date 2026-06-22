import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.reportes import saldo_disponible
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Resumen", page_icon="📊", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Resumen — {tienda_nombre}")

saldo = saldo_disponible(tienda_id)
st.metric("Saldo disponible (Mercado Pago)", f"$ {saldo:,.0f}")

st.caption(
    "Saldo = ingresos netos de todas las ventas (incluye envío) − compras − gastos − retiros "
    "− pagos de envíos. Toda la plata de la tienda en una sola caja."
)
