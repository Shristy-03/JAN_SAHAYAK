"""Shared template context for third-party map tile configuration."""

from django.conf import settings


def map_tiles(request):
    """Expose the public, browser-facing map tile configuration to templates."""
    return {
        'map_tile_url': settings.MAP_TILE_URL,
        'map_tile_attribution': settings.MAP_TILE_ATTRIBUTION,
        'map_tile_max_zoom': settings.MAP_TILE_MAX_ZOOM,
    }
