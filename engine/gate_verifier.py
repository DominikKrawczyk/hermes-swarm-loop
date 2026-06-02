"""Gate 11 Verifier -- validates JSON-schema handoffs and agent completion status."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

class HandoffValidationError(Exception):
    pass

class AgentCompletionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class HandoffSchema:
    id: int
    name: str
    properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    additional_properties: bool = False
    def to_json_schema(self) -> Dict[str, Any]:
        schema: Dict[str, Any] = {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
                                   "properties": {}, "required": list(self.required),
                                   "additionalProperties": self.additional_properties}
        for prop_name, prop_def in self.properties.items():
            schema["properties"][prop_name] = dict(prop_def)
        return schema

@dataclass
class HandoffValidationResult:
    id: int
    schema_name: str
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    agent_status: Optional[AgentCompletionStatus] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "schema_name": self.schema_name, "valid": self.valid,
                "errors": self.errors, "warnings": self.warnings,
                "agent_status": self.agent_status.value if self.agent_status else None}

class GateVerifier:
    TERMINAL_STATUSES: Tuple[AgentCompletionStatus, ...] = (
        AgentCompletionStatus.COMPLETED, AgentCompletionStatus.FAILED, AgentCompletionStatus.SKIPPED,
    )
    def __init__(self) -> None:
        self._next_id: int = 1

    def validate(self, schema: HandoffSchema, payload: Dict[str, Any],
                 agent_status: Optional[Union[str, AgentCompletionStatus]] = None) -> HandoffValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        sid = self._next_id
        self._next_id += 1
        status: Optional[AgentCompletionStatus] = None
        if agent_status is not None:
            if isinstance(agent_status, str):
                try:
                    status = AgentCompletionStatus(agent_status.lower())
                except ValueError:
                    errors.append(f"Unknown agent status: '{agent_status}'. Valid: {[s.value for s in AgentCompletionStatus]}")
            else:
                status = agent_status
        if status is not None and status not in self.TERMINAL_STATUSES:
            errors.append(f"Agent status '{status.value}' is not terminal. Handoff requires one of: {[s.value for s in self.TERMINAL_STATUSES]}")
        for field_name in schema.required:
            if field_name not in payload:
                errors.append(f"Missing required field: '{field_name}'")
        for prop_name, prop_value in payload.items():
            prop_def = schema.properties.get(prop_name)
            if prop_def is None:
                if not schema.additional_properties:
                    warnings.append(f"Unexpected field '{prop_name}' (not in schema and additional_properties=False)")
                continue
            expected_type = prop_def.get("type")
            if expected_type is not None:
                if not self._type_matches(prop_value, expected_type):
                    errors.append(f"Field '{prop_name}' expected type '{expected_type}', got '{type(prop_value).__name__}'")
            enum_values: Optional[List[Any]] = prop_def.get("enum")
            if enum_values is not None and prop_value not in enum_values:
                errors.append(f"Field '{prop_name}' value {prop_value!r} not in allowed enum: {enum_values}")
        return HandoffValidationResult(id=sid, schema_name=schema.name, valid=len(errors) == 0,
                                        errors=errors, warnings=warnings, agent_status=status, payload=payload)

    def validate_json(self, schema: HandoffSchema, raw_json: str,
                      agent_status: Optional[Union[str, AgentCompletionStatus]] = None) -> HandoffValidationResult:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            rid = self._next_id
            self._next_id += 1
            return HandoffValidationResult(id=rid, schema_name=schema.name, valid=False, errors=[f"Invalid JSON: {exc}"])
        if not isinstance(payload, dict):
            rid = self._next_id
            self._next_id += 1
            return HandoffValidationResult(id=rid, schema_name=schema.name, valid=False,
                                            errors=[f"Expected JSON object (dict), got {type(payload).__name__}"])
        return self.validate(schema, payload, agent_status)

    @staticmethod
    def _type_matches(value: Any, expected: str) -> bool:
        mapping: Dict[str, Tuple[type, ...]] = {"string": (str,), "number": (int, float), "integer": (int,),
            "boolean": (bool,), "object": (dict,), "array": (list, tuple), "null": (type(None),)}
        acceptable = mapping.get(expected)
        if acceptable is None:
            return True
        return isinstance(value, acceptable)

    @staticmethod
    def terminal_statuses() -> Tuple[AgentCompletionStatus, ...]:
        return GateVerifier.TERMINAL_STATUSES
