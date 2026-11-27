/* Project C3 world preview: new account/character flow; old alpha stays separate. */
(() => {
"use strict";
const cfg=window.C3_CONFIG, cover=document.getElementById("cover"), panel=cover.querySelector(".panel"),
  play=document.getElementById("play"), progress=document.getElementById("progress"), status=document.getElementById("status");
const el=(tag,cls="",text="")=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text)e.textContent=text;return e};
const btn=(text,action,cls="c3-choice")=>{const b=el("button",cls,text);b.type="button";b.onclick=action;return b};
const races=[["Человек","Ратник","Ученик чар"],["Эльф","Страж","Ученик росы"],["Тёмный эльф","Воин тени","Ученик сумерек"],["Орк","Боец","Ученик духов"],["Гном","Подгорный боец"]];
const raceLabels=["Люди","Эльфы","Ночные эльфы","Орки","Гномы"];
const skinPalettes=[["#e2b797","#cc9c77","#ad7754","#80523c"],["#f0d7bc","#d5ae8d","#b68d68","#977150"],["#aab0c4","#8c91ab","#6f748e","#555a72"],["#a0af78","#82915c","#687448","#485b39"],["#e0b48d","#c28c65","#a36d50","#785039"]];
const hairs=["#362a26","#805039","#d3b075","#d8d9d2"];
const cloth=["#55788e","#5c8560","#6f608a","#876044","#a67c48"];
let client=null, characters=[], selected=null, revision=0, queue=null, saving=false, saveError="", started=false, menuCallback=null, busy=false;
let settings={sound:true,quality:1};try{Object.assign(settings,JSON.parse(localStorage.getItem("c3-world-settings")||"{}"))}catch(_){}
settings.sound=!!settings.sound;settings.quality=Math.max(0,Math.min(2,Number(settings.quality)||0));
const shell=el("div","c3-shell"), view=el("div","c3-screen");
shell.append(view,play,progress,status);
panel.replaceChildren(shell);
play.hidden=true;progress.hidden=true;
const css=el("style");css.textContent=
"#cover{padding:clamp(10px,2.5vw,36px);background:radial-gradient(ellipse at 50% 12%,#52665b 0,#22382d 37%,#101b19 72%,#0a1110 100%);align-items:center}#cover .panel{width:min(920px,100%);padding:clamp(14px,3vw,34px);background:#14231fe8;border:1px solid #aa9564;border-radius:10px;box-shadow:0 20px 70px #0009}.c3-screen h1{font:700 clamp(46px,8vw,82px)/.95 Georgia,serif;color:#f0d59e;letter-spacing:.08em;margin:8px 0}.c3-screen h2{color:#ebd5a5;margin:6px 0 14px;font:400 clamp(22px,4vw,36px) Georgia,serif}.c3-kicker{font:700 11px system-ui;letter-spacing:.23em;color:#cfb47d}.c3-sub{max-width:560px;margin:12px auto;color:#c5d0c3}.c3-choice{background:linear-gradient(180deg,#cbb17c,#a78a50);border:1px solid #e1c98d;color:#172019;font:700 clamp(15px,2.5vw,20px) system-ui;min-height:48px;margin:6px 0;padding:12px;border-radius:6px}.c3-secondary{background:#263c34;color:#e4d7b4;border-color:#857957}.c3-menu-stack{max-width:420px;margin:20px auto 0}.c3-slots{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:16px 0}.c3-slot{min-height:180px;border:1px solid #82795d;background:#23382f;border-radius:8px;color:#eddfbf;padding:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;cursor:pointer}.c3-slot:hover,.c3-slot:focus-visible{border-color:#f0ce84;background:#354d3d}.c3-slot strong{font:700 18px Georgia,serif;overflow-wrap:anywhere}.c3-slot small{font-size:12px;color:#becbbd}.c3-plus{font:38px Georgia;color:#d9bc80}.c3-creation{display:grid;grid-template-columns:minmax(135px,1fr) minmax(0,1.5fr);gap:20px;text-align:left}.c3-portrait{display:flex;flex-direction:column;align-items:center;justify-content:center;border:1px solid #78866e;border-radius:8px;min-height:170px;background:radial-gradient(ellipse,#496251,#1b2c26 75%)}.c3-portrait svg{display:block;width:min(180px,100%);height:auto}.c3-form{display:grid;gap:6px}.c3-form label{font-size:12px;color:#d9c7a2;display:block}.c3-form input,.c3-form select,.c3-screen input,.c3-screen select{min-width:0;width:100%;border:1px solid #7d8c75;background:#101d19;color:#f2e7ca;border-radius:5px;padding:8px;font:16px system-ui}.c3-form .c3-pair{display:grid;grid-template-columns:1fr 1fr;gap:8px}.c3-actions{display:flex;gap:10px}.c3-actions button{flex:1}.c3-screen button:disabled{opacity:.55}.c3-game-menu-button{position:fixed;top:max(6px,env(safe-area-inset-top));left:50%;transform:translateX(-50%);z-index:2;width:auto;margin:0;padding:6px 13px;font-size:12px}.c3-game-overlay{position:fixed;inset:0;display:grid;place-items:center;z-index:5;background:#0a1512d9;padding:14px;overflow:auto}.c3-game-overlay[hidden],.c3-game-menu-button[hidden],#play[hidden]{display:none!important}.c3-game-overlay section{width:min(450px,100%);background:#172820;border:1px solid #bba06a;border-radius:9px;padding:20px}.c3-game-overlay button{margin:5px 0;padding:10px}.c3-game-overlay p{min-height:20px;overflow-wrap:anywhere}@media(max-width:520px){.c3-slots{gap:5px}.c3-slot{min-height:145px;padding:6px}.c3-slot strong{font-size:14px}.c3-slot small{font-size:10px}.c3-creation{gap:8px;grid-template-columns:105px 1fr}.c3-form .c3-pair{gap:5px}.c3-form input,.c3-form select{padding:5px}.c3-portrait svg{width:100%}.c3-choice{min-height:40px;padding:8px}}@media(max-height:500px){#cover{align-items:start}.c3-slot{min-height:120px}.c3-screen h1{font-size:46px}.c3-screen h2{font-size:23px;margin:4px 0}.c3-menu-stack{margin:6px auto}.c3-choice{min-height:40px;padding:7px}.c3-form{gap:4px}.c3-portrait svg{max-height:140px}}";
document.head.append(css);
function setStatus(s){status.textContent=s}
function title(k,h,sub=""){
 view.replaceChildren(el("div","c3-kicker",k),el("h2","",h));
 if(sub)view.append(el("p","c3-sub",sub));
 setStatus("");
}
function main(){
 title("PROJECT C3 · WORLD PREVIEW 0.19","Вересковые земли");
 view.insertBefore(el("h1","","C3"),view.children[1]);
 view.append(el("p","c3-sub","Ты просыпаешься в незнакомой деревне. Ни прошлого, ни воспоминаний — только дорога впереди."));
 const stack=el("div","c3-menu-stack");stack.append(btn("Начать играть",start),btn("Настройки",()=>settingsScreen(main),"c3-choice c3-secondary"),btn("Выйти",()=>{title("PROJECT C3","Сеанс завершён","В браузере вкладку можно закрыть вручную.");view.append(btn("В главное меню",main));},"c3-choice c3-secondary"));view.append(stack);
}
function options(values,initial=0){
 const s=el("select");values.forEach((v,i)=>{const o=el("option","",v);o.value=String(i);s.append(o)});s.value=String(initial);return s;
}
function field(label,input){const box=el("label","",label);box.append(input);return box}
function settingsScreen(back){
 title("PROJECT C3","Настройки");
 const form=el("div","c3-menu-stack");
 const sound=options(["Включён","Выключен"],settings.sound?0:1),quality=options(["Низкая","Средняя","Высокая"],settings.quality);
 form.append(field("Звук",sound),field("Графика",quality),btn("Применить",()=>{settings.sound=sound.value==="0";settings.quality=Number(quality.value);try{localStorage.setItem("c3-world-settings",JSON.stringify(settings))}catch(_){};back()}),btn("Назад",back,"c3-choice c3-secondary"));
 view.append(form);
}
async function rpc(action,payload={}){
 const {data,error}=await client.rpc("c3_world_slots_api",{p_action:action,p_payload:payload});if(error)throw Error(error.message);return data;
}
async function start(){
 if(busy)return;busy=true;setStatus("Подключение...");
 try{
 if(!client)throw Error("Сервис аккаунтов ещё подключается. Повтори попытку.");
 const {data:{session}}=await client.auth.getSession();
 if(!session){login();return}
 characters=await rpc("list");slots();
 }catch(e){setStatus(e.message)}finally{busy=false}
}
function login(){
 title("PROJECT C3","Вход в аккаунт","Используй уже одобренный аккаунт закрытой альфы.");
 const form=el("form","c3-menu-stack"),email=el("input"),password=el("input");
 email.type="email";email.required=true;email.autocomplete="email";email.placeholder="Email";
 password.type="password";password.required=true;password.autocomplete="current-password";password.placeholder="Пароль";
 const submit=el("button","c3-choice","Войти");submit.type="submit";
 form.append(email,password,submit,btn("Назад",main,"c3-choice c3-secondary"));
 form.onsubmit=async e=>{e.preventDefault();if(busy)return;busy=true;submit.disabled=true;setStatus("Вход...");try{
 const {error}=await client.auth.signInWithPassword({email:email.value.trim(),password:password.value});if(error)throw error;
 characters=await rpc("list");password.value="";slots();
 }catch(err){setStatus(err.message)}finally{busy=false;submit.disabled=false}};
 view.append(form);
}
function slots(){
 title("PROJECT C3 · ВЫБОР ПЕРСОНАЖА","Три пути","Новые персонажи этой тестовой сборки имеют отдельные сохранения. Старая альфа не изменена.");
 const list=el("div","c3-slots");
 for(let i=1;i<=3;i++){
 const c=characters.find(c=>Number(c.slot)===i),b=el("button","c3-slot");b.type="button";
 b.append(el("small","","СЛОТ "+i));
 if(c){b.append(makePortrait(c),el("strong","",c.name),el("small","",raceLabels[races.findIndex(r=>r[0]===c.race)]+" · "+c.discipline),el("small","","Войти в мир"));b.onclick=()=>enter(c)}
 else{b.append(el("div","c3-plus","+"),el("strong","","Создать"),el("small","","Свободный слот"));b.onclick=()=>create(i)}
 list.append(b);
 }
 view.append(list);
 const actions=el("div","c3-actions");actions.append(btn("Главное меню",main,"c3-choice c3-secondary"),btn("Сменить аккаунт",async()=>{if(busy)return;busy=true;try{const {error}=await client.auth.signOut({scope:"local"});if(error)throw error;characters=[];login()}catch(e){setStatus(e.message)}finally{busy=false}},"c3-choice c3-secondary"));view.append(actions);
}
const NS="http://www.w3.org/2000/svg";
function makePortrait(c){
 const ri=Math.max(0,races.findIndex(r=>r[0]===c.race)),f=Number(c.face)||0,h=Number(c.hair)||0,sc=Number(c.skin)||0,hc=Number(c.hair_color)||0;
 const skin=skinPalettes[ri][sc],hair=hairs[hc],outfit=cloth[ri],female=c.gender==="female",w=[25,29,23,27][f],jaw=[84,83,89,87][f];
 const svg=document.createElementNS(NS,"svg");svg.setAttribute("viewBox","0 0 120 140");svg.setAttribute("aria-label","Предпросмотр внешности");svg.style.maxHeight="170px";svg.style.maxWidth="160px";
 function add(tag,attrs){const n=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));svg.append(n);return n}
 add("ellipse",{cx:60,cy:132,rx:41,ry:7,fill:"#101915",opacity:.5});
 if(h===2||h===3)add("path",{d:"M29 40 Q18 18 42 13 Q60 2 80 13 Q101 23 95 59 L96 103 Q60 117 24 103 Z",fill:hair});
 add("path",{d:"M19 137 L23 111 Q31 100 48 96 L72 96 Q89 100 97 111 L101 137 Z",fill:outfit,stroke:"#1b211c","stroke-width":2});
 add("path",{d:"M44 98 L49 84 L71 84 L76 98 L60 113 Z",fill:skin});
 if(ri===1||ri===2){add("path",{d:"M36 58 L17 37 L25 69 L36 73 Z",fill:skin});add("path",{d:"M84 58 L103 37 L95 69 L84 73 Z",fill:skin})}
 else{add("ellipse",{cx:34,cy:60,rx:6,ry:10,fill:skin});add("ellipse",{cx:86,cy:60,rx:6,ry:10,fill:skin})}
 add("path",{d:"M"+(60-w)+" 41 Q60 13 "+(60+w)+" 41 L"+(60+w-1)+" 66 Q81 79 60 "+jaw+" Q39 79 "+(61-w)+" 66 Z",fill:skin,stroke:"#28221e","stroke-width":.6});
 if(h===0)add("path",{d:"M30 43 Q31 8 60 14 Q88 9 91 44 L80 35 L65 37 L51 30 L39 41 Z",fill:hair});
 if(h===1)add("path",{d:"M30 46 Q28 13 61 12 Q97 14 90 44 L68 27 L58 42 L42 34 Z",fill:hair});
 if(h===2)add("path",{d:"M29 48 Q23 10 60 11 Q99 10 91 49 L82 30 L66 24 L46 40 L37 78 L29 82 Z",fill:hair});
 if(h===3)add("path",{d:"M31 46 Q25 16 48 13 Q72 5 88 23 L90 49 L74 33 L55 28 L38 43 Z",fill:hair});
 for(const x of [49,71]){add("path",{d:"M"+(x-6)+" 53 Q"+x+" 50 "+(x+6)+" 53",stroke:hair,"stroke-width":2,fill:"none"});add("ellipse",{cx:x,cy:58,rx:4.7,ry:2.6,fill:"#eee6d0"});add("circle",{cx:x,cy:58,r:2.1,fill:ri===2?"#9d5670":ri===3?"#cda65c":"#506f72"})}
 add("path",{d:"M60 59 L57 68 L62 69",fill:"none",stroke:"#694d3e","stroke-width":1.1,opacity:.65});
 add("path",{d:"M54 76 Q60 "+(female?79:77)+" 66 76",fill:"none",stroke:"#805346","stroke-width":1.5});
 if(ri===3){for(const x of [50,70])add("path",{d:"M"+(x-3)+" 77 L"+x+" 68 L"+(x+3)+" 78 Z",fill:"#ede0bf"})}
 if(ri===4&&!female)add("path",{d:"M39 71 Q49 84 60 79 Q71 84 81 71 L78 96 L60 108 L42 96 Z",fill:hair});
 add("path",{d:"M47 98 L60 114 L73 98 M60 114 V137",fill:"none",stroke:"#ceba83","stroke-width":3});
 return svg;
}
function create(slot){
 title("PROJECT C3 · СЛОТ "+slot,"Создание персонажа");
 const layout=el("div","c3-creation"),portrait=el("div","c3-portrait"),form=el("form","c3-form");
 const name=el("input");name.required=true;name.minLength=3;name.maxLength=24;name.placeholder="Имя персонажа";name.autocomplete="off";
 const race=options(raceLabels),discipline=options(["Воин","Маг"]),gender=options(["Мужской","Женский"]);
 const face=options(["Лицо 1","Лицо 2","Лицо 3","Лицо 4"]),hair=options(["Короткая","Асимметричная","Длинная","Зачёс"]),
 hairColor=options(["Чёрный","Каштановый","Светлый","Серебряный"]),skin=options(["Тон 1","Тон 2","Тон 3","Тон 4"]);
 function pair(...children){const p=el("div","c3-pair");p.append(...children);return p}
 function get(){const r=races[Number(race.value)];return{slot,name:name.value.trim(),race:r[0],discipline:r[Number(discipline.value)+1],gender:gender.value==="0"?"male":"female",face:Number(face.value),hair:Number(hair.value),hair_color:Number(hairColor.value),skin:Number(skin.value)}}
 function refresh(){const c=get();portrait.replaceChildren(makePortrait(c),el("strong","",c.race),el("small","",c.discipline||""))}
 function updateRace(){discipline.replaceChildren();races[Number(race.value)].slice(1).forEach((d,i)=>{const o=el("option","",(i===0?"Воин · ":"Маг · ")+d);o.value=String(i);discipline.append(o)});refresh()}
 race.onchange=updateRace;for(const e of [discipline,gender,face,hair,hairColor,skin])e.onchange=refresh;
 form.append(field("Имя",name),pair(field("Раса",race),field("Класс",discipline)),pair(field("Пол",gender),field("Лицо",face)),pair(field("Причёска",hair),field("Цвет волос",hairColor)),field("Цвет кожи",skin));
 const submit=el("button","c3-choice","Создать персонажа");submit.type="submit";form.append(submit,btn("Назад",slots,"c3-choice c3-secondary"));
 form.onsubmit=async e=>{e.preventDefault();if(busy)return;busy=true;submit.disabled=true;try{characters=await rpc("create",get());slots()}catch(err){setStatus(err.message)}finally{busy=false;submit.disabled=false}};
 layout.append(portrait,form);view.append(layout);updateRace();
}
function enter(c){
 if(started||busy)return;started=true;selected=c;revision=Number(c.revision)||0;view.replaceChildren(el("h2","","Загрузка мира"),el("p","c3-sub","Где я? Как я сюда попал? В голове — пустота."));
 play.click();
}
async function flush(){
 if(saving||!queue||!selected||saveError)return;
 saving=true;const snapshot=queue;queue=null;
 try{const r=await rpc("save",{id:selected.id,revision,...snapshot});revision=Number(r.revision)}
 catch(e){saveError=e.message;if(!queue)queue=snapshot}
 finally{saving=false;if(queue&&!saveError)void flush()}
}
const menuButton=btn("⚙ Меню",()=>{if(cover.hidden){overlay.hidden=false;menuText.textContent=""}},"c3-game-menu-button");menuButton.hidden=true;
const overlay=el("div","c3-game-overlay"),box=el("section"),menuText=el("p");overlay.hidden=true;overlay.append(box);
box.append(el("h2","","Игровое меню"),btn("Продолжить",()=>{overlay.hidden=true;document.getElementById("canvas").focus()}),btn("Сохранить и выйти",async()=>{
 if(!menuCallback){menuText.textContent="Движок ещё подключается";return}
 if(busy)return;busy=true;menuText.textContent="Сохранение...";
 try{
  menuCallback("save");for(let i=0;i<100&&(saving||queue)&&!saveError;i++)await new Promise(r=>setTimeout(r,150));
  if(saveError||saving||queue)throw Error(saveError||"Сохранение не подтверждено");
  location.reload();
 }catch(e){menuText.textContent=e.message}finally{busy=false}
 }),btn("Полный экран",()=>{if(document.fullscreenElement)document.exitFullscreen?.();else document.documentElement.requestFullscreen?.().catch(()=>{})}),menuText);
document.body.append(menuButton,overlay);
new MutationObserver(()=>{menuButton.hidden=!cover.hidden}).observe(cover,{attributes:true,attributeFilter:["hidden"]});
window.C3Preview={character:()=>JSON.stringify(selected||{}),settings:()=>JSON.stringify(settings),save:(json,x,z)=>{
 if(!selected)return;try{queue={progress:JSON.parse(String(json)),x:Number(x),z:Number(z)};void flush()}catch(e){saveError=e.message}
 },menuOpen:()=>!overlay.hidden,attach:cb=>{menuCallback=cb},saveError:()=>saveError};
window.addEventListener("keydown",e=>{if(e.key==="Escape"&&cover.hidden){e.preventDefault();e.stopImmediatePropagation();overlay.hidden=!overlay.hidden;if(overlay.hidden)document.getElementById("canvas").focus()}},true);
main();
if(cfg?.url&&cfg?.key)import("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.49.4/+esm").then(({createClient})=>{client=createClient(cfg.url,cfg.key);}).catch(e=>setStatus("Не удалось подключиться: "+e.message));
else setStatus("Не настроено подключение к серверу.");
})();
