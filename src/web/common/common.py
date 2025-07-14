
def get_cookie_domain(hostname: str | None) -> str | None:
    if not hostname:
        return None
    parts = hostname.split('.')
    return "." + ".".join(parts[-2:]) if len(parts) >= 3 else None
