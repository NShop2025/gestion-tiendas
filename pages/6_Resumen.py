import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.reportes import metricas_generales, resumen_mensual, saldo_disponible
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Resumen", page_icon="📊", layout="wide")

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
            $ {saldo:,.0f}</div>
        <div style="font-size: 0.8rem; color: #6B7180; margin-top: 0.3rem;">
            Toda la plata de la tienda en una sola caja</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Métricas secundarias en tarjetas.
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingreso neto total", f"$ {m['ingreso_neto']:,.0f}")
c2.metric("Ganancia total", f"$ {m['ganancia']:,.0f}")
c3.metric("Mercadería comprada", f"$ {m['compras']:,.0f}")
c4.metric("Retiros de socios", f"$ {m['retiros']:,.0f}")

st.divider()

# Evolución de ganancia mensual.
df = resumen_mensual(tienda_id)
if not df.empty:
    st.subheader("Ganancia por mes")
    df_chart = df[["mes", "ganancia"]].set_index("mes")
    st.bar_chart(df_chart, color="#6366F1", height=280)
else:
    st.info("Todavía no hay datos cargados.")
