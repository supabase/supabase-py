import importlib
import importlib.util
import pkgutil
import sys

if importlib.util.find_spec("httpx") is not None:
    sys.exit("httpx is installed")

skipped = {"httpx"}
if importlib.util.find_spec("aiohttp") is None:
    skipped.add("aiohttp")

package = importlib.import_module(sys.argv[1])
for module in pkgutil.walk_packages(package.__path__, f"{package.__name__}."):
    if module.name.rsplit(".", 1)[-1] not in skipped:
        importlib.import_module(module.name)
