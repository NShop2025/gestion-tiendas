insert into tiendas (nombre, slug) values
    ('NeptunoShop', 'neptunoshop'),
    ('Marea Boutique', 'marea')
on conflict (nombre) do nothing;
