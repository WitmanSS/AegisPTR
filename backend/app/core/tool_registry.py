from app.adapters.nmap.adapter import NmapAdapter
from app.adapters.nuclei.adapter import NucleiAdapter
from app.adapters.zap.adapter import ZAPAdapter


def get_available_adapters() -> dict[str, object]:
    adapters = {
        "nmap": NmapAdapter(),
        "nuclei": NucleiAdapter(),
        "zap": ZAPAdapter(),
    }
    return {name: adapter for name, adapter in adapters.items() if adapter.detect()}
