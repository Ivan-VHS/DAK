# Mora Belle — personal workspace suite

**Product:** DuckOS / Mora  
**Suite:** Mora Belle  
**Author/developer:** Ivan-VHS  
**Catalog:** [mora-belle-applications.v1.json](../catalogs/mora-belle-applications.v1.json)  
**Schema:** [mora-belle-applications.v1.schema.json](../schemas/mora-belle-applications.v1.schema.json)

## Purpose

Mora Belle is a first-party personal workspace for wardrobe planning, beauty-product dates, outfit comfort, purchase pauses, environment-aware routine notes, personal wellbeing check-ins, movement ideas, appointment planning, household tasks, trip packing, user-curated places, interest circles, career evidence and personal projects.

The visual direction uses blush and ivory surfaces, muted plum typography, sage details, ornamental lace edges, small ribbons and flower medallions. Decoration is framing only; navigation, focus indicators, labels and controls remain clear.

## Included tools

| # | Tool | Current browser behavior |
|---:|---|---|
| 1 | Капсульный шкаф | Add, categorize, list and remove clothing records |
| 2 | Сроки косметики | Record an opened date and PAO interval; calculate an estimated review date |
| 3 | Посадка и силуэты | Generate outfit guidance from occasion, silhouette and length |
| 4 | Пауза перед покупкой | Add an item to a waiting list and calculate remaining pause time |
| 5 | Уход по среде | Manually enter humidity, UV and water hardness; show general notes |
| 6 | Цикл и энергия | Session-only cycle/energy note; no predictions or persistent health record |
| 7 | Мягкий чек-ин | Session-only overload and recovery check-in |
| 8 | Движение по силам | Generate short general movement ideas from time and energy |
| 9 | План чек-апов | Record and remove appointment labels and dates |
| 10 | Дом без перегруза | Add, assign and remove household tasks |
| 11 | Чемодан за 5 минут | Generate a packing checklist from trip type, duration and manually selected weather |
| 12 | Уютные места | Save user-curated notes about lighting, noise and access |
| 13 | Круг по интересам | Save private interest and meetup ideas |
| 14 | Карьерный дневник | Record achievements, metrics and evidence notes |
| 15 | Мои проекты | Track a next step, target date and progress percentage |

## Run

Open mora/belle/index.html from the Mora desktop launcher or in a modern browser. The page has no third-party runtime dependencies and makes no remote requests. The Mora service worker precaches the Belle page assets.

The browser implementation is an interactive local prototype. It is not a native DuckOS process and does not provide a system-wide reminder engine, calendar broker, authenticated household/community service or hardware integration.

## Data handling

Structured records for wardrobe, beauty products, shopping pause, appointment dates, chores, places, interest ideas, career notes and projects are kept in the current browser profile under duckos.mora-belle.local.v1. The app provides explicit JSON export and delete actions.

Browser local storage is not an encrypted vault. Anyone with access to the same browser profile may be able to inspect it. Do not use a shared or untrusted profile for confidential records. Exported JSON is unencrypted.

Cycle/energy notes, overload check-ins and manual environment results are held in page memory only. Cycle and wellbeing entries are not written to localStorage or included in exports. Reloading or closing the page clears those notes. Before persistent sensitive health data is introduced, DuckOS needs a native encrypted personal-data service, per-app capability checks, key management, retention controls and security review.

No data is sent to a server. Location, calendar, camera, microphone, notifications, weather, bank, messaging and community services are not accessed. The app does not request body measurements or photos.

## Medical, safety and product boundaries

- Cycle and energy panels record personal observations; they do not diagnose, forecast fertility, predict symptoms or recommend treatment.
- Movement suggestions are general ideas, not medical, rehabilitation or individualized exercise advice.
- Appointment dates are a private list, not OS reminders or a recommended screening schedule.
- The skincare panel uses manually supplied conditions and general notes; it does not assess disease or guarantee product compatibility.
- PAO dates depend on the value entered from product packaging. The app cannot verify formulation, contamination or safety.
- Place notes are personal observations, not verified safety ratings or live location intelligence.
- Shopping pause never executes a purchase or payment.

## Native work still required

1. Signed application manifest, trusted launcher, per-app identity and capability broker.
2. Encrypted local personal-data service with key management, backup/restore policy and delete semantics.
3. Native notification and calendar APIs for reminders with explicit permission and revocation.
4. Opt-in weather/location adapters with source labels.
5. Authenticated household sharing and community messaging with consent, abuse handling and block/report controls.
6. Accessibility tests for screen readers, keyboard-only use, text scaling, high contrast and reduced motion.
7. Automated tests on the actual DuckOS image and package/build inclusion checks.

## Maturity

The Mora Belle browser workspace is **partial**: local interactions are implemented in the browser and data boundaries are explicit. Its fifteen concepts are not fifteen native packages. Native notifications, encrypted health storage, multi-user networking and OS permission enforcement remain future work. Existing app IDs and contributor ownership are preserved.
