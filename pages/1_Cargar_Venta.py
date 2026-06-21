from datetime import date, datetime

import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.db import get_engine
from app.services.productos import listar_productos, obtener_o_crear_producto, ultimo_costo_unitario
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Cargar Venta", page_icon="🛒", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar venta — {tienda_nombre}")

productos = listar_productos(tienda_id)
opciones_producto = ["(nuevo producto)"] + productos["nombre"].tolist()

canal = st.radio("Canal", ["Mercado Libre", "Web"], horizontal=True)
canal_db = "mercado_libre" if canal == "Mercado Libre" else "web"

col1, col2 = st.columns(2)
producto_sel = col1.selectbox("Producto", opciones_producto)
producto_nuevo = col2.text_input("Nombre del producto nuevo", disabled=producto_sel != "(nuevo producto)")

with st.form("cargar_venta"):
    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha", value=date.today())
    hora = c2.time_input("Hora", value=datetime.now().time())
    cantidad = c3.number_input("Cantidad", min_value=1, step=1, value=1)

    c4, c5, c6 = st.columns(3)
    precio_unitario = c4.number_input("Precio unitario", min_value=0.0, step=1.0)
    comision_ml = c5.number_input("Comisión ML (impuestos incluidos)", min_value=0.0, step=1.0, value=0.0)
    ingreso_envio = c6.number_input("Ingreso por envío", min_value=0.0, step=1.0, value=0.0)

    costo_sugerido = 0.0
    if producto_sel != "(nuevo producto)":
        producto_id_preview = productos.loc[productos["nombre"] == producto_sel, "id"].iloc[0]
        costo_sugerido = ultimo_costo_unitario(tienda_id, producto_id_preview)

    costo_unitario_venta = st.number_input(
        "Costo unitario (de la última compra, ajustable)",
        min_value=0.0,
        step=1.0,
        value=costo_sugerido,
    )
    comentario = st.text_input("Comentario (opcional)")

    enviado = st.form_submit_button("Guardar venta")

if enviado:
    nombre_producto = producto_nuevo if producto_sel == "(nuevo producto)" else producto_sel
    if not nombre_producto.strip():
        st.error("Falta el nombre del producto.")
        st.stop()

    producto_id = obtener_o_crear_producto(tienda_id, nombre_producto)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into ventas
                    (tienda_id, producto_id, canal, fecha, hora, cantidad, precio_unitario,
                     comision_ml, ingreso_envio, costo_unitario_venta, comentario)
                values
                    (:tienda_id, :producto_id, :canal, :fecha, :hora, :cantidad, :precio_unitario,
                     :comision_ml, :ingreso_envio, :costo_unitario_venta, :comentario)
                """
            ),
            {
                "tienda_id": tienda_id,
                "producto_id": producto_id,
                "canal": canal_db,
                "fecha": fecha,
                "hora": hora,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "comision_ml": comision_ml,
                "ingreso_envio": ingreso_envio,
                "costo_unitario_venta": costo_unitario_venta,
                "comentario": comentario or None,
            },
        )

    st.success(f"Venta de {nombre_producto} guardada.")
    listar_productos.clear()
