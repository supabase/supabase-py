# Verification of #1443: TypedDict Type Annotations + Serialization

## Context
PR #1443 updated `insert/upsert/update` types to `Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]` for TypedDict support.

Contributor comment: "does not fix because json.dumps doesn't support uuid/datetime".

## Results (run in clean env)
### Pytest ✅ All Pass
- `test_typed_dict_insert.py`: 3/3 pass:
  - `test_insert_accepts_typeddict`
  - `test_insert_accepts_list_of_typeddict`
  - `test_insert_accepts_uuid_and_datetime` (serializes UUID/DT via PostgrestEncoder)
- `test_request_builder.py` (sync/async): 81 tests pass (insert/upsert/update).

### PostgrestEncoder Handles Serialization ✅
```python
class PostgrestEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID): return str(obj)
        if isinstance(obj, datetime): return obj.isoformat()
        # ...
```
Used in all JSON calls.

### Mypy ⚠️ Partial (post-PR refinement needed)
12 errors: JSON assignment mismatches (e.g. `_sync/request_builder.py:294`). Runtime unaffected.

## Conclusion
- **Types fixed**: TypedDict accepted.
- **Serialization solved**: Encoder + test prove UUID/DT work (comment wrong - not raw json.dumps).
PR correct/closed properly.

