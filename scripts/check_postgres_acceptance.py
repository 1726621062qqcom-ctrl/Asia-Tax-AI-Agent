"""Real PostgreSQL acceptance in a newly created, disposable database.

The configured database is never migrated or cleared. Requires CREATEDB and
pgvector on the server; child checks inherit only this new database URL.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from packages.persistence.config import Settings

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env')
    parser.add_argument('--system-trust', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/postgres-acceptance-result.json')
    args = parser.parse_args()
    settings = Settings(_env_file=args.env_file)
    if not settings.database_url:
        parser.error('Configure FSIE_DATABASE_URL in the selected local env file.')
    base = make_url(settings.database_url)
    if base.get_backend_name() != 'postgresql':
        parser.error('This check requires PostgreSQL.')
    name = 'fsie_acceptance_' + uuid4().hex
    target = base.set(database=name).render_as_string(hide_password=False)
    admin = create_engine(base.set(database='postgres'), isolation_level='AUTOCOMMIT',
                          connect_args={'connect_timeout': 5})
    env = dict(os.environ, FSIE_DATABASE_URL=target, FSIE_RUN_INTEGRATION='1')
    for key in ('FSIE_MODEL_BASE_URL', 'FSIE_MODEL_API_KEY', 'FSIE_MODEL_NAME'):
        env[key] = ''  # Model checks require separate, explicit real-model acceptance.
    result = {'database': 'disposable_postgresql', 'model': 'not_called', 'checks': {}}
    created = False
    started = monotonic()
    log_dir = args.output.parent / 'postgres-acceptance-logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    def run(label, command, timeout):
        process = subprocess.run([sys.executable] + command, cwd=ROOT, env=env,
                                 capture_output=True, text=True, timeout=timeout)
        output = process.stdout + process.stderr
        for secret in (target, settings.database_url, base.password):
            if secret:
                output = output.replace(secret, '<redacted>')
        (log_dir / (label + '.log')).write_text(output)
        result['checks'][label] = 'passed' if process.returncode == 0 else 'failed'
        if process.returncode:
            raise RuntimeError(label)
        return output

    try:
        with admin.connect() as connection:
            result['database_version'] = connection.execute(text('SHOW server_version')).scalar()
            connection.execute(text('CREATE DATABASE ' + name))
            created = True
        run('migrations', ['-m', 'alembic', 'upgrade', 'head'], 60)
        run('rule_package', ['-m', 'packages.knowledge_loader.cli'], 60)
        bootstrap = 'import truststore; truststore.inject_into_ssl(); ' if args.system_trust else ''
        run('official_knowledge', ['-c', bootstrap +
            'from packages.knowledge_pipeline.cli import main; raise SystemExit(main())'], 900)
        summary = run('persistence_tests', ['-m', 'pytest', '-q', 'tests/persistence'], 180)
        counts = re.search(r'(\d+) passed(?:, (\d+) skipped)?', summary)
        result['persistence_tests'] = {'passed': int(counts[1]), 'skipped': int(counts[2] or 0)} if counts else {}
        combined_file = log_dir / 'combined.json'
        run('combined_http_tax_engine_postgres', ['scripts/check_combined_live.py', '--database-only',
            '--env-file', str(args.env_file), '--output', str(combined_file)], 180)
        result['combined'] = json.loads(combined_file.read_text())
        result['status'] = 'passed'
    except Exception as exc:
        result.update(status='failed', error=type(exc).__name__)
    finally:
        if created:
            try:
                with admin.connect() as connection:
                    connection.execute(text('DROP DATABASE ' + name + ' WITH (FORCE)'))
                result['cleaned_up'] = True
            except Exception:
                result.update(status='failed', cleaned_up=False)
        admin.dispose()
    result['elapsed_seconds'] = round(monotonic() - started, 2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
