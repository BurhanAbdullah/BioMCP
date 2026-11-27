"""Tests for the dependency-light BioIO image metadata contract."""
import pytest

from bioio.image import ImageMetadata, PhysicalSize


def test_image_metadata_serializes_axes_channels_and_calibration():
    metadata = ImageMetadata(
        axes="TCZYX",
        shape=(2, 3, 4, 128, 256),
        dtype="uint16",
        channel_names=("DAPI", "GFP", "RFP"),
        physical_sizes={
            "X": PhysicalSize(0.108, "µm"),
            "Y": PhysicalSize(0.108, "µm"),
            "Z": PhysicalSize(0.5, "µm"),
        },
        acquisition={"instrument": "scope-1", "objective": "40x"},
    )
    assert metadata.to_dict() == {
        "axes": "TCZYX",
        "shape": [2, 3, 4, 128, 256],
        "dtype": "uint16",
        "channel_names": ["DAPI", "GFP", "RFP"],
        "physical_sizes": {
            "X": {"value": 0.108, "unit": "µm"},
            "Y": {"value": 0.108, "unit": "µm"},
            "Z": {"value": 0.5, "unit": "µm"},
        },
        "acquisition": {"instrument": "scope-1", "objective": "40x"},
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"axes": "XX", "shape": (4, 4)},
        {"axes": "YX", "shape": (4,)},
        {"axes": "YX", "shape": (4, 0)},
        {"axes": "AB", "shape": (4, 4)},
        {"axes": "CYX", "shape": (2, 4, 4), "channel_names": ("DAPI",)},
        {"axes": "YX", "shape": (4, 4), "physical_sizes": {"T": PhysicalSize(1, "s")}},
    ],
)
def test_image_metadata_rejects_invalid_dimensions_and_axes(kwargs):
    defaults = {"axes": "YX", "shape": (4, 4), "dtype": "uint16"}
    defaults.update(kwargs)
    with pytest.raises(ValueError):
        ImageMetadata(**defaults)


def test_image_metadata_rejects_non_json_acquisition_metadata():
    with pytest.raises(ValueError, match="acquisition"):
        ImageMetadata("YX", (4, 4), "uint16", acquisition={"bad": object()})


def test_physical_size_requires_positive_finite_value():
    for value in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            PhysicalSize(value, "µm")
