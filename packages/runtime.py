"""One startup configuration and dependency lifecycle for local and cloud API."""
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


@dataclass
class Runtime:
    orchestration: str
    provider: str
    dynamic_planner: bool
    harness_mode: str
    knowledge_process: object = None

    def public(self):
        return dict(orchestration=self.orchestration, provider=self.provider,
                    dynamic_planner=self.dynamic_planner, harness_mode=self.harness_mode,
                    knowledge_ready=self.knowledge_process is not None and self.knowledge_process.poll() is None)


@contextmanager
def application_runtime():
    from packages.agent.providers import ProviderSettings
    from packages.agent.task_contracts import OrchestrationSettings
    from scripts.combined_runtime import knowledge_server

    defaults = json.loads((ROOT / 'config/runtime.json').read_text())
    local = dotenv_values(ROOT / '.env')
    keys = [*defaults, 'FSIE_AGENT_C_URL', 'FSIE_AGENT_C_TOKEN']
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key, value in defaults.items():
            os.environ.setdefault(key, local.get(key) or value)
        settings = OrchestrationSettings()
        provider = ProviderSettings()
        if provider.provider == 'mock':
            raise RuntimeError('Mock knowledge provider is not a production runtime')
        runtime = Runtime(settings.orchestration, provider.provider,
                          settings.dynamic_planner, settings.harness_mode)
        with ExitStack() as stack:
            if provider.provider == 'combined':
                # Both environments manage their own local library service.
                def started(process):
                    runtime.knowledge_process = process
                url, token = stack.enter_context(knowledge_server(on_start=started))
                os.environ.update(FSIE_AGENT_C_URL=url, FSIE_AGENT_C_TOKEN=token)
            logger.info('Taxrora runtime: %s', runtime.public())
            yield runtime
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
