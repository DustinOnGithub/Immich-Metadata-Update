"""Filename-based date filtering for Immich assets."""

from __future__ import annotations

import logging
import re
from datetime import datetime, tzinfo
from typing import NamedTuple

from .models import Asset, CorrectedAsset

logger = logging.getLogger(__name__)


class DatePattern(NamedTuple):
    """A named regex with date and optional time strptime formats."""

    name: str
    regex: str
    date_format: str
    time_format: str | None = None


# Built-in patterns ----------------------------------------------------------

BUILTIN_PATTERNS: dict[str, DatePattern] = {
    "whatsapp": DatePattern(
        name="WhatsApp",
        regex=r"^(?:IMG|VID)-(\d{8})-WA\d{4}(?:[-_~][^.]+)?\.\w+$",
        date_format="%Y%m%d",
    ),
    "screenshot_basic": DatePattern(
        name="Screenshot (basic)",
        regex=r"^Screenshot_(\d{8})-(\d{6})(?:~\d+)?\.\w+$",
        date_format="%Y%m%d",
        time_format="%H%M%S",
    ),
    "screenshot_full": DatePattern(
        name="Screenshot (with app name or 'from')",
        regex=r"^Screenshot(?:_| from )(\d{4}-\d{2}-\d{2}).*$",
        date_format="%Y-%m-%d",
    ),
    "photo_editor": DatePattern(
        name="PhotoEditor",
        regex=r"^PhotoEditor_(\d{8})_\d+\.\w+$",
        date_format="%Y%m%d",
    ),
    "camera_img": DatePattern(
        name="Camera IMG",
        regex=r"^IMG_(\d{8})_(\d{6})(?:_?\d+)?(?:[-_][^.]+)?\.\w+$",
        date_format="%Y%m%d",
        time_format="%H%M%S",
    ),
    "animation": DatePattern(
        name="Animation",
        regex=r"^(?:(?:IMG|VID)_)?(\d{8})_(\d{6})(?:_?\d+)?-ANIMATION\.\w+$",
        date_format="%Y%m%d",
        time_format="%H%M%S",
    ),
    "timestamp": DatePattern(
        name="Timestamp",
        regex=r"^(\d{8})_(\d{6})\.\w+$",
        date_format="%Y%m%d",
        time_format="%H%M%S",
    ),
    "whatsapp_verbose": DatePattern(
        name="WhatsApp (verbose)",
        regex=r"^WhatsApp Image (\d{4}-\d{2}-\d{2}) at (\d{2}\.\d{2}\.\d{2})\.\w+$",
        date_format="%Y-%m-%d",
        time_format="%H.%M.%S",
    ),
    "photo_free": DatePattern(
        name="Photo free",
        regex=r"^photo_free_(\d{8})_(\d{6})\.\w+$",
        date_format="%Y%m%d",
        time_format="%H%M%S",
    ),
    "signal": DatePattern(
        name="Signal",
        regex=r"^signal-(\d{4}-\d{2}-\d{2})-(\d{2}(?:-?\d{2}){2})(?:[-_ ].*)?\.\w+$",
        date_format="%Y-%m-%d",
        time_format="%H%M%S",
    ),
}


def find_mismatched_assets(
    assets: list[Asset],
    regex: str,
    date_format: str,
    target_timezone: tzinfo,
    time_format: str | None = None,
) -> list[CorrectedAsset]:
    """Return assets whose filename date does not match their creation date.

    The corrected datetime is built in *target_timezone*. It preserves the
    original local time unless the pattern includes a time capture group.
    """
    pattern = re.compile(regex, re.IGNORECASE)
    results: list[CorrectedAsset] = []
    matched = 0

    for asset in assets:
        match = pattern.match(asset.filename)
        if not match:
            continue

        matched += 1
        filename_date_str = match.group(1)

        try:
            filename_date = datetime.strptime(filename_date_str, date_format).date()
            filename_time = None
            if time_format:
                filename_time = datetime.strptime(
                    match.group(2).replace("-", ""), time_format
                ).time()
        except ValueError:
            logger.warning(
                "Could not parse date '%s' from filename '%s'",
                filename_date_str,
                asset.filename,
            )
            continue

        creation_date = asset.creation_date.astimezone(target_timezone)
        if (
            filename_date == creation_date.date()
            and (
                filename_time is None
                or filename_time == creation_date.time().replace(microsecond=0)
            )
        ):
            continue  # dates already match — nothing to fix

        corrected_dt = datetime.combine(
            filename_date,
            filename_time or creation_date.time(),
            tzinfo=target_timezone,
        )
        results.append(
            CorrectedAsset(
                asset=asset,
                filename_date=filename_date,
                corrected_datetime=corrected_dt,
            )
        )

    logger.info(
        "Pattern matched %d assets, %d need date correction", matched, len(results)
    )
    return results
