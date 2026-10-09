# Final Fix Report — FastAPI Realtime Rule Engine

## Fix 1 (Critical): engine.py — hardcoded watch_column

**Status: Applied**

Changed the rule evaluation condition in `engine.py` from hardcoded `watch_column == "status"` to dynamically look up the actual column value in the record:

```python
# Before
if (
    rule["watch_column"] == "status"
    and rule["watch_value"] == new_record.get("status")
):

# After
if new_record.get(rule["watch_column"]) == rule["watch_value"]:
```

New test added: `test_rule_with_non_status_column_fires` in `tests/test_engine.py` — verifies a rule watching `title == "urgent"` fires correctly.

---

## Fix 2 (Important): supabase/migrations/001_initial.sql — tasks_update missing WITH CHECK

**Status: Applied**

Added `WITH CHECK` constraint to the `tasks_update` RLS policy so users cannot reassign tasks to other users via an UPDATE:

```sql
CREATE POLICY "tasks_update" ON tasks
    FOR UPDATE TO authenticated
    USING (assigned_to = auth.uid())
    WITH CHECK (assigned_to = auth.uid());
```

---

## Fix 3 (Important): dependencies.py — empty Bearer token passes validation

**Status: Applied**

Added a guard after `removeprefix` to reject `"Bearer "` (with no token):

```python
token = auth.removeprefix("Bearer ")
if not token:
    raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
```

New test added: `test_get_client_raises_401_for_bearer_with_no_token` in `tests/test_dependencies.py`.

---

## Fix 4 (Important): templates — XSS via innerHTML with user data

**Status: Applied**

`templates/index.html` — replaced `innerHTML` template literal in the `rule_fired` broadcast handler with safe DOM construction using `textContent` for all user-controlled strings (`payload.rule.label`, `payload.task.title`).

`templates/rules.html` — replaced the `innerHTML`/`map` pattern in `loadRules()` with a new `renderRules()` helper that builds DOM nodes safely using `textContent` for all rule fields (`r.label`, `r.watch_column`, `r.watch_value`, `r.broadcast_channel`). The `onclick="deleteRule('${r.id}')"` attribute injection was replaced with `addEventListener('click', ...)`.

---

## Fix 5 (Important): routers/auth.py — signout is a no-op

**Status: Applied**

`POST /auth/signout` now calls `client.auth.sign_out()` server-side with best-effort error handling. Added comment explaining that the access JWT remains valid until natural expiry (~1 hour) even after revocation.

---

## Fix 6 (Minor): README Python version

**Status: Applied**

Changed "Python 3.9+" to "Python 3.10+" in the Prerequisites section of `README.md` to match `pyproject.toml`'s `requires-python = ">=3.10"`.

---

## Test Results

```
26 passed, 1 warning in 0.31s
```

All 26 tests pass (up from 24 before this session — 2 new tests added for Fix 1 and Fix 3).

| Test file              | Count |
|------------------------|-------|
| test_auth.py           | 3     |
| test_dependencies.py   | 4     |
| test_engine.py         | 4     |
| test_health.py         | 1     |
| test_migration.py      | 3     |
| test_rules.py          | 5     |
| test_tasks.py          | 6     |
| **Total**              | **26**|

---

## Commit

See git log for commit hash after this report is committed.
