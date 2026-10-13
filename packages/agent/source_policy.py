"""Narrow permission for publicly published Hong Kong official material."""
import re
from urllib.parse import urlsplit


def public_hk_official(source_id: str, url: str | None) -> bool:
    if not url:
        return False
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.username or parsed.password:
        return False
    host = (parsed.hostname or '').lower()
    if source_id == 'hk_hkel_iro_cap112':
        return host in ('elegislation.gov.hk', 'www.elegislation.gov.hk')
    case = re.fullmatch(r'hk_ird_advance_(\d+)', source_id)
    if case:
        return host in ('ird.gov.hk', 'www.ird.gov.hk') and parsed.path == f'/eng/ppr/advance{case.group(1)}.htm'
    return False
