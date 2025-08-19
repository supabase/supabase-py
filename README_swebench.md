# SWE-bench Task: Custom Headers Bug

## Overview
Successfully created and validated a SWE-bench format task based on a real bug from the supabase-py repository.

## Files Created

### Core Task Files
- **`swebench_entry.json`** - Complete SWE-bench format JSON entry
- **`issue_description.md`** - Detailed issue description  
- **`bug_patch.diff`** - Patch that introduces the bug
- **`golden_patch.diff`** - Patch that fixes the bug

### Test Lists
- **`fail_to_pass_tests.txt`** - Tests that fail with bug, pass after fix
- **`pass_to_pass_tests.txt`** - Regression tests that should always pass

### Validation Scripts
- **`validate_swebench.py`** - Full SWE-bench validation with git patches
- **`simple_validate.py`** - Simple validation of bug state
- **`test_fix.py`** - Validation of fix state

## The Bug
**Issue**: Custom headers passed to `ClientOptions` are completely overwritten instead of merged with auth headers.

**Root Cause**: 
```python
# BUGGY (overwrites custom headers)
self.options.headers = copy.copy(self._get_auth_headers())

# FIXED (merges custom headers with auth headers)  
self.options.headers = {
    **options.headers,
    **self._get_auth_headers(),
}
```

**Impact**: Users cannot set custom headers like `x-app-name`, `x-version`, etc.

## Test Results

### Bug State Validation ✅
When bug is present:
- ✅ 4 FAIL_TO_PASS tests fail as expected
- ✅ Core functionality tests still pass (no unrelated breakage)

### Fix State Validation ✅  
When fix is applied:
- ✅ 4 FAIL_TO_PASS tests now pass
- ✅ Core functionality tests still pass (no regressions)

## Usage

### Validate Bug State
```bash
# Apply bug and test
python simple_validate.py
```

### Validate Fix State  
```bash
# With fix applied (current state)
python test_fix.py
```

### Full SWE-bench Validation
```bash
# Complete workflow with git patches
python validate_swebench.py swebench_entry.json
```

## SWE-bench Integration
The `swebench_entry.json` follows the standard SWE-bench format and can be:
1. Added to SWE-bench dataset
2. Used with SWE-bench evaluation harness
3. Validated with official tools

## Key Metrics
- **Instance ID**: `supabase__supabase-py-1155`
- **Repository**: `supabase/supabase-py`  
- **Test Runtime**: <1 second per test
- **Total Validation Time**: <30 seconds
- **FAIL_TO_PASS Tests**: 4 tests
- **PASS_TO_PASS Tests**: 22 tests