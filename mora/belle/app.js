const STORAGE_KEY = "duckos.mora-belle.local.v1";
const persistentFields = ["wardrobe","beauty","shopping","checkups","chores","places","circles","career","projects"];
const data = Object.fromEntries(persistentFields.map((key) => [key, []]));
const session = {cycle:null,reset:null,routine:null};
const modules = [
{id:"wardrobe",title:"Капсульный шкаф",category:"style",icon:"👗",description:"Образы из вещей, которые уже есть. Без давления и лишних покупок."},
{id:"beauty",title:"Сроки косметики",category:"style",icon:"🧴",description:"Дата вскрытия и период после открытия, указанный на упаковке."},
{id:"fit",title:"Посадка и силуэты",category:"style",icon:"🎀",description:"Подсказки к силуэту под задачу и собственный комфорт."},
{id:"shopping",title:"Пауза перед покупкой",category:"style",icon:"🛍️",description:"Список ожидания на 48 часов, 72 часа или неделю."},
{id:"routine",title:"Уход по среде",category:"style",icon:"🌷",description:"Ручные отметки влажности, UV и жёсткости воды."},
{id:"cycle",title:"Цикл и энергия",category:"wellbeing",icon:"🌙",description:"Личные отметки без шаблонных прогнозов. Только на время сеанса."},
{id:"reset",title:"Мягкий чек-ин",category:"wellbeing",icon:"🫶",description:"Нагрузка, триггеры и один небольшой шаг восстановления."},
{id:"move",title:"Движение по силам",category:"wellbeing",icon:"🩰",description:"Короткая общая активность по времени и самочувствию."},
{id:"checkups",title:"План чек-апов",category:"wellbeing",icon:"📅",description:"Личный список визитов и дат без медицинских назначений."},
{id:"chores",title:"Дом без перегруза",category:"home",icon:"🏡",description:"Распределение домашних задач и сроков."},
{id:"packing",title:"Чемодан за 5 минут",category:"home",icon:"🧳",description:"Чек-лист по типу поездки, сроку и погоде."},
{id:"places",title:"Уютные места",category:"home",icon:"☕",description:"Свои заметки об освещении, шуме и доступности."},
{id:"circles",title:"Круг по интересам",category:"growth",icon:"🧶",description:"Идеи встреч, кружков и занятий по увлечениям."},
{id:"career",title:"Карьерный дневник",category:"growth",icon:"✍️",description:"Результаты, метрики и аргументы для переговоров."},
{id:"projects",title:"Мои проекты",category:"growth",icon:"✨",description:"Маленькие шаги, даты возвращения и прогресс."}
];
const storedFields = ["wardrobe","beauty","shopping","checkups","chores","places","circles","career","projects"];
try {
 const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
 for (const key of storedFields) if (Array.isArray(saved[key])) data[key] = saved[key].slice(0,500);
} catch {}
let activeFilter = "all";
let activeModule = null;
const grid = document.getElementById("module-grid");
const dialog = document.getElementById("module-dialog");
const content = document.getElementById("dialog-content");
const search = document.getElementById("module-search");
const toast = document.getElementById("toast");
let toastTimer;
function esc(value){return String(value ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function save(){
 try{localStorage.setItem(STORAGE_KEY,JSON.stringify(Object.fromEntries(storedFields.map(k=>[k,data[k]]))));return true;}
 catch{notify("Не удалось сохранить: хранилище браузера недоступно.");return false;}
}
function notify(message){toast.textContent=message;toast.classList.add("is-visible");clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.classList.remove("is-visible"),2400);}
function dateText(value){if(!value)return "дата не указана";const date=new Date(value+"T12:00:00");return Number.isNaN(date.getTime())?"дата не указана":date.toLocaleDateString("ru-RU",{day:"numeric",month:"long",year:"numeric"});}
function field(label,name,placeholder,type){return '<div class="field"><label for="f-'+name+'">'+label+'</label><input id="f-'+name+'" name="'+name+'" type="'+(type||"text")+'" placeholder="'+(placeholder||"")+'" required></div>';}
function select(label,name,options){return '<div class="field"><label for="f-'+name+'">'+label+'</label><select id="f-'+name+'" name="'+name+'">'+options.map(o=>'<option value="'+esc(o[0])+'">'+esc(o[1])+'</option>').join("")+'</select></div>';}
function form(id,body,button){return '<form class="module-form" data-form="'+id+'">'+body+'<div class="form-actions"><button class="action-button" type="submit">'+button+'</button></div></form>';}
function records(key,empty,format){
 if(!data[key].length)return '<div class="empty-state">'+empty+'</div>';
 return '<div class="record-list">'+data[key].map(item=>'<article class="record-card"><div><strong>'+esc(format(item).title)+'</strong><small>'+esc(format(item).detail)+'</small></div><button type="button" class="remove-button" data-remove="'+key+'" data-id="'+esc(item.id)+'" aria-label="Удалить запись">×</button></article>').join("")+'</div>';
}
function result(text){return '<div class="result-panel" data-result>'+esc(text||"Здесь появится результат.")+'</div>';}
function intro(text){return '<p class="module-intro">'+text+'</p>';}
function note(text){return '<p class="module-footnote">'+text+'</p>';}
function view(id){
 const common = note("Локальная версия: системные уведомления, синхронизация и внешние сервисы DuckOS не подключены.");
 switch(id){
 case "wardrobe": return intro("Добавляй любимые вещи и собирай капсулу из того, что уже есть.")+form(id,field("Название вещи","name","Например, жакет")+select("Категория","category",[["Верх","Верх"],["Низ","Низ"],["Платье","Платье"],["Обувь","Обувь"],["Аксессуар","Аксессуар"]])+field("Цвет","color","Молочный, сливовый…"),"Добавить в шкаф")+'<p class="section-label">Мой шкаф</p>'+records("wardrobe","Пока пусто.",x=>({title:x.name,detail:x.category+" · "+x.color}))+common;
 case "beauty": return intro("Укажи период после вскрытия (PAO) с упаковки. Это ориентир даты, а не проверка безопасности состава.")+form(id,field("Средство","name","Название продукта")+field("Дата вскрытия","opened","","date")+select("PAO","months",[["3","3 месяца"],["6","6 месяцев"],["9","9 месяцев"],["12","12 месяцев"],["18","18 месяцев"],["24","24 месяца"]]),"Добавить средство")+'<p class="section-label">Мои средства</p>'+records("beauty","Записей пока нет.",x=>{const d=new Date(x.opened+"T12:00:00");d.setMonth(d.getMonth()+Number(x.months));return {title:x.name,detail:"Открыто: "+dateText(x.opened)+" · ориентир до "+d.toLocaleDateString("ru-RU")};})+common;
 case "fit": return intro("Подбирай одежду по ситуации и тому, как тебе удобно двигаться. Без оценок фигуры.")+form(id,select("Сценарий","occasion",[["Рабочий день","Рабочий день"],["Прогулка","Прогулка"],["Поездка","Поездка"],["Праздник","Праздник"]])+select("Силуэт","silhouette",[["Свободный","Свободный"],["Структурированный","Структурированный"],["Многослойный","Многослойный"]])+select("Длина","length",[["Укороченная","Укороченная"],["Средняя","Средняя"],["Длинная","Длинная"]]),"Собрать подсказку")+result();
 case "shopping": return intro("Положи покупку на паузу и вернись к решению позже. Никаких покупок или платежей приложение не совершает.")+form(id,field("Что хочется купить?","name","Название вещи")+field("Цена, необязательно","price","Сумма","number")+select("Пауза","hours",[["48","48 часов"],["72","72 часа"],["168","7 дней"]]),"Отложить решение")+'<p class="section-label">Список ожидания</p>'+records("shopping","Пока ничего не отложено.",x=>{const due=new Date(x.created+Number(x.hours)*3600000);const hours=Math.max(0,Math.ceil((due-Date.now())/3600000));return {title:x.name,detail:(x.price?x.price+" · ":"")+(hours?"Осталось примерно "+hours+" ч.":"Пауза завершена — решение за тобой")};})+common;
 case "routine": return intro("Условия введи вручную. Геолокация и прогноз погоды не используются; это не медицинская рекомендация.")+form(id,'<div class="field"><label for="f-humidity">Влажность, %</label><input id="f-humidity" name="humidity" type="number" min="0" max="100" value="45" required></div><div class="field"><label for="f-uv">UV-индекс</label><input id="f-uv" name="uv" type="number" min="0" max="15" value="2" required></div>'+select("Жёсткость воды","water",[["unknown","Не знаю"],["soft","Мягкая"],["medium","Средняя"],["hard","Жёсткая"]]),"Подобрать базовые подсказки")+result();
 case "cycle": return intro("Фаза цикла не предсказывает настроение или работоспособность. Отметки живут только в памяти этой страницы и не сохраняются.")+form(id,select("Моя отметка","phase",[["Не отслеживаю","Не отслеживаю"],["Менструация","Менструация"],["Фолликулярная фаза","Фолликулярная фаза"],["Овуляция","Овуляция"],["Лютеиновая фаза","Лютеиновая фаза"],["Не уверена","Не уверена"]])+select("Энергия","energy",[["1","Очень мало"],["2","Мало"],["3","Средне"],["4","Хорошо"],["5","Много"]])+'<div class="field full"><label for="f-note">Заметка, необязательно</label><textarea id="f-note" name="note"></textarea></div>',"Сделать заметку")+result(session.cycle||"Отметка будет временной.");
 case "reset": return intro("Короткая остановка без оценок и токсичного позитива. Чек-ин не сохраняется после закрытия страницы.")+form(id,select("Перегруз","load",[["1","Почти нет"],["2","Небольшой"],["3","Заметный"],["4","Сильный"],["5","Очень сильный"]])+field("Что забирает силы?","source","Можно коротко")+select("Что может помочь","help",[["Тишина и пауза","Тишина и пауза"],["Вода и еда","Вода и еда"],["Небольшая прогулка","Небольшая прогулка"],["Попросить поддержки","Попросить поддержки"],["Упростить задачу","Упростить задачу"]]),"Сохранить чек-ин на время сеанса")+result(session.reset||"Пока нет отметки")+note("Не диагностика. При тяжёлом или опасном состоянии обратись за поддержкой к человеку или специалисту.");
 case "move": return intro("Общие идеи мягкой активности, не индивидуальная медицинская или реабилитационная программа.")+form(id,select("Время","minutes",[["5","5 минут"],["10","10 минут"],["15","15 минут"],["20","20 минут"]])+select("Фокус","focus",[["Мобильность","Мобильность"],["Спина и осанка","Спина и осанка"],["Лёгкое кардио","Лёгкое кардио"],["Растяжка","Растяжка"]])+select("Энергия","energy",[["Невысокая","Невысокая"],["Средняя","Средняя"],["Высокая","Высокая"]]),"Получить план")+result()+note("Остановись при боли, головокружении или ухудшении самочувствия.");
 case "checkups": return intro("Список твоих планов, а не рекомендация по частоте обследований. Напоминания DuckOS пока не подключены.")+form(id,field("Название визита","name","Например, стоматолог")+field("Дата","date","","date")+field("Комментарий","note","Что взять с собой"),"Добавить дату")+'<p class="section-label">Мой план</p>'+records("checkups","Запланированных визитов нет.",x=>({title:x.name,detail:dateText(x.date)+(x.note?" · "+x.note:"")}))+common;
 case "chores": return intro("Запиши бытовую задачу, ответственного и срок. Это список одного профиля браузера, не семейная синхронизация.")+form(id,field("Задача","name","Например, купить продукты")+select("Ответственный","owner",[["Я","Я"],["Вместе","Вместе"],["Участник семьи","Участник семьи"]])+field("Срок","date","","date"),"Добавить задачу")+'<p class="section-label">Список дел</p>'+records("chores","Пока нет задач.",x=>({title:x.name,detail:x.owner+" · "+dateText(x.date)}))+common;
 case "packing": return intro("Создай стартовый список. Погоду введи вручную — онлайн-прогноз не запрашивается.")+form(id,select("Поездка","kind",[["Город","Город"],["Пляж","Пляж"],["Горы","Горы"],["Работа","Работа"]])+'<div class="field"><label for="f-days">Количество дней</label><input id="f-days" name="days" type="number" min="1" max="60" value="3" required></div>'+select("Погода","weather",[["Умеренная","Умеренная"],["Жаркая","Жаркая"],["Холодная","Холодная"],["Дождливая","Дождливая"]]),"Создать чек-лист")+result();
 case "places": return intro("Записывай собственные наблюдения о кафе, маршрутах и пространствах. Это не рейтинг безопасности.")+form(id,field("Название места","name","Название или ориентир")+select("Освещение","light",[["Хорошее","Хорошее"],["Смешанное","Смешанное"],["Слабое","Слабое"],["Не проверено","Не проверено"]])+select("Шум","noise",[["Тихо","Тихо"],["Умеренно","Умеренно"],["Шумно","Шумно"],["Не проверено","Не проверено"]])+field("Заметка","note","Доступность, транспорт…"),"Сохранить место")+'<p class="section-label">Мои места</p>'+records("places","Список пока пуст.",x=>({title:x.name,detail:"Свет: "+x.light+" · Шум: "+x.noise+(x.note?" · "+x.note:"")}))+common;
 case "circles": return intro("Собирай идеи книжного клуба, прогулки, рукодельной встречи или языкового обмена. Публичных профилей и чата нет.")+form(id,field("Интерес","interest","Книги, бег, керамика…")+select("Формат","format",[["Онлайн","Онлайн"],["Кафе","Кафе"],["На улице","На улице"],["Мастерская","Мастерская"]])+field("Дата или время","date","Например, суббота")+field("Заметка","note","Тема встречи"),"Добавить идею")+'<p class="section-label">Мои идеи</p>'+records("circles","Добавь идею встречи.",x=>({title:x.interest,detail:x.format+" · "+x.date+(x.note?" · "+x.note:"")}))+common;
 case "career": return intro("Фиксируй результаты, чтобы подготовиться к ревью, переговорам о повышении или смене работы.")+form(id,field("Результат","name","Что удалось сделать?")+field("Метрика","metric","Например, сократила срок")+field("Подтверждение","evidence","Ссылка или факт")+field("Дата","date","","date"),"Сохранить достижение")+'<p class="section-label">Мои результаты</p>'+records("career","Пока нет записей.",x=>({title:x.name,detail:x.metric+" · "+x.date+(x.evidence?" · "+x.evidence:"")}))+common;
 case "projects": return intro("Большой проект можно двигать одной маленькой задачей. Возвращаться раз в неделю — тоже прогресс.")+form(id,field("Проект","name","Название хобби или курса")+field("Следующий шаг","step","Самое маленькое действие")+field("Дата возвращения","date","","date")+'<div class="field"><label for="f-progress">Прогресс, %</label><input id="f-progress" name="progress" type="number" min="0" max="100" value="0"></div>',"Добавить проект")+'<p class="section-label">Мои проекты</p>'+records("projects","Пока нет проектов.",x=>({title:x.name,detail:x.progress+"% · "+x.step+" · "+dateText(x.date)}))+common;
 }
 return '<div class="empty-state">Инструмент не найден.</div>';
}
function renderCards(){
 const query=search.value.trim().toLocaleLowerCase("ru-RU");
 const found=modules.filter(m=>(activeFilter==="all"||m.category===activeFilter)&&(!query||(m.title+" "+m.description).toLocaleLowerCase("ru-RU").includes(query)));
 grid.innerHTML=found.map(m=>'<button class="module-card" type="button" data-module="'+m.id+'"><span class="card-icon" aria-hidden="true">'+m.icon+'</span><strong class="card-title">'+esc(m.title)+'</strong><span class="card-description">'+esc(m.description)+'</span><span class="card-foot"><i aria-hidden="true"></i> Локальный инструмент</span></button>').join("");
 document.getElementById("result-count").textContent=found.length+" из 15";
 if(!found.length)grid.innerHTML='<div class="empty-state">Ничего не найдено. Попробуй другое слово.</div>';
}
function openModule(id){const m=modules.find(x=>x.id===id);if(!m)return;activeModule=id;document.getElementById("dialog-title").textContent=m.title;document.getElementById("dialog-eyebrow").textContent="MORA BELLE · "+m.category.toUpperCase();content.innerHTML=view(id);if(!dialog.open)dialog.showModal();}
function setResult(message){const target=content.querySelector("[data-result]");if(target)target.textContent=message;}
function handleSubmit(event){
 const formEl=event.target.closest("[data-form]");if(!formEl)return;event.preventDefault();
 const values=new FormData(formEl),v=k=>String(values.get(k)||"").trim(),record={id:Date.now().toString(36)+Math.random().toString(36).slice(2,7)};
 const add=(key,fields)=>{data[key].unshift({...record,...fields});save();content.innerHTML=view(activeModule);notify("Запись добавлена");};
 switch(formEl.dataset.form){
 case "wardrobe":add("wardrobe",{name:v("name"),category:v("category"),color:v("color")});break;
 case "beauty":{const d=new Date(v("opened")+"T12:00:00");d.setMonth(d.getMonth()+Number(v("months")));add("beauty",{name:v("name"),opened:v("opened"),months:v("months"),review:d.toISOString()});break;}
 case "fit":setResult(v("occasion")+": попробуй "+v("silhouette").toLowerCase()+" силуэт, "+v("length").toLowerCase()+" длину и проверь свободу движения. Главное — твой комфорт.");break;
 case "shopping":add("shopping",{name:v("name"),price:v("price"),hours:v("hours"),created:Date.now()});break;
 case "routine":{const h=Number(v("humidity")),uv=Number(v("uv")),tips=[];tips.push(h<35?"Воздух сухой: обрати внимание на комфортное увлажнение.":h>65?"Влажность высокая: выбирай привычные лёгкие текстуры.":"Влажность умеренная: сохраняй привычную рутину.");if(uv>=3)tips.push("UV-индекс повышен: учитывай инструкции к фотозащите.");if(v("water")==="hard")tips.push("При жёсткой воде наблюдай за ощущением сухости, не усиливая очищение.");if(v("water")==="unknown")tips.push("Жёсткость воды не проверена — не делай выводов.");session.routine=tips.join("\n");setResult(session.routine);break;}
 case "cycle":session.cycle="Отметка на этот сеанс: "+v("phase")+", энергия "+v("energy")+"/5. Это наблюдение, а не прогноз.";setResult(session.cycle);break;
 case "reset":{const suggestions={"Тишина и пауза":"дать себе несколько минут тишины","Вода и еда":"проверить, не пора ли поесть или выпить воды","Небольшая прогулка":"выйти на короткую прогулку","Попросить поддержки":"написать человеку, которому доверяешь","Упростить задачу":"снять с себя одну необязательную задачу"};session.reset="Чек-ин на время сеанса. Маленький шаг: "+suggestions[v("help")]+". Не обязательно решать всё прямо сейчас.";setResult(session.reset);break;}
 case "move":{const moves={"Мобильность":"плавные круговые движения плечами и тазобедренными суставами","Спина и осанка":"мягкая подвижность грудного отдела и расслабление лопаток","Лёгкое кардио":"ходьба в комфортном темпе и шаги в стороны","Растяжка":"мягкая растяжка без боли и спокойное дыхание"};setResult("Идея на "+v("minutes")+" минут: "+moves[v("focus")]+". Делай в комфортном диапазоне; остановись при боли или головокружении.");break;}
 case "checkups":add("checkups",{name:v("name"),date:v("date"),note:v("note")});break;
 case "chores":add("chores",{name:v("name"),owner:v("owner"),date:v("date")});break;
 case "packing":{const lists={"Город":["Нижнее бельё","Носки","Комплекты одежды","Удобная обувь","Средства ухода","Зарядные устройства","Документы"],"Пляж":["Купальник","Лёгкая одежда","Солнцезащита","Головной убор","Сандалии","Полотенце","Вода"],"Горы":["Удобная обувь","Слои одежды","Тёплая вещь","Дождевик","Вода","Фонарик"],"Работа":["Одежда по дресс-коду","Обувь","Документы","Ноутбук и зарядка","Наушники","Средства ухода"]};const list=(lists[v("kind")]||lists["Город"]).slice();list.push("Одежда на "+v("days")+" дней");if(v("weather")==="Жаркая")list.push("Головной убор и лёгкий слой");if(v("weather")==="Холодная")list.push("Тёплый слой и перчатки");if(v("weather")==="Дождливая")list.push("Зонт или дождевик");setResult(list.map(x=>"□ "+x).join("\n"));break;}
 case "places":add("places",{name:v("name"),light:v("light"),noise:v("noise"),note:v("note")});break;
 case "circles":add("circles",{interest:v("interest"),format:v("format"),date:v("date"),note:v("note")});break;
 case "career":add("career",{name:v("name"),metric:v("metric"),evidence:v("evidence"),date:v("date")});break;
 case "projects":add("projects",{name:v("name"),step:v("step"),date:v("date"),progress:Math.max(0,Math.min(100,Number(v("progress"))))});break;
 }
}
function exportData(){const payload={schema:"duckos.mora-belle.local.v1",exportedAt:new Date().toISOString(),data:Object.fromEntries(storedFields.map(k=>[k,data[k]]))};const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="mora-belle-backup.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify("Локальные записи экспортированы");}
function clearData(){if(!confirm("Удалить все локальные записи Mora Belle из этого профиля браузера?"))return;localStorage.removeItem(STORAGE_KEY);for(const k of storedFields)data[k]=[];session.cycle=session.reset=session.routine=null;if(activeModule)content.innerHTML=view(activeModule);notify("Локальные записи удалены");}
document.addEventListener("click",event=>{
 const card=event.target.closest("[data-module]");if(card){openModule(card.dataset.module);return;}
 const filter=event.target.closest("[data-filter]");if(filter){activeFilter=filter.dataset.filter;document.querySelectorAll("[data-filter]").forEach(b=>{const active=b===filter;b.classList.toggle("is-active",active);b.setAttribute("aria-pressed",String(active));});renderCards();return;}
 const remove=event.target.closest("[data-remove]");if(remove){const key=remove.dataset.remove;if(!storedFields.includes(key))return;data[key]=data[key].filter(x=>String(x.id)!==remove.dataset.id);save();content.innerHTML=view(activeModule);notify("Запись удалена");return;}
 const action=event.target.closest("[data-action]");if(!action)return;
 if(action.dataset.action==="close")dialog.close();
 if(action.dataset.action==="export")exportData();
 if(action.dataset.action==="clear")clearData();
 if(action.dataset.action==="theme"){const night=document.documentElement.dataset.theme!=="night";document.documentElement.dataset.theme=night?"night":"blush";action.textContent=night?"☀":"☾";action.setAttribute("aria-label",night?"Переключить на светлую тему":"Переключить на вечернюю тему");}
});
document.addEventListener("submit",handleSubmit);
search.addEventListener("input",renderCards);
renderCards();