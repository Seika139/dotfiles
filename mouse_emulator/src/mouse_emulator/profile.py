from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

from .keys import normalize_combo, normalize_key_name


class ClickPosition(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)


class ProfileEntry(BaseModel):
    description: str
    click_position: ClickPosition
    keys: list[str]

    @field_validator("description")
    @classmethod
    def _strip_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("description cannot be empty")
        return cleaned

    @field_validator("keys")
    @classmethod
    def _validate_keys(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("keys must not be empty")
        normalize_combo(values)
        return [normalize_key_name(key) for key in values]


class Profile(BaseModel):
    actions: list[ProfileEntry]

    @field_validator("actions")
    @classmethod
    def _non_empty(cls, entries: list[ProfileEntry]) -> list[ProfileEntry]:
        if not entries:
            raise ValueError("profile must contain at least one action")
        return entries


@dataclass(slots=True)
class ProfileStore:
    base_dir: Path

    def ensure_base_dir(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def resolve_path(self, name_or_path: str) -> Path:
        candidate = Path(name_or_path)
        if candidate.is_absolute():
            return candidate
        if candidate.suffix:
            if candidate.exists():
                return candidate
            if candidate.parent == Path():
                return self.base_dir / candidate.name
            candidate_in_base = self.base_dir / candidate
            if candidate_in_base.exists():
                return candidate_in_base
            return candidate
        safe_name = candidate.name
        return self.base_dir / f"{safe_name}.json"

    def save(self, path: Path, profile: Profile) -> None:
        self.ensure_base_dir()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fp:
            json.dump(profile.model_dump(mode="json"), fp, ensure_ascii=False, indent=2)

    def load(self, path: Path) -> Profile:
        with path.open("r", encoding="utf-8") as fp:
            raw = json.load(fp)
        try:
            return Profile.model_validate(raw)
        except ValidationError as exc:
            raise ValueError(f"プロファイルの形式が不正です: {path}") from exc
