import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.services.db import get_engine


@st.cache_data(ttl=60)
def saldo_disponible(tienda_id: str) -> float:
    """Saldo disponible en la cuenta de Mercado Pago (la plata real con la que se puede
    comprar/pagar hoy), no el total consolidado de todas las cuentas.

    Ingresos de ventas Mercado Libre + Web (las de Tiendimport no entran: esa plata no cae
    en Mercado Pago) menos compras (las pagadas con otra tarjeta / inversión inicial quedan
    fuera con cuenta='otra'), gastos y envíos pagados con cuenta='mercado_pago', y retiros
    (se asume que siempre se sacan de Mercado Pago). Los gastos/envíos pagados con Santander
    no se restan acá porque no afectan la plata de Mercado Pago; si querés la ganancia total
    de la tienda con todas las cuentas juntas, mirá la pestaña Mensual.

    Excepción: el traspaso histórico de plata de Mercado Pago a Santander (cargado como una
    "venta" del canal Tiendimport con comentario "SALDO INICIAL SANTANDER", el 13/7/2025 en
    NeptunoShop) sí se resta - esa plata salió físicamente de Mercado Pago aunque esté
    registrada en otro canal.
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
        traspasos_a_santander = conn.execute(
            text(
                "select coalesce(sum(ingreso_bruto - comision_ml + ingreso_envio), 0) "
                "from ventas where tienda_id = :tienda_id and canal = 'otro' "
                "and comentario ilike '%SALDO INICIAL SANTANDER%'"
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
    ) - float(traspasos_a_santander)


@st.cache_data(ttl=30)
def ultimas_ventas(tienda_id: str, n: int = 8) -> pd.DataFrame:
    """Últimas ventas por fecha de la venta (no por orden de carga: los históricos migrados
    en bloque comparten el mismo creado_en, así que ordenar por carga mostraba ventas viejas
    primero). Así quien abre la página ve las ventas más recientes y sabe dónde continuar."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select v.creado_en, v.fecha, v.hora, p.nombre as producto, v.cantidad,
                       v.precio_unitario, v.canal
                from ventas v
                join productos p on p.id = v.producto_id
                where v.tienda_id = :tienda_id
                order by v.fecha desc, v.hora desc nulls last, v.creado_en desc
                limit :n
                """
            ),
            conn,
            params={"tienda_id": tienda_id, "n": n},
        )


@st.cache_data(ttl=30)
def ultimas_compras(tienda_id: str, n: int = 8) -> pd.DataFrame:
    """Últimas compras por fecha de la compra, mismo criterio que ultimas_ventas."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select c.creado_en, c.fecha, p.nombre as producto, c.cantidad,
                       c.costo_unitario, c.proveedor_comentario
                from compras c
                join productos p on p.id = c.producto_id
                where c.tienda_id = :tienda_id
                order by c.fecha desc, c.creado_en desc
                limit :n
                """
            ),
            conn,
            params={"tienda_id": tienda_id, "n": n},
        )


@st.cache_data(ttl=30)
def ultimos_gastos(tienda_id: str, n: int = 8) -> pd.DataFrame:
    """Últimos gastos por fecha del gasto, mismo criterio que ultimas_ventas."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select fecha, categoria, concepto, monto, cuenta, comentario
                from gastos
                where tienda_id = :tienda_id
                order by fecha desc, creado_en desc
                limit :n
                """
            ),
            conn,
            params={"tienda_id": tienda_id, "n": n},
        )


@st.cache_data(ttl=60)
def gastos_por_categoria(tienda_id: str) -> pd.DataFrame:
    """Total histórico de gastos agrupado por categoría, para el análisis de en qué se gasta."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select categoria, count(*) as cantidad, sum(monto) as total
                from gastos
                where tienda_id = :tienda_id
                group by categoria
                order by total desc
                """
            ),
            conn,
            params={"tienda_id": tienda_id},
        )


@st.cache_data(ttl=30)
def ultimos_envios(tienda_id: str, n: int = 8) -> pd.DataFrame:
    """Últimos pagos de envíos por fecha, mismo criterio que ultimas_ventas."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select fecha, cuenta, cadete, cantidad_envios, costo_unitario, comentario
                from envios
                where tienda_id = :tienda_id
                order by fecha desc, creado_en desc
                limit :n
                """
            ),
            conn,
            params={"tienda_id": tienda_id, "n": n},
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


def buscar_ventas(tienda_id: str, desde, hasta, texto: str = "", limit: int = 300) -> pd.DataFrame:
    """Busca ventas por rango de fecha y texto libre (producto o comentario), para el panel
    de eliminar. Sin cache: tiene que reflejar filtros en vivo y altas/bajas al instante."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select v.id, v.fecha, v.hora, p.nombre as producto, v.cantidad,
                       v.precio_unitario, v.canal, v.comentario
                from ventas v
                join productos p on p.id = v.producto_id
                where v.tienda_id = :tienda_id
                  and v.fecha between :desde and :hasta
                  and (:texto = '' or p.nombre ilike :texto_like or v.comentario ilike :texto_like)
                order by v.fecha desc, v.hora desc nulls last
                limit :limit
                """
            ),
            conn,
            params={
                "tienda_id": tienda_id,
                "desde": desde,
                "hasta": hasta,
                "texto": texto,
                "texto_like": f"%{texto}%",
                "limit": limit,
            },
        )


def buscar_compras(tienda_id: str, desde, hasta, texto: str = "", limit: int = 300) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select c.id, c.fecha, p.nombre as producto, c.cantidad, c.costo_unitario,
                       c.costo_total, c.cuenta, c.proveedor_comentario
                from compras c
                join productos p on p.id = c.producto_id
                where c.tienda_id = :tienda_id
                  and c.fecha between :desde and :hasta
                  and (:texto = '' or p.nombre ilike :texto_like or c.proveedor_comentario ilike :texto_like)
                order by c.fecha desc
                limit :limit
                """
            ),
            conn,
            params={
                "tienda_id": tienda_id,
                "desde": desde,
                "hasta": hasta,
                "texto": texto,
                "texto_like": f"%{texto}%",
                "limit": limit,
            },
        )


def buscar_gastos(tienda_id: str, desde, hasta, texto: str = "", limit: int = 300) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select id, fecha, categoria, concepto, monto, cuenta, comentario
                from gastos
                where tienda_id = :tienda_id
                  and fecha between :desde and :hasta
                  and (:texto = '' or concepto ilike :texto_like or comentario ilike :texto_like)
                order by fecha desc
                limit :limit
                """
            ),
            conn,
            params={
                "tienda_id": tienda_id,
                "desde": desde,
                "hasta": hasta,
                "texto": texto,
                "texto_like": f"%{texto}%",
                "limit": limit,
            },
        )


def buscar_retiros(tienda_id: str, desde, hasta, texto: str = "", limit: int = 300) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select id, fecha, monto, socio, comentario
                from retiros
                where tienda_id = :tienda_id
                  and fecha between :desde and :hasta
                  and (:texto = '' or socio ilike :texto_like or comentario ilike :texto_like)
                order by fecha desc
                limit :limit
                """
            ),
            conn,
            params={
                "tienda_id": tienda_id,
                "desde": desde,
                "hasta": hasta,
                "texto": texto,
                "texto_like": f"%{texto}%",
                "limit": limit,
            },
        )


def buscar_envios(tienda_id: str, desde, hasta, texto: str = "", limit: int = 300) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select id, fecha, cuenta, cadete, cantidad_envios, costo_unitario, comentario
                from envios
                where tienda_id = :tienda_id
                  and fecha between :desde and :hasta
                  and (:texto = '' or cadete ilike :texto_like or comentario ilike :texto_like)
                order by fecha desc
                limit :limit
                """
            ),
            conn,
            params={
                "tienda_id": tienda_id,
                "desde": desde,
                "hasta": hasta,
                "texto": texto,
                "texto_like": f"%{texto}%",
                "limit": limit,
            },
        )


@st.cache_data(ttl=30)
def ultimos_retiros(tienda_id: str, n: int = 8) -> pd.DataFrame:
    """Últimos retiros por fecha, mismo criterio que ultimas_ventas."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select fecha, monto, socio, comentario
                from retiros
                where tienda_id = :tienda_id
                order by fecha desc, creado_en desc
                limit :n
                """
            ),
            conn,
            params={"tienda_id": tienda_id, "n": n},
        )


@st.cache_data(ttl=60)
def ventas_por_canal(tienda_id: str) -> pd.DataFrame:
    """Total histórico de ventas agrupado por canal (mercado_libre/web/otro)."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select canal, count(*) as cantidad_ventas,
                       sum(ingreso_bruto - comision_ml + ingreso_envio) as ingreso_neto
                from ventas
                where tienda_id = :tienda_id
                group by canal
                order by ingreso_neto desc
                """
            ),
            conn,
            params={"tienda_id": tienda_id},
        )


@st.cache_data(ttl=60)
def top_productos(tienda_id: str, n: int = 10) -> pd.DataFrame:
    """Productos más vendidos históricamente por ingreso neto, con cantidad y ganancia."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                """
                select p.nombre as producto,
                       sum(v.cantidad) as cantidad_vendida,
                       sum(v.ingreso_bruto - v.comision_ml + v.ingreso_envio) as ingreso_neto,
                       sum(v.ingreso_bruto - v.comision_ml + v.ingreso_envio
                           - v.cantidad * v.costo_unitario_venta) as ganancia
                from ventas v
                join productos p on p.id = v.producto_id
                where v.tienda_id = :tienda_id
                group by p.nombre
                order by ingreso_neto desc
                limit :n
                """
            ),
            conn,
            params={"tienda_id": tienda_id, "n": n},
        )


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


def stock_actual_producto(tienda_id: str, nombre: str) -> int | None:
    """Stock actual de un producto puntual, para mostrar al elegirlo en Cargar Venta.
    None si el producto todavía no tiene compras/ventas registradas."""
    df = stock_actual(tienda_id)
    fila = df[df["producto"] == nombre]
    return int(fila["stock_actual"].iloc[0]) if not fila.empty else None
