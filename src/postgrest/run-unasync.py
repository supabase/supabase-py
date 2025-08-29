import unasync
from pathlib import Path

paths = Path("src/supabase").glob("**/*.py")
tests = Path("tests").glob("**/*.py")

rules = (unasync._DEFAULT_RULE,)

files = [str(p) for p in list(paths) + list(tests)]

if __name__ == "__main__":
    unasync.unasync_files(files, rules=rules)
