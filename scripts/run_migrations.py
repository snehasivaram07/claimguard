import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


def run_migrations():
    """Programmatically run Alembic migrations up to head."""
    alembic_ini_path = backend_dir / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    command.upgrade(alembic_cfg, "head")
    print("Database migrations applied successfully.")


if __name__ == "__main__":
    run_migrations()
