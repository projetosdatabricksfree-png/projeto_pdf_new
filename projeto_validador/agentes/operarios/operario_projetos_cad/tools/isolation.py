"""
Isolation Utility — Safely run dangerous functions in a separate process.
Prevents SIGSEGV/crashes from killing the main worker.
"""
from __future__ import annotations

import multiprocessing
import traceback
from typing import Any, Callable


def _worker_wrapper(func, queue, *args, **kwargs):
    """Wrapper to run a function and capture its output/exception."""
    try:
        result = func(*args, **kwargs)
        queue.put((True, result))
    except Exception:
        queue.put((False, traceback.format_exc()))


def run_isolated(func: Callable, timeout: int = 30, *args, **kwargs) -> Any:
    """Run `func` in a separate process.
    
    Returns:
        The result of `func`.
        
    Raises:
        RuntimeError: If the process crashes (SIGSEGV) or times out.
    """
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_worker_wrapper,
        args=(func, queue) + args,
        kwargs=kwargs
    )
    
    process.start()
    process.join(timeout=timeout)
    
    if process.is_alive():
        process.terminate()
        process.join()
        raise RuntimeError(f"Process timeout after {timeout}s")
    
    if process.exitcode != 0:
        # Exit code 11 is SIGSEGV
        exit_msg = f"status {process.exitcode}"
        if process.exitcode == -11:
            exit_msg = "Segmentation Fault (SIGSEGV)"
        raise RuntimeError(f"Isolated process crashed: {exit_msg}")
        
    if queue.empty():
        raise RuntimeError("Isolated process failed without output (possible silent crash)")
        
    success, result = queue.get()
    if not success:
        # result is the traceback string
        raise RuntimeError(f"Isolated process exception:\n{result}")
        
    return result
