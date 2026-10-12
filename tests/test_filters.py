"""Unit tests for built-in filename date patterns."""

from datetime import datetime, timezone
import re

import pytest

from immich_metadata_update.filters import BUILTIN_PATTERNS, find_mismatched_assets
from immich_metadata_update.models import Asset


@pytest.mark.parametrize(
    ("preset", "filename", "expected_date"),
    [
        ("whatsapp", "IMG-20240305-WA0013.jpg", "20240305"),
        ("whatsapp", "VID-20211030-WA0003.mp4", "20211030"),
        ("whatsapp", "IMG-20200624-WA0007-bearbeitet.jpeg", "20200624"),
        ("whatsapp", "VID-20210529-WA0011_exported_1568.jpg", "20210529"),
        ("whatsapp", "img-20200624-wa0007-Edited.JPG", "20200624"),
        ("screenshot_basic", "Screenshot_20220601-123456.png", "20220601"),
        ("screenshot_full", "Screenshot_2022-02-28_app.png", "2022-02-28"),
        ("screenshot_full", "Screenshot from 2022-02-28 18-50-41.png", "2022-02-28"),
        ("photo_editor", "PhotoEditor_20190427_151808482.jpg", "20190427"),
        ("camera_img", "IMG_20230720_223243_780.jpg", "20230720"),
        ("camera_img", "IMG_20200619_201658164.jpg", "20200619"),
        ("animation", "20240324_211032-ANIMATION.gif", "20240324"),
    ],
)
def test_builtin_patterns_extract_dates(preset, filename, expected_date):
    pattern = BUILTIN_PATTERNS[preset]

    match = re.match(pattern.regex, filename, re.IGNORECASE)

    assert match is not None
    assert match.group(1) == expected_date


@pytest.mark.parametrize(
    ("preset", "filename"),
    [
        ("whatsapp", "IMG-20240305-WA013.jpg"),
        ("whatsapp", "IMG_20240305_WA0013.jpg"),
        ("camera_img", "IMG_20200619_20165.jpg"),
        ("camera_img", "IMG_20200619_201658_.jpg"),
        ("animation", "20240324_21103-ANIMATION.gif"),
        ("signal", "signal-2021-04-04-21312.jpg"),
        ("signal", "signal-2021-04-04-21:31:23.jpg"),
    ],
)
def test_builtin_patterns_reject_malformed_filenames(preset, filename):
    pattern = BUILTIN_PATTERNS[preset]

    assert re.match(pattern.regex, filename, re.IGNORECASE) is None


@pytest.mark.parametrize(
    ("filename", "expected_timestamp"),
    [
        ("signal-2021-04-04-21-31-23-copy.jpg", "2021-04-04T21:31:23.000Z"),
        ("signal-2021-04-04-213123 (5).jpg", "2021-04-04T21:31:23.000Z"),
        ("signal-2021-09-14-003021.jpg", "2021-09-14T00:30:21.000Z"),
    ],
)
def test_signal_patterns_correct_date_and_time(filename, expected_timestamp):
    pattern = BUILTIN_PATTERNS["signal"]
    asset = Asset(
        id="asset-1",
        filename=filename,
        creation_date=datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
    )

    corrected = find_mismatched_assets(
        [asset],
        pattern.regex,
        pattern.date_format,
        timezone.utc,
        pattern.time_format,
    )

    assert [item.corrected_date_str for item in corrected] == [expected_timestamp]


def test_date_only_pattern_preserves_existing_time():
    pattern = BUILTIN_PATTERNS["camera_img"]
    asset = Asset(
        id="asset-1",
        filename="IMG_20200619_201658164.jpg",
        creation_date=datetime(2024, 1, 1, 12, 34, 56, tzinfo=timezone.utc),
    )

    corrected = find_mismatched_assets(
        [asset],
        pattern.regex,
        pattern.date_format,
        timezone.utc,
        pattern.time_format,
    )

    assert [item.corrected_date_str for item in corrected] == [
        "2020-06-19T12:34:56.000Z"
    ]


def test_animation_pattern_corrects_date_and_time():
    pattern = BUILTIN_PATTERNS["animation"]
    asset = Asset(
        id="asset-1",
        filename="20240324_211032-ANIMATION.gif",
        creation_date=datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
    )

    corrected = find_mismatched_assets(
        [asset],
        pattern.regex,
        pattern.date_format,
        timezone.utc,
        pattern.time_format,
    )

    assert [item.corrected_date_str for item in corrected] == [
        "2024-03-24T21:10:32.000Z"
    ]


def test_invalid_filename_date_does_not_create_a_correction():
    pattern = BUILTIN_PATTERNS["whatsapp"]
    asset = Asset(
        id="asset-1",
        filename="IMG-20241301-WA0001.jpg",
        creation_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    corrected = find_mismatched_assets(
        [asset],
        pattern.regex,
        pattern.date_format,
        timezone.utc,
        pattern.time_format,
    )

    assert corrected == []


def test_signal_ignores_matching_time_with_fractional_seconds():
    pattern = BUILTIN_PATTERNS["signal"]
    asset = Asset(
        id="asset-1",
        filename="signal-2021-04-04-213123 (5).jpg",
        creation_date=datetime(2021, 4, 4, 21, 31, 23, 456000, tzinfo=timezone.utc),
    )

    corrected = find_mismatched_assets(
        [asset],
        pattern.regex,
        pattern.date_format,
        timezone.utc,
        pattern.time_format,
    )

    assert corrected == []
