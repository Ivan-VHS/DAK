# Concrete Thump — East Slavic ritual sample workflow

**Project:** DuckOS  
**Application:** Mora / Concrete Thump  
**Maintainer:** Ivan-VHS  
**Browser prototype status:** partial local workflow  
**Native DuckOS audio service:** not implemented

## Purpose

Concrete Thump is a tempo, swing and sample-preparation workspace for heavyweight modern Trap. Its default production profile is **160 BPM** with **60% swing**, Orthodox choral references and East Slavic seasonal and ceremonial song traditions.

The source families are deliberately distinct:

- **Orthodox liturgical material:** znamenny chant and Byzantine-Slavic chant.
- **East Slavic folk and seasonal material:** Kolyadky, Vesnyanky, Kupala songs and harvest songs.
- **Ceremonial folk material:** wedding songs and funeral laments.

The application can combine these references in one arrangement profile without claiming that liturgical chant and folk ritual songs have the same history, function or religious context. The production direction favors deep male choir timbres, archaic polyphony, modal minor-key melodies, solemn refrains and deliberate call-and-response.

## Current browser workflow

Open **Mora → Concrete Thump**.

1. Choose the vocal focus: Orthodox liturgical, East Slavic folk, or a layered arrangement that preserves the distinction.
2. Select the chant and song families independently.
3. Choose a sample treatment: chopped call-and-response, long choir beds, or granular vocal fragments.
4. Set BPM and swing. Defaults are 160 BPM and 60%; the controls accept 40–240 BPM and 50–75% swing.
5. Add audio files for local browser preview and choose one as the choir source. Supported formats depend on the browser's native media support; common file types include WAV, MP3, FLAC, OGG, M4A, AAC, AIFF, OPUS and WebM.
6. Enter a source/credit note and the declared rights basis for each sample.
7. Edit the 16-step rows for kick, snare/clap, hi-hat, 808 and choir chops. The default pattern gives a starting point rather than a fixed genre template.
8. Preview four bars. The browser synthesizes the drum and 808 lanes and chops the selected choir recording according to the chosen treatment.
9. Render the same four-bar pattern to WAV, save the profile, or export the prompt, a JSON profile or a Reaper timing helper.

The built-in production prompt is limited to **500 characters** and emphasizes Orthodox choir / East Slavic ritual sources, 808-driven Trap, rapid hi-hats, triplet bursts, swing, double-time bounce, stutter edits and negative-space drops.

## Local files, bounds and rights

Audio import is initiated by the user and stays in the current browser session. Files are previewed through browser object URLs and decoded only when the sequencer plays or renders the selected choir source; closing the Concrete Thump window releases those URLs. The browser profile stores rhythm settings, the step sequence and sample metadata only. It does not persist audio bytes, upload files, search the Internet for recordings, or sync media across devices. Re-select a previously catalogued file to audition it again.

The UI limits imports to eight samples, 25 MiB per file and 80 MiB total per open session. Playback and WAV rendering are bounded to a four-bar sequence. The drum sounds are simple browser-generated tonal/noise voices with a master compressor; they are not acoustic drum samples or a substitute for a dedicated production engine. These are application guardrails, not a general-purpose audio decoder or malware scanner.

Use recordings that you own, have permission to use, or can verify as public-domain or appropriately licensed. The credit and rights fields are declarations entered by the user; DuckOS does not verify copyright status, license terms, performer identity or public-domain status. Sacred and community recordings may have cultural protocols beyond copyright. Respect the source community and any restrictions on reuse.

## Exports

- **JSON profile:** a versioned `duckos.concrete-thump-profile.v2` payload with BPM, swing, selected source families, treatment mode and sample metadata. Audio bytes are not embedded.
- **Production prompt:** a UTF-8 text file containing the generated prompt, capped at 500 characters.
- **Reaper timing helper:** a `.rpr` source file that calculates swung sixteenth-note offbeat markers in milliseconds from BPM and swing.

The timing helper is not an audio renderer, MIDI generator, DAW project, sample slicer or hardware MPC emulator. Its swing calculation is an explicit reference convention for manual arrangement, not a measured model of a physical MPC.

## Architecture and maturity

| Layer | Current behavior | Boundary |
|---|---|---|
| Mora UI | Source selections, rhythm controls, local sample preview, rights metadata and export actions | Browser application panel |
| Profile module | Validated versioned profile, legacy BPM/swing migration and bounded sample metadata | Local browser storage |
| Browser sequencer | 16-step kick/snare/hat/808/choir lanes; Web Audio playback and four-bar WAV rendering | No native driver, device routing, MIDI, multitrack DAW or OS audio service |
| Reaper companion | Reaper source calculates offbeat markers | Uses the existing Reaper CLI/runtime; no audio runtime is added |
| Cockos | Existing, separate audio/recording product | No automatic sample handoff or cross-app audio bus is claimed |

The native DuckOS application remains **specified**. The interactive Mora implementation is **partial**. The application UI does not prove that DuckOS has a kernel audio subsystem, native sound server, device mixer, low-latency driver, or full DAW.

## Verification

From the DuckOS repository root, run:

~~~sh
npm test
python -m json.tool catalogs/preinstalled-applications.v1.json > /dev/null
~~~

The Node test suite covers profile defaults and normalization, 16-step sequence bounds, v1-to-v2 profile migration, local persistence, sample count/size/type limits, the 500-character prompt, Reaper source generation and the Mora AI app-opening alias. Browser playback and WAV export should also be checked in a current browser with Web Audio and OfflineAudioContext support.

For the companion Reaper example, run from the Reaper repository root:

~~~sh
python -m reaper --check examples/duckos_ritual_trap_grid.rpr
python -m reaper examples/duckos_ritual_trap_grid.rpr
~~~

Static checking and execution validate the timing worksheet only; they do not process audio.

## Related documentation

- [Preinstalled application suite](PREINSTALLED_APPLICATIONS.md)
- [Mora integration](MORA_INTEGRATION.md)
- [Native Reaper integration](REAPER_INTEGRATION.md)
- [Reaper timing workflow](https://github.com/Ivan-VHS/Reaper/blob/main/docs/DUCKOS_RITUAL_TRAP_WORKFLOW.md)
