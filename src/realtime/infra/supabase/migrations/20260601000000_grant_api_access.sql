-- Grant API access to tables for anon and authenticated roles.
-- Required since Supabase no longer grants public schema access by default
-- (see https://github.com/orgs/supabase/discussions/45329).
GRANT ALL ON TABLE public.todos TO anon, authenticated;
GRANT ALL ON TABLE public.messages TO anon, authenticated;

-- Grant sequence usage for tables with generated identity primary keys
GRANT USAGE, SELECT ON SEQUENCE public.messages_id_seq TO anon, authenticated;
