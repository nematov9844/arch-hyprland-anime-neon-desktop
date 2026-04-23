# arch-hyprland-anime-neon-desktop

Repo: [nematov9844/arch-hyprland-anime-neon-desktop](https://github.com/nematov9844/arch-hyprland-anime-neon-desktop)

## Features

- Wallpaper system:
  - local image wallpapers
  - Wallhaven search
  - recent history
  - favorites
  - settings menu
  - local video wallpaper foundation

## 🚀 Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/nematov9844/arch-hyprland-anime-neon-desktop/main/bootstrap.sh | bash
```

## 📦 Version

Current version: `v1.0.0`

## 📘 Documentation

- Installation → [docs/installation.md](docs/installation.md)
- Shortcuts → [docs/shortcuts.md](docs/shortcuts.md)
- Troubleshooting → [docs/troubleshooting.md](docs/troubleshooting.md)
- Release Guide → [release.md](release.md)
- Showcase Guide → [docs/showcase.md](docs/showcase.md)
- Localization Guide → [docs/localization.md](docs/localization.md)
- Plugin Guide → [docs/plugins.md](docs/plugins.md)

## Quick Install (Profile)

```bash
curl -fsSL https://raw.githubusercontent.com/nematov9844/arch-hyprland-anime-neon-desktop/main/bootstrap.sh | bash
```

Profile bilan:

```bash
curl -fsSL https://raw.githubusercontent.com/nematov9844/arch-hyprland-anime-neon-desktop/main/bootstrap.sh | bash -s -- full
```

`default | frontend | backend | full` profillari qo'llab-quvvatlanadi.

## Manual Install (git/gh clone)

HTTPS (`git clone`):

```bash
git clone https://github.com/nematov9844/arch-hyprland-anime-neon-desktop.git
cd arch-hyprland-anime-neon-desktop
bash install.sh
```

SSH (`git clone`):

```bash
git clone git@github.com:nematov9844/arch-hyprland-anime-neon-desktop.git
cd arch-hyprland-anime-neon-desktop
bash install.sh
```

GitHub CLI (`gh repo clone`):

```bash
gh repo clone nematov9844/arch-hyprland-anime-neon-desktop
cd arch-hyprland-anime-neon-desktop
bash install.sh
```

Profil tanlab:

```bash
bash install.sh frontend
bash install.sh backend
bash install.sh full
```

## Bootstrap haqida

`bootstrap.sh` git talab qilmaydi. U repo tarball'ni vaqtinchalik papkaga yuklaydi va `install.sh` ni ishga tushiradi.

Fork yoki boshqa branch bilan ishlatish:

```bash
REPO_OWNER=<github_username> REPO_BRANCH=main bash bootstrap.sh full
```
