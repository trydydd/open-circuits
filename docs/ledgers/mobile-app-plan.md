# Open Circuits — Mobile App Release Plan

## Context

Open Circuits today ships three artifacts: GitHub Pages site, release tarball,
and a Kiwix ZIM. The content is already fully offline-capable: 48 MB of pure
HTML/CSS/JS with vendored fonts and zero external URLs (validated in
`overlay/inject_overlay.py:354`). A mobile app is a natural fourth artifact —
same content, distribution-store reach, persistent install on the user's device.

Hard requirements from the user:
- **Offline access to the full data is mandatory** (rules out anything that
  depends on a live URL)
- **Android first**, iOS to follow
- **Shippable to Google Play *and* alt-stores** (F-Droid, IzzyOnDroid, Aurora,
  GitHub Releases APK)
- **New features**: font/theme toggle, bookmarks + last-read, in-app search

---

## Architecture: pros/cons of each wrapper, with recommendation

### Option 1 — TWA (Trusted Web Activity) — **rejected**
A thin app that opens the GitHub Pages URL in Chrome.
- ✅ Tiny APK (~1 MB), trivial to build with Bubblewrap.
- ❌ **Requires network on first launch and for any uncached page** — even with
  a service worker, F-Droid does not accept TWAs because they delegate
  rendering to a proprietary browser (Chrome).
- ❌ No iOS counterpart.
- ❌ Tied to Digital Asset Links + a hosted PWA — adds web infra coupling we
  don't currently need.
- **Verdict: rules itself out — fails the offline-must and F-Droid goals.**

### Option 2 — Capacitor (Ionic) hybrid
One TypeScript/JS project; one `npx cap` invocation produces Android Studio
and Xcode projects. Bundles the static site as app assets.
- ✅ Single codebase, single build command for both platforms.
- ✅ Bundles assets — fully offline.
- ✅ Mature plugin ecosystem (StatusBar, SplashScreen, Preferences).
- ❌ Pulls Node + npm + ~hundreds of transitive deps into the project. F-Droid
  inclusion is possible but every dep must be reproducible-buildable from
  source; this is the most common F-Droid rejection cause.
- ❌ Capacitor itself ships first-party plugins that touch Google Play
  Services in some configurations — has to be carefully configured to stay
  fully FOSS.
- ❌ Conflicts with the project's "vanilla JS only, no framework" ethos. The
  mobile repo would feel different from everything else.
- ❌ Larger APK (~5–8 MB framework overhead before content).

### Option 3 — Native WebView wrappers (Kotlin + Swift) — **recommended**
A `MainActivity` (Android) and a `ViewController` (iOS), each ~100 LOC,
loading bundled HTML via `file:///android_asset/...` and `Bundle.main.url`.
- ✅ Fully offline by construction; no network code in the app at all.
- ✅ Smallest dependency surface — Android uses only AndroidX + the system
  WebView; iOS uses only `WKWebView`. F-Droid's preferred shape.
- ✅ No Google Play Services, no Firebase, no analytics — clean inclusion in
  F-Droid / IzzyOnDroid / Aurora without code changes.
- ✅ Smallest APK overhead (~1–2 MB before content).
- ✅ Native bridge for the three new features is straightforward (settings via
  `SharedPreferences` / `UserDefaults`, or just localStorage in the WebView).
- ❌ Two codebases instead of one. Each is tiny, but they need to be
  maintained in step.
- ❌ Slightly more upfront work than Capacitor for the iOS path — but the
  Android wrapper takes the same effort either way, and iOS is "later".

**Recommendation: Option 3 (native WebView wrappers).** It's the only option
that satisfies *both* the offline-must and the F-Droid-must without
contortions. The "two codebases" downside is small because each wrapper is
glue code; all real logic lives in the bundled HTML/CSS/JS that the website
already uses.

---

## Strategy

The clean split is:

- **This repo (`open-circuits`)** — implement the three new features
  (font/theme toggle, bookmarks, search) in the existing overlay so they
  benefit web, ZIM, *and* app simultaneously. The mobile app is then mostly
  chrome around an unchanged content bundle.
- **New repo (`open-circuits-mobile`)** — native Android and iOS wrappers.
  Pulls release tarballs from `open-circuits` as the content source.

This keeps the Python build pristine, keeps Android SDK / Xcode out of this
repo, and means a content-only update can ship to the website without
touching the mobile repo.

---

## Workstream A — Enhancements in this repo (`open-circuits`)

These all live in the existing `overlay/` directory and are picked up by the
existing `make build`. They benefit web/ZIM as well as the app.

### A1. Settings panel (font size + theme override)
- **`overlay/css/open-circuits.css`** — add `[data-font-scale="lg"]` /
  `["xl"]` rules and `[data-theme="dark"]` / `["light"]` overrides that win
  over `prefers-color-scheme`.
- **`overlay/js/settings.js`** *(new)* — small module that reads/writes
  `localStorage` keys `oc:font-scale`, `oc:theme`, applies them to
  `<html>` on load.
- **`overlay/templates/header.html`** — add a settings button (gear icon
  inline SVG) that opens a small popover. Behind `<noscript>` it stays
  hidden; the underlying CSS still respects `prefers-color-scheme`.
- Reuse: existing CSS theming structure already uses
  `prefers-color-scheme: dark` (per CLAUDE.md design context). Just layer a
  manual override on top.

### A2. Bookmarks + last-read
- **`overlay/js/bookmarks.js`** *(new)* — on every page load, store
  `oc:last-read = {path, scrollPct, title, ts}`; expose
  `oc:bookmarks = [{path, title, ts}]` add/remove API.
- **`overlay/js/navigation.js`** — already builds the sidebar TOC
  (`overlay/js/navigation.js`); extend it to render a "Resume" pill at top
  if `oc:last-read` is set, plus a "Bookmarks" section. No new files needed
  for UI.
- All in localStorage — works identically on web and inside WebView (need
  to enable DOM storage in the wrapper, see B1).

### A3. In-app search (also benefits website)
- **Index format**: pre-built JSON shipped with the site. Use
  [MiniSearch](https://github.com/lucaong/minisearch) or
  [FlexSearch](https://github.com/nextapps-de/flexsearch) — small (~10 KB),
  vendor into `overlay/js/vendor/`, no CDN.
- **Build step**: extend `overlay/inject_overlay.py` (or a new
  `overlay/build_search_index.py` invoked from `build/build_html.py`) to walk
  the processed pages, extract `<h1>`/`<h2>`/section text, and write
  `output/html/search-index.json`. Index size estimate: ~2–4 MB
  uncompressed; gzip-able for web, raw for app.
- **`overlay/js/search.js`** *(new)* — loads index on demand, renders
  results in a slide-down panel from the header search button.
- **`overlay/templates/header.html`** — add a search input (already has the
  brand row; sit it in there).
- **Tests**: `tests/test_search_index.py` checks the index covers all
  volumes (DC/AC/Semi/Digital/Ref/Exper) and basic queries match.

### A4. Manifest + icons (lets the web build also be installable as a PWA)
- **`overlay/templates/manifest.json`** *(new)* — copied to
  `output/html/manifest.json`; injected via `<link rel="manifest">` in
  `overlay/inject_overlay.py:313`.
- **`overlay/icons/`** *(new)* — generate 192×192, 512×512, maskable, and
  Apple-touch-icon variants from `overlay/logo.svg`.
- This is a small bonus: the website becomes installable on Android Chrome
  even before the native app ships, and the same icons feed the native
  wrappers.

**Effort estimate (Workstream A):** ~3–5 days of focused work. All
incremental improvements to existing files; no new infrastructure.

---

## Workstream B — Companion repo `open-circuits-mobile`

### B1. Android wrapper (Kotlin)
Layout:
```
open-circuits-mobile/
├── android/
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/org/hearth/circuits/MainActivity.kt
│   │   │   ├── assets/html/                      # downloaded from open-circuits release
│   │   │   ├── res/mipmap-*/ic_launcher.*        # adaptive icons
│   │   │   ├── res/values/strings.xml
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle.kts
│   ├── build.gradle.kts
│   └── settings.gradle.kts
├── fastlane/metadata/android/                    # Play + F-Droid descriptions
└── scripts/sync_content.sh                       # pulls tarball from open-circuits release
```

`MainActivity.kt` essentials (~80 LOC):
- `WebView` set to `loadUrl("file:///android_asset/html/index.html")`
- Enable `domStorageEnabled = true`, `javaScriptEnabled = true`
- Disable network access entirely: override `shouldInterceptRequest` so
  any non-`file://` URL returns an empty response (defence in depth — there
  shouldn't be any, but blocking enforces it)
- Override back button to use `webView.goBack()` until at root
- `WebViewAssetLoader` from AndroidX is the modern way to do this without
  `file://` security caveats.

Manifest: no `INTERNET` permission. This is a strong signal to F-Droid
auditors and to users (Play listing will say "no permissions").

Build & sign:
- Two flavours in `app/build.gradle.kts`:
  - `play` — AAB for Play Store, signed with upload key (Play App Signing
    handles the rest)
  - `foss` — APK for F-Droid / IzzyOnDroid / GitHub Releases, signed with
    a self-managed key (F-Droid will resign with their key for their build,
    so the project key is for the GitHub-direct APK)
- No flavour-specific code differences — both flavours are the same source.
  This is required for [Reproducible Builds on F-Droid](https://f-droid.org/docs/Reproducible_Builds/).

### B2. iOS wrapper (Swift) — phase 2
Layout:
```
open-circuits-mobile/ios/
├── OpenCircuits.xcodeproj
├── OpenCircuits/
│   ├── AppDelegate.swift
│   ├── ViewController.swift
│   ├── Assets.xcassets/AppIcon.appiconset/
│   └── html/                                     # bundled content
└── fastlane/metadata/ios/
```

`ViewController.swift` essentials (~60 LOC):
- `WKWebView` configured with `WKWebViewConfiguration().preferences`
- Load via `webView.loadFileURL(_:allowingReadAccessTo:)` pointing at
  `Bundle.main.url(forResource: "html/index", withExtension: "html")`
- `WKContentRuleListStore` rule blocking all non-`file:` requests
- Disable telephone-link autodetection, disable JS alert popups for cleanliness

Distribution channels for iOS:
- App Store (requires Apple Developer Program, $99/yr)
- AltStore / sideload via `.ipa` published to GitHub Releases (requires no
  Apple account, but users need their own signing — note in README)

### B3. Content sync
`scripts/sync_content.sh` (in companion repo):
- Take a tag/version (`open-circuits` release)
- Download tarball from `https://github.com/.../releases/download/...`
- Verify SHA256 against checksum file
- Extract into `android/app/src/main/assets/html/` and
  `ios/OpenCircuits/html/`
- Commit the resulting tree (so the mobile repo has reproducible-from-source
  content; F-Droid cannot fetch external tarballs at build time)

This is run *before* a mobile-app release, not at every Android build — keeps
Android builds hermetic.

### B4. CI in the companion repo
GitHub Actions:
- `android-build.yml` — on PR + tag: assemble both `play` and `foss`
  variants, upload artifacts.
- `android-release.yml` — on tag `v*`: build signed AAB, upload to Play
  Console via [`r0adkll/upload-google-play`](https://github.com/r0adkll/upload-google-play);
  also build signed APK and attach to GitHub Release.
- F-Droid does *not* need a CI job in our repo — once published, F-Droid's
  buildserver pulls from the tag and builds independently. We just need a
  metadata PR to fdroiddata (one-time + version bumps).
- `ios-build.yml` (later) — Xcode build, TestFlight upload via fastlane.

**Effort estimate (Workstream B):**
- Android wrapper end-to-end: ~3–5 days
- F-Droid metadata + first inclusion PR: ~1–2 days (often slow on F-Droid's
  side; budget weeks of calendar time for review)
- iOS wrapper: ~3 days once Android is stable

---

## Assets & metadata to prepare

- App name, short description, long description (3 variants — Play, F-Droid
  fastlane, App Store all want different lengths)
- Adaptive icon foreground/background (Android) — derive from
  `overlay/logo.svg`; copper accent on warm cream background
- iOS icon set (1024×1024 master, system generates the rest)
- Feature graphic (Play Store, 1024×500)
- Screenshots: phone + 7" + 10" tablet (Play Store wants at least 2 each;
  F-Droid wants at least 1)
- Privacy policy (required by Play; can be a static page on the same
  GitHub Pages site stating "no data collected, no network access")
- License: app code is GPL-3.0 (F-Droid friendly). Content remains CC BY-SA
  4.0 (already settled).

---

## Distribution channels

| Channel | Format | Signing | Effort |
|---|---|---|---|
| Google Play | AAB | Upload key + Play App Signing | One-time $25 dev account |
| F-Droid | APK | F-Droid's build infra | Inclusion PR to fdroiddata |
| IzzyOnDroid | APK | Project's own key | Just point at GitHub Releases |
| Aurora Store | (proxies Play) | n/a | Free once Play is live |
| GitHub Releases | APK | Project's own key | Already part of CI |
| App Store | IPA | Apple Developer Program | $99/yr, review process |
| AltStore | IPA | Self-signed in repo release | None beyond GitHub Releases |

---

## Compliance call-outs

- **Play Store target SDK**: must be current-1 (currently API 34). Trivial in
  Kotlin/AGP setup.
- **Play Data Safety form**: declare "no data collected, no data shared".
  Truthful since no `INTERNET` permission.
- **F-Droid anti-features**: with the above setup, none should apply
  (no NonFreeNet, no NonFreeDep, no Tracking).
- **Reproducible builds (F-Droid)**: keep `gradle.properties`,
  `build.gradle.kts` minimal; pin AGP and Kotlin versions; commit
  `gradle/wrapper/gradle-wrapper.properties`. Don't depend on env vars at
  build time.
- **Content licensing**: ATTRIBUTION.md and LICENSE.txt are already in
  `output/html/`; surface them via a "Credits" link in the app's
  WebView (already in `overlay/templates/footer.html`).

---

## Critical files (this repo) to be modified

- `overlay/css/open-circuits.css` — theme/font-scale overrides
- `overlay/js/navigation.js` — bookmarks + last-read UI in sidebar
- `overlay/js/settings.js` *(new)* — settings panel logic
- `overlay/js/bookmarks.js` *(new)* — bookmark store
- `overlay/js/search.js` *(new)* — search UI + index loading
- `overlay/js/vendor/minisearch.min.js` *(new, vendored)*
- `overlay/templates/header.html` — settings + search buttons
- `overlay/templates/manifest.json` *(new)* — PWA manifest
- `overlay/icons/` *(new)* — 192/512/maskable/apple-touch
- `overlay/inject_overlay.py` — inject manifest link, copy icons, validate
- `build/build_html.py` — call new search-index step
- `overlay/build_search_index.py` *(new)* — emit `output/html/search-index.json`
- `tests/test_search_index.py` *(new)*
- `tests/test_settings_assets.py` *(new)* — verify manifest/icons exist
- `Makefile` — no changes; existing `make build` picks up new steps
- `.github/workflows/build.yml` — no functional change; tests cover
- `README.md` — add "Mobile app" section linking to companion repo

## Critical files (new companion repo) to create

- `android/app/src/main/java/org/hearth/circuits/MainActivity.kt`
- `android/app/src/main/AndroidManifest.xml`
- `android/app/build.gradle.kts`
- `android/gradle/wrapper/gradle-wrapper.properties`
- `fastlane/metadata/android/en-US/{title,short_description,full_description}.txt`
- `fastlane/metadata/android/en-US/images/{icon,featureGraphic,phoneScreenshots/*}.png`
- `scripts/sync_content.sh`
- `.github/workflows/android-build.yml`
- `.github/workflows/android-release.yml`
- `README.md` — describe the architecture, point at `open-circuits` for content
- `LICENSE` — GPL-3.0
- (later) `ios/...`

---

## Verification

After Workstream A (this repo):
1. `make build` succeeds and `output/html/search-index.json` exists.
2. `make test` passes including new search/manifest/icon tests.
3. Open `output/html/index.html` in a browser:
   - Settings popover toggles font scale + theme; persists across reload
   - Search returns hits across all six volumes
   - Reading a chapter then reopening the site shows a "Resume" pill
   - Bookmarking a chapter and reopening shows it in the sidebar
4. Run [Lighthouse](https://developers.google.com/web/tools/lighthouse) PWA
   audit on `index.html` — should pass installability checks.

After Workstream B (companion repo):
1. `./gradlew :app:assembleFossDebug` produces an APK.
2. Install on a device with Wi-Fi off → all six volumes browseable, search
   works, settings persist, bookmarks survive app kill.
3. `adb shell dumpsys package org.hearth.circuits | grep permission` →
   no `INTERNET` permission listed.
4. APK's `META-INF` does not contain Google Play Services traces
   (`unzip -l app-foss-release.apk | grep -i google` → no hits beyond
   AndroidX).
5. F-Droid: run their reproducible-builds verification locally with
   [`fdroidserver`](https://gitlab.com/fdroid/fdroidserver) before opening
   inclusion PR.
6. iOS (later): open in simulator, verify offline (Airplane Mode), verify
   WKWebView blocks non-file URLs.

---

## Total effort estimate

- Workstream A (in this repo): ~1 working week
- Workstream B Android: ~1 working week
- Asset/metadata prep: ~2 days
- F-Droid inclusion: ~2 days work + weeks of review calendar time
- Workstream B iOS: ~3 days (after Android stable)
- Apple Developer Program enrolment + first App Store review: ~1–2 weeks
  calendar time

**Realistic timeline to first Play Store + GitHub Releases APK: ~3 weeks of
focused work. F-Droid live: +2–6 weeks waiting on F-Droid review. iOS App
Store: +1 month after Android ships.**
