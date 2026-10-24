"""Strict acceptance probe: exits nonzero if the protected browser cannot launch."""
import asyncio
import sys
import json
from app.diagnostics import startup_diagnostic
from app.browser_manager import BrowserManager
from app.config import Settings


async def main():
    manager=BrowserManager(Settings())
    try:
        await manager.start()
        print('PASS: sandbox-enabled Playwright Chromium launched.')
    except Exception as exc:
        print('FAIL: sandbox-enabled Chromium could not launch. Essential acceptance criterion failed.',file=sys.stderr)
        print(json.dumps(manager.startup_error or startup_diagnostic(exc),indent=2),file=sys.stderr)
        return 1
    finally:
        await manager.stop()
    return 0


if __name__=='__main__':
    sys.exit(asyncio.run(main()))
