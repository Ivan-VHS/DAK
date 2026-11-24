const COMPONENTS = Object.freeze({
  "text.editor": {
    name: "Text Editor",
    label: "Текстовый редактор",
    token: "Lexi",
    singleName: "LexiDesk"
  },
  "audio.editor": {
    name: "Audio Editor",
    label: "Аудиоредактор",
    token: "Tone",
    singleName: "SonicLab"
  },
  "translation.workspace": {
    name: "Translator",
    label: "Переводчик",
    token: "Lingua",
    singleName: "LinguaDesk"
  }
});

const LOCALES = new Set(["en", "ru", "uk", "most"]);

function safeText(value, maximum, field) {
  if (typeof value !== "string") {
    throw new TypeError(field + " must be text");
  }
  const normalized = value.trim();
  if (normalized.length > maximum) {
    throw new RangeError(field + " exceeds " + maximum + " characters");
  }
  return normalized;
}

export function composeJoraRequest(options = {}) {
  const componentIds = options.components;
  const localeIds = options.locales;

  if (!Array.isArray(componentIds) || componentIds.length < 1 || componentIds.length > 24) {
    throw new TypeError("Select between 1 and 24 application components.");
  }
  const uniqueComponents = new Set();
  for (const id of componentIds) {
    if (typeof id !== "string" || !Object.hasOwn(COMPONENTS, id)) {
      throw new TypeError("Unknown Jora component: " + String(id));
    }
    if (uniqueComponents.has(id)) {
      throw new TypeError("Duplicate Jora component: " + id);
    }
    uniqueComponents.add(id);
  }

  if (!Array.isArray(localeIds) || localeIds.length < 1 || localeIds.length > 8) {
    throw new TypeError("Select at least one interface language.");
  }
  const uniqueLocales = new Set();
  for (const locale of localeIds) {
    if (!LOCALES.has(locale)) {
      throw new TypeError("Unsupported interface language: " + String(locale));
    }
    if (uniqueLocales.has(locale)) {
      throw new TypeError("Duplicate interface language: " + locale);
    }
    uniqueLocales.add(locale);
  }

  const preferredLocale = safeText(options.preferredLocale || localeIds[0], 16, "preferred locale");
  if (!uniqueLocales.has(preferredLocale)) {
    throw new TypeError("The primary language must be among selected interface languages.");
  }

  const customName = safeText(options.name || "", 80, "application name");
  const description = safeText(options.description || "", 500, "application description");
  const formula = componentIds.map((id) => COMPONENTS[id].name).join(" + ");
  const productName = customName || (
    componentIds.length === 1
      ? COMPONENTS[componentIds[0]].singleName
      : COMPONENTS[componentIds[0]].token +
        COMPONENTS[componentIds[1]].token +
        (componentIds.length > 2 ? " " + componentIds.length + "D" : "")
  );

  const request = {
    schema: "reaper.jora.request.v1",
    name: customName,
    description,
    components: [...componentIds],
    locales: [...localeIds],
    preferred_locale: preferredLocale,
    syntax_mode: "flow",
    language_targets: "auto"
  };

  return Object.freeze({
    name: productName,
    formula,
    request,
    target: "Reaper .rpr scaffold",
    generatedLocales: [...localeIds]
  });
}
