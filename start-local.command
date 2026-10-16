#!/bin/zsh
set -euo pipefail
cd -- "$(dirname -- "$0")"

if [[ ! -x .venv/bin/python ]]; then
  print -u2 'Missing .venv. Install the project dependencies first.'
  exit 1
fi

print 'Starting Taxora at http://127.0.0.1:8000'
print 'The application and statutory library run locally; authentication and PostgreSQL use the configured Supabase project.'
print 'Press Ctrl+C to stop the application and its temporary knowledge service.'

# Use the macOS trusted certificate store while retaining TLS verification.
exec .venv/bin/python -c 'import truststore, runpy; truststore.inject_into_ssl(); runpy.run_module("scripts.run_combined", run_name="__main__")'
