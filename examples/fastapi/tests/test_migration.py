def test_migration_contains_required_tables() -> None:
    with open("supabase/migrations/001_initial.sql") as f:
        sql = f.read()
    assert "CREATE TABLE tasks" in sql
    assert "CREATE TABLE rules" in sql
    assert "CREATE TABLE rule_events" in sql


def test_migration_enables_rls() -> None:
    with open("supabase/migrations/001_initial.sql") as f:
        sql = f.read()
    assert sql.count("ENABLE ROW LEVEL SECURITY") == 3


def test_migration_adds_realtime_publication() -> None:
    with open("supabase/migrations/001_initial.sql") as f:
        sql = f.read()
    assert "supabase_realtime" in sql
    assert "tasks" in sql
