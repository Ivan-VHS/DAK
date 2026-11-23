const CATALOG_URL = "./compatibility-targets.v1.json";
const BRIDGE_PROTOCOL = "duckos.compat.v1";

const mechanismLabels = {
  "native-execution":"Нативное исполнение",
  "api-translation":"Трансляция API",
  "binary-translation":"Бинарная трансляция",
  "emulation-virtualization":"Эмуляция / виртуализация"
};

function element(tag,className,text) {
  const node=document.createElement(tag);
  if(className)node.className=className;
  if(text!==undefined)node.textContent=text;
  return node;
}

function profileCard(profile) {
  const card=element("article","compat-profile");
  card.append(
    element("span","compat-model",mechanismLabels[profile.mechanism]||profile.mechanism),
    element("h4","",profile.name),
    element("p","",profile.approach),
    element("p","compat-caveat",profile.caveat)
  );
  return card;
}

function renderProfiles(container,profiles,query,mechanism) {
  const phrase=query.trim().toLocaleLowerCase("ru-RU");
  const matches=profiles.filter(profile=>{
    const modelMatches=mechanism==="all"||profile.mechanism===mechanism;
    const searchable=[profile.name,profile.approach,profile.caveat,...profile.formats]
      .join(" ").toLocaleLowerCase("ru-RU");
    return modelMatches&&searchable.includes(phrase);
  });
  container.replaceChildren();
  matches.forEach(profile=>container.append(profileCard(profile)));
  if(!matches.length)container.append(element("p","compat-empty","По этому запросу ничего не найдено."));
  return matches.length;
}

function showNativeStatus(container) {
  const status=element("div","compat-native-status");
  const bridge=globalThis.duckos&&globalThis.duckos.compatibility;

  if(!bridge||bridge.protocol!==BRIDGE_PROTOCOL||typeof bridge.getCapabilities!=="function") {
    status.append(
      element("strong","","Нативный исполнитель не подключён"),
      element("p","","Текущая Mora работает в браузере. Для реального запуска нужен процесс-менеджер DuckOS и установленная среда совместимости.")
    );
    container.append(status);
    return;
  }

  status.append(
    element("strong","","Нативный мост обнаружен"),
    element("p","","Проверяю список сред, объявленный процесс-менеджером DuckOS…")
  );
  container.append(status);

  Promise.resolve().then(()=>bridge.getCapabilities()).then(capabilities=>{
    if(!capabilities||capabilities.protocol!==BRIDGE_PROTOCOL||!Array.isArray(capabilities.runtimes)) {
      throw new Error("Неверный контракт нативного моста.");
    }
    const host=capabilities.host||{};
    const ready=capabilities.runtimes.filter(runtime=>
      runtime&&runtime.ready===true&&typeof runtime.id==="string"
    );
    status.replaceChildren(
      element("strong","","Нативный мост отвечает"),
      element("p","compat-native-host","Хост: "+(host.os||"неизвестная ОС")+" · "+(host.architecture||"архитектура не определена")),
      element("p","",ready.length
        ?"Готовые среды: "+ready.map(runtime=>runtime.name||runtime.id).join(", ")
        :"Процесс-менеджер не объявил готовых сред запуска.")
    );
  }).catch(error=>{
    status.replaceChildren(
      element("strong","","Ошибка нативного моста"),
      element("p","",error&&error.message?error.message:"Не удалось получить список исполнительных сред.")
    );
  });
}

export async function renderCompatibilityReference(container) {
  if(!container)return;
  container.replaceChildren(element("p","compat-loading","Загружаю каталог совместимости…"));

  try {
    const response=await fetch(CATALOG_URL,{cache:"no-cache"});
    if(!response.ok)throw new Error("HTTP "+response.status);
    const catalog=await response.json();

    if(catalog.schema!=="duckos.compatibility-targets.v1"||
       !Array.isArray(catalog.mechanisms)||catalog.mechanisms.length!==4||
       !Array.isArray(catalog.targets)||catalog.targets.length!==15) {
      throw new Error("Каталог не прошёл проверку структуры.");
    }

    const fragment=document.createDocumentFragment();
    fragment.append(
      element("h3","compat-heading","Модели исполнения"),
      element("p","compat-intro","Одно расширение .exe не означает один способ запуска. Важно отличать формат файла, CPU, системный API и графическую среду.")
    );

    const mechanisms=element("div","compat-mechanisms");
    catalog.mechanisms.forEach(item=>{
      const card=element("article","compat-mechanism");
      card.append(element("strong","",item.name),element("p","",item.description));
      mechanisms.append(card);
    });
    fragment.append(mechanisms);
    fragment.append(
      element("h3","compat-heading","Пятнадцать систем"),
      element("p","compat-intro","Справочник показывает используемые подходы и практические ограничения. Это не означает, что эти runtime установлены в DuckOS.")
    );

    const controls=element("div","compat-filters");
    const search=element("input","compat-search");
    search.type="search";
    search.placeholder="Найти ОС, формат или технологию…";
    search.setAttribute("aria-label","Поиск по справочнику совместимости");

    const filter=element("select","compat-select");
    filter.setAttribute("aria-label","Фильтр по механизму");
    const all=element("option","","Все механизмы");
    all.value="all";
    filter.append(all);
    catalog.mechanisms.forEach(item=>{
      const option=element("option","",item.name);
      option.value=item.id;
      filter.append(option);
    });
    controls.append(search,filter);

    const count=element("p","compat-count");
    const results=element("div","compat-profiles");
    const update=()=>{
      const visible=renderProfiles(results,catalog.targets,search.value,filter.value);
      count.textContent="Показано систем: "+visible+" из "+catalog.targets.length;
    };
    search.addEventListener("input",update);
    filter.addEventListener("change",update);
    update();
    fragment.append(controls,count,results);

    fragment.append(element("h3","compat-heading","Состояние DuckOS"));
    const nativeArea=element("div","compat-native-area");
    showNativeStatus(nativeArea);
    fragment.append(nativeArea);

    fragment.append(element("p","compat-disclaimer",
      "Безопасность: браузерная Mora не исполняет выбранный файл. Будущий native launcher должен проверять манифест, архитектуру, права, изолированное окружение и разрешённый путь; создавать процесс через нативный process API со структурированным списком аргументов, а не через shell."
    ));
    container.replaceChildren(fragment);
  } catch(error) {
    container.replaceChildren(element("p","compat-error",
      "Не удалось загрузить справочник: "+(error&&error.message?error.message:"неизвестная ошибка")));
  }
}
