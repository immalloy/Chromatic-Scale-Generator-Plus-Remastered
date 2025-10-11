# 🎵 Chromatic Scale Generator PLUS! (Remastered)

### The ALMOST-ultimate modern tool for **Friday Night Funkin’** musicians, modders, and sound designers

*Remastered by Malloy — based on the original by ChillSpaceIRL and nullfrequency*

---

*Stuff is still being fixed btw :D*

![Version](https://img.shields.io/badge/version-3.1.3-pink?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge\&logo=python)
![License](https://img.shields.io/badge/License-GPLv3-green?style=for-the-badge)
![Build](https://img.shields.io/badge/Build-PyInstaller-lightgrey?style=for-the-badge)
![Community](https://img.shields.io/badge/FNF-Modding%20Tool-blueviolet?style=for-the-badge\&logo=fridaynightfunkin)

---

## 💾 Latest Release

➡️ [**Download the Latest Build**](https://github.com/immalloy/Chromatic-Scale-Generator-Plus-Remastered/releases)
Includes prebuilt EXE, sample presets, and language packs.

---

## What Is This?

An **FNF (Friday Night Funkin') chromatic scale** is a set of voice samples taken from a character’s vocals — each sample corresponds to a different musical note (C, C#, D, D#, etc.).
Together, they form a **complete octave**, letting you play the character’s voice like an instrument in FL Studio, Ableton, or any DAW.

This app automates that entire process — **extracting**, **pitching**, and **organizing** your samples with perfect tuning and structure.

No more manual pitch editing, no more pain — just clean, playable chromatics in minutes.

---

## Features

* **Modern PySide6 UI** — sleek, responsive, and enjoyable to use
* **Light and Dark themes** — choose your preferred appearance
* **Pink / Blue palettes** — optional color schemes for a personalized look
* **Multi-language support** — includes more than ten languages
* **Drag and Drop** — quickly load a folder of samples
* **Automatic validation** — detects missing or invalid `.wav` files
* **Custom order presets & templates** — arrange tagged vowels symbolically with import/export
* **Peak normalization** — optional pre-step to level audio before processing
* **“Ask before overwrite”** — prevents accidental file replacement
* **Threaded generation** — background processing without freezing the interface
* **Open Output Folder** — instantly access your generated files
* **Credits window** — includes contributors and Discord community link
* **Unified dialogs** — consistent notifications for information, errors, and warnings

---

## Perfect For

* **FNF musicians** creating or refining character voicebanks
* **Mod developers** producing chromatic scales for new characters
* **Tool developers** expanding or improving FNF modding utilities
* **Music producers** transforming FNF vocals into playable instruments

---

## Source Installation

1️⃣ Clone the repo

```
git clone https://github.com/YOUR_USERNAME/Chromatic-Scale-Generator-Plus-Remastered.git
cd Chromatic-Scale-Generator-Plus-Remastered
```

2️⃣ Install requirements

```
pip install -r requirements.txt
```

3️⃣ Run the app

```
python CSGPR.py
```

---

## 🧱 Building a Standalone App

For Windows:

```
build_chromatic_plus.bat
```

This script installs everything needed, then builds a **standalone EXE** with your icon.
When finished, your app will be inside:

```
dist\chromatic_gen_qt_plus_modular_i18n\
```

If it doesn’t open, use:

```
run_with_logs.bat
```

to view error logs safely.

---

## 🌍 Supported Languages

| Language           | File       | Status |
| ------------------ | ---------- | ------ |
| English            | lang_en.py | ✅      |
| Español (Simple)   | lang_es.py | ✅      |
| Português (Brasil) | lang_pt.py | ✅      |
| हिन्दी (Hindi)     | lang_hi.py | ✅      |
| 中文 (Mandarin)      | lang_zh.py | ✅      |
| 日本語 (Japanese)     | lang_ja.py | ✅      |
| 한국어 (Korean)       | lang_ko.py | ✅      |
| Русский (Russian)  | lang_ru.py | ✅      |
| Français (French)  | lang_fr.py | ✅      |
| বাংলা (Bengali)    | lang_bn.py | ✅      |

You can easily add new ones — just copy a file from `i18n_pkg/` and translate the strings.

---

## 🧠 Tech Stack

| Component        | Technology              |
| ---------------- | ----------------------- |
| GUI              | PySide6                 |
| Audio Processing | Praat (via Parselmouth) |
| Pitch Logic      | NumPy                   |
| Packaging        | PyInstaller             |
| Localization     | Modular i18n System     |

---

## 💬 Community & Credits

| Role              | Contributor       |
| ----------------- | ----------------- |
| 🧩 Original Tool  | **ChillSpaceIRL** |
| 🔄 First Remaster | **nullfrequency** |
| 🎨 Modern Edition | **Malloy (me!)** |

Join our Discord!
[![Discord](https://img.shields.io/badge/Join%20Discord-FNF%20Modding-7289da?style=for-the-badge\&logo=discord)](https://discord.gg/pe6J4FbcCU)

We share chromatics, FNF tools, tutorials, and modding fun!

---

## ⚖️ License

This project is open-source under the **GNU General Public License v3 (GPLv3)**.
That means you can modify, redistribute, and share — just keep it open-source.

> Copyright © 2025 ChillSpaceIRL, nullfrequency, and Malloy
> This software is free and open — forever.

See [LICENSE](LICENSE) for the full terms.

---

## 🧭 Roadmap

✅ Pink/Blue themes
✅ Multilingual interface
✅ Threaded “Cancel” button
✅ Unified dialogs
🕒 Add splash screen
🕒 macOS / Linux compatibility

---

<div align="center">

🎹 *“Built for modders. Tuned for musicians. Remastered for everyone.”*
**— Malloy, 2025**

</div>
