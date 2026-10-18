"""Query agent logs locally: list runs, inspect a trace, or aggregate diagnostics."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.agent.logs import log_dir, matches, records, statistics


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('list', 'show', 'stats'))
    parser.add_argument('--directory', type=Path, help='Log directory; default is the configured local agent log directory')
    parser.add_argument('--trace-id')
    parser.add_argument('--case-id')
    parser.add_argument('--request-id')
    parser.add_argument('--errors', action='store_true', help='Failed/partial runs or rejected/error events')
    parser.add_argument('--event', help='Event name prefix, e.g. tool. or route.validation')
    parser.add_argument('--limit', type=int, default=20, help='Maximum displayed records; 0 means all retained records')
    parser.add_argument('--json', action='store_true', help='Machine-readable output')
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error('--limit must be nonnegative')
    directory = args.directory or log_dir()
    if directory is None:
        parser.error('Logging is disabled; supply --directory to inspect existing logs')
    if not directory.is_dir():
        parser.error('Log directory does not exist yet')
    def selected(record):
        return matches(record, args.trace_id, args.case_id, args.request_id)
    runs = [r for r in records(directory, 'runs') if selected(r)]
    events = [e for e in records(directory, 'events') if selected(e)]
    if args.errors:
        failed_ids = {r['trace_id'] for r in runs if r.get('status') == 'error' or
                      r.get('result_status') in ('partial_failure', 'paused_gap') or r.get('rejected_events', 0)}
        runs = [r for r in runs if r['trace_id'] in failed_ids]
        events = [e for e in events if e.get('status') in ('error', 'rejected')]
    if args.event:
        events = [e for e in events if e.get('name', '').startswith(args.event)]
    if args.command == 'stats':
        print(json.dumps(statistics(runs, events), ensure_ascii=False, indent=2))
        return
    result = runs if args.command == 'list' else events
    if args.limit:
        result = result[-args.limit:]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == 'list':
        for run in result:
            print(f"{run.get('started_at')}  {run['trace_id']}  case={run.get('case_id')}  "
                  f"{run.get('result_status') or run.get('status')}  {run.get('duration_ms')}ms  "
                  f"models={run.get('model_calls', 0)}  tools={','.join(run.get('tools', [])) or '-'}")
    else:
        for event in result:
            print(f"{event['trace_id']} #{event.get('seq')} +{event.get('elapsed_ms')}ms "
                  f"{event.get('name')} [{event.get('status')}]")
            print('  ' + json.dumps(event.get('data', {}), ensure_ascii=False))


if __name__ == '__main__':
    main()
