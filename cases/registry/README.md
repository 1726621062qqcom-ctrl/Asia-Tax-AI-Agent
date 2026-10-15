# Register records (channel B)

The program can only query Singapore itself (ACRA's public dataset on data.gov.sg; `tax_graph/registry/sg.py` looks a company up by its exact name). The Hong Kong Companies Registry's e-Services Portal needs a paid login and has no public API; the Mainland's 国家企业信用信息公示系统 has no API. For these two, a person copies the register page into one record here, and the program cross-checks it the same way.

Directory: `cases/registry/<JUR>/<any name>.json`, where JUR is HK / CN / SG / VN. One file per company:

```json
{
  "jur": "HK",
  "id": "1234567",
  "name": "TOP VICTORY DEVELOPMENT LIMITED",
  "former_names": [],
  "status": "Live",
  "type": "Private company limited by shares",
  "incorporated_on": "2009-03-18",
  "address": "...",
  "source": "https://www.e-services.cr.gov.hk/ ... 公司資料 页面（抄录日 2026-10-15）",
  "retrieved_at": "2026-10-15"
}
```

- `name` as written in the register (Hong Kong: the English name in upper case; the Mainland: the Chinese name); the aliases in the case file's `names` are compared with it (similarity >= 0.9 after legal-form suffixes are removed).
- `incorporated_on` is an ISO date; leave it out if unknown, the program only compares the fields that are present.
- What is compared (`tax_graph/registry/cross_check`): the case's jurisdiction vs the record's jurisdiction; a holding's `since` must not be earlier than the held company's incorporation date; name similarity; a note when the status is not live. Every difference is reported; the program never chooses for the person.
