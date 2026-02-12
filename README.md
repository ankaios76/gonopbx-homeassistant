# GonoPBX Home Assistant Integration

Custom HACS integration for [GonoPBX](https://github.com/ankaios76/gonopbx) — an Asterisk PBX web GUI.

## Features

- **Sensors:** Active calls, calls today, missed calls, unread voicemail
- **Binary Sensors:** Extension online/offline, trunk registration, system connectivity
- **Services:** Originate calls, toggle call forwarding
- **MQTT Events:** Real-time call events for automations (call started/answered/ended)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/ankaios76/gonopbx-homeassistant` as an **Integration**
4. Search for "GonoPBX" and install
5. Restart Home Assistant

### Manual

Copy `custom_components/gonopbx/` to your Home Assistant `config/custom_components/` directory.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **GonoPBX**
3. Enter:
   - **Host:** IP address of your GonoPBX server
   - **Port:** API port (default 8000)
   - **API Key:** The `HA_API_KEY` from your GonoPBX `.env` file
   - **Enable MQTT:** Check if you have MQTT configured in GonoPBX

## GonoPBX Setup

In your GonoPBX `.env` file, configure:

```env
# Generate a secure API key
HA_API_KEY=your-api-key-here

# Optional: MQTT for real-time events
MQTT_BROKER=192.168.1.x    # Your Mosquitto broker IP
MQTT_PORT=1883
MQTT_USER=ha_user
MQTT_PASSWORD=ha_password
```

Then rebuild: `docker compose up -d --build`

## Services

### `gonopbx.make_call`

Originate a call from an extension.

```yaml
service: gonopbx.make_call
data:
  extension: "1001"
  number: "004930123456"
```

### `gonopbx.toggle_forwarding`

Enable/disable call forwarding.

```yaml
service: gonopbx.toggle_forwarding
data:
  forward_id: 1
  enabled: true
```

## Automation Examples

### Notify on missed call

```yaml
automation:
  - alias: "Missed Call Notification"
    trigger:
      - platform: event
        event_type: gonopbx_call_ended
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.disposition == 'NO ANSWER' }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Missed Call"
          message: "Call from {{ trigger.event.data.caller }}"
```

### Mute TV during call

```yaml
automation:
  - alias: "Mute TV on incoming call"
    trigger:
      - platform: event
        event_type: gonopbx_call_started
    action:
      - service: media_player.volume_mute
        target:
          entity_id: media_player.living_room_tv
        data:
          is_volume_muted: true
```
