-- The functions of the typed rpc tests: one that returns a set of rows, one
-- that returns a single row and one that returns a scalar, all over the
-- books of the typed API migration.

create function public.books_with_pages(min_pages int4 default 0)
    returns setof public.books
    language sql
    stable
as $function$
    select * from public.books where pages >= min_pages;
$function$;

create function public.book_by_id(book_id int8)
    returns public.books
    language sql
    stable
as $function$
    select * from public.books where id = book_id;
$function$;

create function public.book_title(book_id int8)
    returns text
    language sql
    stable
as $function$
    select title from public.books where id = book_id;
$function$;

grant execute on function public.books_with_pages(int4) to anon;
grant execute on function public.book_by_id(int8) to anon;
grant execute on function public.book_title(int8) to anon;
