from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')


FactKey = Literal['company_location', 'hk_business', 'group_structure', 'income_type',
                  'holding_percentage', 'holding_period', 'accrual_date', 'receipt_route',
                  'distribution_form', 'foreign_tax', 'economic_substance', 'commercial_purpose']


class FactCandidate(Contract):
    key: FactKey
    value: str = Field(min_length=1, max_length=400)
    quote: str = Field(min_length=1, max_length=800)


class Fact(Contract):
    key: FactKey
    label: str
    value: str
    quote: str
    turn: int
    status: Literal['user_stated', 'conflict'] = 'user_stated'
    previous: list[dict] = Field(default_factory=list)


class PlanningResult(Contract):
    intent: Literal['law', 'case', 'planning', 'correction', 'out_of_scope', 'unknown']
    facts: list[FactCandidate] = Field(default_factory=list, max_length=12)
    search_terms: str = Field(default='', max_length=600)


class Paragraph(Contract):
    text: str = Field(min_length=1, max_length=2400)
    citations: list[str] = Field(default_factory=list, max_length=6)


class Section(Contract):
    title: str = Field(min_length=1, max_length=80)
    paragraphs: list[Paragraph] = Field(min_length=1, max_length=8)


class Draft(Contract):
    sections: list[Section] = Field(min_length=1, max_length=6)
    questions: list[str] = Field(default_factory=list, max_length=3)


class Citation(Contract):
    id: str
    source_id: str
    title: str
    url: str
    source_type: str
    locator: str
    excerpt: str
    text_sha256: str
    retrieved_at: str
    professional_validation_status: str
    statute_reference: str
    statute_url: str


class Answer(Contract):
    turn: int
    intent: str
    mode: Literal['local_research', 'model_research', 'model_fallback']
    sections: list[Section]
    questions: list[str]
    facts: list[Fact]
    citations: list[Citation]
    warnings: list[str]
    research_only: Literal[True] = True
    prompt_version: str
    corpus_version: str
    legal_coverage_cutoff: str


class SessionCreate(Contract):
    synthetic_acknowledged: Literal[True]


class ChatRequest(Contract):
    message: str = Field(min_length=1, max_length=4000)
    request_id: str = Field(min_length=8, max_length=80, pattern=r'^[A-Za-z0-9_-]+$')
