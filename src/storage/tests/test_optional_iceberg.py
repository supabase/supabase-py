import subprocess
import sys


def test_import_works_without_pyiceberg() -> None:
    code = (
        "import sys\n"
        "sys.modules['pyiceberg'] = None\n"
        "import storage3\n"
        "import storage3.analytics\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
