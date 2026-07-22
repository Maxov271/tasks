"""
Callback data konventsiyasi: "domain:action:params..."
Masalan: "task:view:42", "group:members:7:page:2", "admin:users:ban:882"

Bu modul callback_data'ni parse qilish va yig'ish uchun yagona joy —
handler'lar hech qachon string split'ni o'zi qo'lda yozmaydi.
"""
from dataclasses import dataclass, field


MAX_CALLBACK_LEN = 64  # Telegram Bot API cheklovi


@dataclass
class ParsedCallback:
    domain: str
    action: str
    params: list = field(default_factory=list)

    def param(self, index: int, cast=str, default=None):
        try:
            return cast(self.params[index])
        except (IndexError, ValueError, TypeError):
            return default


def parse(callback_data: str) -> ParsedCallback:
    parts = callback_data.split(":")
    domain = parts[0] if len(parts) > 0 else ""
    action = parts[1] if len(parts) > 1 else ""
    params = parts[2:] if len(parts) > 2 else []
    return ParsedCallback(domain=domain, action=action, params=params)


def build(domain: str, action: str, *params) -> str:
    parts = [domain, action, *[str(p) for p in params]]
    data = ":".join(parts)
    if len(data.encode("utf-8")) > MAX_CALLBACK_LEN:
        raise ValueError(f"callback_data {MAX_CALLBACK_LEN} baytdan oshib ketdi: {data}")
    return data
