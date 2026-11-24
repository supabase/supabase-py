# supabase_typegen

Generates the typed tables and functions of a Supabase database for the typed
API of `postgrest` and `supabase`, so a query names its columns through
attributes the type checker knows and reads its rows as pydantic models.

For every table, view and materialized view it generates:

- a `Row` pydantic model, `BooksRow`, the row `select()` reads,
- an `Insert` and an `Update` `TypedDict`, `BooksInsert` and `BooksUpdate`,
  the only values the typed `insert()`, `upsert()` and `update()` accept. A
  key left out of an insert gets the database default, and `None` writes
  `NULL`. Columns the database generates itself are left out. A view gets
  them only when it is insertable or updatable, and a materialized view never,
- a namespace class, `Books`, with a `Column` or `NullableColumn` per column,
  a `ComputedField` per computed field, a `ToOneRelation` or `ToManyRelation`
  per foreign key and computed relationship, and the `Table` that
  `client.table(Books.table)` queries, in its own schema.

Postgres enums become `StrEnum`s and composite types pydantic models. A
`bytea` column reads as `postgrest.Bytea`, `bytes` decoded from the `\x…`
hex text PostgREST sends, and takes plain `bytes` on writes and filters. A
`Functions` class has a static method per function PostgREST exposes, which
takes the arguments as keyword parameters, optional where the function has a
default, and returns the `FunctionCall` that `client.rpc()` runs.

Objects of the `public` schema are named after themselves, `books` becomes
`Books` and `BooksRow`. Objects of any other schema carry the schema as a
prefix, so `inventory.books` becomes `InventoryBooks` and `InventoryBooksRow`.
A name that is a keyword, or that the module uses itself, gets a trailing
underscore, and a column whose attribute differs from its name is sent under
its name.

## Usage

Add `supabase_typegen` as a development dependency of your project, next to
`supabase` or `postgrest`:

```sh
uv add --dev supabase_typegen
```

It reads the `GeneratorMetadata` document of
[`@supabase/postgrest-typegen`](https://github.com/supabase/sdk/tree/main/packages/postgrest-typegen)
on standard input and writes the module to standard output:

```sh
python -m supabase_typegen < generator_metadata.json > supabase_schema.py
```

The Supabase CLI introspects the database into that document, so
`supabase gen types --lang python` runs it in your project once the CLI
supports it. Regenerate the module after every change to the database schema
and commit it. Never edit it by hand.

```python skip
from supabase import Client

from .supabase_schema import Books, BooksInsert, Functions


def recent_books(client: Client) -> None:
    books = (
        client.table(Books.table)
        .select()
        .where(Books.title.like("%Python%") & ~Books.published_on.is_null())
        .order(Books.created_at.desc())
        .limit(10)
        .execute()
    )
    row: BooksInsert = {"title": "A typed row", "author_id": 2}
    client.table(Books.table).insert(row).execute()
    matches = client.rpc(Functions.search_books(query="dune")).execute()
```

## Known limitations

- An optional function argument passed as `None` is left out, so the
  function uses its default. A `NULL` for such an argument can only be sent
  with `client.rpc("name", params)`.
- A model field whose attribute differs from its column name, such as
  `class_` for `class`, is read and written under the column name, which
  type checkers also take as its parameter name. Build such a model from its
  columns: `Address.model_validate({"class": "first"})`.
- A function returning `json`, `jsonb`, a record or rows of a relation that
  is not generated returns `object`.
- `numeric` is `float`, ranges and `interval` are `str`, and arrays assume
  their elements are not `NULL`.
