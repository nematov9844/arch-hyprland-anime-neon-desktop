# 🛠 Troubleshooting

Common issues and how to fix them.

Repo: [nematov9844/arch-hyprland-anime-neon-desktop](https://github.com/nematov9844/arch-hyprland-anime-neon-desktop)

---

## ❌ Waybar not starting

```bash
waybar
```

Check logs:

```bash
waybar 2>&1 | less
```

---

## ❌ Hyprland config error

```bash
Hyprland --verify-config -c ~/.config/hypr/hyprland.conf
```

---

## ❌ Scripts not working

Check permissions:

```bash
chmod +x ~/.local/bin/*.sh
```

Check syntax:

```bash
bash -n ~/.local/bin/script.sh
```

---

## ❌ No sound control

Install:

```bash
sudo pacman -S pamixer
```

---

## ❌ Brightness not working

Check:

```bash
brightnessctl info
```

---

## ❌ Clipboard not working

Install:

```bash
sudo pacman -S wl-clipboard
```

---

## ❌ Notifications not showing

Install:

```bash
sudo pacman -S libnotify
```

---

## ❌ Bluetooth not working

```bash
sudo systemctl enable --now bluetooth
```

---

## ❌ Network issues

```bash
sudo systemctl enable --now NetworkManager
```

---

## ❌ Wallpaper not changing

Check if hyprpaper is running:

```bash
pgrep hyprpaper
```

Start it manually:

```bash
hyprpaper &
```

Check wallpaper scripts:

```bash
bash -n ~/.local/bin/wallpaper-apply.sh
bash -n ~/.local/bin/wallpaper-fetch.sh
```

---

## ❌ Video wallpaper not working

Make sure `mpvpaper` is installed and engine is set to `mpvpaper` in Wallpaper Settings.

---

## 🔍 Full system check

```bash
./doctor.sh
```

---

## 💡 Tip

Always run:

```bash
hyprctl logs | tail -n 100
```

to debug runtime issues.

---
