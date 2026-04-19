#!/usr/bin/env bash
# Simple node rotation for two known nodes and run async CCXT test.

CLASH_CTL="/home/kali/Project/clash-verge-rev/clash-ctl"
SCRIPT="/home/kali/Project/freqtrade/user_data/scripts/test_async_ccxt.py"
REPORT="/home/kali/Project/freqtrade/user_data/notebooks/\u4ea4\u6613\u6240\u8fde\u63a5\u6d4b\u8bd5.md"
PROXY_GROUP="GLOBAL"

# Ensure report exists with header
if [[ ! -f "$REPORT" ]]; then
    cat <<'MD' >"$REPORT"
# \u4ea4\u6613\u6240\u5f02\u6b65 ccxt \u8fde\u63a5\u6d4b\u8bd5 (\u8282\u70b9\u8f6e\u6362\u7248)

| \u8282\u70b9 | \u5207\u6362\u524d IP | \u5207\u6362\u540e IP | \u7ed3\u679c |
|----------|----------------|-----------------|------|
MD
fi

# Define nodes to test (you can extend this list)
NODES=(
    "20251228cf - US-443-WS-TLS"
    "20251228cf - cloudflare.182682.xyz-443-WS-TLS"
)

for node in "${NODES[@]}"; do
    echo "=== Switching to node: $node ==="
    ip_before=$(curl -s -x http://127.0.0.1:7897 https://api.ipify.org || echo "N/A")
    $CLASH_CTL switch "$PROXY_GROUP" "$node"
    sleep 3
    ip_after=$(curl -s -x http://127.0.0.1:7897 https://api.ipify.org || echo "N/A")
    # Run the async ccxt test script (it appends results to the same markdown file)
    python3 "$SCRIPT"
    # Append a summary line to our report
    echo "| $node | $ip_before | $ip_after | $(tail -n 1 $REPORT) |" >> "$REPORT"
    echo "---" >> "$REPORT"
done

echo "\u2705 All nodes tested. Report saved at $REPORT"
