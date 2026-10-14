import os

ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")


def load_env(path=ENV_FILE):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def gurobi_params():
    load_env()
    params = {}
    for key in ("WLSACCESSID", "WLSSECRET", "LICENSEID"):
        value = os.environ.get("GUROBI_" + key)
        if value:
            params[key] = int(value) if key == "LICENSEID" else value
    return params
