# Gestión Tiendas

App para reemplazar el Excel de control financiero de NeptunoShop y Marea Boutique:
ventas, compras, gastos, retiros y envíos, multi-tienda.

## Puesta en marcha

1. Crear proyecto en [Supabase](https://supabase.com) (plan gratis).
2. Copiar `.env.example` a `.env` y completar `DATABASE_URL` con el connection string
   de Supabase (Project Settings → Database → Connection string).
3. Definir `APP_USERS` en `.env` con tu usuario y el de Facu, ej: `nacho:clave1,facu:clave2`.
4. Instalar dependencias: `pip install -r requirements.txt`
5. Aplicar el schema en Supabase (SQL Editor, en orden):
   - `db/migrations/001_schema.sql`
   - `db/migrations/002_seed_tiendas.sql`
6. Reconciliar el stock negativo del Excel actual antes de migrar histórico
   (ver `Stock_negativo_revisar.xlsx`).
7. Migrar el histórico de NeptunoShop:
   ```
   python scripts/migrar_excel.py "C:/ruta/a/Libro.xlsx" --tienda neptunoshop --dry-run
   python scripts/migrar_excel.py "C:/ruta/a/Libro.xlsx" --tienda neptunoshop
   ```
8. Correr la app: `streamlit run app.py`

Cuando arranquen a vender en Marea, los datos van a la misma base con
`--tienda marea` (ya está sembrada en `002_seed_tiendas.sql`); no hace falta
tocar el schema. Para agregar otra tienda a futuro, solo se inserta una fila más
en la tabla `tiendas`.
