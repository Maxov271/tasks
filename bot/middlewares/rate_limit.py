"""
Oddiy in-memory token-bucket rate limiter. Bitta process ichida ishlaydi;
production'da (bir nechta worker bo'lsa) Redis-based versiyaga almashtiriladi
(interfeys bir xil qoladi — faqat `_buckets` saqlash joyi o'zgaradi).
"""
import time
import threading

_buckets = {}
_lock = threading.Lock()

MAX_CALLS = 5          # bitta foydalanuvchi uchun
PER_SECONDS = 3         # shu vaqt oralig'ida


def is_rate_limited(telegram_id: int) -> bool:
    now = time.monotonic()
    with _lock:
        calls = _buckets.setdefault(telegram_id, [])
        # eskirgan yozuvlarni tozalash
        calls[:] = [t for t in calls if now - t < PER_SECONDS]
        if len(calls) >= MAX_CALLS:
            return True
        calls.append(now)
        return False
