from datetime import date, datetime

import pandas as pd
import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.db import get_engine
from app.services.productos import (
    listar_productos,
    obtener_o_crear_producto,
    ultimo_costo_unitario_por_nombre,
)
from app.services.reportes import ultimas_ventas
from app.services.tiendas import selector_tienda

cargar_config()
st.set_page_config(page_title="Cargar Venta", page_icon="🛒", layout="wide")

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar venta — {tienda_nombre}")
st.caption(
    "Si la venta tiene varios productos, agregalos todos al carrito y guardalos juntos "
    "(misma fecha y hora), como en el Excel."
)

with st.expander("🕒 Últimas ventas cargadas (para ver dónde quedó el último que cargó)", expanded=True):
    df_ultimas = ultimas_ventas(tienda_id)
    if df_ultimas.empty:
        st.caption("Todavía no hay ventas cargadas.")
    else:
        st.dataframe(
            df_ultimas.drop(columns=["creado_en"]).rename(
                columns={
                    "fecha": "Fecha",
                    "hora": "Hora",
                    "producto": "Producto",
                    "cantidad": "Cantidad",
                    "precio_unitario": "Precio unitario",
                    "canal": "Canal",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

if "carrito_venta" not in st.session_state:
    st.session_state["carrito_venta"] = []
if "item_form_key" not in st.session_state:
    st.session_state["item_form_key"] = 0

productos = listar_productos(tienda_id)
opciones_producto = productos["nombre"].tolist()

c1, c2, c3 = st.columns(3)
canal = c1.radio("Canal", ["Mercado Libre", "Web"], horizontal=True)
fecha = c2.date_input("Fecha", value=date.today())
hora = c3.time_input("Hora", value=datetime.now().time())
canal_db = "mercado_libre" if canal == "Mercado Libre" else "web"

st.divider()
st.subheader("Agregar producto")

form_key = f"agregar_item_{st.session_state['item_form_key']}"

# Fuera del form: así la página reacciona al toque y el costo sugerido se actualiza
# apenas elegís el producto (adentro de un form, Streamlit no reacciona hasta enviarlo).
producto_nombre = st.selectbox(
    "Producto (escribí para buscar o cargar uno nuevo)",
    opciones_producto,
    index=None,
    accept_new_options=True,
    placeholder="Empezá a escribir...",
    key=f"producto_{form_key}",
)
costo_sugerido = ultimo_costo_unitario_por_nombre(tienda_id, producto_nombre) if producto_nombre else 0.0

with st.form(form_key, clear_on_submit=True):
    c4, c5 = st.columns(2)
    cantidad = c4.number_input("Cantidad", min_value=1, step=1, value=1)
    precio_unitario = c5.number_input("Precio unitario (precio de venta)", min_value=0.0, step=1.0)

    c6, c7, c8 = st.columns(3)
    ingreso_neto = c6.number_input(
        "Ingreso neto (lo que te quedó después de la comisión de ML)",
        min_value=0.0,
        step=1.0,
        help="La comisión se calcula sola: precio x cantidad − este valor.",
    )
    ingreso_envio = c7.number_input("Ingreso por envío (opcional)", min_value=0.0, step=1.0, value=0.0)
    costo_unitario_venta = c8.number_input(
        "Costo unitario (de la última compra, ajustable)",
        min_value=0.0,
        step=1.0,
        value=costo_sugerido,
        key=f"costo_{form_key}_{producto_nombre}",
    )
    comentario = st.text_input("Comentario (opcional)")

    agregado = st.form_submit_button("➕ Agregar al carrito")

if agregado:
    if not producto_nombre or not producto_nombre.strip():
        st.error("Falta el nombre del producto.")
    else:
        ingreso_bruto = precio_unitario * cantidad
        comision_ml = max(ingreso_bruto - ingreso_neto, 0)
        st.session_state["carrito_venta"].append(
            {
                "producto": producto_nombre.strip(),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "comision_ml": comision_ml,
                "ingreso_envio": ingreso_envio,
                "costo_unitario_venta": costo_unitario_venta,
                "comentario": comentario or None,
            }
        )
        st.session_state["item_form_key"] += 1
        st.rerun()

carrito = st.session_state["carrito_venta"]

if carrito:
    st.divider()
    st.subheader(f"Carrito ({len(carrito)} producto{'s' if len(carrito) != 1 else ''})")

    df_carrito = pd.DataFrame(carrito)
    df_mostrar = df_carrito.rename(
        columns={
            "producto": "Producto",
            "cantidad": "Cantidad",
            "precio_unitario": "Precio unitario",
            "comision_ml": "Comisión ML",
            "ingreso_envio": "Ingreso envío",
            "costo_unitario_venta": "Costo unitario",
            "comentario": "Comentario",
        }
    )
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

    col_quitar, col_vaciar, col_guardar = st.columns([2, 1, 1])
    indice_quitar = col_quitar.selectbox(
        "Quitar producto del carrito",
        options=list(range(len(carrito))),
        format_func=lambda i: f"{i + 1}. {carrito[i]['producto']}",
    )
    if col_quitar.button("Quitar"):
        carrito.pop(indice_quitar)
        st.rerun()

    if col_vaciar.button("Vaciar carrito"):
        st.session_state["carrito_venta"] = []
        st.rerun()

    if col_guardar.button("💾 Guardar venta completa", type="primary"):
        engine = get_engine()
        with engine.begin() as conn:
            for item in carrito:
                producto_id = obtener_o_crear_producto(tienda_id, item["producto"])
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
                        "cantidad": item["cantidad"],
                        "precio_unitario": item["precio_unitario"],
                        "comision_ml": item["comision_ml"],
                        "ingreso_envio": item["ingreso_envio"],
                        "costo_unitario_venta": item["costo_unitario_venta"],
                        "comentario": item["comentario"],
                    },
                )

        st.session_state["carrito_venta"] = []
        listar_productos.clear()
        ultimas_ventas.clear()
        st.success(f"Venta guardada con {len(carrito)} producto(s).")
