from __future__ import annotations

import pytest

from mouse_core.region import Region


def test_relative_and_absolute_conversion() -> None:
    region = Region(left=0, top=0, right=200, bottom=100)
    rel_x, rel_y = region.to_relative(50, 25)
    assert pytest.approx(rel_x) == 0.25
    assert pytest.approx(rel_y) == 0.25

    abs_x, abs_y = region.to_absolute(rel_x, rel_y)
    assert abs_x == 50
    assert abs_y == 25


def test_to_relative_outside_region_raises() -> None:
    region = Region(left=0, top=0, right=100, bottom=100)
    with pytest.raises(ValueError, match="領域外"):
        region.to_relative(150, 50)


def test_to_absolute_invalid_range() -> None:
    region = Region(left=0, top=0, right=100, bottom=100)
    with pytest.raises(ValueError, match="範囲"):
        region.to_absolute(-0.1, 0.5)
