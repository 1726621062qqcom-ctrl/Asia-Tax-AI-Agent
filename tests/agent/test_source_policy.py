from packages.agent.source_policy import public_hk_official


def test_only_named_hk_public_official_sources_are_model_eligible():
    assert public_hk_official('hk_hkel_iro_cap112', 'https://www.elegislation.gov.hk/hk/cap112')
    assert public_hk_official('hk_ird_advance_68', 'https://www.ird.gov.hk/eng/ppr/advance68.htm')
    for source, url in [
        ('client_case', 'https://www.ird.gov.hk/eng/ppr/advance68.htm'),
        ('hk_ird_advance_68', 'https://www.ird.gov.hk.evil.example/case'),
        ('hk_ird_advance_68', 'http://www.ird.gov.hk/eng/ppr/advance68.htm'),
        ('hk_ird_advance_68_private', 'https://www.ird.gov.hk/eng/ppr/advance68.htm'),
        ('hk_ird_advance_68', 'https://www.ird.gov.hk/eng/login.htm'),
        ('hk_ird_advance_68', 'https://www.ird.gov.hk/eng/ppr/advance69.htm'),
        ('hk_hkel_iro_cap112', None),
        ('cn_law', 'https://www.elegislation.gov.hk/hk/cap112'),
    ]:
        assert not public_hk_official(source, url)
