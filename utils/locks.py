import multiprocessing
import os

def get_process_lock(name: str) -> multiprocessing.Lock:
    """
    Returns a cross-process lock using a file lock.
    Use this if Celery concurrency = prefork (default).
    """
    import fcntl

    class FileLock:
        def __init__(self, path: str):
            self._path = path
            self._fd = None

        def __enter__(self):
            self._fd = open(self._path, "w")
            fcntl.flock(self._fd, fcntl.LOCK_EX)
            return self

        def __exit__(self, *args):
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            self._fd.close()

    lock_dir = "/tmp/celery_locks"
    os.makedirs(lock_dir, exist_ok=True)
    return FileLock(os.path.join(lock_dir, f"{name}.lock"))

smtp_lock = get_process_lock("smtp_client")
github_lock = get_process_lock("github_client")