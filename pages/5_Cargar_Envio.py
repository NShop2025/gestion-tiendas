from datetime import date

import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.db import get_engine
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Cargar Envío", page_icon="🚚", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar pago de envíos — {tienda_nombre}")
st.caption("Pagos a cadetería (FLEX). Se descuentan de la cuenta elegida.")

with st.form("cargar_envio"):
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", value=date.today())
    cuenta = c2.selectbox("Cuenta", ["mercado_pago", "santander"])

    cadete = st.text_input("Cadete")
    c3, c4 = st.columns(2)
    cantidad_envios = c3.number_input("Cantidad de envíos", min_value=0, step=1)
    costo_unitario = c4.number_input("Costo por envío", min_value=0.0, step=1.0)
    comentario = st.text_input("Comentario (opcional)")

    enviado = st.form_submit_button("Guardar pago de envíos")

if enviado:
    if not cadete.strip():
        st.error("Falta el nombre del cadete.")
        st.stop()

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into envios (tienda_id, cuenta, fecha, cadete, cantidad_envios, costo_unitario, comentario)
                values (:tienda_id, :cuenta, :fecha, :cadete, :cantidad_envios, :costo_unitario, :comentario)
                """
            ),
            {
                "tienda_id": tienda_id,
                "cuenta": cuenta,
                "fecha": fecha,
                "cadete": cadete,
                "cantidad_envios": cantidad_envios,
                "costo_unitario": costo_unitario,
                "comentario": comentario or None,
            },
        )

    st.success("Pago de envíos guardado.")
