from __future__ import annotations

from datetime import date

SEASON_MONTHS = (1, 4, 7, 10)
MISSING_SEASONS = {(2019, 4)}


def season_month_for(month: int) -> int:
    for season_month in reversed(SEASON_MONTHS):
        if month >= season_month:
            return season_month
    return 1


def iter_ani_open_seasons(
    start_year: int = 2019,
    start_month: int = 1,
    today: date | None = None,
) -> list[tuple[int, int]]:
    today = today or date.today()
    end_year = today.year
    end_month = season_month_for(today.month)
    seasons: list[tuple[int, int]] = []

    for year in range(start_year, end_year + 1):
        for month in SEASON_MONTHS:
            if (year, month) < (start_year, start_month):
                continue
            if (year, month) > (end_year, end_month):
                continue
            if (year, month) in MISSING_SEASONS:
                continue
            seasons.append((year, month))

    return seasons

