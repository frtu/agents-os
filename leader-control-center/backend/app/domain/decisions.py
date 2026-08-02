"""Which decision actions an open request (decision-to-make) accepts. The client
renders exactly these controls, so the action set lives on the server rather than
being hardcoded in the UI (specs/api/rest-api.md, Decisions)."""
from __future__ import annotations

from app.domain.enums import DecisionKind, HumanRequestType

_A = DecisionKind

_ACTIONS_BY_TYPE: dict[HumanRequestType, list[DecisionKind]] = {
    HumanRequestType.APPROVAL: [_A.APPROVE, _A.REJECT, _A.CLARIFY, _A.ABORT],
    HumanRequestType.CLARIFICATION: [_A.CLARIFY, _A.CONTINUE, _A.ABORT],
    HumanRequestType.MISSING_INFORMATION: [_A.CLARIFY, _A.CONTINUE, _A.ABORT],
    HumanRequestType.BUDGET: [_A.APPROVE, _A.REJECT, _A.ABORT],
    HumanRequestType.TOOL_PERMISSION: [_A.APPROVE, _A.REJECT, _A.ABORT],
    HumanRequestType.RISK_ACCEPTANCE: [_A.APPROVE, _A.REJECT, _A.ABORT],
    HumanRequestType.CHOOSE_OPTION: [_A.SELECT_OPTION, _A.ABORT],
}

_DEFAULT = [_A.APPROVE, _A.CONTINUE, _A.REJECT, _A.ABORT]


def actions_for(request_type: HumanRequestType) -> list[DecisionKind]:
    return list(_ACTIONS_BY_TYPE.get(request_type, _DEFAULT))
