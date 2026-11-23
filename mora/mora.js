const projects=[
{id:"pytyliki",name:"Pytyliki",category:"system",role:"Processor diagnostics",description:"CPU-профили, измерения, мониторинг и локальные отчёты.",icon:"▣",colors:["#D5AA75","#78543A"],repo:"https://github.com/Ivan-VHS/Pytyliki",image:"https://raw.githubusercontent.com/Ivan-VHS/Pytyliki/main/assets/screenshots/pytyliki-workstation.png"},
{id:"reaper",name:"Reaper",category:"developer",role:"Language & Studio IDE",description:"Язык Reaper, редактор, запуск, отладчик, LSP и DAP.",icon:"R",colors:["#B2A0A1","#62556A"],repo:"https://github.com/Ivan-VHS/Reaper",image:"https://raw.githubusercontent.com/Ivan-VHS/Reaper/main/assets/screenshots/reaper-studio.png"},
{id:"oplague",name:"OPlague",category:"system",role:"Hardware workbench",description:"Инвентаризация устройств и безопасная инспекция пакетов.",icon:"O",colors:["#A7A08B","#5E624B"],repo:"https://github.com/Ivan-VHS/OPlague",image:"https://raw.githubusercontent.com/Ivan-VHS/OPlague/main/assets/screenshots/oplague-workbench.png"},
{id:"ventu",name:"VentuSample",category:"creative",role:"Sample workstation",description:"Создание лупов, сэмплов и офлайн-обработка аудио.",icon:"V",colors:["#AF6C60","#5C302A"],repo:"https://github.com/Ivan-VHS/VentuSample",image:"https://raw.githubusercontent.com/Ivan-VHS/VentuSample/main/assets/screenshots/ventusample-studio.png"},
{id:"duckos",name:"DuckOS",category:"system",role:"Operating system",description:"Системная платформа и домашний экран Mora.",icon:"🦆",colors:["#D6A65E","#80562F"],repo:"https://github.com/Ivan-VHS/DuckOS",image:""},
{id:"cockos",name:"Cockos",category:"creative",role:"Звук и запись",description:"Микшер по приложениям, входные устройства и запись.",icon:"♫",colors:["#A37E61","#5A3828"]},
{id:"kavun",name:"Kavun",category:"creative",role:"Фото и галерея",description:"Альбомы, изображения и быстрый просмотр.",icon:"◉",colors:["#A6AB87","#55634B"]},
{id:"kabon",name:"Ka-bon",category:"system",role:"Финансы",description:"Расходы, категории, лимиты и локальные отчёты.",icon:"₴",colors:["#D58B3D","#80562F"]},
{id:"gloverty",name:"Gloverty",category:"system",role:"Автоматизация",description:"Сценарии, условия и действия для повседневных задач.",icon:"ϟ",colors:["#A7A1A0","#5D5150"]},
{id:"po",name:"Po",category:"developer",role:"Браузер",description:"Поиск, вкладки, команды и рабочие ссылки.",icon:"⌕",colors:["#A5B4B0","#4D6963"]},
{id:"illidia",name:"Illidia",category:"creative",role:"Игры",description:"Игровая библиотека, ярлыки и коллекции.",icon:"⌘",colors:["#72908A","#354F4B"]},
{id:"unify",name:"Unify",category:"system",role:"Устройства",description:"Статусы устройств и передача файлов между инструментами.",icon:"⌁",colors:["#D9C4A4","#78634B"]}
];
const $=s=>document.querySelector(s), apps=$("#apps"), projectGrid=$("#projectGrid"), dialog=$("#appDialog"), search=$("#search");
let filter="all";
function card(app){const el=document.createElement("article");el.className="app-card";el.style.setProperty("--a",app.colors[0]);el.style.setProperty("--b",app.colors[1]);el.innerHTML=`<div class="app-top"><span class="app-icon">${app.icon}</span><span><h3>${app.name}</h3><small class="kind">${app.role}</small></span></div><p>${app.description}</p><button class="open-app" data-id="${app.id}">${app.repo?"Открыть пространство":"Открыть модуль"}</button>`;return el}
function render(){const q=search.value.trim().toLocaleLowerCase("ru");const visible=projects.concat(builtins).filter(a=>(filter==="all"||a.category===filter)&&[a.name,a.role,a.description].join(" ").toLocaleLowerCase("ru").includes(q));apps.replaceChildren(...visible.map(card));if(!visible.length){const p=document.createElement("p");p.textContent="Ничего не найдено";apps.append(p)}}
const builtins=projects.length?[
{id:"cockos",name:"Cockos",category:"creative",role:"Звук и запись",description:"Микшер по приложениям, запись и входные устройства.",icon:"♫",colors:["#ff83ad","#bd3e74"]},
{id:"kavun",name:"Kavun",category:"creative",role:"Фото и галерея",description:"Альбомы и быстрый просмотр изображений.",icon:"◉",colors:["#75e4a9","#219d6b"]},
{id:"kabon",name:"Ka-bon",category:"system",role:"Финансы",description:"Расходы, категории, лимиты и отчёты.",icon:"₴",colors:["#ffd45c","#c28a1d"]},
{id:"gloverty",name:"Gloverty",category:"system",role:"Автоматизация",description:"Сценарии и действия для повседневных задач.",icon:"ϟ",colors:["#ad98ff","#5c43bd"]},
{id:"po",name:"Po",category:"developer",role:"Браузер",description:"Поиск, вкладки и рабочие ссылки.",icon:"⌕",colors:["#82bfff","#275fba"]},
{id:"illidia",name:"Illidia",category:"creative",role:"Игры",description:"Игровая библиотека и коллекции.",icon:"⌘",colors:["#6ce4e0","#168c9c"]},
{id:"unify",name:"Unify",category:"system",role:"Устройства",description:"Статусы устройств и передача файлов.",icon:"⌁",colors:["#d8dcff","#7788cc"]}
]:[];
function openApp(id){const app=projects.concat(builtins).find(a=>a.id===id);if(!app)return;$("#dialogTitle").textContent=app.name;const content=$("#dialogContent");content.replaceChildren();if(app.image){const img=document.createElement("img");img.className="dialog-image";img.src=app.image;img.alt=app.name+" desktop capture";img.onerror=()=>img.remove();content.append(img)}const p=document.createElement("p");p.className="dialog-copy";p.textContent=app.description;content.append(p);const actions=document.createElement("div");actions.className="dialog-actions";if(app.repo){const a=document.createElement("a");a.href=app.repo;a.target="_blank";a.rel="noreferrer";a.textContent="Открыть репозиторий ↗";actions.append(a);const b=document.createElement("a");b.href=app.repo+"/releases";b.target="_blank";b.rel="noreferrer";b.textContent="Релизы и сборки ↗";actions.append(b)}else{const note=document.createElement("span");note.className="dialog-copy";note.textContent="Модуль зарегистрирован в Mora. Подключение самостоятельной реализации будет идти через контракт приложения.";actions.append(note)}content.append(actions);dialog.showModal()}
apps.addEventListener("click",e=>{const b=e.target.closest("[data-id]");if(b)openApp(b.dataset.id)});
search.addEventListener("input",render);
document.querySelectorAll(".nav").forEach(b=>b.addEventListener("click",()=>{filter=b.dataset.filter;document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("active",x===b));document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("selected",x.dataset.filter===filter));render()}));
document.querySelectorAll(".chip").forEach(b=>b.addEventListener("click",()=>{filter=b.dataset.filter;document.querySelectorAll(".chip").forEach(x=>x.classList.toggle("selected",x===b));document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("active",x.dataset.filter===filter));render()}));
function projectCard(app){const el=document.createElement("article");el.className="project-card";const img=document.createElement("img");img.className="project-image";img.alt=app.name+" desktop capture";img.loading="lazy";if(app.image)img.src=app.image;img.onerror=()=>img.removeAttribute("src");const info=document.createElement("div");const h=document.createElement("h3");h.textContent=app.name;const p=document.createElement("p");p.textContent=app.description;const actions=document.createElement("div");actions.className="actions";const repo=document.createElement("a");repo.href=app.repo;repo.target="_blank";repo.rel="noreferrer";repo.textContent="Репозиторий ↗";const details=document.createElement("a");details.href="#";details.textContent="Подробнее";details.onclick=e=>{e.preventDefault();openApp(app.id)};actions.append(repo,details);info.append(h,p,actions);el.append(img,info);return el}
projectGrid.replaceChildren(...projects.map(projectCard));
const themeOrder=["amber","light","dark"];
function setTheme(theme){
  if(theme==="amber") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme=theme;
  localStorage.setItem("mora-theme",theme);
}
$("#theme").onclick=()=>{
  const current=document.documentElement.dataset.theme||"amber";
  const index=themeOrder.indexOf(current);
  setTheme(themeOrder[(index+1)%themeOrder.length]);
};
$("#closeDialog").onclick=()=>dialog.close();dialog.addEventListener("click",e=>{if(e.target===dialog)dialog.close()});document.addEventListener("keydown",e=>{if(e.key==="Escape"&&dialog.open)dialog.close()});
$("#projectsJump").onclick=()=>$("#projects").scrollIntoView({
  behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"
});
function tick(){const now=new Date();$("#clock").textContent=new Intl.DateTimeFormat("ru-RU",{hour:"2-digit",minute:"2-digit"}).format(now);$("#heroClock").textContent=$("#clock").textContent;$("#date").textContent=new Intl.DateTimeFormat("ru-RU",{weekday:"long",day:"numeric",month:"long"}).format(now)}
const saved=localStorage.getItem("mora-theme");
if(themeOrder.includes(saved)) setTheme(saved);
else setTheme("amber");
tick();setInterval(tick,10000);render();
if("serviceWorker"in navigator&&location.protocol!=="file:")addEventListener("load",()=>navigator.serviceWorker.register("service-worker.js").catch(()=>{}));
