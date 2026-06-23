from datetime import date

import pandas as pd
import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.cuentas import CUENTAS
from app.services.db import get_engine
from app.services.eliminar import panel_eliminar
from app.services.productos import listar_productos, obtener_o_crear_producto
from app.services.reportes import buscar_compras, ultimas_compras
from app.services.tiendas import selector_tienda


def _buscar_compras_con_etiqueta(tienda_id, desde, hasta, texto):
    df = buscar_compras(tienda_id, desde, hasta, texto)
    if not df.empty:
        df["cuenta"] = df["cuenta"].map(CUENTAS)
    return df

cargar_config()

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar compra — {tienda_nombre}")
st.caption(
    "Si la compra tiene varios productos del mismo proveedor, agregalos todos al carrito "
    "y guardalos juntos (misma fecha y proveedor), como en el Excel."
)

if "carrito_compra" not in st.session_state:
    st.session_state["carrito_compra"] = []
if "item_form_key_compra" not in st.session_state:
    st.session_state["item_form_key_compra"] = 0

productos = listar_productos(tienda_id)
opciones_producto = productos["nombre"].tolist()

c1, c2 = st.columns(2)
fecha = c1.date_input("Fecha", value=date.today())
proveedor_comentario = c2.text_input("Proveedor / comentario (ej: TEMU)")

st.divider()
st.subheader("Agregar producto")

form_key = f"agregar_item_compra_{st.session_state['item_form_key_compra']}"

producto_nombre = st.selectbox(
    "Producto (escribí para buscar o cargar uno nuevo)",
    opciones_producto,
    index=None,
    accept_new_options=True,
    placeholder="Empezá a escribir...",
    key=f"producto_{form_key}",
)

with st.form(form_key, clear_on_submit=True):
    c3, c4 = st.columns(2)
    cantidad = c3.number_input("Cantidad", min_value=1, step=1, value=1)
    costo_unitario = c4.number_input("Costo unitario", min_value=0.0, step=1.0)

    agregado = st.form_submit_button("➕ Agregar al carrito")

if agregado:
    if not producto_nombre or not producto_nombre.strip():
        st.error("Falta el nombre del producto.")
    else:
        st.session_state["carrito_compra"].append(
            {
                "producto": producto_nombre.strip(),
                "cantidad": cantidad,
                "costo_unitario": costo_unitario,
            }
        )
        st.session_state["item_form_key_compra"] += 1
        st.rerun()

carrito = st.session_state["carrito_compra"]

if carrito:
    st.divider()
    st.subheader(f"Carrito ({len(carrito)} producto{'s' if len(carrito) != 1 else ''})")

    df_carrito = pd.DataFrame(carrito)
    df_mostrar = df_carrito.rename(
        columns={
            "producto": "Producto",
            "cantidad": "Cantidad",
            "costo_unitario": "Costo unitario",
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
        st.session_state["carrito_compra"] = []
        st.rerun()

    if col_guardar.button("💾 Guardar compra completa", type="primary"):
        engine = get_engine()
        with engine.begin() as conn:
            for item in carrito:
                producto_id = obtener_o_crear_producto(tienda_id, item["producto"])
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
                        "cantidad": item["cantidad"],
                        "costo_unitario": item["costo_unitario"],
                        "costo_total": item["cantidad"] * item["costo_unitario"],
                        "proveedor_comentario": proveedor_comentario or None,
                    },
                )

        st.session_state["carrito_compra"] = []
        listar_productos.clear()
        ultimas_compras.clear()
        st.success(f"Compra guardada con {len(carrito)} producto(s).")

st.divider()
st.subheader("🗂️ Historial")

with st.expander("🕒 Últimas compras cargadas (para ver dónde quedó el último que cargó)", expanded=False):
    df_ultimas = ultimas_compras(tienda_id)
    if df_ultimas.empty:
        st.caption("Todavía no hay compras cargadas.")
    else:
        st.dataframe(
            df_ultimas.drop(columns=["creado_en"]).rename(
                columns={
                    "fecha": "Fecha",
                    "producto": "Producto",
                    "cantidad": "Cantidad",
                    "costo_unitario": "Costo unitario",
                    "proveedor_comentario": "Proveedor / comentario",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

panel_eliminar(
    tienda_id=tienda_id,
    tabla="compras",
    buscar_fn=_buscar_compras_con_etiqueta,
    columnas={
        "fecha": "Fecha",
        "producto": "Producto",
        "cantidad": "Cantidad",
        "costo_unitario": "Costo unitario",
        "costo_total": "Costo total",
        "cuenta": "Cuenta",
        "proveedor_comentario": "Proveedor / comentario",
    },
    key="compras",
    limpiar_cache=(ultimas_compras,),
)
