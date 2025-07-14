
def get_cookie_domain(hostname: str | None) -> str | None:
    if not hostname:
        return None
    parts = hostname.split(".")
    if len(parts) >= 3:
        return "." + ".".join(parts[-2:])
    return None
