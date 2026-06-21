import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.services.db import get_engine


@st.cache_data(ttl=60)
def listar_productos(tienda_id: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                "select id, nombre from productos "
                "where tienda_id = :tienda_id and activo order by nombre"
            ),
            conn,
            params={"tienda_id": tienda_id},
        )


def obtener_o_crear_producto(tienda_id: str, nombre: str) -> str:
    nombre = nombre.strip()
    engine = get_engine()
    with engine.begin() as conn:
        fila = conn.execute(
            text("select id from productos where tienda_id = :tienda_id and nombre = :nombre"),
            {"tienda_id": tienda_id, "nombre": nombre},
        ).fetchone()
        if fila:
            return str(fila[0])

        nueva = conn.execute(
            text(
                "insert into productos (tienda_id, nombre) values (:tienda_id, :nombre) "
                "returning id"
            ),
            {"tienda_id": tienda_id, "nombre": nombre},
        ).fetchone()
        return str(nueva[0])


def ultimo_costo_unitario(tienda_id: str, producto_id: str) -> float:
    """Costo unitario de la compra más reciente de este producto, para sugerir el costo de venta."""
    engine = get_engine()
    with engine.connect() as conn:
        fila = conn.execute(
            text(
                "select costo_unitario from compras "
                "where tienda_id = :tienda_id and producto_id = :producto_id "
                "order by fecha desc, creado_en desc limit 1"
            ),
            {"tienda_id": tienda_id, "producto_id": producto_id},
        ).fetchone()
        return float(fila[0]) if fila else 0.0
