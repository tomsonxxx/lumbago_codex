# SZPIEG — Przeprojektowanie DJ Player + Odtwarzacz podstawowy (2026-06-15)

**Źródło user:** weDJ (Pioneer Android) screenshot + WMP/VLC/foobar + „crossfader za duży, burdel, nakładanie”.

## 12 referencji (punktowanie 1–10 dla Lumbago)

| # | UI | Układ kluczowy | Głośność / transport | Lumbago |
|---|-----|----------------|----------------------|---------|
| 1 | **Pioneer weDJ** | Wave top, jog center, **cienki crossfader na dole**, CUE/PLAY/SYNC per deck | Side faders, master implicit | **10** (binding) |
| 2 | Windows Media Player 11+ | Title+seek bar, **vol slider**, play/pause/stop, shuffle/repeat | Horizontal vol | **10** (basic odt) |
| 3 | VLC | Seek + time + **vol** + fullscreen | Minimal chrome | **9** |
| 4 | foobar2000 | Compact + columns, **vol w toolbar** | Skin tokens | **8** |
| 5 | Winamp 5 | **Mini mode** = wave strip + transport + vol | Pilot reference | **9** (compact) |
| 6 | Serato DJ Lite | 2 deck + **krótki crossfader** + gain per deck | Pro but clean | **9** |
| 7 | Rekordbox 7 Performance | Wave dominant, transport pod wave, mixer osobno | Booth standard | **9** |
| 8 | Traktor Pro | Modular strips, **crossfader ~25% szerokości** | Fader per deck | **8** |
| 9 | Mixxx | Preview deck + **compact deck** sizes | HP cue split | **8** |
| 10 | djay Pro | Touch 44pt, **round transport**, thin XF | iPad scale | **7** |
| 11 | Engine DJ | 4-deck grid, **mixer strip 1 row** | Color badges | **7** |
| 12 | VirtualDJ | Skin zones, **XF nie dominuje** | Skin % | **7** |

## Analiza weDJ (binding wizualny)

```
┌─────────────────────────────────────────────────────────────┐
│ [1] art + title + time    WeDJ logo    [2] art + title      │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │  ← waveform full width
├─────────────────────────────────────────────────────────────┤
│  (jog / deck controls — opcjonalnie w Lumbago Console)      │
├─────────────────────────────────────────────────────────────┤
│ CUE ▶ SYNC  │═══════ XF ═══════│  SYNC ▶ CUE               │  ← JEDEN rząd, XF ~20% wys.
│             MASTER / HP inline (opcjonalnie po bokach)       │
└─────────────────────────────────────────────────────────────┘
```

**Reguła:** Crossfader max **240px** szerokości, wys. **22px** — nigdy stretch=1 na całą szerokość.

## Build Spec — Odtwarzacz podstawowy (WMP minimum)

| Strefa | Elementy | Rozmiar @ 96 DPI |
|--------|----------|------------------|
| Header | Title stretch + BPM + spin (compact) | 1 row |
| Wave | RGB waveform stretch 7 | min 36% panelu |
| Time | `0:00 / 4:12` mono center | 14px |
| **Controls** | **VOL slider** + mute + CUE PLAY STOP | vol 120px, transport jak CDJ |
| Status | 1 linia muted | 10px |

## Build Spec — Konsola DJ (dual)

| Strefa | Elementy |
|--------|----------|
| Splitter | Deck A \| Deck B (bez transportu w decku — na mixer bar) |
| Deck panel | Badge, title, BPM, wave, time, TRIM, PITCH, SYNC/PFL/Q, EQ, hotcue, MEM/LOOP |
| **MixerCompactBar** | A-transport \| XF(240) \| B-transport \| MASTER \| CUE HP |

## Build Spec — Compact pilot (Winamp/weDJ mini)

| Strefa | Elementy |
|--------|----------|
| Header | Title truncated + spin anim |
| Wave | min 28% height, 80px floor |
| Bottom strip | VOL icon + slider + CUE ▶ ■ (icon-only) |
| Window | min 420×300, StaysOnTop optional |

## Lista przeróbek (binding — wykonanie 2026-06-15)

1. `MixerCompactBar` — weDJ bottom row, XF capped
2. `DualConsoleWidget` — zastąp pionowy mixer; deck bez TransportBar
3. `ConsoleDeckView` — rozdziel transport od TRIM/PITCH (2 rzędy)
4. `PlayerControlsBar` — VOL + mute dla OdtwarzaczView
5. `SimpleDeckController.set_volume()`
6. Tokeny `dual_mixer`: crossfader_max_w=240, crossfader_h=22
7. Compact: bottom strip layout, usuń stretch burdel
8. Testy layout + volume

*Per SZPIEG + user weDJ link + „przeprojektujcie cały dj player". must document identical.*