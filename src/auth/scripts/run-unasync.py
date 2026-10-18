from pathlib import Path

import unasync

paths = Path("src/supabase_auth").glob("**/*.py")
tests = Path("tests").glob("**/*.py")

rules = (
    unasync.Rule(
        fromdir="/_async/",
        todir="/_sync/",
        additional_replacements={
            "AsyncClient": "Client",
            "aclose": "close",
            # asyncio is only used for the Lock in the PKCE verifier store
            "asyncio": "threading",
        },
    ),
    unasync._DEFAULT_RULE,
)

files = [str(p) for p in list(paths) + list(tests)]

if __name__ == "__main__":
    unasync.unasync_files(files, rules=rules)
