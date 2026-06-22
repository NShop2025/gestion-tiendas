from datetime import date

import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.db import get_engine
from app.services.productos import listar_productos, obtener_o_crear_producto
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Cargar Compra", page_icon="📦", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar compra — {tienda_nombre}")

productos = listar_productos(tienda_id)
opciones_producto = ["(nuevo producto)"] + productos["nombre"].tolist()

col1, col2 = st.columns(2)
producto_sel = col1.selectbox("Producto", opciones_producto)
producto_nuevo = col2.text_input("Nombre del producto nuevo", disabled=producto_sel != "(nuevo producto)")

with st.form("cargar_compra"):
    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha", value=date.today())
    cantidad = c2.number_input("Cantidad", min_value=1, step=1, value=1)
    costo_unitario = c3.number_input("Costo unitario", min_value=0.0, step=1.0)

    proveedor_comentario = st.text_input("Proveedor / comentario (ej: TEMU)")

    enviado = st.form_submit_button("Guardar compra")

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
                insert into compras
                    (tienda_id, producto_id, fecha, cantidad, costo_unitario, costo_total, proveedor_comentario)
                values
                    (:tienda_id, :producto_id, :fecha, :cantidad, :costo_unitario, :costo_total, :proveedor_comentario)
                """
            ),
            {
                "tienda_id": tienda_id,
                "producto_id": producto_id,
                "fecha": fecha,
                "cantidad": cantidad,
                "costo_unitario": costo_unitario,
                "costo_total": cantidad * costo_unitario,
                "proveedor_comentario": proveedor_comentario or None,
            },
        )

    st.success(f"Compra de {nombre_producto} guardada.")
    listar_productos.clear()
