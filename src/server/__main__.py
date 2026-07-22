#!/usr/bin/env python3
"""`python -m src.server` 入口：启动 FastAPI (uvicorn)。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import uvicorn

from src.server import app

HOST = os.getenv("RULEWHISPER_HOST", "127.0.0.1")
PORT = int(os.getenv("RULEWHISPER_PORT", "9731"))


def main():
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
