"""Build the CI test matrix from the files a change touches.

Reads changed file paths from stdin, one per line, or tests every package
when called with --all. Prints GitHub Actions outputs to stdout.
"""

import fnmatch
import json
import sys

PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]
LOWEST_PYTHON_VERSION = PYTHON_VERSIONS[0]
PACKAGES = [
    "functions",
    "realtime",
    "storage",
    "auth",
    "postgrest",
    "supabase",
    "utils",
]
PACKAGES_WITHOUT_COVERAGE = {"utils"}
IMPORT_NAMES = {
    "functions": "supabase_functions",
    "realtime": "realtime",
    "storage": "storage3",
    "auth": "supabase_auth",
    "postgrest": "postgrest",
    "supabase": "supabase",
    "utils": "supabase_utils",
}
DEPENDENTS = {
    "utils": set(PACKAGES),
    "functions": {"supabase"},
    "realtime": {"supabase"},
    "storage": {"supabase"},
    "auth": {"supabase"},
    "postgrest": {"supabase"},
    "supabase": set(),
}
IGNORED_PATTERNS = [
    "*.md",
    ".devcontainer/*",
    ".github/*",
    "LICENSE",
    "sdk-compliance.yaml",
    "release-please-config.json",
    ".release-please-manifest.json",
]
ALWAYS_TEST_ALL_PATTERNS = [".github/workflows/ci.yml", ".github/scripts/ci_matrix.py"]


def affected_packages(paths: list[str]) -> set[str]:
    affected: set[str] = set()
    for path in paths:
        if any(fnmatch.fnmatch(path, pattern) for pattern in ALWAYS_TEST_ALL_PATTERNS):
            return set(PACKAGES)
        if any(fnmatch.fnmatch(path, pattern) for pattern in IGNORED_PATTERNS):
            continue
        parts = path.split("/")
        if len(parts) > 2 and parts[0] == "src" and parts[1] in DEPENDENTS:
            affected.add(parts[1])
            affected |= DEPENDENTS[parts[1]]
        else:
            return set(PACKAGES)
    return affected


def flag_name(entry: dict[str, str]) -> str:
    return f"{entry['package']}-py{entry['python-version']}-{entry['resolution']}"


def matrix_entry(version: str, package: str, resolution: str) -> dict[str, str]:
    return {
        "python-version": version,
        "package": package,
        "import-name": IMPORT_NAMES[package],
        "resolution": resolution,
    }


def matrix_entries(packages: set[str]) -> list[dict[str, str]]:
    ordered = [package for package in PACKAGES if package in packages]
    entries = [
        matrix_entry(version, package, "highest")
        for version in PYTHON_VERSIONS
        for package in ordered
    ]
    entries += [
        matrix_entry(LOWEST_PYTHON_VERSION, package, "lowest-direct")
        for package in ordered
    ]
    return entries


def main() -> None:
    if "--all" in sys.argv[1:]:
        packages = set(PACKAGES)
    else:
        packages = affected_packages(
            [line.strip() for line in sys.stdin if line.strip()]
        )
    entries = matrix_entries(packages)
    coverage_flags = [
        flag_name(entry)
        for entry in matrix_entries(set(PACKAGES))
        if entry["package"] not in PACKAGES_WITHOUT_COVERAGE
    ]
    print(f"matrix={json.dumps({'include': entries})}")
    print(f"has-tests={'true' if entries else 'false'}")
    print(f"coverage-flags={','.join(coverage_flags)}")


if __name__ == "__main__":
    main()
