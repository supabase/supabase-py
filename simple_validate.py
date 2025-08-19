#!/usr/bin/env python3
"""
Simple validation without git patches
"""

import subprocess
import sys

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
    print("Simple SWE-bench validation test")
    print("="*50)
    
    # Test 1: With current bug state, FAIL_TO_PASS tests should fail
    print("\n--- Testing current state (with bug) ---")
    fail_to_pass_tests = [
        "tests/_sync/test_client.py::test_custom_headers",
        "tests/_sync/test_client.py::test_custom_headers_immutable",
        "tests/_async/test_client.py::test_custom_headers",
        "tests/_async/test_client.py::test_custom_headers_immutable"
    ]
    
    if run_tests(fail_to_pass_tests, should_pass=False):
        print("✅ Bug state confirmed: FAIL_TO_PASS tests fail correctly")
    else:
        print("❌ Bug state not confirmed")
        return False
    
    # Test 2: PASS_TO_PASS tests should still pass even with bug
    print("\n--- Testing regression tests (should pass even with bug) ---")
    pass_to_pass_tests = [
        "tests/_sync/test_client.py::test_supabase_exception",
        "tests/_sync/test_client.py::test_postgrest_client",
        "tests/_sync/test_client.py::test_function_initialization"
    ]
    
    if run_tests(pass_to_pass_tests, should_pass=True):
        print("✅ No regressions: core tests still pass")
    else:
        print("❌ Regressions detected")
        return False
    
    print(f"\n{'='*50}")
    print("✅ VALIDATION SUCCESSFUL!")
    print("The bug is properly isolated and testable")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)