import cProfile
import pstats
import io
import functools
import asyncio
from pathlib import Path
import time
import logging

logger = logging.getLogger(__name__)

# Create a directory for profiles if it doesn't exist
PROFILES_DIR = Path(__file__).parent.parent.parent / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)


def profile_to_file(filename_prefix: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info(f"Profiling function: {func.__name__}")
            profiler = cProfile.Profile()
            profiler.enable()

            try:
                result = await func(*args, **kwargs)
            finally:
                profiler.disable()

                timestamp = int(time.time() * 1000)
                filename = PROFILES_DIR / f"{filename_prefix}_{timestamp}.prof"

                s = io.StringIO()
                sortby = pstats.SortKey.CUMULATIVE
                ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
                ps.print_stats()

                try:
                    with open(filename, "w") as f:
                        f.write(s.getvalue())
                except Exception as e:
                    logger.error(f"Failed to write profile file {filename}: {e}")

            return result

        return wrapper

    return decorator
