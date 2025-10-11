# Chromatic Scale Generator PLUS! – Beginner-Friendly Tutorial

Welcome! This guide walks you from the very first launch of **Chromatic Scale Generator PLUS! (Remastered)** to exporting polished chromatic scale folders. No prior audio engineering or coding experience is required—each step explains *what* to do and *why* it matters.

---

## 1. Understand the Workflow

Chromatic scales are organized collections of voice samples, one per musical note. The app helps you:

1. **Collect samples** (existing WAV files for a character).
2. **Tune and normalize** them automatically.
3. **Order the final notes** (Normal, Random, or a Custom symbolic pattern).
4. **Export** a ready-to-use chromatic folder for your DAW or mod.

Keep this big-picture flow in mind as you walk through the tutorial.

---

## 2. Install & Launch the App

### Option A – Use the Prebuilt Release
1. Download the latest ZIP from the [GitHub Releases page](https://github.com/immalloy/Chromatic-Scale-Generator-Plus-Remastered/releases).
2. Extract the ZIP anywhere you like (e.g., `Documents/CSGPR`).
3. Double-click `Chromatic Scale Generator PLUS!.exe`.

### Option B – Run from Source (Windows, macOS, Linux)
1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/).
2. Open a terminal or PowerShell.
3. Run:
   ```bash
   git clone https://github.com/immalloy/Chromatic-Scale-Generator-Plus-Remastered.git
   cd Chromatic-Scale-Generator-Plus-Remastered
   pip install -r requirements.txt
   python CSGPR.py
   ```

> 💡 **Tip:** If you hit any errors during launch, run `run_with_logs.bat` (Windows) or check the terminal output to see a detailed error log you can share with the community.

---

## 3. Tour the Interface

When the app opens you will see two tabs under **Configuration** on the right:

### 3.1 Scale Settings Tab
This tab controls how the app processes audio once files are selected.

- **Note / Octave / Semitones** – defines the pitch range of the export.
- **Normalization & Gap** – optional audio processing helpers.
- **Mode Toggle** – choose **Normal**, **Random**, or **Custom** sequencing behavior.
- **Randomization options** – seed controls for reproducible random runs.

### 3.2 Custom Order Tab
Visible when **Mode → Custom** is selected. It enables symbolic ordering based on vowel tags like `__A.wav` or folders named `A`.

Key parts of the tab:

| Section | Purpose |
| ------- | ------- |
| **Preset Dropdown** | Select the order/policy preset currently in use. |
| **Preset Actions** | New, Edit, Save As, Delete, Import, Export buttons for managing your presets. |
| **Selection Policy** | How the resolver picks files inside a bucket (First, Cycle, Random Seed). |
| **Length Handling** | Whether to Pad, Truncate, or Error if the preset order is shorter or longer than the required semitone count. |
| **Preview** | Opens a modal showing which files will be used or skipped. |
| **Template Controls** | Save/Load/Import/Export entire app templates (preset + configuration snapshot). |

All controls are disabled until **Custom** mode is selected to keep the classic workflow uncluttered.

---

## 4. Prepare Your Samples

1. Gather your `.wav` files into a folder.
2. Add **filename tags** to indicate which vowel each file represents. Use the pattern `sample__A.wav`, `growl__E.wav`, etc. Supported symbols are `A`, `E`, `I`, `O`, `U`, and `AY` (uppercase or lowercase).
3. If renaming files isn’t convenient, place files into subfolders named after the symbol (e.g., `vocals/A/1.wav`). The filename tag always wins if both are present.
4. Drop the folder onto the main window or click **Browse** to select it.

The file browser on the left lists every detected sample. Any symbol conflicts or unlabeled files appear with warnings in the log panel.

---

## 5. Generate a Chromatic in Normal or Random Mode

### Normal Mode (Classic Behavior)
1. Select **Mode → Normal**.
2. Adjust the **Base Note**, **Semitone Count**, and other processing preferences.
3. Choose an output directory.
4. Click **Generate Chromatic**.

The app processes files in alphabetical order, just like the legacy releases.

### Random Mode (Quick Variation)
1. Pick **Mode → Random**.
2. Optional: set a **Random Seed** so results are repeatable.
3. Generate—each pitch pulls a random sample from the input pool.

---

## 6. Craft a Custom Symbolic Order

Custom mode lets you build sophisticated vocal patterns (e.g., alternating vowels) and ensure consistent sequence lengths.

1. Switch the **Mode** toggle to **Custom**. The Custom Order tab becomes active.
2. Choose an existing preset from the dropdown (try **Standard Cycle** if you imported the examples) or click **New** to open the **Order Editor**.
3. In the editor:
   - Give your preset a name.
   - Add the symbol tokens you want (e.g., `A`, `I`, `AY`, `U`). Duplicate tokens are allowed.
   - Set the **Selection Policy**:
     - **First** – always uses the first file for each symbol.
     - **Cycle** – rotates through files in order each time the symbol appears.
     - **Random** – selects randomly, repeatable with a seed.
   - Pick a **Length Policy** (Pad is the easiest starting point).
   - Decide how to react if a symbol is missing (Skip, Ask, or Error).
   - Click **Preview** to see how the resolver will fill notes and which tokens will be skipped.
4. Click **Save**. The preset is now available in the dropdown.
5. Press **Preview** from the Custom Order tab if you want a final sanity check.
6. Run **Generate Chromatic**. The resolver follows your preset order while respecting the policies you set.

> 📝 **Remember:** Presets only define ordering behavior. You can reuse the same preset across many projects, regardless of the audio configuration.

---

## 7. Templates – One-Click Project Snapshots

Templates bundle the **current preset** *and* every option on the Scale Settings tab (note range, toggles, etc.). They are perfect when you regularly export the same configuration for multiple characters.

- **Save Template** – captures the current state into a `.csgtemplate.json` file.
- **Load Template** – applies a saved template immediately.
- **Import/Export** – share templates with collaborators or move them between machines.

Try the included examples in [`assets/examples`](../assets/examples/):

- `cycle_36_template.csgtemplate.json` – a 36-note standard cycle setup.
- `random_bounce_template.csgtemplate.json` – 24 notes using seeded random selection.

---

## 8. Exporting & Verifying Results

1. After generation finishes, open the output folder using **Open Output Folder**.
2. The app creates a structured directory containing tuned WAVs and metadata.
3. Drag the folder into your DAW or sampler to audition the notes.
4. If anything sounds off, tweak the preset policies or normalization settings and regenerate.

---

## 9. Troubleshooting Checklist

| Issue | What to Check |
| ----- | ------------- |
| **Files missing from output** | Confirm they have valid symbol tags or folders, and that your preset references those symbols. Preview will highlight skipped tokens. |
| **“Missing symbol” warnings** | Either rename the file with the `__SYMBOL` pattern or adjust your preset order to omit that symbol. |
| **Generation stopped with an error** | Length policy is set to **Error**, and the resolver could not fill the requested semitones. Change to **Pad** or **Truncate**, or add more samples. |
| **UI buttons greyed out** | Make sure the Mode toggle is on **Custom** when managing presets and templates. |
| **Random results change each run** | Provide a Random Seed (Random Mode) or enable seeded selection in your preset. |
| **App feels slow during scanning** | The app caches bucket scans per symbol set. Keep your sample folders tidy and avoid extremely deep directory trees for best results. |

---

## 10. Next Steps & Community

- Explore the `assets/examples` folder for more preset ideas and share your own in the community Discord.
- Translate the UI by copying a file from `i18n_pkg/` and customizing the strings.
- Open an issue or pull request on GitHub if you spot bugs or want to contribute improvements.

Happy chromatic crafting! 🎤🎹

