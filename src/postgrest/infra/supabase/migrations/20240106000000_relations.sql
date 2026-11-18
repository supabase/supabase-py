-- Two tables joined by a foreign key, for the embedded relations of the
-- typed query builder. A novel without an author and an author without a
-- novel cover the rows an inner join drops.

create table public.authors (
    id int8 primary key,
    name text not null,
    born_on date
);

create table public.novels (
    id int8 primary key,
    title text not null,
    author_id int8 references public.authors
);

insert into public.authors (id, name, born_on) values
    (1, 'Frank Herbert', '1920-10-08'),
    (2, 'William Gibson', '1948-03-17'),
    (3, 'Nobody', null);

insert into public.novels (id, title, author_id) values
    (1, 'Dune', 1),
    (2, 'Dune Messiah', 1),
    (3, 'Neuromancer', 2),
    (4, 'Anonymous', null);

grant select on public.authors to anon;
grant select, delete on public.novels to anon;
