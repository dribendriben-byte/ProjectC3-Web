"""Additive UI upgrade on the pinned successful 0.18 alpha. No auth or save migration."""
from pathlib import Path
import sys,re
root=Path(sys.argv[1])
bridge=Path(sys.argv[2])
def edit(path,pairs):
    p=root/path;s=p.read_text(encoding="utf-8")
    for a,b in pairs:
        if s.count(a)!=1:raise RuntimeError(f"{path}: expected one anchor {a[:100]!r}, got {s.count(a)}")
        s=s.replace(a,b,1)
    p.write_text(s,encoding="utf-8")

# Shared 10 slots, different geometry. The book always uses its own fixed ten-slot assignment row.
edit("field/hud.gd",[
('var playing := false','var playing := false\nvar mobile_bar:=false'),
('s.bg_color = color','''s.bg_color = color
	s.set_border_width_all(1)
	s.border_color=Color("#9c8254")'''),
('Color("#172823ec")','Color("#1b1914eb")'),
('Color("#345348")','Color("#352c1e")'),
('Color("#476654")','Color("#55432a")'),
('Color("#756445")','Color("#9b7846")'),
('Color("#20362f")','Color("#252018")'),
('b.flat=true\n\tb.mouse_default_cursor_shape','''b.flat=false
	b.add_theme_stylebox_override("normal",style(Color("#211d17ed"),10))
	b.add_theme_stylebox_override("hover",style(Color("#50422c"),10))
	b.add_theme_stylebox_override("pressed",style(Color("#79613c"),10))
	b.mouse_default_cursor_shape'''),
('''		floating.position = floating.position.clamp(Vector2.ZERO,(ui.size-floating.size).max(Vector2.ZERO))''','''		floating.position = floating.position.clamp(Vector2.ZERO,(ui.size-floating.size).max(Vector2.ZERO))
	apply_bar_layout()

func set_mobile_bar(value:bool)->void:
	mobile_bar=value
	cancel_bar_drag()
	layout_screen()

func apply_bar_layout()->void:
	var extra:Vector2=(ui.size-Vector2(960,540)).max(Vector2.ZERO)
	for i in slots.size():
		if mobile_bar:
			slots[i].position=Vector2(605+(i%5)*60,335+floori(i/5.0)*60)+extra
			slots[i].size=Vector2(56,56)
		else:
			slots[i].position=SkillButton.bar_rect(i).position+Vector2(extra.x*.5,extra.y)
			slots[i].size=SkillButton.bar_rect(i).size
	stick.visible=mobile_bar
	if not mobile_bar:stick.reset()
	if mobile_bar:
		autoattack.position=Vector2(866,462)+extra
		pickup_button.position=Vector2(804,468)+extra
		target_button.position=Vector2(866+extra.x,205)
		feed.get_parent().position=Vector2(145+extra.x*.5,458+extra.y)
		target_name.get_parent().position=Vector2(704+extra.x,275)
	else:
		feed.get_parent().position=Vector2(144+extra.x*.5,421+extra.y)
		target_name.get_parent().position=Vector2(704+extra.x,419+extra.y)'''),
])
edit("field/skill_button.gd",[
('Color("#142522f2")','Color("#211c16f2")'),
('const EDGE=Color("#a79569")','const EDGE=Color("#ae905c")'),
])
# A redesigned book retains the exact external signal/field contract.
p=root/"field/spellbook.gd"
p.write_text('''extends Control
signal closed
signal changed
signal learn_requested(index:int)
const Slot=preload("res://field/skill_button.gd")
const Icons=preload("res://field/icon_library.gd")
const GOLD=Color("#e9c784")
const PAPER=Color("#f4ead0")
const MUTED=Color("#aaa497")
const INK=Color("#191611f8")
const CLOSE=Rect2(848,22,70,42)
const ACTION=Rect2(603,342,298,46)
const REMOVE=Rect2(603,293,298,40)
const ACTIVE=Rect2(45,89,156,38)
const PASSIVE=Rect2(210,89,156,38)
var hero
var catalog:Dictionary={}
var training:=false
var chosen:=""
var passive:=false
var pointer:=-99
var origin:=Vector2.ZERO
var current:=Vector2.ZERO
var pressed_id:=""
var pressed_slot:=-1
var dragging:=false
var status:=""

func present(profile,entries:Dictionary,at_trainer:bool=false)->void:
	hero=profile
	catalog=entries
	training=at_trainer
	passive=false
	chosen=""
	status=""
	reset_pointer()
	show()
	queue_redraw()

func reset_pointer()->void:
	pointer=-99
	pressed_id=""
	pressed_slot=-1
	dragging=false

func allowed(id:String)->bool:
	return catalog.has(id) and (not catalog[id].has("index") or hero.knows(catalog[id]))

func group_of(sk:Dictionary)->int:
	var effect:String=str(sk.get("effect",""))
	if effect in ["heal","guard","haste","focus","renew","barrier","mend","surge"]:return 1
	if effect in ["stun","spoil"]:return 2
	return 0

func spell_ids()->Array:
	var ids:Array=[]
	if passive:return ids
	for group in 3:
		for id in catalog:
			if catalog[id].has("index") and group_of(catalog[id])==group:ids.append(id)
	return ids

func card_rect(i:int)->Rect2:
	return Rect2(47+(i%5)*106,152+floori(i/5.0)*113,98,102)

func card_at(p:Vector2)->String:
	var ids:=spell_ids()
	for i in mini(ids.size(),10):
		if card_rect(i).has_point(p):return str(ids[i])
	return ""

func slot_at(p:Vector2)->int:
	for i in mini(10,hero.hotbar.size()):
		if Slot.bar_rect(i).has_point(p):return i
	return -1

func assign(id:String,to:int)->void:
	if not allowed(id) or to<0 or to>=hero.hotbar.size():return
	var old:int=hero.hotbar.find(id)
	if old>=0:hero.hotbar[old]=hero.hotbar[to]
	hero.hotbar[to]=id
	status="%s → %d" % [catalog[id].name,(to+1)%10]
	changed.emit()

func finish(p:Vector2)->void:
	if origin.distance_to(p)>8:
		var to:=slot_at(p)
		if allowed(pressed_id) and to>=0:assign(pressed_id,to)
		return
	if CLOSE.has_point(p):closed.emit();return
	if ACTIVE.has_point(p) or PASSIVE.has_point(p):
		passive=PASSIVE.has_point(p);chosen="";return
	if chosen!="" and catalog.has(chosen):
		var rec:Dictionary=catalog[chosen]
		if REMOVE.has_point(p) and allowed(chosen):
			var ix:int=hero.hotbar.find(chosen)
			if ix>=0:hero.hotbar[ix]="";changed.emit()
			return
		if ACTION.has_point(p):
			if allowed(chosen):
				var ix:int=hero.hotbar.find("")
				if ix>=0 and not hero.hotbar.has(chosen):assign(chosen,ix)
				else:status="Коснись нужной ячейки внизу."
			elif training and hero.level()>=rec.level and hero.sp>=rec.sp:learn_requested.emit(rec.index)
			return
	var destination:=slot_at(p)
	if destination>=0 and pressed_slot==destination:
		if allowed(chosen):assign(chosen,destination)
		elif pressed_id!="":chosen=pressed_id
		return
	var id:=card_at(p)
	if id!="":chosen=id;status=""

func _gui_input(e:InputEvent)->void:
	if hero==null:return
	var id:int
	if e is InputEventScreenTouch or e is InputEventScreenDrag:id=e.index
	elif e is InputEventMouseButton or e is InputEventMouseMotion:
		if e.device==InputEvent.DEVICE_ID_EMULATION:return
		id=-1
	else:return
	if e is InputEventMouseButton and e.button_index!=MOUSE_BUTTON_LEFT:return
	var p:Vector2=e.position
	if e is InputEventMouseButton or e is InputEventScreenTouch:
		if e.pressed and pointer==-99:
			pointer=id;origin=p;current=p
			pressed_slot=slot_at(p)
			pressed_id=card_at(p) if pressed_slot<0 else str(hero.hotbar[pressed_slot])
		elif not e.pressed and pointer==id:
			if not e.canceled:finish(p)
			reset_pointer()
	elif pointer==id:
		current=p
		dragging=allowed(pressed_id) and origin.distance_to(p)>8
	queue_redraw()
	accept_event()

func box(r:Rect2,bg:Color,edge:Color,thick:int=1)->void:
	draw_rect(r,bg)
	draw_rect(r.grow(-1),edge,false,thick)

func words(p:Vector2,t:String,px:int,tint:Color,span:float=-1,align:=HORIZONTAL_ALIGNMENT_LEFT)->void:
	draw_string(ThemeDB.fallback_font,p,t,align,span,px,tint)

func centered(r:Rect2,t:String,selected:bool=false)->void:
	box(r,Color("#473822") if selected else Color("#28221a"),GOLD if selected else Color("#756449"))
	words(r.position+Vector2(0,r.size.y*.5+6),t,16,PAPER,r.size.x,HORIZONTAL_ALIGNMENT_CENTER)

func _draw()->void:
	if hero==null:return
	box(Rect2(25,12,910,396),INK,Color("#927a4f"))
	words(Vector2(47,47),"МАСТЕР КЛАССА" if training else "КНИГА УМЕНИЙ",25,PAPER)
	words(Vector2(47,72),"%s · Ур. %d · %d SP" % [hero.title(),hero.level(),hero.sp],15,GOLD,770)
	centered(CLOSE,"×")
	centered(ACTIVE,"Активные",not passive)
	centered(PASSIVE,"Пассивные",passive)
	draw_line(Vector2(584,91),Vector2(584,389),Color("#6c5a3f"),1)
	var ids:=spell_ids()
	if passive:words(Vector2(49,181),"Пассивные навыки пока не реализованы.",17,MUTED,520)
	for i in mini(ids.size(),10):
		var id:String=ids[i]
		var sk:Dictionary=catalog[id]
		var r:=card_rect(i)
		var known:=allowed(id)
		var selected:=id==chosen
		box(r,Color("#473822") if selected else Color("#27231c"),GOLD if selected else Color("#6c5d43"),2 if selected else 1)
		draw_texture_rect(Icons.for_skill(sk),Rect2(r.position+Vector2(26,5),Vector2(46,46)),false,Color.WHITE if known else Color("#808078"))
		words(r.position+Vector2(4,63),str(["Атака","Усиление","Ослабление"][group_of(sk)]),11,GOLD,r.size.x-8,HORIZONTAL_ALIGNMENT_CENTER)
		words(r.position+Vector2(4,78),str(sk.name),12,PAPER if known else MUTED,r.size.x-8)
		words(r.position+Vector2(4,94),"Изучено" if known else "Ур. "+str(sk.level),11,MUTED,r.size.x-8)
	if chosen!="" and catalog.has(chosen):
		var sk:Dictionary=catalog[chosen]
		words(Vector2(603,115),str(sk.name),20,GOLD,298)
		draw_multiline_string(ThemeDB.fallback_font,Vector2(603,146),str(sk.get("description","")),HORIZONTAL_ALIGNMENT_LEFT,296,15,3,PAPER)
		if sk.has("index"):
			words(Vector2(603,212),"Мана: %d  ·  КД: %.1f с" % [sk.mp,sk.cd],15,PAPER)
			words(Vector2(603,237),"Требуется уровень %d" % sk.level,15,Color("#b8d598") if hero.level()>=sk.level else Color("#d59382"))
			words(Vector2(603,262),"Стоимость: %d SP" % sk.sp,15,Color("#b8d598") if hero.sp>=sk.sp else Color("#d59382"))
		if allowed(chosen):
			if hero.hotbar.has(chosen):centered(REMOVE,"Убрать с панели")
			centered(ACTION,"На панель",true)
		else:
			centered(ACTION,"Изучить" if training and hero.level()>=sk.level and hero.sp>=sk.sp else ("Недоступно" if training else "Только у мастера"))
	else:
		words(Vector2(603,132),"Выбери умение",20,GOLD)
		words(Vector2(603,164),"Описание, мана, перезарядка",14,MUTED)
		words(Vector2(603,184),"и требования появятся здесь.",14,MUTED)
	box(Rect2(130,413,670,121),INK,Color("#927a4f"))
	words(Vector2(145,440),status if status!="" else "Выбери умение, затем ячейку 1–0",16,GOLD,640)
	for i in mini(10,hero.hotbar.size()):
		var rec:Dictionary=catalog.get(hero.hotbar[i],{})
		Slot.paint(self,Slot.bar_rect(i),i+1,rec,false,dragging and slot_at(current)==i)
	if dragging and catalog.has(pressed_id):
		var ghost:=Rect2(current-Vector2(25,57),Vector2(50,50))
		draw_texture_rect(Icons.for_skill(catalog[pressed_id]),ghost,false)
		draw_rect(ghost,GOLD,false,2)

func _notification(what:int)->void:
	if what==NOTIFICATION_VISIBILITY_CHANGED or what==NOTIFICATION_APPLICATION_FOCUS_OUT:reset_pointer()
''',encoding="utf-8")
# Sound controls have separate real volume paths; existing mute toggle remains.
edit("ford/audio.gd",[
('var muted := false','var muted := false\nvar effects_gain:=1.0'),
('voice.volume_db=LEVELS[id]','voice.volume_db=LEVELS[id]+linear_to_db(maxf(.0001,effects_gain))'),
])
edit("ford/world.gd",[
('var menu_callback\n','''var menu_callback
var ui_fps_label:Label
var ui_names:=0
var ui_fps_elapsed:=0.0
var ui_ambient:Environment
var ui_default_far:=150.0
'''),
('\t\t"quality":\n\t\t\tif args.size()<2: return\n\t\t\tapply_quality(clampi(int(args[1]),0,2))','''		"quality":
			if args.size()<2: return
			apply_quality(clampi(int(args[1]),0,2))
		"layout":
			if args.size()>=2:hud.set_mobile_bar(bool(args[1]))
		"window":
			if args.size()>=2:
				match str(args[1]):
					"Задания":open_journal()
					"Профессии":hud.show_careers(profile,near_trainer())
					"Карта":open_ui_map()
					_:open_window(str(args[1]))
		"graphics":
			if args.size()>=2:
				var settings=JSON.parse_string(str(args[1]))
				if settings is Dictionary:apply_ui_graphics(settings)
		"audio":
			if args.size()>=2:
				var settings=JSON.parse_string(str(args[1]))
				if settings is Dictionary:apply_ui_audio(settings)'''),
('\tonline_process(dt)\n\tif web_menu_open()','\tonline_process(dt)\n\tupdate_ui_display(dt)\n\tif web_menu_open()'),
])
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")+'''
func open_ui_map()->void:
	var rows:VBoxContainer=hud.show_panel("Карта текущей области")
	var map:=preload("res://field/radar.gd").new()
	map.custom_minimum_size=Vector2(440,260)
	map.town=town
	map.player=actor
	map.creatures=hud.radar.creatures.duplicate()
	map.hostile=hud.radar.hostile.duplicate()
	rows.add_child(map)
	var close:=hud.button("Закрыть")
	rows.add_child(close)
	close.pressed.connect(hud.shade.hide)

func apply_ui_graphics(opts:Dictionary)->void:
	apply_quality(clampi(int(opts.get("quality",quality_level)),0,2))
	var view:=get_viewport()
	Engine.max_fps=int([30,60,0][clampi(int(opts.get("fps",1)),0,2)])
	view.scaling_3d_scale=float([.6,.85,1.0][clampi(int(opts.get("resolution",2)),0,2)])
	view.msaa_3d=Viewport.MSAA_2X if bool(opts.get("aa",true)) else Viewport.MSAA_DISABLED
	var shadows:=clampi(int(opts.get("shadows",2)),0,2)
	$Sun.shadow_enabled=shadows>0
	$Sun.directional_shadow_max_distance=42.0 if shadows==2 else 22.0
	cam.far=float([65,100,150][clampi(int(opts.get("distance",2)),0,2)])
	ui_names=clampi(int(opts.get("names",0)),0,1)
	if ui_ambient==null:
		for child in get_children():
			if child is WorldEnvironment:ui_ambient=child.environment;break
	if ui_ambient!=null:
		ui_ambient.adjustment_enabled=true
		ui_ambient.adjustment_brightness=clampf(float(opts.get("brightness",100))*.01,.65,1.4)
		ui_ambient.adjustment_saturation=1.08 if bool(opts.get("color",true)) else 1.0
		ui_ambient.adjustment_contrast=1.04 if bool(opts.get("color",true)) else 1.0
	if ui_fps_label==null:
		ui_fps_label=hud.label("",13,Color("#efce8b"))
		hud.place(hud.ui,ui_fps_label,Rect2(322,10,110,25))
	ui_fps_label.visible=bool(opts.get("showFps",false))

func apply_ui_audio(opts:Dictionary)->void:
	AudioServer.set_bus_volume_db(0,linear_to_db(maxf(.0001,clampf(float(opts.get("master",100))*.01,0,1))))
	sound.music.volume_db=-11+linear_to_db(maxf(.0001,clampf(float(opts.get("music",100))*.01,0,1)))
	sound.effects_gain=clampf(float(opts.get("effects",100))*.01,0,1)

func update_ui_display(dt:float)->void:
	ui_fps_elapsed+=dt
	if ui_fps_elapsed<.25:return
	ui_fps_elapsed=0.0
	if ui_fps_label!=null and ui_fps_label.visible:ui_fps_label.text="FPS %d" % Engine.get_frames_per_second()
	for mob in mobs:
		if mob.label!=null:mob.label.visible=ui_names==0 or mob==target
'''
p.write_text(s,encoding="utf-8")
# Keep original bridge and all its account/login/save handlers. Add UI elements in its closure.
s=bridge.read_text(encoding="utf-8")
anchor="  window.C3Online={"
if s.count(anchor)!=1:raise RuntimeError("Unknown bridge")
s=s.replace(anchor,'''  // C3 0.20 interface: existing session and save handlers remain intact.
  const prefKey="c3-ui-020";
  const defaults={layout:matchMedia("(pointer: coarse)").matches?"mobile":"desktop",quality:2,resolution:2,shadows:2,distance:2,names:0,fps:1,aa:true,brightness:100,color:true,showFps:false,master:100,music:100,effects:100};
  let prefs={...defaults};try{Object.assign(prefs,JSON.parse(localStorage.getItem(prefKey)||"{}"))}catch(_){}
  const writePrefs=()=>{try{localStorage.setItem(prefKey,JSON.stringify(prefs))}catch(_){}};
  function applyPrefs(){if(!command)return;command("layout",prefs.layout==="mobile");command("graphics",JSON.stringify(prefs));command("audio",JSON.stringify(prefs));}
  const uiCss=document.createElement("style");
  uiCss.textContent=`#c3-game-menu section,#c3-social section{background:linear-gradient(150deg,#272219,#16140f);border:1px solid #a98a54;color:#f0e4c9;border-radius:10px}#c3-game-menu section{width:min(650px,100%);padding:16px;box-sizing:border-box}#c3-game-menu h2,#c3-social h2{font:normal 25px Georgia,serif;color:#ecd09a}#c3-game-menu button,#c3-social button,#c3-menu-button,#c3-social-button{background:linear-gradient(#403526,#211b14);border:1px solid #9d8255;color:#f0dfbd;border-radius:7px}#c3-game-menu button:disabled{opacity:.5}#c3-game-menu button:hover,#c3-game-menu button:focus-visible{border-color:#f5d28d}#c3-game-menu #c3-resume,#c3-game-menu #c3-ui-done{background:linear-gradient(#d0ad6c,#9e783c);color:#20170d;font-weight:700}#c3-ui-nav{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin:10px 0}#c3-ui-nav button{min-height:65px;white-space:normal;font-size:13px}#c3-ui-nav span{display:block;font-size:24px;line-height:1.2;color:#e5bf7f}#c3-ui-settings[hidden],#c3-ui-home[hidden],#c3-ui-settings [hidden]{display:none!important}#c3-ui-tabs{display:flex;gap:6px;margin:12px 0}#c3-ui-tabs button{flex:1}#c3-ui-tabs button.selected{border-color:#e5bf7f;background:#54442a}#c3-ui-content{display:grid;gap:8px;max-height:48vh;overflow:auto;overscroll-behavior:contain;padding-right:4px}#c3-ui-content .setting{display:grid;grid-template-columns:minmax(105px,1fr) minmax(0,1.35fr);gap:8px;align-items:center;padding:7px 0;border-bottom:1px solid #51442e}#c3-ui-content .choices{display:flex;gap:5px;flex-wrap:wrap}#c3-ui-content .choices button{flex:1;min-width:0;width:auto;padding:8px 6px;white-space:normal}#c3-ui-content .choices button.selected{background:#675332;border-color:#e9c784}#c3-ui-content input[type=range]{width:100%;accent-color:#d7b471}#c3-ui-content label{font-size:14px;color:#e6d9bd}#c3-ui-content output{font-size:12px;color:#e8ca91}#c3-ui-note{font-size:11px;color:#cbbd9f}#c3-game-menu .c3-menu-grid{grid-template-columns:1fr 1fr}#c3-game-menu #c3-quality,#c3-game-menu #c3-quality-label{display:none}#c3-game-menu #c3-menu-mode{color:#ccb98e}@media(max-width:420px){#c3-ui-nav{grid-template-columns:repeat(3,minmax(0,1fr))}#c3-ui-content .setting{grid-template-columns:1fr}#c3-ui-content{max-height:55vh}}`;
  document.head.append(uiCss);
  const menuSection=modal.querySelector("section"),oldGrid=modal.querySelector(".c3-menu-grid");
  by("c3-quality").parentElement.id="c3-quality-label";
  const home=document.createElement("div");home.id="c3-ui-home";
  const nav=document.createElement("div");nav.id="c3-ui-nav";
  function tile(icon,title,fn){const b=document.createElement("button");b.type="button";const mark=document.createElement("span");mark.textContent=icon;mark.setAttribute("aria-hidden","true");b.append(mark,document.createTextNode(title));b.onclick=fn;nav.append(b);}
  for(const [icon,title] of [["♙","Персонаж"],["▣","Инвентарь"],["✦","Умения"],["▤","Задания"],["◇","Карта"],["♜","Профессии"]])tile(icon,title,()=>{if(!command)return;hideMenu();command("window",title);});
  tile("♧","Группа / чат",()=>{hideMenu();showSocial();});
  tile("⚙","Настройки",()=>openSettings("graphics"));
  home.append(nav);
  menuSection.insertBefore(home,oldGrid);
  home.append(oldGrid,by("c3-resume"),by("c3-main-menu"),by("c3-switch-account"));
  const settings=document.createElement("div");settings.id="c3-ui-settings";settings.hidden=true;
  settings.innerHTML='<div id="c3-ui-tabs"><button data-ui-tab="audio">Звук</button><button data-ui-tab="panel">Панель</button><button data-ui-tab="graphics">Графика</button></div><div id="c3-ui-content"></div><p id="c3-ui-note"></p><button id="c3-ui-done">Готово</button>';
  menuSection.insertBefore(settings,by("c3-menu-status"));
  let activeSettings="graphics";
  function updatePref(key,value){prefs[key]=value;if(key==="quality"){Object.assign(prefs,value===0?{resolution:0,shadows:0,distance:0,aa:false}:value===1?{resolution:1,shadows:1,distance:1,aa:false}:{resolution:2,shadows:2,distance:2,aa:true});by("c3-quality").value=String(value);}writePrefs();applyPrefs();}
  function setting(label){const row=document.createElement("div");row.className="setting";const l=document.createElement("label");l.textContent=label;row.append(l);by("c3-ui-content").append(row);return row;}
  function choices(label,key,options){const row=setting(label),buttons=document.createElement("div");buttons.className="choices";row.append(buttons);for(const [value,title]of options){const b=document.createElement("button");b.type="button";b.textContent=title;b.classList.toggle("selected",prefs[key]===value);b.onclick=()=>{updatePref(key,value);renderSettings()};buttons.append(b);}}
  function slider(label,key,min,max){const row=setting(label),right=document.createElement("div"),input=document.createElement("input"),out=document.createElement("output");input.type="range";input.min=min;input.max=max;input.value=String(prefs[key]);input.setAttribute("aria-label",label);out.textContent=input.value+"%";input.oninput=()=>{out.textContent=input.value+"%";updatePref(key,Number(input.value));};right.append(input,out);row.append(right);}
  const triples=(a,b,c)=>[[0,a],[1,b],[2,c]];
  const yesno=[[false,"Выкл"],[true,"Вкл"]];
  function renderSettings(){by("c3-ui-content").replaceChildren();for(const b of settings.querySelectorAll("[data-ui-tab]"))b.classList.toggle("selected",b.dataset.uiTab===activeSettings);
    if(activeSettings==="audio"){slider("Общая громкость","master",0,100);slider("Музыка","music",0,100);slider("Эффекты","effects",0,100);by("c3-ui-note").textContent="Общий выключатель звука остаётся в игровом меню.";}
    else if(activeSettings==="panel"){choices("Управление","layout",[["mobile","Телефон"],["desktop","Компьютер"]]);by("c3-ui-note").textContent="Те же десять ячеек и назначения. На ПК: 1–0, пробел — атака. На телефоне: сенсорные ячейки справа.";}
    else{slider("Яркость","brightness",65,140);choices("Качество","quality",triples("Низкое","Среднее","Высокое"));choices("Разрешение 3D","resolution",triples("60%","85%","100%"));choices("Тени","shadows",triples("Нет","Близко","Далеко"));choices("Прорисовка","distance",triples("65 м","100 м","150 м"));choices("Имена мобов","names",[[0,"Все"],[1,"Только цель"]]);choices("FPS","fps",triples("30","60","Без лимита"));choices("Сглаживание","aa",yesno);choices("Цвет и контраст","color",yesno);choices("Показывать FPS","showFps",yesno);by("c3-ui-note").textContent="Параметры меняются сразу; поддержка эффектов зависит от браузера и графического драйвера.";}
  }
  function openSettings(tab){activeSettings=tab;home.hidden=true;settings.hidden=false;renderSettings();}
  for(const b of settings.querySelectorAll("[data-ui-tab]"))b.onclick=()=>openSettings(b.dataset.uiTab);
  by("c3-ui-done").onclick=()=>{settings.hidden=true;home.hidden=false;};
  menuButton.addEventListener("click",()=>{if(!modal.hidden){home.hidden=false;settings.hidden=true;}});
  window.C3Online={''')
s=s.replace('by(\\'c3-quality\\').value=String(quality);enableMenu();','by(\\'c3-quality\\').value=String(prefs.quality);enableMenu();applyPrefs();')
if "enableMenu();applyPrefs();" not in s:raise RuntimeError("No settings initialization")
bridge.write_text(s,encoding="utf-8")
# Cache-safe UI patch label, retain exact original authentication and bridge paths in historical build.
p=root/"web/shell.html";s=p.read_text(encoding="utf-8");s=s.replace("PRE-ALPHA 0.18","PRE-ALPHA 0.20 UI TEST");p.write_text(s,encoding="utf-8")
(root/"ui_test.gd").write_text('''extends SceneTree
func _initialize()->void:
	call_deferred("run_test")
func fail(reason:String)->void:
	push_error(reason)
	quit(1)
func run_test()->void:
	var w=preload("res://ford/ford.tscn").instantiate()
	root.add_child(w)
	await process_frame
	var saved:Array=w.profile.hotbar.duplicate()
	w.hud.set_mobile_bar(true)
	if w.hud.slots.size()!=10 or not w.hud.stick.visible or w.hud.slots[0].position.x<500:
		fail("Mobile layout invalid");return
	for i in 10:
		if w.hud.bar_at(w.hud.slots[i].get_rect().get_center())!=i:
			fail("Mobile slot hit test failed");return
	w.hud.set_mobile_bar(false)
	if w.hud.stick.visible or w.hud.slots[0].position.x>=500 or w.profile.hotbar!=saved:
		fail("Desktop layout or slot preservation invalid");return
	w.hud.show_book(w.profile,w.catalog,false)
	if not w.hud.book_editor.visible or w.hud.book_editor.training:
		fail("Spellbook invalid");return
	w.hud.shade.hide()
	w.apply_ui_graphics({"quality":0,"fps":0,"resolution":0,"shadows":0,"distance":0,"showFps":true})
	if Engine.max_fps!=30 or w.get_node("Sun").shadow_enabled or not w.ui_fps_label.visible:
		fail("Graphics settings not applied");return
	w.apply_ui_audio({"master":50,"music":50,"effects":50})
	if absf(w.sound.effects_gain-.5)>.01:
		fail("Audio setting invalid");return
	print("C3 UI 020 smoke test passed")
	quit(0)
''',encoding="utf-8")
print("C3 UI 020 patch applied")
