"""Music Assistant Playlist Sensors Integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ma_playlist_select"
CONF_CONFIG_ENTRY_ID = "config_entry_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_FAVORITE_ONLY = "favorite_only"
DEFAULT_SCAN_INTERVAL = 21600
PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry (UI configured)."""

    # Options override initial data if the user has edited them
    config_entry_id = entry.data[CONF_CONFIG_ENTRY_ID]
    scan_interval = timedelta(
        seconds=(entry.options or entry.data).get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    favorite_only = (entry.options or entry.data).get(CONF_FAVORITE_ONLY, False)

    async def fetch_playlists():
        """Fetch all playlists from Music Assistant using pagination."""
        if not hass.services.has_service("music_assistant", "get_library"):
            raise UpdateFailed(
                "music_assistant.get_library is not yet available - "
                "Music Assistant may still be starting up"
            )
        try:
            all_items = []
            offset = 0
            limit = 25

            while True:
                response = await hass.services.async_call(
                    "music_assistant",
                    "get_library",
                    {
                        "media_type": "playlist",
                        "config_entry_id": config_entry_id,
                        "offset": offset,
                        "favorite": favorite_only,
                        "limit": limit,
                    },
                    blocking=True,
                    return_response=True,
                )

                if isinstance(response, list):
                    page_items = response
                elif isinstance(response, dict):
                    page_items = response.get("items", [])
                else:
                    break

                all_items.extend(page_items)
                _LOGGER.debug("Fetched %d playlists so far (offset %d)", len(all_items), offset)

                if len(page_items) < limit:
                    break

                offset += limit

            _LOGGER.info("Fetched %d total playlists from Music Assistant", len(all_items))
            return {"items": all_items}

        except Exception as err:
            raise UpdateFailed(f"Failed to fetch playlists: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="MA Playlists",
        update_method=fetch_playlists,
        update_interval=scan_interval,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _initial_fetch(_event=None):
        _LOGGER.debug("Music Assistant ready - fetching playlists")
        await coordinator.async_refresh()

    if hass.services.has_service("music_assistant", "get_library"):
        hass.async_create_task(_initial_fetch())
    else:
        @callback
        def _on_component_loaded(event):
            if event.data.get("component") == "music_assistant":
                hass.async_create_task(_initial_fetch())

        hass.bus.async_listen(EVENT_COMPONENT_LOADED, _on_component_loaded)

    # Re-init if options are changed via the UI
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
