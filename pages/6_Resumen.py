import altair as alt
import pandas as pd
import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.formato import fmt_money, fmt_money_delta, tarjeta_metrica
from app.services.gastos import CATEGORIAS_GASTO
from app.services.reportes import (
    gastos_por_categoria,
    metricas_generales,
    productos_a_reponer,
    resumen_mensual,
    saldo_disponible,
    top_productos,
    ventas_por_canal,
)
from app.services.tiendas import selector_tienda

cargar_config()

usuario = requerir_login()
# mostrar_saldo=False: esta página ya tiene su propia tarjeta de saldo grande más abajo,
# repetirla en la sidebar sería redundante.
tienda_id, tienda_nombre = selector_tienda(mostrar_saldo=False)

df_reponer = productos_a_reponer(tienda_id)
if not df_reponer.empty:
    with st.expander(
        f"🔥 {len(df_reponer)} producto(s) que se venden bien y se están quedando sin stock",
        expanded=True,
    ):
        st.caption("Vendieron varias unidades en los últimos 30 días y les queda muy poco stock.")
        st.dataframe(
            df_reponer.rename(
                columns={"producto": "Producto", "vendido": "Vendido (30 días)", "stock_actual": "Stock actual"}
            ),
            use_container_width=True,
            hide_index=True,
        )

st.title(f"Resumen — {tienda_nombre}")

saldo = saldo_disponible(tienda_id)
m = metricas_generales(tienda_id)

# Tarjeta principal: saldo disponible, destacado.
color = "#34D399" if saldo >= 0 else "#F87171"
st.markdown(
    f"""
    <div style="padding: 1.6rem 1.8rem; border-radius: 16px; margin-bottom: 1.4rem;
        background: linear-gradient(135deg, #1E2230 0%, #14171F 100%);
        border: 1px solid #2A2F3C;">
        <div style="font-size: 0.8rem; letter-spacing: 0.05em; text-transform: uppercase;
                    color: #8A90A0;">Saldo disponible (Mercado Pago)</div>
        <div style="font-size: 2.6rem; font-weight: 700; color: {color}; line-height: 1.2;">
            {fmt_money(saldo)}</div>
        <div style="font-size: 0.8rem; color: #6B7180; margin-top: 0.3rem;">
            Toda la plata de la tienda en una sola caja</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Métricas históricas (totales de toda la vida de la tienda).
c1, c2, c3, c4 = st.columns(4)
c1.markdown(tarjeta_metrica("Ingreso neto total", fmt_money(m["ingreso_neto"])), unsafe_allow_html=True)
c2.markdown(tarjeta_metrica("Ganancia total", fmt_money(m["ganancia"])), unsafe_allow_html=True)
c3.markdown(tarjeta_metrica("Mercadería comprada", fmt_money(m["compras"])), unsafe_allow_html=True)
c4.markdown(tarjeta_metrica("Retiros de socios", fmt_money(m["retiros"])), unsafe_allow_html=True)
st.write("")

df_mensual = resumen_mensual(tienda_id)

tab_general, tab_mensual, tab_productos, tab_gastos = st.tabs(
    ["📊 General", "📅 Mensual", "🏆 Productos", "💸 Gastos por categoría"]
)

with tab_general:
    if df_mensual.empty:
        st.info("Todavía no hay datos cargados.")
    else:
        df_mensual = df_mensual.sort_values("mes")
        df_mensual["mes"] = pd.to_datetime(df_mensual["mes"])

        # Mes actual vs mes anterior, para dar contexto de tendencia inmediata.
        if len(df_mensual) >= 2:
            actual, anterior = df_mensual.iloc[-1], df_mensual.iloc[-2]
            st.caption(
                f"Comparado contra {anterior['mes'].strftime('%B %Y')} — si el mes en curso no "
                "terminó, esta comparación todavía no es 1 a 1."
            )
            d1, d2, d3 = st.columns(3)
            d1.metric(
                "Ventas brutas (mes actual)",
                fmt_money(actual["ventas_brutas"]),
                delta=fmt_money_delta(actual["ventas_brutas"] - anterior["ventas_brutas"]),
            )
            d2.metric(
                "Ganancia (mes actual)",
                fmt_money(actual["ganancia"]),
                delta=fmt_money_delta(actual["ganancia"] - anterior["ganancia"]),
            )
            margen_actual = actual["ganancia"] / actual["ventas_brutas"] * 100 if actual["ventas_brutas"] else 0
            margen_anterior = (
                anterior["ganancia"] / anterior["ventas_brutas"] * 100 if anterior["ventas_brutas"] else 0
            )
            d3.metric(
                "Margen de ganancia (mes actual)",
                f"{margen_actual:.1f}%",
                delta=f"{margen_actual - margen_anterior:.1f} pp",
            )
            st.divider()

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Ganancia por mes")
            df_chart = df_mensual[["mes", "ganancia"]].copy()
            df_chart["ganancia"] = df_chart["ganancia"].round(0)
            df_chart["Mes"] = df_chart["mes"].dt.strftime("%b %Y")
            df_chart["Ganancia"] = df_chart["ganancia"].map(fmt_money)

            chart = (
                alt.Chart(df_chart)
                .mark_bar(color="#6366F1", cornerRadiusTopLeft=3, cornerRadiusTopRight=3, size=18)
                .encode(
                    x=alt.X("mes:T", title=None, axis=alt.Axis(format="%b %y")),
                    y=alt.Y("ganancia:Q", title=None),
                    tooltip=[
                        alt.Tooltip("Mes:N", title="Mes"),
                        alt.Tooltip("Ganancia:N", title="Ganancia"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(chart, use_container_width=True)

        with col_b:
            st.subheader("Ventas por canal")
            df_canal = ventas_por_canal(tienda_id)
            if df_canal.empty:
                st.caption("Todavía no hay ventas cargadas.")
            else:
                etiquetas_canal = {"mercado_libre": "Mercado Libre", "web": "Web", "otro": "Otro"}
                df_canal["Canal"] = df_canal["canal"].map(etiquetas_canal).fillna(df_canal["canal"])
                df_canal["Ingreso fmt"] = df_canal["ingreso_neto"].map(fmt_money)

                chart_canal = (
                    alt.Chart(df_canal)
                    .mark_arc(innerRadius=60)
                    .encode(
                        theta=alt.Theta("ingreso_neto:Q", title=None),
                        color=alt.Color(
                            "Canal:N", title=None, scale=alt.Scale(range=["#6366F1", "#34D399", "#F59E0B"])
                        ),
                        tooltip=[
                            alt.Tooltip("Canal:N", title="Canal"),
                            alt.Tooltip("Ingreso fmt:N", title="Ingreso neto"),
                            alt.Tooltip("cantidad_ventas:Q", title="Cantidad de ventas"),
                        ],
                    )
                    .properties(height=300)
                )
                st.altair_chart(chart_canal, use_container_width=True)

with tab_mensual:
    if df_mensual.empty:
        st.info("Todavía no hay datos cargados.")
    else:
        df_mostrar = pd.DataFrame({"Mes": df_mensual["mes"].dt.strftime("%b %Y")})
        columnas = {
            "ventas_brutas": "Ventas brutas",
            "costo_mercaderia_vendida": "Costo mercadería vendida",
            "gastos_envios": "Gastos de envíos",
            "gastos_varios": "Gastos varios",
            "ganancia": "Ganancia",
            "retiros": "Retiros",
            "saldo_final": "Saldo final",
            "mercaderia_comprada": "Mercadería comprada",
        }
        for col, titulo in columnas.items():
            if col in df_mensual.columns:
                df_mostrar[titulo] = df_mensual[col].map(fmt_money)

        # Pinta en rojo las celdas cuyo valor numérico original es negativo (ej. un mes con
        # más retiros que ganancia), para que salte a la vista sin tener que leer cada número.
        def _texto_negativos(_):
            estilos = pd.DataFrame("", index=df_mostrar.index, columns=df_mostrar.columns)
            for col, titulo in columnas.items():
                if titulo in estilos.columns and col in df_mensual.columns:
                    estilos.loc[df_mensual[col] < 0, titulo] = "color: #F87171"
            return estilos

        st.dataframe(
            df_mostrar.style.apply(_texto_negativos, axis=None), use_container_width=True, hide_index=True
        )

        df_chart = df_mensual[["mes", "ganancia", "ventas_brutas"]].copy()
        df_largo = df_chart.melt("mes", var_name="serie", value_name="monto")
        df_largo["serie"] = df_largo["serie"].map({"ganancia": "Ganancia", "ventas_brutas": "Ventas brutas"})
        df_largo["Mes"] = df_largo["mes"].dt.strftime("%b %Y")
        df_largo["Monto"] = df_largo["monto"].map(fmt_money)

        chart = (
            alt.Chart(df_largo)
            .mark_line(point=True)
            .encode(
                x=alt.X("mes:T", title=None, axis=alt.Axis(format="%b %y")),
                y=alt.Y("monto:Q", title=None),
                color=alt.Color("serie:N", title=None, scale=alt.Scale(range=["#6366F1", "#34D399"])),
                tooltip=[
                    alt.Tooltip("serie:N", title=""),
                    alt.Tooltip("Mes:N", title="Mes"),
                    alt.Tooltip("Monto:N", title="Monto"),
                ],
            )
            .properties(height=320)
        )
        st.altair_chart(chart, use_container_width=True)

with tab_productos:
    df_top = top_productos(tienda_id)
    if df_top.empty:
        st.info("Todavía no hay ventas cargadas.")
    else:
        st.caption("Top 10 productos por ingreso neto histórico.")
        col_a, col_b = st.columns([1, 1])

        with col_a:
            df_mostrar = df_top.rename(
                columns={
                    "producto": "Producto",
                    "cantidad_vendida": "Cantidad vendida",
                    "ingreso_neto": "Ingreso neto",
                    "ganancia": "Ganancia",
                }
            )
            df_mostrar["Ingreso neto"] = df_mostrar["Ingreso neto"].map(fmt_money)
            df_mostrar["Ganancia"] = df_mostrar["Ganancia"].map(fmt_money)
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

        with col_b:
            df_chart = df_top.copy()
            df_chart["Ingreso fmt"] = df_chart["ingreso_neto"].map(fmt_money)
            chart = (
                alt.Chart(df_chart)
                .mark_bar(color="#6366F1")
                .encode(
                    x=alt.X("ingreso_neto:Q", title=None),
                    y=alt.Y("producto:N", sort="-x", title=None),
                    tooltip=[
                        alt.Tooltip("producto:N", title="Producto"),
                        alt.Tooltip("Ingreso fmt:N", title="Ingreso neto"),
                        alt.Tooltip("cantidad_vendida:Q", title="Cantidad vendida"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, use_container_width=True)

with tab_gastos:
    df_gastos = gastos_por_categoria(tienda_id)
    if df_gastos.empty:
        st.info("Todavía no hay gastos cargados.")
    else:
        df_gastos["Categoría"] = df_gastos["categoria"].map(CATEGORIAS_GASTO)
        df_gastos = df_gastos.sort_values("total", ascending=False)

        col_a, col_b = st.columns([1, 1])

        with col_a:
            df_mostrar = df_gastos[["Categoría", "cantidad", "total"]].rename(
                columns={"cantidad": "Cantidad de gastos", "total": "Total"}
            )
            df_mostrar["Total"] = df_mostrar["Total"].map(fmt_money)
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

        with col_b:
            df_chart = df_gastos.copy()
            df_chart["Total fmt"] = df_chart["total"].map(fmt_money)
            chart = (
                alt.Chart(df_chart)
                .mark_bar(color="#6366F1")
                .encode(
                    x=alt.X("total:Q", title=None),
                    y=alt.Y("Categoría:N", sort="-x", title=None),
                    tooltip=[
                        alt.Tooltip("Categoría:N", title="Categoría"),
                        alt.Tooltip("Total fmt:N", title="Total"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, use_container_width=True)
