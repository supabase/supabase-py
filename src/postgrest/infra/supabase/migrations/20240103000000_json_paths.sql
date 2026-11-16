create table public.documents (
    id int8 primary key,
    data jsonb
);

insert into public.documents (id, data) values
    (1, '{"a.b": "dotted", "a,b": "comma", "0": "text zero", "items": ["first", "second"]}'),
    (2, '{"a.b": "other", "a,b": "other", "0": "other", "items": ["third"]}');

grant select on public.documents to anon;
