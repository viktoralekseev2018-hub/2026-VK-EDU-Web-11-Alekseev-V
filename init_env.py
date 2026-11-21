"""Создать конфигурации для разработки из .env.example."""
from pathlib import Path
from secrets import token_urlsafe

root = Path(__file__).resolve().parent
example = (root / ".env.example").read_text(encoding="utf-8")
local = root / ".env.local"
docker = root / ".env.docker"
if local.exists() or docker.exists():
    raise SystemExit("Конфигурация уже существует. Для изменений откройте файлы .env вручную.")

config = example.replace("DJANGO_SECRET_KEY=\n", f"DJANGO_SECRET_KEY={token_urlsafe(48)}\n")
config = config.replace("POSTGRES_PASSWORD=\n", f"POSTGRES_PASSWORD={token_urlsafe(32)}\n")
local.write_text(config, encoding="utf-8")
docker.write_text(config.replace("POSTGRES_HOST=127.0.0.1", "POSTGRES_HOST=db"), encoding="utf-8")
print("Созданы .env.local и .env.docker.")
