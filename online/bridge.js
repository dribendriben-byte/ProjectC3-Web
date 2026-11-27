// Optional closed alpha frontend. Load before the Godot shell's play handler.
(() => {
  const cfg=window.C3_CONFIG;
  if(!cfg?.url || !cfg?.key) return;
  const by=id=>document.getElementById(id);
  const play=by("play"), cover=by("cover"), panel=cover.querySelector(".panel");
  const ui=document.createElement("section");
  ui.style.cssText="text-align:left;border-top:1px solid #536352;margin-top:12px;padding-top:12px";
  ui.innerHTML='<h3>Онлайн · закрытая альфа</h3><div id="c3form"><input id="c3email" type="email" placeholder="Email" autocomplete="email"><input id="c3pass" type="password" placeholder="Пароль (8+ символов)" autocomplete="current-password"><button id="c3login">Войти</button><button id="c3signup">Регистрация</button></div><div id="c3character" hidden><input id="c3name" maxlength="24" placeholder="Имя персонажа"><select id="c3race"></select><select id="c3discipline"></select><select id="c3gender"><option value="male">Мужской</option><option value="female">Женский</option></select><select id="c3appearance"><option value="0">Стиль 1</option><option value="1">Стиль 2</option><option value="2">Стиль 3</option><option value="3">Стиль 4</option></select><button id="c3create">Создать персонажа</button></div><button id="c3enter" hidden>Войти в онлайн-мир</button><button id="c3gm" hidden>GM Management</button><button id="c3logout" hidden>Выйти из аккаунта</button><p id="c3status" role="status"></p><div id="c3admin" hidden></div>';
  panel.append(ui);
  const css=document.createElement("style");
  css.textContent="#c3form input,#c3character input,#c3character select{display:block;width:100%;padding:10px;margin:6px 0;border:1px solid #677c64;border-radius:5px;background:#172720;color:#f2e7ca;font:16px system-ui}#c3admin article{border-top:1px solid #677c64;padding:8px 0}#c3form button,#c3character button,#c3enter,#c3gm,#c3logout,#c3admin button{padding:9px;margin:4px 0;font-size:14px}#c3status{overflow-wrap:anywhere}#cover{overflow:auto;align-items:start}#cover .panel{margin:auto}";
  document.head.append(css);
  play.textContent="Играть офлайн (локальное сохранение)";
  document.getElementById("notice").textContent="Закрытая онлайн-альфа. Аккаунт требует одобрения GM. Сохранения онлайн и офлайн раздельные.";
  by("c3login").disabled=true;by("c3signup").disabled=true;
  const races={"Человек":["Ратник","Ученик чар"],"Эльф":["Страж","Ученик росы"],"Тёмный эльф":["Воин тени","Ученик сумерек"],"Орк":["Боец","Ученик духов"],"Гном":["Подгорный боец"]};
  const options=(node,values)=>{node.replaceChildren(...values.map(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;return o;}));};
  options(by("c3race"),Object.keys(races));
  function setDisc(){options(by("c3discipline"),races[by("c3race").value]);}
  by("c3race").onchange=setDisc;setDisc();
  let client, character=null, active=false, players=[], busy=false, saveBusy=false, pendingSave=null, blocked=false;
  const msg=t=>by("c3status").textContent=t;
  const rpc=async(name,args={})=>{const {data,error}=await client.rpc(name,args);if(error)throw new Error(error.message);return data;};
  async function refresh(){
    const {data:{session}}=await client.auth.getSession();
    by("c3form").hidden=!!session;by("c3logout").hidden=!session;
    by("c3character").hidden=true;by("c3enter").hidden=true;by("c3gm").hidden=true;by("c3admin").hidden=true;
    character=null;if(!session)return;
    if(!(await rpc("c3_alpha_allowed"))){msg("Закрытая альфа: аккаунт ожидает одобрения GM.");return;}
    character=await rpc("c3_my_character");
    by("c3gm").hidden=!(await rpc("c3_is_gm"));
    by("c3character").hidden=!!character;
    if(character?.banned){msg("Персонаж заблокирован.");return;}
    by("c3enter").hidden=!character;
    msg(character?character.name+" · "+character.race+" · "+character.discipline:"Создай персонажа.");
  }
  const guarded=fn=>async()=>{try{await fn();}catch(e){msg(e.message);}};
  by("c3login").onclick=guarded(async()=>{
    const {error}=await client.auth.signInWithPassword({email:by("c3email").value.trim(),password:by("c3pass").value});if(error)throw error;by("c3pass").value="";await refresh();
  });
  by("c3signup").onclick=guarded(async()=>{
    const password=by("c3pass").value;if(password.length<8)throw Error("Минимум 8 символов.");
    const {data,error}=await client.auth.signUp({email:by("c3email").value.trim(),password,options:{emailRedirectTo:location.origin+location.pathname}});if(error)throw error;by("c3pass").value="";await refresh();if(!data.session)msg("Подтверди email по ссылке из письма.");
  });
  by("c3logout").onclick=guarded(async()=>{await client.auth.signOut();await refresh();msg("Вы вышли.");});
  by("c3create").onclick=guarded(async()=>{
    await rpc("c3_create_character",{p_name:by("c3name").value.trim(),p_race:by("c3race").value,p_discipline:by("c3discipline").value,p_gender:by("c3gender").value,p_appearance:Number(by("c3appearance").value)});await refresh();
  });
  by("c3enter").onclick=()=>{if(!character||character.banned)return;active=true;play.click();};
  by("c3gm").onclick=guarded(async()=>{
    const rows=await rpc("c3_gm_players"), box=by("c3admin");box.hidden=false;box.replaceChildren();
    const title=document.createElement("h4");title.textContent="GM · онлайн "+rows.filter(r=>r.online).length+" / персонажей "+rows.length;box.append(title);
    for(const r of rows){const line=document.createElement("article"), text=document.createElement("div"), button=document.createElement("button");
      text.textContent=r.name+" · "+r.race+" · EXP "+(r.progress?.total_xp??1)+" · адена "+(r.progress?.adena??0)+" · "+(r.online?"ONLINE":"offline");
      button.textContent=r.banned?"Разблокировать":"Заблокировать";button.onclick=guarded(async()=>{if(!confirm(button.textContent+" "+r.name+"?"))return;await rpc("c3_gm_ban",{p_id:r.id,p_banned:!r.banned});by("c3gm").click();});line.append(text,button);box.append(line);}
  });
  const banner=document.createElement("div");banner.hidden=true;banner.style.cssText="position:fixed;top:78px;left:50%;transform:translateX(-50%);z-index:2;padding:3px 7px;border-radius:4px;background:#15221ed9;color:#e7d5a4;font:10px system-ui;pointer-events:none;white-space:nowrap";document.body.append(banner);
  function report(t){banner.hidden=!active;banner.textContent=t;}
  async function flush(){
    if(saveBusy||!pendingSave||!active||blocked)return;
    saveBusy=true;const args=pendingSave;pendingSave=null;
    try{await rpc("c3_save",args);report("ONLINE · сохранено");}
    catch(e){if(!pendingSave)pendingSave=args;report("Ошибка облачного сохранения");if(e.message.includes("unavailable")){blocked=true;report("Доступ прекращён · обнови страницу");}}
    finally{saveBusy=false;}
  }

  // In-game settings and explicit save-before-exit.
  let command=null, ack=null, exiting=false, menuBusy=false;
  const menuButton=document.createElement("button");
  menuButton.id="c3-menu-button";menuButton.type="button";menuButton.textContent="⚙ Меню";menuButton.hidden=true;
  const modal=document.createElement("div");modal.id="c3-game-menu";modal.hidden=true;
  modal.innerHTML='<section role="dialog" aria-modal="true" aria-labelledby="c3-menu-title"><h2 id="c3-menu-title">Игровое меню</h2><p id="c3-menu-mode"></p><div class="c3-menu-grid"><label>Графика<select id="c3-quality"><option value="0">Низкая</option><option value="1">Средняя</option><option value="2">Высокая</option></select></label><label>Звук<select id="c3-sound"><option value="on">Включён</option><option value="off">Выключен</option></select></label><button id="c3-fullscreen">Полный экран</button><button id="c3-save-now">Сохранить</button></div><p id="c3-menu-status" role="status" aria-live="polite"></p><button id="c3-resume">Продолжить игру</button><button id="c3-main-menu">Выйти в главное меню</button><button id="c3-switch-account">Выйти из аккаунта / сменить аккаунт</button></section>';
  document.body.append(menuButton,modal);
  const menuStyle=document.createElement("style");
  menuStyle.textContent="#c3-menu-button{position:fixed;top:max(43px,calc(env(safe-area-inset-top) + 35px));left:50%;transform:translateX(-50%);z-index:4;width:auto;margin:0;padding:6px 12px;font-size:13px;background:#172823ed;color:#f2e7ca;border:1px solid #8a7754}#c3-menu-button[hidden],#c3-game-menu[hidden]{display:none}#c3-game-menu{position:fixed;inset:0;z-index:6;background:#09120dcc;display:grid;place-items:center;overflow:auto;touch-action:pan-y;padding:12px}#c3-game-menu section{width:min(440px,100%);max-height:100%;overflow:auto;padding:16px;background:#172720;border:1px solid #b89a65;border-radius:12px;box-shadow:0 12px 40px #0009}#c3-game-menu h2{margin:0 0 6px}#c3-game-menu p{margin:5px 0;font-size:12px}#c3-game-menu button{font-size:13px;margin:4px 0;padding:9px 10px}#c3-game-menu select{display:block;width:100%;font-size:14px;padding:8px;margin:5px 0;border:1px solid #677c64;background:#101b18;color:#f2e7ca;border-radius:5px}#c3-game-menu label{font-size:12px;color:#c5d0c6}.c3-menu-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px}#c3-menu-status{min-height:18px;overflow-wrap:anywhere}#c3-resume{background:#a9bf88}#c3-switch-account{background:#795d47;color:#fff4db}";
  document.head.append(menuStyle);
  const menuStatus=t=>by("c3-menu-status").textContent=t;
  function enableMenu(){menuButton.hidden=cover.hidden!==true;}
  new MutationObserver(enableMenu).observe(cover,{attributes:true,attributeFilter:["hidden"]});
  function setMenuBusy(value){menuBusy=value;for(const el of modal.querySelectorAll("button,select"))el.disabled=value;}
  function showMenu(){
    if(menuBusy||!cover.hidden||!social.hidden)return;
    modal.hidden=false;by("c3-menu-mode").textContent=active?"ONLINE · "+(character?.name||""):"Офлайн · локальное сохранение";
    menuStatus(command?"":"Игровое меню ожидает подключения движка. Если не появится, обнови страницу.");for(const id of ["c3-quality","c3-sound","c3-save-now","c3-main-menu","c3-switch-account"])by(id).disabled=!command;by("c3-fullscreen").disabled=!by("fullscreen")||by("fullscreen").hidden;
    by("c3-resume").focus();
  }
  function hideMenu(){if(menuBusy)return;modal.hidden=true;by("canvas").focus();}
  menuButton.onclick=showMenu;
  by("c3-resume").onclick=hideMenu;
  by("c3-quality").onchange=()=>{command?.("quality",Number(by("c3-quality").value));};
  by("c3-sound").onchange=()=>{command?.("sound",by("c3-sound").value==="off");};
  by("c3-fullscreen").onclick=()=>by("fullscreen")?.click();
  window.addEventListener("keydown",e=>{if(e.key!=="Escape"||cover.hidden!==true)return;e.preventDefault();e.stopImmediatePropagation();if(!social.hidden){closeSocial();return;}if(modal.hidden)showMenu();else hideMenu();},true);
  const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  async function saveBeforeExit(){
    ack=null;command("save");
    // Godot callback submits a fresh snapshot; wait for its acknowledgement.
    for(let i=0;ack===null&&i<30;i++)await delay(100);
    if(!ack?.ok)throw Error(ack?.message||"Игра не подтвердила сохранение.");
    if(active){
      // Existing saves are serialized; don't leave until the last snapshot is acknowledged.
      const end=Date.now()+15000;
      while((pendingSave||saveBusy)&&Date.now()<end){
        if(blocked)throw Error("Доступ к персонажу прекращён.");
        if(!saveBusy&&pendingSave)void flush();
        await delay(350);
      }
      if(pendingSave||saveBusy||blocked)throw Error("Облачное сохранение не подтверждено. Повтори попытку.");
    }
  }
  async function menuAction(action){
    if(menuBusy||!command)return;
    setMenuBusy(true);exiting=action!=="save";menuStatus("Сохранение…");
    try{
      await saveBeforeExit();
      menuStatus(active?"Прогресс сохранён в облаке.":"Локальный прогресс записан.");
      if(action==="save")return;
      if(active){
        const end=Date.now()+5000;
        while(busy&&Date.now()<end)await delay(100);
        if(busy)throw Error("Сервер ещё отвечает. Повтори выход.");
        await rpc("c3_leave");
      }
      if(action==="logout"){
        if(!client)throw Error("Сервис аккаунтов ещё не подключён.");
        const {error}=await client.auth.signOut({scope:"local"});if(error)throw error;
      }
      active=false;location.reload();
    }catch(e){menuStatus(e.message||"Не удалось сохранить. Попробуй ещё раз.");}
    finally{exiting=false;setMenuBusy(false);}
  }
  by("c3-save-now").onclick=()=>void menuAction("save");
  by("c3-main-menu").onclick=()=>void menuAction("menu");
  by("c3-switch-account").onclick=()=>void menuAction("logout");


  // v0.17: server-backed social panel; no legacy inventory or currency mutations.
  const socialButton=document.createElement("button");
  socialButton.id="c3-social-button";socialButton.type="button";socialButton.textContent="Чат / Группа";socialButton.hidden=true;
  const social=document.createElement("div");social.id="c3-social";social.hidden=true;
  social.innerHTML='<section role="dialog" aria-modal="true" aria-labelledby="c3-social-title"><header><h2 id="c3-social-title">Project C3 · Онлайн</h2><button id="c3-social-close" type="button" aria-label="Закрыть">×</button></header><nav><button data-tab="chat">Чат</button><button data-tab="party">Группа</button><button data-tab="training">Тренировка</button></nav><p id="c3-social-status" role="status" aria-live="polite"></p><div id="c3-social-chat"><div id="c3-chat-log" role="log" aria-live="off"></div><form id="c3-chat-form"><select id="c3-chat-channel"><option value="world">Общий</option><option value="party">Группа</option></select><input id="c3-chat-input" maxlength="200" placeholder="Сообщение..." autocomplete="off"><button type="submit">Отпр.</button></form></div><div id="c3-social-party" hidden><div id="c3-party-members"></div><div id="c3-party-invites"></div><div id="c3-party-players"></div><button id="c3-party-leave" hidden>Покинуть группу</button></div><div id="c3-social-training" hidden><h3>Общая тренировочная цель</h3><p>Подойди к стартовой заставе. Урон и HP определяются сервером. Без EXP и добычи.</p><div class="c3-hp"><div id="c3-training-hp"></div></div><p id="c3-training-detail">Загрузка...</p><button id="c3-training-hit">Ударить</button></div></section>';
  document.body.append(socialButton,social);
  const socialCss=document.createElement("style");
  socialCss.textContent="#c3-menu-button{left:calc(50% + 45px)}#c3-social-button{position:fixed;top:max(43px,calc(env(safe-area-inset-top) + 35px));left:calc(50% - 65px);transform:translateX(-50%);z-index:4;width:auto;margin:0;padding:6px 10px;font-size:12px;background:#172823ed;color:#f2e7ca;border:1px solid #8a7754}#c3-social[hidden],#c3-social-button[hidden],#c3-social [hidden]{display:none!important}#c3-social{position:fixed;inset:0;z-index:7;display:grid;place-items:center;overflow:auto;touch-action:pan-y;padding:10px;background:#09120dcc}#c3-social section{width:min(560px,100%);max-height:100%;overflow:auto;background:#172720;border:1px solid #b89a65;border-radius:10px;padding:12px;color:#f2e7ca;box-sizing:border-box;font:14px system-ui}#c3-social header,#c3-social nav,#c3-social form,#c3-social .c3-party-row{display:flex;align-items:center;gap:6px}#c3-social header{justify-content:space-between}#c3-social h2{font-size:18px;margin:0}#c3-social h3{font-size:14px;margin:12px 0 6px}#c3-social button{font:13px system-ui;padding:8px;margin:3px 0;width:auto;border-radius:5px}#c3-social nav button{flex:1}#c3-social nav button.selected{background:#b4c38d;color:#172720}#c3-social p{font-size:12px;margin:6px 0;overflow-wrap:anywhere}#c3-social input,#c3-social select{min-width:0;padding:8px;background:#101b18;color:#f2e7ca;border:1px solid #677c64;border-radius:4px;font:16px system-ui}#c3-social input{flex:1}#c3-chat-log{height:clamp(90px,28vh,240px);overflow:auto;border:1px solid #526353;padding:8px;overflow-wrap:anywhere;white-space:pre-wrap}#c3-chat-log p{margin:0 0 5px}#c3-social .c3-party-row{border-bottom:1px solid #405646;justify-content:space-between;padding:4px 0}#c3-social-status{min-height:16px;color:#e9cf8c}#c3-social .c3-hp{height:18px;background:#442b2b;border:1px solid #99795b;border-radius:4px;overflow:hidden}#c3-training-hp{height:100%;background:#a75048;width:100%;transition:width .2s}";
  document.head.append(socialCss);
  let socialState=null,socialTab="chat",socialBusy=false,socialLast=0,readPromise=null;
  const socialStatus=t=>by("c3-social-status").textContent=t;
  function showSocialButton(){
    socialButton.hidden=!active||!cover.hidden||blocked;
  }
  new MutationObserver(showSocialButton).observe(cover,{attributes:true,attributeFilter:["hidden"]});
  function closeSocial(){social.hidden=true;by("canvas")?.focus();}
  function showSocial(){
    if(!active||!cover.hidden||blocked||!modal.hidden)return;
    social.hidden=false;socialStatus("");void refreshSocial();
  }
  socialButton.onclick=showSocial;by("c3-social-close").onclick=closeSocial;
  function chooseSocialTab(tab){
    socialTab=tab;
    for(const key of ["chat","party","training"])by("c3-social-"+key).hidden=key!==tab;
    for(const button of social.querySelectorAll("nav button"))button.classList.toggle("selected",button.dataset.tab===tab);
  }
  for(const button of social.querySelectorAll("nav button"))button.onclick=()=>chooseSocialTab(button.dataset.tab);
  chooseSocialTab("chat");
  function row(parent,label,actions=[]){
    const line=document.createElement("div");line.className="c3-party-row";
    const text=document.createElement("span");text.textContent=label;line.append(text);
    const buttons=document.createElement("div");line.append(buttons);
    for(const [name,fn] of actions){
      const b=document.createElement("button");b.type="button";b.textContent=name;b.onclick=fn;buttons.append(b);
    }
    parent.append(line);
  }
  function section(id,heading){
    const node=by(id);node.replaceChildren();
    const h=document.createElement("h3");h.textContent=heading;node.append(h);return node;
  }
  function renderSocial(state){
    if(!state)return;
    socialState=state;
    socialButton.textContent=(state.invites?.length?"Группа ("+state.invites.length+")":"Чат / Группа");
    showSocialButton();
    if(social.hidden)return;
    const chat=by("c3-chat-log"),atBottom=chat.scrollHeight-chat.scrollTop-chat.clientHeight<35;
    chat.replaceChildren();
    for(const m of state.messages||[]){
      const p=document.createElement("p"),name=document.createElement("strong");
      name.textContent=(m.channel==="party"?"[Группа] ":"[Мир] ")+m.name+": ";
      name.style.color=m.channel==="party"?"#a8cbea":"#e7c883";
      p.append(name,document.createTextNode(m.body));chat.append(p);
    }
    if(atBottom||!chat.scrollTop)chat.scrollTop=chat.scrollHeight;
    const select=by("c3-chat-channel");select.options[1].disabled=!state.party;
    if(!state.party&&select.value==="party")select.value="world";
    const members=section("c3-party-members","Группа · "+(state.members?.length||0)+"/4");
    if(!state.party)row(members,"Ты пока не в группе.");
    for(const m of state.members||[])row(members,(m.id===state.leader?"★ ":"")+m.name+(m.online?" · онлайн":" · офлайн"));
    by("c3-party-leave").hidden=!state.party;
    const invites=section("c3-party-invites","Приглашения");
    if(!state.invites?.length)row(invites,"Нет приглашений");
    for(const i of state.invites||[])row(invites,i.from,[["Принять",()=>socialAction("accept",{invite:i.id})],["Отклонить",()=>socialAction("decline",{invite:i.id})]]);
    const online=section("c3-party-players","Игроки онлайн");
    if(!state.players?.length)row(online,"Других игроков пока нет");
    const canInvite=!state.party||state.leader===state.me;
    for(const p of state.players||[])row(online,p.name,canInvite&&!state.members?.some(m=>m.id===p.id)?[["Пригласить",()=>socialAction("invite",{target:p.id})]]:[]);
    const t=state.training;
    if(t){
      by("c3-training-hp").style.width=Math.max(0,Math.min(100,t.hp/t.max_hp*100))+"%";
      by("c3-training-detail").textContent="HP "+t.hp+"/"+t.max_hp+" · Побед всего: "+t.defeats+" · Твой урон: "+t.damage+" · Добивания: "+t.finishing_hits;
      by("c3-training-hit").disabled=t.hp<=0||socialBusy;
    }
  }
  async function refreshSocial(){
    if(!active||blocked||exiting||!client||!cover.hidden||socialBusy||readPromise)return;
    socialLast=Date.now();
    readPromise=rpc("c3_social",{p_action:"state",p_payload:{}});
    try{renderSocial(await readPromise);}
    catch(e){if(!social.hidden)socialStatus("Связь: "+e.message);}
    finally{readPromise=null;}
  }
  async function socialAction(action,payload={}){
    if(socialBusy||!active||blocked||!client)return;
    socialBusy=true;socialStatus("...");
    for(const b of social.querySelectorAll("button:not(#c3-social-close)"))b.disabled=true;
    try{
      if(readPromise)try{await readPromise;}catch(_){}
      const state=await rpc("c3_social",{p_action:action,p_payload:payload});
      socialLast=Date.now();
      socialStatus(action==="attack"?"Урон: "+(state.training?.last_damage||0):action==="invite"?"Приглашение отправлено.":"Готово.");
      renderSocial(state);
      return true;
    }catch(e){socialStatus(e.message);return false;}
    finally{
      socialBusy=false;
      for(const b of social.querySelectorAll("button"))b.disabled=false;
      if(socialState?.training)by("c3-training-hit").disabled=socialState.training.hp<=0;
    }
  }
  by("c3-chat-form").onsubmit=async e=>{
    e.preventDefault();
    const input=by("c3-chat-input"),body=input.value.trim();
    if(!body)return;
    if(await socialAction("chat",{channel:by("c3-chat-channel").value,body})&&input.value.trim()===body)input.value="";
  };
  by("c3-party-leave").onclick=()=>void socialAction("leave");
  by("c3-training-hit").onclick=()=>void socialAction("attack");
  setInterval(()=>{
    if(active&&cover.hidden&&!blocked&&Date.now()-socialLast>(social.hidden?12000:3000))void refreshSocial();
  },1000);

  window.C3Online={
    attachMenu:(callback,muted,quality)=>{command=callback;by('c3-sound').value=muted?'off':'on';by('c3-quality').value=String(quality);enableMenu();},
    menuOpen:()=>!modal.hidden||!social.hidden,
    menuAck:(ok,message)=>{ack={ok:!!ok,message:String(message||'')};},
    character:()=>active?JSON.stringify(character):"",
    peers:()=>JSON.stringify(players),
    blocked:()=>blocked,
    save:(progress,region,x,z)=>{if(active&&!blocked){try{pendingSave={p_progress:JSON.parse(progress),p_region:region,p_x:x,p_z:z};void flush();}catch(e){report("Ошибка формата сохранения");}}},
    tick:async(region,x,z,heading)=>{if(!active||busy||blocked||exiting)return;busy=true;try{players=await rpc("c3_world_tick",{p_region:region,p_x:x,p_z:z,p_heading:heading});report("ONLINE · рядом "+players.length+(pendingSave?" · сохранение…":""));}catch(e){players=[];report("Связь потеряна");if(e.message.includes("unavailable")){blocked=true;report("Доступ прекращён · обнови страницу");}}finally{busy=false;}}
  };
  setInterval(flush,3000);
  window.addEventListener("pagehide",()=>{if(active&&!blocked){void flush();void rpc("c3_leave").catch(()=>{});}});
  import("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.49.4/+esm").then(async({createClient})=>{
    client=createClient(cfg.url,cfg.key);by("c3login").disabled=false;by("c3signup").disabled=false;await refresh();
  }).catch(e=>msg("Сервер недоступен: "+e.message));
})();
