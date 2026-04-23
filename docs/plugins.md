# Plugin System Foundation

This project now includes a foundation for provider plugins.

## Structure

- `plugins/providers/registry.json`
- `plugins/providers/*.sh`

## Provider contract

Each provider script should support:

- `search <query>`
- `download <url> <dest>`

## Example providers

- `wallhaven`

## Next step

- Add plugin loader in wallpaper scripts
- Resolve provider by `config/wallpaper/sources.json`
