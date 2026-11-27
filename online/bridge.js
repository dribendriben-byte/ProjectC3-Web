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
  window.C3Online={
    character:()=>active?JSON.stringify(character):"",
    peers:()=>JSON.stringify(players),
    blocked:()=>blocked,
    save:(progress,region,x,z)=>{if(active&&!blocked){try{pendingSave={p_progress:JSON.parse(progress),p_region:region,p_x:x,p_z:z};void flush();}catch(e){report("Ошибка формата сохранения");}}},
    tick:async(region,x,z,heading)=>{if(!active||busy||blocked)return;busy=true;try{players=await rpc("c3_world_tick",{p_region:region,p_x:x,p_z:z,p_heading:heading});report("ONLINE · рядом "+players.length+(pendingSave?" · сохранение…":""));}catch(e){players=[];report("Связь потеряна");if(e.message.includes("unavailable")){blocked=true;report("Доступ прекращён · обнови страницу");}}finally{busy=false;}}
  };
  setInterval(flush,3000);
  window.addEventListener("pagehide",()=>{if(active&&!blocked){void flush();void rpc("c3_leave").catch(()=>{});}});
  import("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.49.4/+esm").then(async({createClient})=>{
    client=createClient(cfg.url,cfg.key);by("c3login").disabled=false;by("c3signup").disabled=false;await refresh();
  }).catch(e=>msg("Сервер недоступен: "+e.message));
})();
