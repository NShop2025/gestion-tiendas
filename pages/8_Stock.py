import streamlit as st
from app.services.config import cargar_config

from app.services.auth import requerir_login
from app.services.reportes import stock_actual
from app.services.tiendas import selector_tienda

cargar_config()

usuario = requerir_login()
tienda_id, tienda_nombre = selector_tienda()

st.title(f"Stock — {tienda_nombre}")

df = stock_actual(tienda_id)
if df.empty:
    st.info("Todavía no hay productos cargados.")
    st.stop()

with st.expander("⚠️ Productos con poco stock (para reponerle al proveedor)", expanded=True):
    umbral = st.number_input(
        "Avisar cuando el stock sea menor o igual a", min_value=1, step=1, value=5
    )
    bajo_stock = df[(df["stock_actual"] > 0) & (df["stock_actual"] <= umbral)].sort_values("stock_actual")
    if bajo_stock.empty:
        st.caption("Ningún producto está por debajo de ese umbral.")
    else:
        st.dataframe(
            bajo_stock.rename(
                columns={
                    "producto": "Producto",
                    "total_comprado": "Comprado",
                    "total_vendido": "Vendido",
                    "stock_actual": "Stock actual",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

buscar = st.text_input("Buscar producto")
df_filtrado = df[df["producto"].str.contains(buscar, case=False, na=False)] if buscar else df

st.dataframe(
    df_filtrado.rename(
        columns={
            "producto": "Producto",
            "total_comprado": "Comprado",
            "total_vendido": "Vendido",
            "stock_actual": "Stock actual",
        }
    ),
    use_container_width=True,
    hide_index=True,
)
