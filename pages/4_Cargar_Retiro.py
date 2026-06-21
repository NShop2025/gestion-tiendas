from datetime import date

import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.db import get_engine
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Cargar Retiro", page_icon="💰", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar retiro — {tienda_nombre}")

with st.form("cargar_retiro"):
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", value=date.today())
    socio = c2.text_input("Quién retira")

    monto = st.number_input("Monto", min_value=0.0, step=1.0)
    comentario = st.text_input("Comentario (opcional)")

    enviado = st.form_submit_button("Guardar retiro")

if enviado:
    if not socio.strip():
        st.error("Falta indicar quién retira.")
        st.stop()

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into retiros (tienda_id, fecha, monto, socio, comentario)
                values (:tienda_id, :fecha, :monto, :socio, :comentario)
                """
            ),
            {
                "tienda_id": tienda_id,
                "fecha": fecha,
                "monto": monto,
                "socio": socio,
                "comentario": comentario or None,
            },
        )

    st.success("Retiro guardado.")
