"""Config flow for Music Assistant Playlist integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ma_playlist_select"
CONF_CONFIG_ENTRY_ID = "config_entry_id"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_FAVORITE_ONLY = "favorite_only"
DEFAULT_SCAN_INTERVAL = 21600


def _get_ma_instances(hass: HomeAssistant) -> dict[str, str]:
    """Return a dict of {config_entry_id: title} for all MA instances."""
    return {
        entry.entry_id: entry.title
        for entry in hass.config_entries.async_entries("music_assistant")
    }


class MAPlaylistConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user initiation step."""
        errors: dict[str, str] = {}

        ma_instances = _get_ma_instances(self.hass)

        if not ma_instances:
            return self.async_abort(reason="no_music_assistant")

        if user_input is not None:
            # Prevent duplicate entries for the same MA instance
            await self.async_set_unique_id(user_input[CONF_CONFIG_ENTRY_ID])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=ma_instances[user_input[CONF_CONFIG_ENTRY_ID]],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_CONFIG_ENTRY_ID): vol.In(ma_instances),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    int, vol.Range(min=60)
                ),
                vol.Optional(CONF_FAVORITE_ONLY, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return MAPlaylistOptionsFlow(config_entry)


class MAPlaylistOptionsFlow(config_entries.OptionsFlow):
    """Handle options (edit after setup) flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialise the options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the options form."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options or self.config_entry.data

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=60)),
                vol.Optional(
                    CONF_FAVORITE_ONLY,
                    default=current.get(CONF_FAVORITE_ONLY, False),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
