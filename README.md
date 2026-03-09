# Music Assistant Playlist Sensors

A custom Home Assistant integration that creates sensor entities for every playlist in your [Music Assistant](https://music-assistant.io/) library, making playlist data available across automations, dashboards, and template selects.

---

## What It Does

Home Assistant has no native way to expose Music Assistant playlist data as entities. This integration solves that by:

- Querying your Music Assistant library on a configurable schedule
- Creating a dedicated `sensor` entity for **each playlist** it finds
- Paginating through your full library (no 25-item cap)
- Waiting for Music Assistant to finish loading before fetching, so sensors are populated on startup without manual intervention

---

## Entities Created

One sensor per playlist, following this naming convention:

```
sensor.musicassistant_playlist_<playlist_name>
```

Examples:

```
sensor.musicassistant_playlist_all_music
sensor.musicassistant_playlist_christmas
sensor.musicassistant_playlist_500_random_tracks_from_library
```

### Sensor State

The state of each sensor is the **playlist name**.

### Sensor Attributes

| Attribute | Description |
|---|---|
| `uri` | Music Assistant URI (e.g. `library://playlist/2`) — use this to play the playlist |
| `media_type` | Always `playlist` |
| `image` | URL to the playlist artwork |
| `favorite` | Whether the playlist is marked as a favorite |
| `explicit` | Explicit content flag |
| `version` | Playlist version string |

---

## Installation

1. Copy the `ma_playlist_select` folder into your HA `custom_components` directory:

```
config/
  custom_components/
    ma_playlist_select/
      __init__.py
      config_flow.py
      sensor.py
      manifest.json
      translations/
        en.json
```

2. Restart Home Assistant.

3. Go to **Settings → Integrations → Add Integration** and search for **Music Assistant Playlist Sensors**.

4. Complete the setup form (see [Configuration](#configuration) below).

---

## Configuration

Setup is done entirely through the UI — no `configuration.yaml` changes required.

| Field | Description | Default |
|---|---|---|
| **Music Assistant Instance** | Dropdown of your connected MA instances | Required |
| **Refresh interval (seconds)** | How often to re-fetch your library | `21600` (6 hours) |
| **Favorites only** | Only create sensors for favorited playlists | `false` |

You can update the refresh interval and favorites toggle at any time via the integration's **Configure** button without restarting HA.

---

## Optional: Template Select Dropdown

If you want a single dropdown entity that lists all your playlists (useful for dashboards and automations), add the following to your `configuration.yaml`:

```yaml
input_text:
  ma_selected_playlist:
    name: MA Selected Playlist
    max: 255

template:
  - select:
      name: Music Assistant Playlist
      unique_id: ma_playlist_select
      icon: mdi:playlist-music
      options: >
        {{ states.sensor
          | selectattr('entity_id', 'match', 'sensor.musicassistant_playlist_.*')
          | map(attribute='state')
          | list
          | sort }}
      state: >
        {% set current = states('input_text.ma_selected_playlist') %}
        {% if current not in ('', 'unknown', 'unavailable') %}
          {{ current }}
        {% else %}
          {{ states.sensor
            | selectattr('entity_id', 'match', 'sensor.musicassistant_playlist_.*')
            | map(attribute='state')
            | list
            | sort
            | first }}
        {% endif %}
      select_option:
        action: input_text.set_value
        target:
          entity_id: input_text.ma_selected_playlist
        data:
          value: "{{ option }}"
```

The dropdown will automatically update whenever the integration fetches new playlist data.

---

## Using Playlist Data in Automations

### Get the name of the selected playlist
```yaml
{{ states('input_text.ma_selected_playlist') }}
```

### Get the URI of the selected playlist (for playback)
```yaml
{{ states.sensor
  | selectattr('entity_id', 'match', 'sensor.musicassistant_playlist_.*')
  | selectattr('state', 'eq', states('input_text.ma_selected_playlist'))
  | map(attribute='attributes.uri')
  | first }}
```

### Play the selected playlist on a media player
```yaml
action: music_assistant.play_media
data:
  entity_id: media_player.your_player
  media_id: >
    {{ states.sensor
      | selectattr('entity_id', 'match', 'sensor.musicassistant_playlist_.*')
      | selectattr('state', 'eq', states('input_text.ma_selected_playlist'))
      | map(attribute='attributes.uri')
      | first }}
  media_type: playlist
```

---

## Requirements

- Home Assistant 2023.x or newer
- [Music Assistant](https://music-assistant.io/) integration installed and configured

---

## Notes

- If two playlist names produce the same slug (e.g. `My List!` and `My List`), the second one will be skipped. Rename one of them to resolve the conflict.
- New playlists added to Music Assistant will appear automatically on the next scheduled refresh — no restart needed.
- The integration respects the `dependencies` field in `manifest.json`, so HA will always load Music Assistant before this integration.
