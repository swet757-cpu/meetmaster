#!/bin/sh
set -eu

python - <<'PY'
import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine


async def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    for attempt in range(1, 61):
        engine = create_async_engine(database_url)
        try:
            async with engine.connect():
                return
        except Exception as exc:
            if attempt == 60:
                raise
            print(f"Database is not ready yet ({attempt}/60): {exc}")
            await asyncio.sleep(2)
        finally:
            await engine.dispose()


asyncio.run(main())
PY

alembic upgrade head

exec "$@"
