import altair as alt
import pandas as pd
import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.formato import fmt_money
from app.services.reportes import resumen_mensual
from app.services.tiendas import selector_tienda

cargar_config()

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Resumen mensual — {tienda_nombre}")

df = resumen_mensual(tienda_id)
if df.empty:
    st.info("Todavía no hay datos cargados.")
    st.stop()

df = df.sort_values("mes")
df["mes"] = pd.to_datetime(df["mes"])

# Tabla con montos formateados (punto de miles, sin decimales) y mes legible.
df_mostrar = pd.DataFrame({"Mes": df["mes"].dt.strftime("%b %Y")})
columnas = {
    "ventas_brutas": "Ventas brutas",
    "costo_mercaderia_vendida": "Costo mercadería vendida",
    "gastos_envios": "Gastos de envíos",
    "gastos_varios": "Gastos varios",
    "ganancia": "Ganancia",
    "retiros": "Retiros",
    "saldo_final": "Saldo final",
    "mercaderia_comprada": "Mercadería comprada",
}
for col, titulo in columnas.items():
    if col in df.columns:
        df_mostrar[titulo] = df[col].map(fmt_money)

st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# Evolución de ganancia y ventas, con tooltip formateado.
df_chart = df[["mes", "ganancia", "ventas_brutas"]].copy()
df_largo = df_chart.melt("mes", var_name="serie", value_name="monto")
df_largo["serie"] = df_largo["serie"].map({"ganancia": "Ganancia", "ventas_brutas": "Ventas brutas"})
df_largo["Mes"] = df_largo["mes"].dt.strftime("%b %Y")
df_largo["Monto"] = df_largo["monto"].map(fmt_money)

chart = (
    alt.Chart(df_largo)
    .mark_line(point=True)
    .encode(
        x=alt.X("mes:T", title=None, axis=alt.Axis(format="%b %y")),
        y=alt.Y("monto:Q", title=None),
        color=alt.Color("serie:N", title=None, scale=alt.Scale(range=["#6366F1", "#34D399"])),
        tooltip=[
            alt.Tooltip("serie:N", title=""),
            alt.Tooltip("Mes:N", title="Mes"),
            alt.Tooltip("Monto:N", title="Monto"),
        ],
    )
    .properties(height=320)
)
st.altair_chart(chart, use_container_width=True)
