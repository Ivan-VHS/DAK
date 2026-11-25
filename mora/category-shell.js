const categoryPath = "./categories.v1.json";
const manifestPath = "./apps.json";

export function validateMoraCategoryRegistry(categoryRegistry, manifest) {
  if (categoryRegistry?.schema !== "duckos.mora.categories.v1" ||
      categoryRegistry.version !== 1 ||
      !Array.isArray(categoryRegistry.categories) ||
      categoryRegistry.categories.length !== 7) {
    throw new Error("Unsupported Mora category registry");
  }

  const apps = [
    ...(Array.isArray(manifest?.built_in_apps) ? manifest.built_in_apps : []),
    ...(Array.isArray(manifest?.ecosystem_workbenches) ? manifest.ecosystem_workbenches : [])
  ];
  const categories = new Map();
  const seen = new Set();

  for (const category of categoryRegistry.categories) {
    if (!category.id || categories.has(category.id)) {
      throw new Error("Duplicate or empty Mora category");
    }
    categories.set(category.id, category);
  }

  for (const app of apps) {
    if (!app.id || seen.has(app.id)) throw new Error("Duplicate or empty application ID");
    seen.add(app.id);
    const category = categories.get(app.category);
    if (!category || !category.application_ids.includes(app.id)) {
      throw new Error("Application category mismatch: " + app.id);
    }
    const expected = category.required_capabilities;
    const actual = Array.isArray(app.required_capabilities) ? app.required_capabilities : [];
    if (expected.length !== actual.length || expected.some((value, index) => value !== actual[index])) {
      throw new Error("Application capability mismatch: " + app.id);
    }
  }

  for (const category of categories.values()) {
    for (const id of category.application_ids) {
      if (!seen.has(id)) throw new Error("Category references an unknown application: " + id);
    }
    if (category.access === "privileged" &&
        (category.required_capabilities.length === 0 ||
         category.native_launch_policy !== "required-capability-and-native-broker")) {
      throw new Error("Privileged category must declare a capability and native broker gate");
    }
    if (category.access === "user" && category.required_capabilities.length !== 0) {
      throw new Error("User category must not inherit privileged launch capabilities");
    }
  }

  const assigned = categoryRegistry.categories.flatMap((category) => category.application_ids);
  if (assigned.length !== seen.size || new Set(assigned).size !== assigned.length) {
    throw new Error("Every application must appear in exactly one category");
  }
  return { apps, categories };
}

function makeElement(documentRef, tag, className, text) {
  const element = documentRef.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

export async function initializeMoraCategories(
  documentRef = document,
  fetcher = globalThis.fetch?.bind(globalThis)
) {
  const browser = documentRef.getElementById("mora-category-browser");
  const area = documentRef.querySelector(".app-area");
  const status = documentRef.getElementById("mora-category-status");
  if (!browser || !area || typeof fetcher !== "function") return false;

  try {
    const [categoryResponse, manifestResponse] = await Promise.all([
      fetcher(categoryPath),
      fetcher(manifestPath)
    ]);
    if (!categoryResponse.ok || !manifestResponse.ok) throw new Error("Application manifests are unavailable");
    const [categoryRegistry, manifest] = await Promise.all([
      categoryResponse.json(),
      manifestResponse.json()
    ]);
    const { apps } = validateMoraCategoryRegistry(categoryRegistry, manifest);
    const tiles = new Map();
    for (const tile of area.querySelectorAll(".app-tile[data-app]")) {
      if (!tiles.has(tile.dataset.app)) tiles.set(tile.dataset.app, tile);
    }
    for (const app of apps) {
      if (!tiles.has(app.id)) throw new Error("Mora launcher tile is missing: " + app.id);
    }

    const groups = documentRef.getElementById("mora-category-groups");
    const filters = documentRef.getElementById("mora-category-filters");
    if (!groups || !filters) throw new Error("Mora category surfaces are missing");
    groups.replaceChildren();
    filters.replaceChildren();

    const allButton = makeElement(documentRef,"button","mora-category-filter","Все");
    allButton.type = "button";
    allButton.dataset.categoryFilter = "all";
    allButton.setAttribute("aria-pressed","true");
    filters.append(allButton);

    for (const category of [...categoryRegistry.categories].sort((a,b)=>a.order-b.order)) {
      const section = makeElement(documentRef,"section","mora-category-section");
      section.dataset.categorySection = category.id;

      const heading = makeElement(documentRef,"div","mora-category-heading");
      heading.append(
        makeElement(documentRef,"h2","",category.title_ru),
        makeElement(documentRef,"span","",category.application_ids.length + " прилож.")
      );
      section.append(heading);
      section.append(makeElement(documentRef,"p","mora-category-description",category.description_ru));

      if (category.access === "privileged") {
        const capList = category.required_capabilities.join(", ");
        section.append(makeElement(
          documentRef,
          "p",
          "mora-category-access-note",
          "Повышенный доступ: " + capList +
          ". Нативный запуск запрещён до подключения capability broker и проверки гранта на стороне ОС. Плитки здесь открывают только локальные панели Mora."
        ));
      } else if (category.id === "development-federation") {
        section.append(makeElement(
          documentRef,
          "p",
          "mora-category-access-note",
          "Федеративные панели показывают исходные проекты, документацию и команды проверки. Mora не запускает внешние процессы."
        ));
      }

      const grid = makeElement(documentRef,"div","mora-category-grid");
      for (const id of category.application_ids) {
        const app = apps.find((entry)=>entry.id===id);
        const tile = tiles.get(id);
        tile.dataset.systemCategory = category.id;
        tile.dataset.requiredCapabilities = app.required_capabilities.join(" ");
        tile.dataset.nativeProcessLaunch = app.native_process_launch;
        grid.append(tile);
      }
      section.append(grid);
      groups.append(section);

      const button = makeElement(documentRef,"button","mora-category-filter",category.title_ru);
      button.type = "button";
      button.dataset.categoryFilter = category.id;
      button.setAttribute("aria-pressed","false");
      filters.append(button);
    }

    for (const child of [...area.children]) {
      if (child !== browser && !child.classList.contains("section-heading")) child.remove();
    }
    browser.hidden = false;

    filters.addEventListener("click",(event)=>{
      const button = event.target.closest("[data-category-filter]");
      if (!button || !filters.contains(button)) return;
      const selected = button.dataset.categoryFilter;
      for (const item of filters.querySelectorAll("[data-category-filter]")) {
        item.setAttribute("aria-pressed",String(item===button));
      }
      for (const section of groups.querySelectorAll("[data-category-section]")) {
        section.hidden = selected !== "all" && section.dataset.categorySection !== selected;
      }
    });

    if (status) status.textContent = "Категории загружены из манифестов: " + apps.length + " приложений, 7 групп.";
    return true;
  } catch (error) {
    if (status) status.textContent = "Категорийный реестр не применён: " + (error?.message || "ошибка проверки") + ". Показан исходный список Mora.";
    return false;
  }
}
