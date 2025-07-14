from urllib.parse import urlparse


def get_cookie_domain_from_url(url: str) -> str | None:
    hostname = urlparse(url).hostname or ''
    parts = hostname.split('.')
    if len(parts) >= 3:
        return '.' + '.'.join(parts[-2:])
    return None