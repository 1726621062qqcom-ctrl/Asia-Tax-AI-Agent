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
    return (host in ('ird.gov.hk', 'www.ird.gov.hk') and
            parsed.path == FSIE_GUIDANCE_PATHS.get(source_id))


FSIE_GUIDANCE_PATHS = {
    'hk_ird_fsie_landing': '/eng/tax/bus_fsie.htm',
    'hk_ird_fsie_faq': '/eng/faq/fsie.htm',
    'hk_ird_fsie_examples': '/eng/tax/fsie_example.htm',
    'hk_ird_fsie_esr_advance_ruling': '/eng/tax/fsie_aru.htm',
}

SOURCE_TYPES = {
    'law': frozenset(('law', 'regulation', 'structured_legislation_xml', 'ordinance_material')),
    'guidance': frozenset(('guidance', 'guide', 'example', 'page', 'official_guidance',
                          'official_faq', 'official_examples', 'official_web_page',
                          'official_advance_ruling_guidance')),
    'ruling': frozenset(('official_advance_ruling',)),
}


def source_kind(source_type):
    return next((kind for kind, types in SOURCE_TYPES.items() if source_type in types), None)


def canonical_source_id(source_id, url):
    """Map only known official URLs; aliases do not expand source permissions."""
    parsed = urlsplit(url or '')
    if parsed.scheme == 'https' and parsed.hostname in ('ird.gov.hk', 'www.ird.gov.hk'):
        return next((sid for sid, path in FSIE_GUIDANCE_PATHS.items() if parsed.path == path), source_id)
    return source_id
