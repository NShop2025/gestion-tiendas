-- Schema inicial: gestión financiera multi-tienda (Neptuno Shop, Marea Boutique, futuras)
-- Pensado para Postgres / Supabase.

create extension if not exists "pgcrypto";

create table tiendas (
    id uuid primary key default gen_random_uuid(),
    nombre text not null unique,
    slug text not null unique,
    activa boolean not null default true,
    creada_en timestamptz not null default now()
);

create table usuarios_app (
    id uuid primary key default gen_random_uuid(),
    nombre text not null,
    email text not null unique,
    creada_en timestamptz not null default now()
);

-- Relación N:N por si en el futuro hay socios distintos por tienda.
create table usuarios_tiendas (
    usuario_id uuid not null references usuarios_app(id) on delete cascade,
    tienda_id uuid not null references tiendas(id) on delete cascade,
    primary key (usuario_id, tienda_id)
);

create table productos (
    id uuid primary key default gen_random_uuid(),
    tienda_id uuid not null references tiendas(id) on delete cascade,
    nombre text not null,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    unique (tienda_id, nombre)
);

create type canal_venta as enum ('mercado_libre', 'web', 'otro');

create table compras (
    id uuid primary key default gen_random_uuid(),
    tienda_id uuid not null references tiendas(id) on delete cascade,
    producto_id uuid not null references productos(id),
    fecha date not null,
    cantidad numeric not null check (cantidad <> 0), -- negativo = devolucion a proveedor
    costo_unitario numeric not null, -- puede ser negativo: credito/reembolso de un proveedor
    costo_total numeric generated always as (cantidad * costo_unitario) stored,
    proveedor_comentario text,
    creado_en timestamptz not null default now()
);

create table ventas (
    id uuid primary key default gen_random_uuid(),
    tienda_id uuid not null references tiendas(id) on delete cascade,
    producto_id uuid not null references productos(id),
    canal canal_venta not null,
    fecha date not null,
    hora time,
    cantidad numeric not null check (cantidad > 0),
    precio_unitario numeric not null check (precio_unitario >= 0),
    ingreso_bruto numeric generated always as (cantidad * precio_unitario) stored,
    comision_ml numeric not null default 0,
    ingreso_envio numeric not null default 0,
    costo_unitario_venta numeric not null default 0, -- snapshot del costo al momento de vender
    comentario text,
    creado_en timestamptz not null default now()
);

create table gastos (
    id uuid primary key default gen_random_uuid(),
    tienda_id uuid not null references tiendas(id) on delete cascade,
    fecha date not null,
    concepto text not null,
    monto numeric not null check (monto >= 0),
    cuenta text not null default 'mercado_pago', -- mercado_pago | santander | otra
    comentario text,
    creado_en timestamptz not null default now()
);

create table retiros (
    id uuid primary key default gen_random_uuid(),
    tienda_id uuid not null references tiendas(id) on delete cascade,
    fecha date not null,
    monto numeric not null check (monto <> 0), -- negativo = reembolso/pago recibido del socio
    socio text not null,
    comentario text,
    creado_en timestamptz not null default now()
);

create table envios (
    id uuid primary key default gen_random_uuid(),
    tienda_id uuid not null references tiendas(id) on delete cascade,
    cuenta text not null default 'mercado_pago', -- mercado_pago | santander
    fecha date not null,
    cadete text not null,
    cantidad_envios numeric not null check (cantidad_envios >= 0),
    costo_unitario numeric not null check (costo_unitario >= 0),
    costo_total numeric generated always as (cantidad_envios * costo_unitario) stored,
    comentario text,
    creado_en timestamptz not null default now()
);

create index on compras (tienda_id, fecha);
create index on ventas (tienda_id, fecha);
create index on gastos (tienda_id, fecha);
create index on retiros (tienda_id, fecha);
create index on envios (tienda_id, fecha);

-- Vista de stock por producto: compras acumuladas - ventas acumuladas.
create view stock_actual as
select
    p.id as producto_id,
    p.tienda_id,
    p.nombre as producto,
    coalesce(c.total_comprado, 0) as total_comprado,
    coalesce(v.total_vendido, 0) as total_vendido,
    coalesce(c.total_comprado, 0) - coalesce(v.total_vendido, 0) as stock_actual
from productos p
left join (
    select producto_id, sum(cantidad) as total_comprado
    from compras
    group by producto_id
) c on c.producto_id = p.id
left join (
    select producto_id, sum(cantidad) as total_vendido
    from ventas
    group by producto_id
) v on v.producto_id = p.id;

-- Ganancia por venta: ingreso neto menos costo de mercadería vendida.
create view ventas_detalle as
select
    v.*,
    (v.ingreso_bruto - v.comision_ml) as ingreso_neto,
    (v.cantidad * v.costo_unitario_venta) as costo_total_venta,
    (v.ingreso_bruto - v.comision_ml + v.ingreso_envio - (v.cantidad * v.costo_unitario_venta)) as ganancia_total
from ventas v;

-- Resumen mensual por tienda: equivalente a la hoja "Resumen mensual" del Excel.
create view resumen_mensual as
select
    tienda_id,
    date_trunc('month', fecha)::date as mes,
    sum(ingreso_bruto) as ventas_brutas,
    sum(costo_total_venta) as costo_mercaderia_vendida,
    sum(ganancia_total) as ganancia
from ventas_detalle
group by tienda_id, date_trunc('month', fecha);
