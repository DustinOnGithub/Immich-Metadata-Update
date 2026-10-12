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
        ("whatsapp", "VID-20210530-WA0001~2.mp4", "20210530"),
        ("whatsapp", "img-20200624-wa0007-Edited.JPG", "20200624"),
        ("screenshot_basic", "Screenshot_20220601-123456.png", "20220601"),
        ("screenshot_basic", "Screenshot_20211010-224958~2.png", "20211010"),
        ("screenshot_full", "Screenshot_2022-02-28_app.png", "2022-02-28"),
        ("screenshot_full", "Screenshot from 2022-02-28 18-50-41.png", "2022-02-28"),
        ("photo_editor", "PhotoEditor_20190427_151808482.jpg", "20190427"),
        ("camera_img", "IMG_20230720_223243_780.jpg", "20230720"),
        ("camera_img", "IMG_20200619_201658164.jpg", "20200619"),
        ("camera_img", "IMG_20211107_112711_159-bearbeitet.jpg", "20211107"),
        ("camera_img", "IMG_20170715_124845341_HDR-COLLAGE.jpg", "20170715"),
        (
            "camera_img",
            "IMG_20210706_131559655_BURST000_COVER-ANIMATION.gif",
            "20210706",
        ),
        ("animation", "20240324_211032-ANIMATION.gif", "20240324"),
        ("animation", "IMG_20220723_173027622-ANIMATION.gif", "20220723"),
        ("animation", "VID_20230211_113813889-ANIMATION.gif", "20230211"),
        ("timestamp", "20250815_093002.mp4", "20250815"),
        (
            "whatsapp_verbose",
            "WhatsApp Image 2022-02-28 at 19.03.43.jpeg",
            "2022-02-28",
        ),
        ("photo_free", "photo_free_20210318_160158.jpg", "20210318"),
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
        ("timestamp", "20250815_09300.mp4"),
        ("whatsapp_verbose", "WhatsApp Image 2022-02-28 at 19.03.jpeg"),
        ("photo_free", "photo_free_20210318_16015.jpg"),
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
        (
            "signal-2021-06-20-034442_exported_3335.jpg",
            "2021-06-20T03:44:42.000Z",
        ),
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


@pytest.mark.parametrize(
    ("filename", "expected_timestamp"),
    [
        ("IMG_20200619_201658164.jpg", "2020-06-19T20:16:58.000Z"),
        (
            "IMG_20211107_112711_159-bearbeitet.jpg",
            "2021-11-07T11:27:11.000Z",
        ),
        (
            "IMG_20170715_124845341_HDR-COLLAGE.jpg",
            "2017-07-15T12:48:45.000Z",
        ),
        (
            "IMG_20210706_131559655_BURST000_COVER-ANIMATION.gif",
            "2021-07-06T13:15:59.000Z",
        ),
    ],
)
def test_camera_pattern_corrects_date_and_time(filename, expected_timestamp):
    pattern = BUILTIN_PATTERNS["camera_img"]
    asset = Asset(
        id="asset-1",
        filename=filename,
        creation_date=datetime(2024, 1, 1, 12, 34, 56, tzinfo=timezone.utc),
    )

    corrected = find_mismatched_assets(
        [asset],
        pattern.regex,
        pattern.date_format,
        timezone.utc,
        pattern.time_format,
    )

    assert [item.corrected_date_str for item in corrected] == [expected_timestamp]


@pytest.mark.parametrize(
    ("filename", "expected_timestamp"),
    [
        ("20240324_211032-ANIMATION.gif", "2024-03-24T21:10:32.000Z"),
        (
            "IMG_20220723_173027622-ANIMATION.gif",
            "2022-07-23T17:30:27.000Z",
        ),
        (
            "VID_20230211_113813889-ANIMATION.gif",
            "2023-02-11T11:38:13.000Z",
        ),
    ],
)
def test_animation_pattern_corrects_date_and_time(filename, expected_timestamp):
    pattern = BUILTIN_PATTERNS["animation"]
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


@pytest.mark.parametrize(
    ("preset", "filename", "expected_timestamp"),
    [
        (
            "screenshot_basic",
            "Screenshot_20211010-224958~2.png",
            "2021-10-10T22:49:58.000Z",
        ),
        ("timestamp", "20250815_093002.mp4", "2025-08-15T09:30:02.000Z"),
        (
            "whatsapp_verbose",
            "WhatsApp Image 2022-02-28 at 19.03.43.jpeg",
            "2022-02-28T19:03:43.000Z",
        ),
        (
            "photo_free",
            "photo_free_20210318_160158.jpg",
            "2021-03-18T16:01:58.000Z",
        ),
    ],
)
def test_timestamp_patterns_correct_date_and_time(
    preset, filename, expected_timestamp
):
    pattern = BUILTIN_PATTERNS[preset]
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
