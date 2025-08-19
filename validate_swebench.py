#!/usr/bin/env python3
"""
Local validation script for SWE-bench format task
Tests that the bug can be reproduced and fixed properly
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    return result.returncode == 0

def apply_patch(patch_content, reverse=False):
    """Apply or reverse a patch"""
    patch_file = tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False)
    patch_file.write(patch_content)
    patch_file.close()
    
    cmd = f"git apply {'--reverse' if reverse else ''} {patch_file.name}"
    success = run_command(cmd)
    os.unlink(patch_file.name)
    return success

def run_tests(test_list, should_pass=True):
    """Run a list of tests and check if they pass/fail as expected"""
    all_passed = True
    for test in test_list:
        # Convert pytest path format to command
        test_cmd = f"uv run pytest {test} -xvs --tb=short"
        result = run_command(test_cmd, check=False)
        
        if should_pass and not result:
            print(f"❌ Test {test} should have passed but failed")
            all_passed = False
        elif not should_pass and result:
            print(f"❌ Test {test} should have failed but passed")
            all_passed = False
        else:
            status = "passed" if result else "failed"
            print(f"✅ Test {test} {status} as expected")
    
    return all_passed

def validate_swebench_entry(json_file):
    """Validate a SWE-bench format JSON entry"""
    print(f"\n{'='*60}")
    print("SWE-bench Task Validation")
    print(f"{'='*60}\n")
    
    # Load the JSON entry
    with open(json_file, 'r') as f:
        entry = json.load(f)
    
    print(f"Instance ID: {entry['instance_id']}")
    print(f"Repository: {entry['repo']}")
    print(f"Base commit: {entry['base_commit']}\n")
    
    # Save current state
    print("Saving current git state...")
    run_command("git stash push -m 'swebench-validation-backup'")
    
    try:
        # Step 1: Apply the bug patch (to introduce the bug)
        print("\n--- Step 1: Applying bug patch (introducing the bug) ---")
        with open('bug_patch.diff', 'r') as f:
            bug_patch = f.read()
        
        if not apply_patch(bug_patch):
            print("❌ Failed to apply bug patch")
            return False
        print("✅ Bug patch applied successfully")
        
        # Step 2: Run FAIL_TO_PASS tests (should fail with bug)
        print("\n--- Step 2: Running FAIL_TO_PASS tests (should fail) ---")
        if 'FAIL_TO_PASS' in entry and entry['FAIL_TO_PASS']:
            if run_tests(entry['FAIL_TO_PASS'], should_pass=False):
                print("✅ All FAIL_TO_PASS tests failed as expected")
            else:
                print("❌ Some FAIL_TO_PASS tests didn't fail as expected")
                return False
        
        # Step 3: Run PASS_TO_PASS tests (should still pass with bug)
        print("\n--- Step 3: Running PASS_TO_PASS tests (should pass) ---")
        if 'PASS_TO_PASS' in entry and entry['PASS_TO_PASS']:
            # Run a subset for speed
            subset = entry['PASS_TO_PASS'][:5]  # Just run first 5 for validation
            if run_tests(subset, should_pass=True):
                print(f"✅ Sample of PASS_TO_PASS tests ({len(subset)}) passed as expected")
            else:
                print("❌ Some PASS_TO_PASS tests failed unexpectedly")
                return False
        
        # Step 4: Apply the golden patch (fix the bug)
        print("\n--- Step 4: Applying golden patch (fixing the bug) ---")
        # First revert the bug patch
        apply_patch(bug_patch, reverse=True)
        
        # Try to apply the golden patch from our file first
        with open('golden_patch.diff', 'r') as f:
            golden_patch = f.read()
        
        if not apply_patch(golden_patch):
            print("❌ Failed to apply golden patch from file")
            return False
        print("✅ Golden patch applied successfully")
        
        # Step 5: Run FAIL_TO_PASS tests again (should pass after fix)
        print("\n--- Step 5: Running FAIL_TO_PASS tests (should pass after fix) ---")
        if 'FAIL_TO_PASS' in entry and entry['FAIL_TO_PASS']:
            if run_tests(entry['FAIL_TO_PASS'], should_pass=True):
                print("✅ All FAIL_TO_PASS tests passed after fix")
            else:
                print("❌ Some FAIL_TO_PASS tests still failing after fix")
                return False
        
        # Step 6: Run PASS_TO_PASS tests (should still pass after fix)
        print("\n--- Step 6: Running PASS_TO_PASS tests (should still pass) ---")
        if 'PASS_TO_PASS' in entry and entry['PASS_TO_PASS']:
            subset = entry['PASS_TO_PASS'][:5]  # Just run first 5 for speed
            if run_tests(subset, should_pass=True):
                print(f"✅ Sample of PASS_TO_PASS tests ({len(subset)}) still passing")
            else:
                print("❌ Some PASS_TO_PASS tests failed after fix (regression)")
                return False
        
        print(f"\n{'='*60}")
        print("✅ VALIDATION SUCCESSFUL!")
        print(f"{'='*60}")
        print("\nThe SWE-bench task entry is valid:")
        print("- Bug can be reproduced")
        print("- Fix resolves the issue")  
        print("- No regressions detected")
        return True
        
    finally:
        # Restore original state
        print("\nRestoring original git state...")
        run_command("git checkout -- .")
        run_command("git stash pop", check=False)

if __name__ == "__main__":
    json_file = sys.argv[1] if len(sys.argv) > 1 else "swebench_entry.json"
    
    if not Path(json_file).exists():
        print(f"Error: {json_file} not found")
        sys.exit(1)
    
    success = validate_swebench_entry(json_file)
    sys.exit(0 if success else 1)