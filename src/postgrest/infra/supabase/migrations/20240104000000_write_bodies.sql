-- A table with the column types the Insert and Update TypedDicts of
-- `supabase gen types --lang python` carry as Python objects, for the tests
-- of the bodies the string builder sends. The tests write rows with random
-- ids and delete them.

create table public.files (
    id uuid primary key,
    name text not null,
    content bytea,
    uploaded_at timestamptz,
    uploaded_on date
);

grant select, insert, update, delete on public.files to anon;
