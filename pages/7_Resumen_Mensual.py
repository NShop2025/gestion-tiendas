import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.reportes import resumen_mensual
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Resumen Mensual", page_icon="📅", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Resumen mensual — {tienda_nombre}")

df = resumen_mensual(tienda_id)
if df.empty:
    st.info("Todavía no hay datos cargados.")
    st.stop()

df_mostrar = df.rename(
    columns={
        "mes": "Mes",
        "ventas_brutas": "Ventas brutas",
        "costo_mercaderia_vendida": "Costo mercadería vendida",
        "gastos_envios": "Gastos de envíos",
        "gastos_varios": "Gastos varios",
        "ganancia": "Ganancia",
        "retiros": "Retiros",
        "saldo_final": "Saldo final",
        "mercaderia_comprada": "Mercadería comprada",
    }
)

st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
st.line_chart(df.set_index("mes")[["ganancia", "ventas_brutas"]])
