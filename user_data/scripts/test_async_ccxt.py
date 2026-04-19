#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test async ccxt connections for a set of exchanges.

Requirements:
- Do NOT modify freqtrade source code.
- Use existing HTTP proxy (env: HTTP_PROXY/HTTPS_PROXY) which points to Clash‑Verge.
- Only OKX has API credentials; other exchanges will be tested with public endpoints.
- Results are saved to `/home/kali/Project/freqtrade/user_data/notebooks/交易所连接测试.md`.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Exchange list to test (add/remove as needed)
# ---------------------------------------------------------------------------
EXCHANGES = [
    "kraken",
    "bybit",
    "bitmart",
    "bitget",
    "bingx",
    "okx",
]

# OKX credentials (provided by the user)
OKX_API_KEY = "bd04e9f6-3f37-495d-97d6-e8490f116d49"
OKX_SECRET = "E31F54E46A21835A5FB2A57C9AE8A06F"

# Output markdown file
OUTPUT_MD = Path("/home/kali/Project/freqtrade/user_data/notebooks/交易所连接测试.md")

# ---------------------------------------------------------------------------
# Helper: write markdown header
# ---------------------------------------------------------------------------
def init_md():
    import datetime
    header = "# 交易所异步 ccxt 连接测试\n\n"
    header += f"测试时间：{datetime.datetime.now().isoformat()}\n\n"
    header += "| 交易所 | 结果 | 备注 |\n"
    header += "|------|------|------|\n"
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(header, encoding="utf-8")

# ---------------------------------------------------------------------------
# Perform async test for a single exchange
# ---------------------------------------------------------------------------
async def test_exchange(name: str) -> tuple[str, bool, str]:
    """Return (name, success, message)."""
    try:
        # Dynamically import the async ccxt module for the exchange name
        import ccxt.async_support as ccxt
        # Resolve class name (ccxt expects lower case name)
        exchange_cls = getattr(ccxt, name.lower())
    except Exception as e:
        return name, False, f"ccxt 没有该交易所类: {e}"

    # Build basic config – include proxy via env (already set) and optional credentials
    ex_config = {
        "enableRateLimit": True,
    }
    if name.lower() == "okx":
        ex_config.update({"apiKey": OKX_API_KEY, "secret": OKX_SECRET})
    # Some exchanges require `options` dict for futures/margin – not needed for metadata

    try:
        exchange = exchange_cls(ex_config)
    except Exception as e:
        return name, False, f"实例化失败: {e}"

    try:
        await exchange.load_markets()
        # If load succeeds, we can also query a simple public endpoint to be sure
        # Example: fetch ticker for a known pair (if exists)
        # We'll just pick the first market symbol if any
        symbols = list(exchange.symbols)
        if symbols:
            ticker = await exchange.fetch_ticker(symbols[0])
            # discard ticker, just ensure call works
        await exchange.close()
        return name, True, "成功加载 markets"
    except Exception as e:
        # Ensure we close the session to free resources
        try:
            await exchange.close()
        except Exception:
            pass
        return name, False, f"异常: {type(e).__name__}: {e}"

# ---------------------------------------------------------------------------
# Main coroutine
# ---------------------------------------------------------------------------
async def main():
    init_md()
    results = []
    for exch in EXCHANGES:
        name, success, msg = await test_exchange(exch)
        results.append((name, success, msg))
        # Append line to markdown immediately (so we see progress even if script crashes later)
        line = f"| {name} | {'✅ 成功' if success else '❌ 失败'} | {msg} |\n"
        with OUTPUT_MD.open("a", encoding="utf-8") as f:
            f.write(line)
        # Small pause to avoid hitting rate limits
        await asyncio.sleep(0.5)
    # Summary footer
    success_cnt = sum(1 for _, ok, _ in results if ok)
    fail_cnt = len(results) - success_cnt
    footer = "\n**总结**: 成功 {}，失败 {}\n".format(success_cnt, fail_cnt)
    with OUTPUT_MD.open("a", encoding="utf-8") as f:
        f.write(footer)

if __name__ == "__main__":
    # Ensure the async event loop runs
    asyncio.run(main())
