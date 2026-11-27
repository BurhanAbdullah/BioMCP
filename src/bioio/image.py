"""Dependency-light metadata contracts for microscopy image datasets."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from .core import _json_value


@dataclass(frozen=True)
class PhysicalSize:
    """Physical pixel/voxel spacing for one spatial axis."""

    value: float
    unit: str

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("physical size value must be numeric")
        if not math.isfinite(float(self.value)) or self.value <= 0:
            raise ValueError("physical size value must be finite and positive")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("physical size unit must be a non-empty string")


@dataclass(frozen=True)
class ImageMetadata:
    """Validated image shape, axes, channels and physical calibration."""

    axes: str
    shape: tuple[int, ...]
    dtype: str
    channel_names: tuple[str, ...] = ()
    physical_sizes: Mapping[str, PhysicalSize] = field(default_factory=dict)
    acquisition: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.axes, str) or not self.axes or len(set(self.axes)) != len(self.axes):
            raise ValueError("axes must be a non-empty string of unique axis labels")
        if any(axis not in "TCZYXS" for axis in self.axes):
            raise ValueError("axes may contain only T, C, Z, Y, X and S")
        if not isinstance(self.shape, (tuple, list)) or len(self.shape) != len(self.axes):
            raise ValueError("shape length must match the number of axes")
        shape = tuple(self.shape)
        if any(isinstance(n, bool) or not isinstance(n, int) or n <= 0 for n in shape):
            raise ValueError("shape dimensions must be positive integers")
        if not isinstance(self.dtype, str) or not self.dtype.strip():
            raise ValueError("dtype must be a non-empty string")
        channels = tuple(self.channel_names)
        if any(not isinstance(name, str) or not name.strip() for name in channels):
            raise ValueError("channel_names must contain non-empty strings")
        if channels and ("C" not in self.axes or len(channels) != shape[self.axes.index("C")]):
            raise ValueError("channel_names length must match the C axis")
        if not isinstance(self.physical_sizes, Mapping):
            raise ValueError("physical_sizes must be a mapping")
        sizes: dict[str, PhysicalSize] = {}
        for axis, size in self.physical_sizes.items():
            if axis not in "XYZ" or len(axis) != 1:
                raise ValueError("physical_sizes keys must be spatial axes X, Y or Z")
            if not isinstance(size, PhysicalSize):
                if isinstance(size, Mapping) and set(size) >= {"value", "unit"}:
                    size = PhysicalSize(size["value"], size["unit"])
                else:
                    raise ValueError("physical_sizes values must be PhysicalSize records")
            sizes[axis] = size
        if not isinstance(self.acquisition, Mapping):
            raise ValueError("acquisition must be a mapping")
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "channel_names", channels)
        object.__setattr__(self, "physical_sizes", sizes)
        object.__setattr__(self, "acquisition", _json_value(dict(self.acquisition), label="acquisition"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "axes": self.axes,
            "shape": list(self.shape),
            "dtype": self.dtype,
            "channel_names": list(self.channel_names),
            "physical_sizes": {
                axis: {"value": size.value, "unit": size.unit}
                for axis, size in self.physical_sizes.items()
            },
            "acquisition": _json_value(dict(self.acquisition), label="acquisition"),
        }
