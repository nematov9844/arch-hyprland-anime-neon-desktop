# 📦 Installation Guide

This guide explains how to install the **Arch Hyprland Anime Neon Desktop**.

Repo: [nematov9844/arch-hyprland-anime-neon-desktop](https://github.com/nematov9844/arch-hyprland-anime-neon-desktop)

---

## 🔧 Requirements

* Arch Linux (or Arch-based distro)
* Internet connection
* sudo access

---

## 🚀 Quick Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/nematov9844/arch-hyprland-anime-neon-desktop/main/bootstrap.sh | bash
```

---

## 📥 Manual Install

```bash
git clone https://github.com/nematov9844/arch-hyprland-anime-neon-desktop.git
cd arch-hyprland-anime-neon-desktop
bash install.sh
```

---

## 🎯 Install Profiles

### Default (minimal)

```bash
bash install.sh
```

### Frontend developer

```bash
bash install.sh frontend
```

### Backend developer

```bash
bash install.sh backend
```

### Full setup

```bash
bash install.sh full
```

---

## 🧪 Verify installation

```bash
./doctor.sh
```

---

## 🔄 Update

```bash
bash update.sh
```

---

## 💾 Backup

```bash
bash backup.sh
```

---

## ♻️ Restore

```bash
bash restore.sh
```

---

## ❌ Uninstall

```bash
bash uninstall.sh
```

---

## ⚠️ Notes

* This setup modifies your `~/.config`
* Backup is recommended before install
* Wayland only (Hyprland)

---
