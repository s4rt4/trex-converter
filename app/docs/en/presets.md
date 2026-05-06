# Presets

Save and load favorite option combos per conversion page.

## Description

Every conversion page has a **Preset** combo plus **Load**, **Save**, **Delete** buttons below the options panel. Presets persist as JSON to `~/.config/trex-converter/presets/<kind>/<name>.json`.

Save captures `_options()` (every panel field plus main-form fields like quality and resize) minus the auto-injected `category` field. Load applies scalar fields to the main form, then delegates the payload to `extra_options_widget.apply_preset(payload)` when the panel exposes that hook.

## How to use

### Save a preset

1. Open a conversion page (such as **Image**).
2. Set options however you want (such as Quality 95, Resize `1920x>`, Strip metadata on).
3. Click **Save**. Enter a preset name (1 to 40 characters, alphanumeric plus space, hyphen, underscore).
4. The preset appears in the combo.

### Load a preset

1. Pick a preset from the combo.
2. Click **Load**. The saved fields are applied.
3. Browse for an input file.
4. Click **Add to Queue**.

### Delete a preset

1. Pick a preset from the combo.
2. Click **Delete** and confirm.

## Tips & Trick

- Presets are per page (kind), not global. Image presets are separate from Video presets, etc.
- Naming: descriptive but short. Such as `web-jpg`, `archive-pdf`, `4k-720p`, `mp3-320k`.
- The JSON file is readable, you can edit it manually with a text editor in `~/.config/trex-converter/presets/<kind>/`.
- Sync to another machine: copy the `~/.config/trex-converter/presets/` folder to the target.

## Troubleshooting

**"Preset name must be 1-40 characters of letters, digits, spaces, hyphens, or underscores".** Invalid characters (such as `/`, `\`, comma). Stick to alphanumeric plus space, hyphen, underscore.

**Preset doesn't appear after Save.** Refresh the page (click the sidebar entry again). Or check the JSON file in the config folder, it might have been written but the listing hasn't reloaded.

**Load doesn't apply all fields.** The panel doesn't implement the `apply_preset` hook. Only scalar fields (quality, resize, strip, bitrate) are applied by default.
