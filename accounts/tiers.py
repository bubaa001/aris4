"""
Shared tier/XP helper functions used by views and context processors.
"""
import math

TIER_COLORS = {
    'Initiate':        'bg-gray-600 text-white',
    'Scholar':         'bg-emerald-700 text-white',
    'Alpha Vanguard':  'bg-amber-600 text-white',
    'Elite Scholar':   'bg-purple-700 text-white',
    'Grandmaster':     'bg-red-700 text-white',
}


def get_tier_info(xp):
    """Return (level, tier_title, range_min, range_max) for a given XP value."""
    if xp < 500:
        return (1, 'Initiate', 0, 500)
    elif xp < 1500:
        return (2, 'Scholar', 500, 1500)
    elif xp < 3000:
        return (3, 'Alpha Vanguard', 1500, 3000)
    elif xp < 5000:
        return (4, 'Elite Scholar', 3000, 5000)
    else:
        level = 5 + (xp - 5000) // 3000
        rmin = 5000 + ((xp - 5000) // 3000) * 3000
        rmax = rmin + 3000
        return (level, 'Grandmaster', rmin, rmax)


def build_xp_context(current_xp):
    """Build XP progress context dict from a raw XP value."""
    base_level, tier_title, level_range_min, level_range_max = get_tier_info(current_xp)
    total_in_tier = level_range_max - level_range_min
    progress_in_tier = current_xp - level_range_min
    xp_percentage = int((progress_in_tier / total_in_tier) * 100) if total_in_tier > 0 else 100
    xp_to_next = max(0, level_range_max - current_xp)
    return {
        'current_level': base_level,
        'tier_title': tier_title,
        'xp_percentage': min(100, max(0, xp_percentage)),
        'xp_to_next': xp_to_next,
    }
