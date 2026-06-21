from datetime import date

import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.db import get_engine
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Cargar Gasto", page_icon="💸", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar gasto — {tienda_nombre}")
st.caption("Gastos varios (packing, bolsas, etc.) que se descuentan de la cuenta elegida.")

with st.form("cargar_gasto"):
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", value=date.today())
    cuenta = c2.selectbox("Cuenta", ["mercado_pago", "santander", "otra"])

    concepto = st.text_input("Concepto")
    monto = st.number_input("Monto", min_value=0.0, step=1.0)
    comentario = st.text_input("Comentario (opcional)")

    enviado = st.form_submit_button("Guardar gasto")

if enviado:
    if not concepto.strip():
        st.error("Falta el concepto.")
        st.stop()

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into gastos (tienda_id, fecha, concepto, monto, cuenta, comentario)
                values (:tienda_id, :fecha, :concepto, :monto, :cuenta, :comentario)
                """
            ),
            {
                "tienda_id": tienda_id,
                "fecha": fecha,
                "concepto": concepto,
                "monto": monto,
                "cuenta": cuenta,
                "comentario": comentario or None,
            },
        )

    st.success("Gasto guardado.")
