import altair as alt
import pandas as pd
import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.formato import fmt_money
from app.services.reportes import metricas_generales, resumen_mensual, saldo_disponible
from app.services.tiendas import selector_tienda

cargar_config()

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Resumen — {tienda_nombre}")

saldo = saldo_disponible(tienda_id)
m = metricas_generales(tienda_id)

# Tarjeta principal: saldo disponible, destacado.
color = "#34D399" if saldo >= 0 else "#F87171"
st.markdown(
    f"""
    <div style="padding: 1.6rem 1.8rem; border-radius: 16px; margin-bottom: 1.4rem;
        background: linear-gradient(135deg, #1E2230 0%, #14171F 100%);
        border: 1px solid #2A2F3C;">
        <div style="font-size: 0.8rem; letter-spacing: 0.05em; text-transform: uppercase;
                    color: #8A90A0;">Saldo disponible (Mercado Pago)</div>
        <div style="font-size: 2.6rem; font-weight: 700; color: {color}; line-height: 1.2;">
            {fmt_money(saldo)}</div>
        <div style="font-size: 0.8rem; color: #6B7180; margin-top: 0.3rem;">
            Toda la plata de la tienda en una sola caja</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Métricas secundarias en tarjetas.
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingreso neto total", fmt_money(m["ingreso_neto"]))
c2.metric("Ganancia total", fmt_money(m["ganancia"]))
c3.metric("Mercadería comprada", fmt_money(m["compras"]))
c4.metric("Retiros de socios", fmt_money(m["retiros"]))

st.divider()

# Evolución de ganancia mensual.
df = resumen_mensual(tienda_id)
if not df.empty:
    st.subheader("Ganancia por mes")
    df_chart = df[["mes", "ganancia"]].copy()
    df_chart["mes"] = pd.to_datetime(df_chart["mes"])
    df_chart["ganancia"] = df_chart["ganancia"].round(0)
    df_chart["Mes"] = df_chart["mes"].dt.strftime("%b %Y")
    df_chart["Ganancia"] = df_chart["ganancia"].map(fmt_money)

    chart = (
        alt.Chart(df_chart)
        .mark_bar(color="#6366F1", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("mes:T", title=None, axis=alt.Axis(format="%b %y")),
            y=alt.Y("ganancia:Q", title=None),
            tooltip=[
                alt.Tooltip("Mes:N", title="Mes"),
                alt.Tooltip("Ganancia:N", title="Ganancia"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Todavía no hay datos cargados.")
