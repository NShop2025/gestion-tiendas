from datetime import date

import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.db import get_engine
from app.services.eliminar import panel_eliminar
from app.services.reportes import buscar_envios, ultimos_envios
from app.services.tiendas import selector_tienda

cargar_config()

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar pago de envíos — {tienda_nombre}")
st.caption("Pagos a cadetería (FLEX). Se descuentan de la cuenta elegida.")

with st.expander("🕒 Últimos pagos de envíos cargados (para ver dónde quedó el último que cargó)", expanded=False):
    df_ultimos = ultimos_envios(tienda_id)
    if df_ultimos.empty:
        st.caption("Todavía no hay pagos de envíos cargados.")
    else:
        st.dataframe(
            df_ultimos.rename(
                columns={
                    "fecha": "Fecha",
                    "cuenta": "Cuenta",
                    "cadete": "Cadete",
                    "cantidad_envios": "Cantidad de envíos",
                    "costo_unitario": "Costo por envío",
                    "comentario": "Comentario",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

panel_eliminar(
    tienda_id=tienda_id,
    tabla="envios",
    buscar_fn=buscar_envios,
    columnas={
        "fecha": "Fecha",
        "cuenta": "Cuenta",
        "cadete": "Cadete",
        "cantidad_envios": "Cantidad de envíos",
        "costo_unitario": "Costo por envío",
        "comentario": "Comentario",
    },
    key="envios",
    limpiar_cache=(ultimos_envios,),
)

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

    ultimos_envios.clear()
    st.success("Pago de envíos guardado.")
