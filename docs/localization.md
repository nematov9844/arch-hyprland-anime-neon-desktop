# Localization Guide

Localization foundation is prepared with key-based labels.

## Current approach

- Keep UI strings in label files
- Resolve by keys in scripts
- Fallback to English when key is missing

## Suggested language files

- `localization/en/settings.json`
- `localization/uz/settings.json`
- `localization/ru/settings.json`

## Next step

- Add `LANG` selector in settings
- Load proper label file based on selected language
- Reuse same keys across wallpaper/settings/system modules
