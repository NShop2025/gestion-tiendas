-- Categoría fija para gastos, separada del texto libre "concepto", para poder sumar
-- cuánto se gasta por tipo (BPS, publicidad, etc.) sin depender de cómo cada uno tipeó
-- el concepto. concepto sigue existiendo como el detalle dentro de la categoría.

create type categoria_gasto as enum (
    'bps_impuestos',
    'publicidad',
    'packing_insumos',
    'contabilidad_software',
    'combustible_viaticos',
    'envios_cadeteria',
    'otros'
);

alter table gastos
    add column categoria categoria_gasto not null default 'otros';

alter table gastos
    alter column categoria drop default;
