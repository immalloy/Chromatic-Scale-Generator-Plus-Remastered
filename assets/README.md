# Splash Artwork

Splash screens are configured through `splashes.json`. Each entry lets you point to a different artwork file and toggle UI elements such as the title, subtitle, icon, credit panel, accent overlays and background dimming.

## Recommendations

* Target **1280×720** PNG files so they fill the splash window without stretching.
* Use descriptive filenames (for example `sirthegamercodersplash.png`) to keep variants organised.

If every configured image is missing the app falls back to the procedural gradient background.

```json
{
  "file": "artist_splash.png",
  "show_title": false,
  "show_subtitle": false,
  "show_icon": false,
  "show_credits": true,
  "show_title_panel": false,
  "show_credits_panel": false,
  "dim_background": false,
  "show_decorations": false
}
```

The example above keeps only the credits overlay visible for a particular splash screen.
