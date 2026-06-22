import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.services.db import get_engine


@st.cache_data(ttl=60)
def saldo_disponible(tienda_id: str) -> float:
    """Saldo único consolidado de toda la plata de la tienda (una sola caja).

    Ingresos de TODAS las ventas (todos los canales) menos compras (las pagadas con otra
    tarjeta / inversión inicial quedan fuera con cuenta='otra'), gastos, retiros y envíos,
    sin importar la cuenta. Las transferencias internas entre cuentas no se cuentan (mover
    plata de un bolsillo a otro no cambia el total).
    """
    engine = get_engine()
    with engine.connect() as conn:
        ingresos_ventas = conn.execute(
            text(
                "select coalesce(sum(ingreso_bruto - comision_ml + ingreso_envio), 0) "
                "from ventas where tienda_id = :tienda_id"
            ),
            {"tienda_id": tienda_id},
        ).scalar()
        total_compras = conn.execute(
            text(
                "select coalesce(sum(costo_total), 0) from compras "
                "where tienda_id = :tienda_id and cuenta <> 'otra'"
            ),
            {"tienda_id": tienda_id},
        ).scalar()
        total_gastos = conn.execute(
            text("select coalesce(sum(monto), 0) from gastos where tienda_id = :tienda_id"),
            {"tienda_id": tienda_id},
        ).scalar()
        total_retiros = conn.execute(
            text("select coalesce(sum(monto), 0) from retiros where tienda_id = :tienda_id"),
            {"tienda_id": tienda_id},
        ).scalar()
        total_envios = conn.execute(
            text("select coalesce(sum(costo_total), 0) from envios where tienda_id = :tienda_id"),
            {"tienda_id": tienda_id},
        ).scalar()

    return float(ingresos_ventas) - float(total_compras) - float(total_gastos) - float(total_retiros) - float(
        total_envios
    )


@st.cache_data(ttl=60)
def metricas_generales(tienda_id: str) -> dict:
    """Totales históricos de la tienda para las tarjetas del Resumen."""
    engine = get_engine()
    with engine.connect() as conn:
        ventas = conn.execute(
            text(
                """
                select
                    coalesce(sum(ingreso_bruto - comision_ml + ingreso_envio), 0) as ingreso_neto,
                    coalesce(sum(ingreso_bruto - comision_ml + ingreso_envio
                                 - cantidad * costo_unitario_venta), 0) as ganancia,
                    count(*) as cantidad_ventas
                from ventas where tienda_id = :t
                """
            ),
            {"t": tienda_id},
        ).mappings().first()
        compras = conn.execute(
            text("select coalesce(sum(costo_total), 0) from compras where tienda_id = :t and cuenta <> 'otra'"),
            {"t": tienda_id},
        ).scalar()
        retiros = conn.execute(
            text("select coalesce(sum(monto), 0) from retiros where tienda_id = :t"),
            {"t": tienda_id},
        ).scalar()

    return {
        "ingreso_neto": float(ventas["ingreso_neto"]),
        "ganancia": float(ventas["ganancia"]),
        "cantidad_ventas": int(ventas["cantidad_ventas"]),
        "compras": float(compras),
        "retiros": float(retiros),
    }


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
                       sum(ingreso_bruto - comision_ml + ingreso_envio - cantidad * costo_unitario_venta) as margen_bruto
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
    # Ganancia igual que la hoja Resumen del Excel: margen bruto (ventas neto + envío - costo
    # mercadería) menos los gastos de envíos y los gastos varios del mes.
    df["ganancia"] = df["margen_bruto"] - df["gastos_envios"] - df["gastos_varios"]
    df["saldo_final"] = df["ganancia"] - df["retiros"]
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
