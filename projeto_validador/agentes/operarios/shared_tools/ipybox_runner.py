"""
ipybox Runner — SY-04 Secure Sandbox Execution.

Provides a Docker-based sandbox to run deep-script analysis on untrusted PDFs.
Implements:
- detector: scans PDF for /JS, /JavaScript, /Action, /Launch triggers.
- runner: executes analysis inside an isolated 'ipybox' container.
- resource limits: 60s timeout, no network, read-only PDF mount.
"""
from __future__ import annotations

import os
import re
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Dangerous PDF triggers per SY-04
DANGEROUS_TRIGGERS = [
    rb"/JS", rb"/JavaScript", rb"/Action", rb"/Launch", rb"/EmbeddedFiles", rb"/OpenAction"
]

class SandboxError(Exception):
    """Base class for sandbox execution errors."""
    pass

def scan_pdf_risk(file_path: str) -> bool:
    """
    Rapid binary scan for potential malicious triggers.
    Returns True if the file is considered 'High Risk' and needs the Sandbox.
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        # Scan first 1MB and last 1MB (where most triggers live)
        size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            head = f.read(1024 * 1024)
            if any(t in head for t in DANGEROUS_TRIGGERS):
                return True
                
            if size > 1024 * 1024:
                f.seek(-1024 * 1024, os.SEEK_END)
                tail = f.read()
                if any(t in tail for t in DANGEROUS_TRIGGERS):
                    return True
    except Exception as e:
        logger.error(f"Error scanning PDF risk: {e}")
        return True # Safety first
        
    return False

def run_in_sandbox(file_path: str, command: List[str], timeout: int = 60) -> Dict[str, Any]:
    """
    Executes a command inside the ipybox sandbox for the given PDF.
    Rule 2 — Subprocesso Seguro: subprocess.run with shell=False.
    """
    abs_path = str(Path(file_path).resolve())
    file_name = os.path.basename(abs_path)
    
    # Construction of Docker command
    # --network none: isolation
    # --read-only: immutable rootfs
    # --tmpfs: allow small writes only in memory
    # -v {path}:/data/{name}:ro : Read-only PDF mount
    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1.0",
        "--read-only",
        "--tmpfs", "/tmp",
        "-v", f"{abs_path}:/data/{file_name}:ro",
        "graphic-pro-ipybox:latest"
    ] + command
    
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )
        return {
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Sandbox timeout for {file_name}")
        return {"status": "TIMEOUT", "error": f"Execution exceeded {timeout}s"}
    except Exception as e:
        logger.error(f"Sandbox error: {e}")
        return {"status": "ERROR", "error": str(e)}

if __name__ == "__main__":
    # Test Detector
    import sys
    if len(sys.argv) > 1:
        risk = scan_pdf_risk(sys.argv[1])
        print(f"File: {sys.argv[1]} | High Risk: {risk}")
