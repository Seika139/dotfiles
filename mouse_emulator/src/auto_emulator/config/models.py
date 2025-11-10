from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from mouse_core import Region


class CalibrationPreset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left: float
    top: float
    right: float
    bottom: float

    @model_validator(mode="after")
    def _validate_bounds(self) -> CalibrationPreset:
        if self.right <= self.left:
            msg = "preset.right は preset.left より大きな値でなければなりません"
            raise ValueError(msg)
        if self.bottom <= self.top:
            msg = "preset.bottom は preset.top より大きな値でなければなりません"
            raise ValueError(msg)
        return self

    def to_region(self) -> Region:
        return Region(
            left=self.left,
            top=self.top,
            right=self.right,
            bottom=self.bottom,
        )


class CalibrationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    color: Literal["default", "green", "blue", "warning", "fail"] = "green"
    preset: CalibrationPreset | None = None


class ControlSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pause_toggle: str | None = Field(
        default="ctrl+p",
        description="一時停止/再開をトグルするキーコンボ (例: 'ctrl+p')",
    )

    @field_validator("pause_toggle")
    @classmethod
    def _validate_pause_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned


class LoggingSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str | None = Field(default=None, description="ログ出力先ファイル")
    mode: Literal["append", "overwrite"] = "append"


class RuntimeSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capture_interval: float = Field(default=0.2, gt=0.0)
    max_iterations: int | None = Field(default=None, gt=0)
    calibration: CalibrationSettings = Field(default_factory=CalibrationSettings)
    controls: ControlSettings = Field(default_factory=ControlSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


class RegionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    left: float = Field(ge=0.0, le=1.0)
    top: float = Field(ge=0.0, le=1.0)
    right: float = Field(ge=0.0, le=1.0)
    bottom: float = Field(ge=0.0, le=1.0)

    @field_validator("right")
    @classmethod
    def _validate_horizontal(cls, right: float, info: ValidationInfo) -> float:
        left = info.data.get("left")
        if left is not None and right <= left:
            msg = "right は left より大きな値でなければなりません"
            raise ValueError(msg)
        return right

    @field_validator("bottom")
    @classmethod
    def _validate_vertical(cls, bottom: float, info: ValidationInfo) -> float:
        top = info.data.get("top")
        if top is not None and bottom <= top:
            msg = "bottom は top より大きな値でなければなりません"
            raise ValueError(msg)
        return bottom


class DetectorSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    name: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def _canonical_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            msg = "detector.type は空にできません"
            raise ValueError(msg)
        return cleaned


class WatchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detector: DetectorSpec
    region: str | None = Field(
        default=None,
        description="region definitions の name を参照する省略記法",
    )
    interval: float | None = Field(default=None, gt=0.0)
    timeout: float | None = Field(default=None, gt=0.0)
    max_attempts: int | Literal["infinite"] | None = Field(default=1)
    stop_on_failure: bool = False

    @field_validator("max_attempts")
    @classmethod
    def _validate_attempts(
        cls,
        value: int | Literal["infinite"] | None,
    ) -> int | Literal["infinite"] | None:
        if isinstance(value, int) and value <= 0:
            msg = "max_attempts は 1 以上で指定してください"
            raise ValueError(msg)
        return value


class ConditionNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    op: Literal[
        "all",
        "any",
        "not",
        "match",
        "never",
        "always",
        "state_equals",
        "state_not_equals",
        "text_contains",
        "text_equals",
        "text_matches",
    ]
    conditions: list[ConditionNode] = Field(default_factory=list)
    target: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("conditions")
    @classmethod
    def _validate_children(
        cls,
        value: list[ConditionNode],
        info: ValidationInfo,
    ) -> list[ConditionNode]:
        op = info.data.get("op")
        if op in {"match", "never", "always"} and value:
            msg = f"{op} 条件に子ノードは指定できません"
            raise ValueError(msg)
        if op in {"state_equals", "state_not_equals"} and value:
            msg = f"{op} 条件に子ノードは指定できません"
            raise ValueError(msg)
        if op in {"text_contains", "text_equals", "text_matches"} and value:
            msg = f"{op} 条件に子ノードは指定できません"
            raise ValueError(msg)
        if op in {"all", "any"} and not value:
            msg = f"{op} 条件は 1 つ以上の子ノードが必要です"
            raise ValueError(msg)
        if op == "not" and len(value) != 1:
            msg = "not 条件は 1 つの子ノードのみ指定できます"
            raise ValueError(msg)
        return value


class ActionSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    pointer_mode: Literal["move", "absolute", "adaptive"] = "move"
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def _canonical_type(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            msg = "action.type は空にできません"
            raise ValueError(msg)
        return cleaned


class TransitionMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default: str | None = None
    success: str | None = None
    failure: str | None = None
    timeout: str | None = None


class StepControl(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repeat: int | Literal["infinite"] | None = Field(default=None, gt=0)
    break_on: str | None = None
    max_duration: float | None = Field(default=None, gt=0.0)


class AutomationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str | None = None
    watch: WatchConfig
    conditions: ConditionNode | None = None
    actions: list[ActionSpec] = Field(default_factory=list)
    transitions: TransitionMapping | None = None
    control: StepControl | None = None

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            msg = "step.id は空にできません"
            raise ValueError(msg)
        return cleaned


class AutomationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    name: str | None = None
    description: str | None = None
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    regions: list[RegionDefinition] = Field(default_factory=list)
    steps: list[AutomationStep]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("version")
    @classmethod
    def _canonical_version(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            msg = "version は空にできません"
            raise ValueError(msg)
        return cleaned

    @model_validator(mode="after")
    def _ensure_unique_step_ids(self) -> AutomationConfig:
        seen = {step.id for step in self.steps}
        if len(seen) != len(self.steps):
            msg = "step.id は一意である必要があります"
            raise ValueError(msg)
        return self

    @property
    def needs_calibration(self) -> bool:
        return self.runtime.calibration.enabled
