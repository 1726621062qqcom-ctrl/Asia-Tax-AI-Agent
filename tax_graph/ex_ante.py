"""ex_ante / finalize (伪代码.md §6): every candidate structure of a template on a case, its (lo, hi) and pending
groups; the human ticks, a pure function picks the minimum. Rows are flagged as dominated when another row is no
worse on both bounds. The objective is the group total (I1); `subject` only adds a view of who bears it."""
from dataclasses import dataclass
from typing import List

from .data.domain import ADJUSTABLE
from .engine import EX_ANTE, Bounds, CaseCtx, Reject, bounds, by_source, outside_steps
from .model import Graph
from .rules.tri import DISCRETION, MISSING, PLAN
from .claims import claims
from .scenarios import GROUP, Case, Template, same_settled, views
from . import scope as scope_mod


@dataclass
class Row:
    cand: dict
    b: Bounds
    n_entities: int
    graph: object = None                 # the candidate's graph (for claims and views)
    subject: tuple = (0.0, 0.0)          # the subject's share of the group's floor run and of its ceiling run (a projection,
                                         # not the subject's own extremes: another member's tax may lower this one's credit)
    dominated: bool = False

    @property
    def unmodelled(self):
        """Steps the structure needs whose tax no rule computes (decision D19): its bounds leave them out, so it is no plan."""
        return getattr(self.graph, "unmodelled", ()) if self.graph is not None else ()

    @property
    def n_discretion(self):
        return sum(1 for ns in self.b.groups.values() for n in ns if n.source == DISCRETION)

    @property
    def n_plan(self):
        return sum(1 for ns in self.b.groups.values() for n in ns if n.source == PLAN)

    @property
    def fragility(self):
        """Part of the gap above the floor that rests on judgement: the costs of the DISCRETION groups (not additive
        across groups, so an indication, not a bound)."""
        return round(sum(self.b.cost.get(g, 0.0) for g, ns in self.b.groups.items() if any(n.source == DISCRETION for n in ns)), 2)

    @property
    def key(self):
        return (self.b.lo, self.b.hi, self.n_discretion, self.n_plan, self.n_entities)


@dataclass
class ExAnteOutput:
    table: List[Row]
    needs: list                          # (cost, group, keys) for MISSING, cost descending, best row only
    conditions: list                     # same for PLAN and DISCRETION
    claims: list = None                  # settled items of the best row: what is recoverable / exposed (claims.Claim)
    archived: list = None                # settled items that are closed: nothing to claim, nothing pending
    out_of_scope: list = None            # decision D52: (candidate, [scope.Outside]) the income-only scope left out of the table


def validate_core(graph: Graph):
    for e in graph.entities.values():
        if not e.loc:
            raise Reject("entity without a jurisdiction: %s" % e.id)
    for f in graph.flows:
        if f.payer not in graph.entities or f.payee not in graph.entities or not f.on or f.amount is None:
            raise Reject("flow with missing core fields: %s" % f.id)


def _rows(template: Template, event, case: Case, cands, ctx_of, P, subject, ticks=None, scope=None):
    rows, skipped = [], []
    g0 = template.build(event, case.present, case) if case.settled else None
    for a in cands:
        g = template.build(event, a, case)
        validate_core(g)
        if scope_mod.active(scope):                      # decision D52: a structure that attracts another levy is not compared
            bad = scope_mod.outside(g)
            if bad:
                skipped.append((a, bad))
                continue
        if g0 is not None and not same_settled(g, g0, case.settled):
            continue                                     # would undo a flow already taxed somewhere: not a plan
        b = bounds(g, ctx_of, P, settled=case.settled, as_at=event.as_at, closed=case.closed, ticks=ticks)
        steps = outside_steps(b, g)[0]                   # decision D30: a group-borne levy outside the library — a step
        if steps:                                        # whose tax is unknown, as in the planner
            g.unmodelled = tuple(g.unmodelled) + tuple(x for x in steps if x not in g.unmodelled)
        rows.append(Row(a, b, len(g.entities), g, views(b, subject, g)))
    return rows, skipped


def ex_ante(template: Template, event, case: Case, ticks=None, P=None, subject=GROUP, scope=None) -> ExAnteOutput:
    """scope: None = the product's policy (scope.POLICY, income tax only); scope.ALL = the whole library (harnesses)."""
    missing = template.check_case(event, case)
    if missing:
        raise Reject("case does not place the roles the template needs: %s" % missing)
    ctx_of = lambda facts: CaseCtx(facts, ticks or {}, EX_ANTE, ADJUSTABLE)
    table, skipped = _rows(template, event, case, template.candidates(event, case), ctx_of, P, subject, ticks, scope=scope)
    for r in table:                                      # Pareto dominance on (lo, hi) before any ordering; a row
        r.dominated = any(o is not r and not o.unmodelled and o.b.lo <= r.b.lo and o.b.hi <= r.b.hi   # whose bounds leave a
                          and (o.b.lo < r.b.lo or o.b.hi < r.b.hi) for o in table)                     # step out dominates none
    table.sort(key=lambda r: (bool(r.unmodelled), r.dominated, r.key))
    if not table:
        if skipped:                                      # decision D52: every structure attracts a levy other than income tax
            items = {(x.flow, x.jur, x.levy): x for _, bad in skipped for x in bad}
            raise scope_mod.OutOfScope(scope_mod.reason(list(items.values()), case.names).replace("outside the scope", "no candidate structure is within the scope", 1))
        raise Reject("no candidate keeps every settled flow as it was")
    best = table[0].b
    cl, archived = claims(best, case.settled, event.as_at, table[0].graph)
    return ExAnteOutput(table, by_source(best, {MISSING}), by_source(best, {PLAN, DISCRETION}), cl, archived, skipped)


def finalize(template: Template, event, case: Case, table: List[Row], ticks, P=None, subject=GROUP, scope=None) -> Row:
    """After the human round: ticks are facts now; recompute and take the minimum (no further human step)."""
    ctx_of = lambda facts: CaseCtx(facts, ticks, EX_ANTE, ADJUSTABLE)
    rows, _ = _rows(template, event, case, [r.cand for r in table], ctx_of, P, subject, ticks, scope=scope)
    return min(rows, key=lambda r: r.key)
