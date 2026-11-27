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
  const banner=document.createElement("div");banner.hidden=true;banner.style.cssText="position:fixed;top:4px;left:4px;z-index:2;padding:4px 8px;background:#15221e;color:#e7d5a4;font:11px system-ui;pointer-events:none";document.body.append(banner);
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
  menuStyle.textContent="#c3-menu-button{position:fixed;top:max(8px,env(safe-area-inset-top));left:calc(50% + 86px);z-index:2;width:auto;margin:0;padding:7px 12px;font-size:12px;background:#172823ed;color:#f2e7ca;border:1px solid #8a7754}#c3-menu-button[hidden],#c3-game-menu[hidden]{display:none}#c3-game-menu{position:fixed;inset:0;z-index:6;background:#09120dcc;display:grid;place-items:center;overflow:auto;touch-action:pan-y;padding:12px}#c3-game-menu section{width:min(440px,100%);max-height:100%;overflow:auto;padding:16px;background:#172720;border:1px solid #b89a65;border-radius:12px;box-shadow:0 12px 40px #0009}#c3-game-menu h2{margin:0 0 6px}#c3-game-menu p{margin:5px 0;font-size:12px}#c3-game-menu button{font-size:13px;margin:4px 0;padding:9px 10px}#c3-game-menu select{display:block;width:100%;font-size:14px;padding:8px;margin:5px 0;border:1px solid #677c64;background:#101b18;color:#f2e7ca;border-radius:5px}#c3-game-menu label{font-size:12px;color:#c5d0c6}.c3-menu-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px}#c3-menu-status{min-height:18px;overflow-wrap:anywhere}#c3-resume{background:#a9bf88}#c3-switch-account{background:#795d47;color:#fff4db}";
  document.head.append(menuStyle);
  const menuStatus=t=>by("c3-menu-status").textContent=t;
  function enableMenu(){menuButton.hidden=cover.hidden!==true||!command;}
  new MutationObserver(enableMenu).observe(cover,{attributes:true,attributeFilter:["hidden"]});
  function setMenuBusy(value){menuBusy=value;for(const el of modal.querySelectorAll("button,select"))el.disabled=value;}
  function showMenu(){
    if(!command||menuBusy||!cover.hidden)return;
    modal.hidden=false;by("c3-menu-mode").textContent=active?"ONLINE · "+(character?.name||""):"Офлайн · локальное сохранение";
    menuStatus("");by("c3-fullscreen").disabled=!by("fullscreen")||by("fullscreen").hidden;
    by("c3-resume").focus();
  }
  function hideMenu(){if(menuBusy)return;modal.hidden=true;by("canvas").focus();}
  menuButton.onclick=showMenu;
  by("c3-resume").onclick=hideMenu;
  by("c3-quality").onchange=()=>{command?.("quality",Number(by("c3-quality").value));};
  by("c3-sound").onchange=()=>{command?.("sound",by("c3-sound").value==="off");};
  by("c3-fullscreen").onclick=()=>by("fullscreen")?.click();
  window.addEventListener("keydown",e=>{if(e.key!=="Escape"||cover.hidden!==true||!command)return;e.preventDefault();e.stopImmediatePropagation();if(modal.hidden)showMenu();else hideMenu();},true);
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

  window.C3Online={
    attachMenu:(callback,muted,quality)=>{command=callback;by('c3-sound').value=muted?'off':'on';by('c3-quality').value=String(quality);enableMenu();},
    menuOpen:()=>!modal.hidden,
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
