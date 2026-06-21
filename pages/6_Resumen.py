import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.reportes import gastos_pagados_santander, saldo_mercado_pago
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Resumen", page_icon="📊", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Resumen — {tienda_nombre}")

col1, col2 = st.columns(2)
saldo_mp = saldo_mercado_pago(tienda_id)
gastos_santander = gastos_pagados_santander(tienda_id)

col1.metric("Saldo Mercado Pago", f"$ {saldo_mp:,.0f}")
col2.metric("Pagado con Santander (histórico)", f"$ {gastos_santander:,.0f}")

st.caption(
    "Saldo Mercado Pago = ingresos netos de ventas Mercado Libre + Web (incluye envío) "
    "− compras − gastos pagados con Mercado Pago − retiros − envíos pagados con Mercado Pago."
)
st.caption(
    "Santander no es una caja activa hoy (no tiene ingresos propios cargados), así que en vez "
    "de un saldo mostramos cuánto se pagó históricamente con esa cuenta (gastos + envíos)."
)
