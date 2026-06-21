import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.services.db import get_engine


@st.cache_data(ttl=60)
def saldo_mercado_pago(tienda_id: str) -> float:
    """Saldo real de la única caja activa hoy (Mercado Pago). Replica la fórmula de la
    hoja 'Resumen' del Excel: ingresos de ventas (solo Mercado Libre + Web, igual que el
    Excel original) - compras - gastos de MP - retiros - envíos de MP.

    Compras, retiros e ingresos de ventas son una sola bolsa para toda la tienda (no están
    separados por cuenta en los datos), por eso este saldo solo tiene sentido para la
    cuenta que de verdad se usa como caja.
    """
    engine = get_engine()
    with engine.connect() as conn:
        ingresos_ventas = conn.execute(
            text(
                "select coalesce(sum(ingreso_bruto - comision_ml + ingreso_envio), 0) "
                "from ventas where tienda_id = :tienda_id and canal in ('mercado_libre', 'web')"
            ),
            {"tienda_id": tienda_id},
        ).scalar()
        total_compras = conn.execute(
            text("select coalesce(sum(costo_total), 0) from compras where tienda_id = :tienda_id"),
            {"tienda_id": tienda_id},
        ).scalar()
        total_gastos = conn.execute(
            text(
                "select coalesce(sum(monto), 0) from gastos "
                "where tienda_id = :tienda_id and cuenta = 'mercado_pago'"
            ),
            {"tienda_id": tienda_id},
        ).scalar()
        total_retiros = conn.execute(
            text("select coalesce(sum(monto), 0) from retiros where tienda_id = :tienda_id"),
            {"tienda_id": tienda_id},
        ).scalar()
        total_envios = conn.execute(
            text(
                "select coalesce(sum(costo_total), 0) from envios "
                "where tienda_id = :tienda_id and cuenta = 'mercado_pago'"
            ),
            {"tienda_id": tienda_id},
        ).scalar()

    return float(ingresos_ventas) - float(total_compras) - float(total_gastos) - float(total_retiros) - float(
        total_envios
    )


@st.cache_data(ttl=60)
def gastos_pagados_santander(tienda_id: str) -> float:
    """Santander no es una caja activa (no tiene ingresos propios registrados), así que en
    vez de un 'saldo' inventado mostramos cuánto se pagó históricamente con esa cuenta."""
    engine = get_engine()
    with engine.connect() as conn:
        total_gastos = conn.execute(
            text(
                "select coalesce(sum(monto), 0) from gastos "
                "where tienda_id = :tienda_id and cuenta = 'santander'"
            ),
            {"tienda_id": tienda_id},
        ).scalar()
        total_envios = conn.execute(
            text(
                "select coalesce(sum(costo_total), 0) from envios "
                "where tienda_id = :tienda_id and cuenta = 'santander'"
            ),
            {"tienda_id": tienda_id},
        ).scalar()
    return float(total_gastos) + float(total_envios)


@st.cache_data(ttl=60)
def resumen_mensual(tienda_id: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        ventas = pd.read_sql(
            text(
                """
                select date_trunc('month', fecha)::date as mes,
                       sum(ingreso_bruto) as ventas_brutas,
                       sum(cantidad * costo_unitario_venta) as costo_mercaderia_vendida,
                       sum(ingreso_bruto - comision_ml + ingreso_envio - cantidad * costo_unitario_venta) as ganancia
                from ventas
                where tienda_id = :tienda_id
                group by 1
                """
            ),
            conn,
            params={"tienda_id": tienda_id},
        )
        gastos = pd.read_sql(
            text(
                """
                select date_trunc('month', fecha)::date as mes, sum(monto) as gastos_varios
                from gastos where tienda_id = :tienda_id group by 1
                """
            ),
            conn,
            params={"tienda_id": tienda_id},
        )
        envios = pd.read_sql(
            text(
                """
                select date_trunc('month', fecha)::date as mes, sum(costo_total) as gastos_envios
                from envios where tienda_id = :tienda_id group by 1
                """
            ),
            conn,
            params={"tienda_id": tienda_id},
        )
        retiros = pd.read_sql(
            text(
                """
                select date_trunc('month', fecha)::date as mes, sum(monto) as retiros
                from retiros where tienda_id = :tienda_id group by 1
                """
            ),
            conn,
            params={"tienda_id": tienda_id},
        )
        compras = pd.read_sql(
            text(
                """
                select date_trunc('month', fecha)::date as mes, sum(costo_total) as mercaderia_comprada
                from compras where tienda_id = :tienda_id group by 1
                """
            ),
            conn,
            params={"tienda_id": tienda_id},
        )

    df = ventas
    for otro in (gastos, envios, retiros, compras):
        df = df.merge(otro, on="mes", how="outer")

    df = df.fillna(0).sort_values("mes")
    df["saldo_final"] = df.get("ganancia", 0) - df.get("retiros", 0)
    return df


@st.cache_data(ttl=60)
def stock_actual(tienda_id: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                "select producto, total_comprado, total_vendido, stock_actual "
                "from stock_actual where tienda_id = :tienda_id order by stock_actual asc"
            ),
            conn,
            params={"tienda_id": tienda_id},
        )
