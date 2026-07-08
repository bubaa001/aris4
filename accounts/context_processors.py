"""
Template context processor that injects tier/XP info for authenticated users
into every template context so the navbar and all pages can display it.
"""
from .tiers import get_tier_info, build_xp_context, TIER_COLORS

# Role-based styling for non-student users who don't have XP tiers
ROLE_BADGES = {
    'instructor': {'title': 'Instructor', 'color': 'bg-black text-white'},
    'admin':      {'title': 'Admin',      'color': 'bg-red-800 text-white'},
}


def user_tier_context(request):
    """Return tier info for the current user, or empty dict if anonymous."""
    ctx = {}
    if request.user.is_authenticated:
        user = request.user
        role = user.role

        if role == 'student':
            xp = getattr(user, 'xp', 0) or 0
            level, tier_title, _, _ = get_tier_info(xp)
            xp_ctx = build_xp_context(xp)
            ctx['user_tier'] = {
                'level': level,
                'title': tier_title,
                'xp': xp,
                'xp_percentage': xp_ctx['xp_percentage'],
                'xp_to_next': xp_ctx['xp_to_next'],
                'role': role,
                'tier_color_class': TIER_COLORS.get(tier_title, 'bg-gray-600 text-white'),
            }
        else:
            # Instructor / Admin: use role-based badge
            badge = ROLE_BADGES.get(role, {'title': role.title(), 'color': 'bg-gray-600 text-white'})
            ctx['user_tier'] = {
                'level': None,
                'title': badge['title'],
                'xp': 0,
                'xp_percentage': 0,
                'xp_to_next': 0,
                'role': role,
                'tier_color_class': badge['color'],
            }
    return ctx
