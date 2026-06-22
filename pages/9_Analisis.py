import altair as alt
import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.formato import fmt_money
from app.services.gastos import CATEGORIAS_GASTO
from app.services.reportes import gastos_por_categoria
from app.services.tiendas import selector_tienda

cargar_config()

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Análisis de gastos — {tienda_nombre}")
st.caption("Cuánto se gastó históricamente en cada categoría.")

df = gastos_por_categoria(tienda_id)
if df.empty:
    st.info("Todavía no hay gastos cargados.")
    st.stop()

df["Categoría"] = df["categoria"].map(CATEGORIAS_GASTO)
df = df.sort_values("total", ascending=False)

c1, c2 = st.columns([1, 1])

with c1:
    df_mostrar = df[["Categoría", "cantidad", "total"]].rename(
        columns={"cantidad": "Cantidad de gastos", "total": "Total"}
    )
    df_mostrar["Total"] = df_mostrar["Total"].map(fmt_money)
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

with c2:
    df_chart = df.copy()
    df_chart["Total fmt"] = df_chart["total"].map(fmt_money)
    chart = (
        alt.Chart(df_chart)
        .mark_bar(color="#6366F1")
        .encode(
            x=alt.X("total:Q", title=None),
            y=alt.Y("Categoría:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("Categoría:N", title="Categoría"),
                alt.Tooltip("Total fmt:N", title="Total"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)
