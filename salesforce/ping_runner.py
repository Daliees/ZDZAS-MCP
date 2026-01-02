"""Simple ping loop to hit the ZAS chat API /ping endpoint every minute.

Configure env ZAS_CHAT_API_BASE (default: http://127.0.0.1:9000) and optional timeout.
"""
import os
import time
import requests

API_BASE = os.getenv("ZAS_CHAT_API_BASE", "http://127.0.0.1:9000")
PING_URL = f"{API_BASE.rstrip('/')}/ping"
SLEEP_SECONDS = 60
TIMEOUT = float(os.getenv("ZAS_PING_TIMEOUT", "5"))


def main() -> None:
	while True:
		try:
			resp = requests.get(PING_URL, timeout=TIMEOUT)
			ok = resp.status_code == 200 and resp.json().get("ok") is True
			print(f"[ping] ok={ok} status={resp.status_code}")
		except Exception as e:
			print(f"[ping] error: {e}")
		time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
	main()
