"""Music Assistant Playlist Sensor Entities."""
from __future__ import annotations

import logging
import re

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ma_playlist_select"


def _slug(name: str) -> str:
    """Convert a playlist name to a clean entity slug."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    return name


def _get_items(data) -> list[dict]:
    """Extract item list from coordinator data regardless of shape."""
    if not data:
        return []
    if isinstance(data, dict):
        return data.get("items", [])
    if isinstance(data, list):
        return data
    return []


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MA Playlist sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    known_slugs: set[str] = set()

    def _create_new_entities():
        items = _get_items(coordinator.data)
        new_entities = []
        for item in items:
            name = item.get("name") or ""
            if not name:
                continue
            slug = _slug(name)
            if slug not in known_slugs:
                known_slugs.add(slug)
                new_entities.append(MAPlaylistSensor(coordinator, item, slug))
        if new_entities:
            _LOGGER.info("Adding %d new playlist sensor(s)", len(new_entities))
            async_add_entities(new_entities, True)

    _create_new_entities()
    coordinator.async_add_listener(_create_new_entities)


class MAPlaylistSensor(CoordinatorEntity, SensorEntity):
    """A sensor entity representing a single Music Assistant playlist."""

    def __init__(self, coordinator, item: dict, slug: str) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._slug = slug
        self._item_name = item.get("name", "")
        self._attr_unique_id = f"musicassistant_playlist_{slug}"
        self._attr_name = f"MusicAssistant Playlist {self._item_name}"
        self._attr_icon = "mdi:playlist-music"

    def _current_item(self) -> dict | None:
        """Find this playlist's current data from the coordinator by slug."""
        for item in _get_items(self.coordinator.data):
            if _slug(item.get("name", "")) == self._slug:
                return item
        return None

    @property
    def entity_id(self) -> str:
        return f"sensor.musicassistant_playlist_{self._slug}"

    @entity_id.setter
    def entity_id(self, value: str) -> None:
        pass

    @property
    def native_value(self) -> str | None:
        item = self._current_item()
        return item.get("name") if item else None

    @property
    def extra_state_attributes(self) -> dict:
        item = self._current_item()
        if not item:
            return {}
        return {
            "uri": item.get("uri"),
            "media_type": item.get("media_type"),
            "image": item.get("image"),
            "favorite": item.get("favorite"),
            "explicit": item.get("explicit"),
            "version": item.get("version"),
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self._current_item() is not None
