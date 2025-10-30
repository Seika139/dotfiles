from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Region:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    def to_relative(self, x: float, y: float) -> tuple[float, float]:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("キャリブレーション領域が無効です")
        if not self.contains(x, y):
            raise ValueError("キャリブレーション領域外の座標です")
        rel_x = (x - self.left) / self.width
        rel_y = (y - self.top) / self.height
        return rel_x, rel_y

    def to_absolute(self, rel_x: float, rel_y: float) -> tuple[float, float]:
        if not 0.0 <= rel_x <= 1.0 or not 0.0 <= rel_y <= 1.0:
            raise ValueError("相対座標は 0.0〜1.0 の範囲で指定してください")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("キャリブレーション領域が無効です")
        abs_x = self.left + rel_x * self.width
        abs_y = self.top + rel_y * self.height
        return abs_x, abs_y

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom

    @classmethod
    def from_points(cls, first: tuple[float, float], second: tuple[float, float]) -> Region:
        x1, y1 = first
        x2, y2 = second
        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        if right - left < 10 or bottom - top < 10:
            raise ValueError("キャリブレーション領域は十分な大きさが必要です")
        return cls(left=left, top=top, right=right, bottom=bottom)
