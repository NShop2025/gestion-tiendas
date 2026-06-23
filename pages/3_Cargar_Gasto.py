from datetime import date

import streamlit as st
from app.services.config import cargar_config
from sqlalchemy import text

from app.services.auth import requerir_login
from app.services.cuentas import CUENTAS
from app.services.db import get_engine
from app.services.eliminar import panel_eliminar
from app.services.gastos import CATEGORIAS_GASTO
from app.services.reportes import buscar_gastos, ultimos_gastos
from app.services.tiendas import selector_tienda

cargar_config()

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Cargar gasto — {tienda_nombre}")
st.caption("Gastos varios (packing, bolsas, etc.) que se descuentan de la cuenta elegida.")

def _buscar_gastos_con_etiqueta(tienda_id, desde, hasta, texto):
    df = buscar_gastos(tienda_id, desde, hasta, texto)
    if not df.empty:
        df["categoria"] = df["categoria"].map(CATEGORIAS_GASTO)
        df["cuenta"] = df["cuenta"].map(CUENTAS)
    return df


with st.form("cargar_gasto"):
    c1, c2 = st.columns(2)
    fecha = c1.date_input("Fecha", value=date.today())
    cuenta = c2.selectbox("Cuenta", list(CUENTAS.keys()), format_func=lambda k: CUENTAS[k])

    categoria = st.selectbox(
        "Categoría",
        options=list(CATEGORIAS_GASTO.keys()),
        format_func=lambda k: CATEGORIAS_GASTO[k],
    )
    concepto = st.text_input("Concepto (detalle dentro de la categoría)")
    monto = st.number_input("Monto", min_value=0.0, step=1.0)
    comentario = st.text_input("Comentario (opcional)")

    enviado = st.form_submit_button("Guardar gasto")

if enviado:
    if not concepto.strip():
        st.error("Falta el concepto.")
        st.stop()

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into gastos (tienda_id, fecha, concepto, monto, cuenta, categoria, comentario)
                values (:tienda_id, :fecha, :concepto, :monto, :cuenta, :categoria, :comentario)
                """
            ),
            {
                "tienda_id": tienda_id,
                "fecha": fecha,
                "concepto": concepto,
                "monto": monto,
                "cuenta": cuenta,
                "categoria": categoria,
                "comentario": comentario or None,
            },
        )

    ultimos_gastos.clear()
    st.success("Gasto guardado.")

st.divider()
st.subheader("🗂️ Historial")

with st.expander("🕒 Últimos gastos cargados (para ver dónde quedó el último que cargó)", expanded=False):
    df_ultimos = ultimos_gastos(tienda_id)
    if df_ultimos.empty:
        st.caption("Todavía no hay gastos cargados.")
    else:
        st.dataframe(
            df_ultimos.assign(
                categoria=df_ultimos["categoria"].map(CATEGORIAS_GASTO),
                cuenta=df_ultimos["cuenta"].map(CUENTAS),
            ).rename(
                columns={
                    "fecha": "Fecha",
                    "categoria": "Categoría",
                    "concepto": "Concepto",
                    "monto": "Monto",
                    "cuenta": "Cuenta",
                    "comentario": "Comentario",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

panel_eliminar(
    tienda_id=tienda_id,
    tabla="gastos",
    buscar_fn=_buscar_gastos_con_etiqueta,
    columnas={
        "fecha": "Fecha",
        "categoria": "Categoría",
        "concepto": "Concepto",
        "monto": "Monto",
        "cuenta": "Cuenta",
        "comentario": "Comentario",
    },
    key="gastos",
    limpiar_cache=(ultimos_gastos,),
)
