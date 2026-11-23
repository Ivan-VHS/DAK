# Mora Commons — единый центр приложений DuckOS

**Product ID:** ivan-vhs.duckos.mora-commons  
**Catalog module:** mora/commons-catalog.js  
**Maturity:** the Mora Commons catalogue interface is implemented in the browser shell; the fifteen listed application products are specified, not shipped native applications.

## Purpose

Mora Commons is the shared discovery and organization surface for applications that support workshop work, training, outdoor activity, work and daily planning. It is part of the Mora desktop, not a separate operating system or a gender-specific product suite.

The catalogue groups applications by **user task**, never by gender. Every person has equal access to every entry. The product does not infer a user's interests, abilities, role or permissions from gender, and it does not use gender to rank, price, filter or recommend applications.

## Catalogue

| Area | Applications |
|---|---|
| Workshop and tools | TorqueSpec, Bore & Thread, GarageBay Log, Blade & Edge, RigCheck |
| Strength and recovery | IronCadence, RoundTimer Pro, RuckLedger, Grip & Hang, RecoveryLedger |
| Outdoors and autonomy | DeadReckon, CampLoad, WatchDesk |
| Work and personal discipline | MarginLine, ColdStart |

Each catalogue record defines a purpose, initial capability list, keywords and a specified maturity boundary in mora/commons-catalog.js.

## Implemented in the Mora shell

- Open Mora Commons from the system application grid.
- Search all fifteen catalogue entries by name, description, capability or keyword.
- Filter entries by four task-oriented categories.
- Open an information panel with the purpose, feature list and maturity notice.
- Save and remove favourites in the current browser profile.
- Use the same Mora theme, keyboard focus, responsive grid and reduced-motion behavior as the rest of the shell.

The catalogue and favourites are local to the browser profile. No account, cloud sync, background telemetry or gender-based personalization is introduced.

## Product maturity and boundaries

The **Mora Commons interface and catalogue interactions** are implemented in the browser shell.

The **fifteen application products** remain at specified maturity. Their cards are product records, not installed packages or executable application windows. No app-specific native service, persistent domain database, device driver, location engine, training sensor integration, bank connection or OS-level scheduler is claimed by this catalogue.

A product may be promoted to partial, implemented or verified only when its own code, interfaces, tests and platform evidence support that status. A visible card or a saved favourite is not evidence that the underlying application is implemented.

## Integration requirements for future app modules

Each future module must provide a versioned manifest with:

- Stable application ID, display name, version and entry point.
- Declared capabilities and permission rationale.
- Explicit data ownership and export/import contracts.
- Clear offline and network-dependent behavior.
- Keyboard, screen-reader, text-scaling and reduced-motion support.
- A lifecycle, error model and user-visible recovery path.
- Tests that distinguish browser behavior from native OS behavior.

Cross-app workflows must use versioned, validated events, least-privilege access, explicit consent, duplicate handling and visible completion or failure. A receiving app remains responsible for validating its own inputs and permissions.

## Equality and accessibility policy

- Equal discoverability and availability for every user.
- No “men's” or “women's” shelves, app gates, pricing, default permissions or recommendation rules.
- No assumptions that technical work, care, fitness, navigation, finance or creative work belongs to one gender.
- Inclusive language and neutral examples in product copy.
- Accessible operation through keyboard and assistive technology.
- Personalization may follow a user's chosen interests and settings, not inferred gender.

## Related architecture

- [Mora desktop and native integration](MORA_INTEGRATION.md)
- [Mora Design System](../MORA_DESIGN_SYSTEM.md)
- [Versioned Mora application registry](../mora/apps.json)
