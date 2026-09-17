import os
from pathlib import Path

from dotenv import find_dotenv

ENV_PATH = Path(
    os.getenv("ENV_FILE")
    or find_dotenv()
    or (Path(__file__).resolve().parent.parent.parent / ".env")
)


def ensure_env_file() -> None:
    ENV_PATH.touch(exist_ok=True)


def read_env() -> dict[str, str]:
    result: dict[str, str] = {}
    ensure_env_file()
    for raw_line in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def write_env(env: dict[str, str]) -> None:
    ensure_env_file()
    lines = ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    written: set[str] = set()
    output: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        key = line.partition("=")[0].strip() if "=" in line and not line.startswith("#") else None
        if key in env and key not in written:
            output.append(f"{key}={env[key]}")
            written.add(key)
        else:
            output.append(raw_line)
    for key, value in env.items():
        if key not in written:
            output.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(output), encoding="utf-8")


def set_env_value(key: str, value: str) -> None:
    env = read_env()
    env[key] = value
    write_env(env)


def add_to_list_env(key: str, item: int) -> None:
    env = read_env()
    items = [int(i) for i in env.get(key, "").split(",") if i.strip().lstrip("-").isdigit()]
    if item not in items:
        items.append(item)
    env[key] = ",".join(str(i) for i in sorted(items))
    write_env(env)


def remove_from_list_env(key: str, item: int) -> None:
    env = read_env()
    items = [int(i) for i in env.get(key, "").split(",") if i.strip().lstrip("-").isdigit()]
    items = [i for i in items if i != item]
    env[key] = ",".join(str(i) for i in sorted(items))
    write_env(env)