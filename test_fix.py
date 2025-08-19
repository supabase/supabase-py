#!/usr/bin/env python3
"""
Test that the fix works
"""

import subprocess

def run_tests(test_list, should_pass=True):
    """Run a list of tests and check if they pass/fail as expected"""
    all_passed = True
    for test in test_list:
        test_cmd = f"uv run pytest {test} -xvs --tb=no"
        result = subprocess.run(test_cmd, shell=True, capture_output=True)
        
        if should_pass and result.returncode != 0:
            print(f"❌ Test {test} should have passed but failed")
            all_passed = False
        elif not should_pass and result.returncode == 0:
            print(f"❌ Test {test} should have failed but passed")
            all_passed = False
        else:
            status = "passed" if result.returncode == 0 else "failed"
            print(f"✅ Test {test} {status} as expected")
    
    return all_passed

def main():
    print("Testing fix state")
    print("="*30)
    
    # FAIL_TO_PASS tests should now pass
    print("\n--- Testing FAIL_TO_PASS tests (should pass after fix) ---")
    fail_to_pass_tests = [
        "tests/_sync/test_client.py::test_custom_headers",
        "tests/_sync/test_client.py::test_custom_headers_immutable",
        "tests/_async/test_client.py::test_custom_headers",
        "tests/_async/test_client.py::test_custom_headers_immutable"
    ]
    
    if run_tests(fail_to_pass_tests, should_pass=True):
        print("✅ Fix confirmed: FAIL_TO_PASS tests now pass")
    else:
        print("❌ Fix not working")
        return False
    
    # PASS_TO_PASS tests should still pass
    print("\n--- Testing PASS_TO_PASS tests (should still pass) ---")
    pass_to_pass_tests = [
        "tests/_sync/test_client.py::test_supabase_exception",
        "tests/_sync/test_client.py::test_postgrest_client",
        "tests/_sync/test_client.py::test_function_initialization"
    ]
    
    if run_tests(pass_to_pass_tests, should_pass=True):
        print("✅ No regressions after fix")
    else:
        print("❌ Regressions detected after fix")
        return False
    
    print(f"\n{'='*30}")
    print("✅ FIX VALIDATED!")
    return True

if __name__ == "__main__":
    main()