"""Build the isolated 0.19 world preview directly from the retained v0.9 source.
Do not apply on the live alpha. No changes to legacy characters or save paths.
"""
from pathlib import Path
import shutil,sys
root=Path(sys.argv[1])
here=Path(__file__).parent

def edit(file,pairs):
    p=root/file
    s=p.read_text(encoding="utf-8")
    for a,b in pairs:
        if s.count(a)!=1:
            raise RuntimeError(f"{file}: expected one anchor, found {s.count(a)}: {a[:100]!r}")
        s=s.replace(a,b,1)
    p.write_text(s,encoding="utf-8")
def section(file,start,end,body):
    p=root/file;s=p.read_text(encoding="utf-8")
    a=s.index(start);b=s.index(end,a+len(start))
    p.write_text(s[:a]+body+"\n\n"+s[b:],encoding="utf-8")
def append(file,body):
    p=root/file;p.write_text(p.read_text(encoding="utf-8")+"\n"+body,encoding="utf-8")

for f in ["ground.gd","stage.gd","looks.gd","worn.gd","creature.gd"]:
    shutil.copyfile(here/f,root/"ford"/f)

edit("project.godot",[
('config/name="Project C3 — Травяной брод 3D"','config/name="Project C3 — Вересковые земли"'),
('config/version="0.9.0"','config/version="0.19.0"'),
('[rendering]\n','[rendering]\ntextures/vram_compression/import_etc2_astc=true\n'),
])
edit("web/shell.html",[
('PRE-ALPHA 0.9 · SINGLE PLAYER','WORLD PREVIEW 0.19'),
('<script src="$GODOT_URL"></script>','<script src="c3-config.js"></script>\n<script src="c3-menu-019.js"></script>\n<script src="$GODOT_URL"></script>'),
])
# Start equipment. These IDs are independent of the legacy alpha.
edit("field/loot.gd",[
('const ITEMS := {','''const ITEMS := {
	"ng_sword":["Меч новичка · NG","Оружие",4],
	"ng_staff":["Посох новичка · NG","Оружие",4],
	"ng_dagger":["Кинжал новичка · NG","Оружие",4],
	"ng_axe":["Топор новичка · NG","Оружие",4],
	"ng_hammer":["Молот новичка · NG","Оружие",4],'''),
('var t: Array = TABLE[kind]','var t: Array = TABLE[mini(kind,2)]'),
('[0.5,0.16,1.54][kind]','[0.5,0.16,1.54,1.8][kind]'),
])
edit("field/icon_library.gd",[
('const TEXTURES := {','''const TEXTURES := {
	"ng_sword":preload("res://field/art/icons/strike.svg"),
	"ng_staff":preload("res://field/art/icons/renew.svg"),
	"ng_dagger":preload("res://field/art/icons/knife.svg"),
	"ng_axe":preload("res://field/art/icons/crush.svg"),
	"ng_hammer":preload("res://field/art/icons/hammer.svg"),'''),
])
edit("field/careers.gd",[
('var race := ""','var appearance:Dictionary={}\nvar character_name:="Путник"\nvar race := ""'),
('return sk.level==1 or learned.has(sk.name)','return learned.has(sk.name)'),
])
(root/"field/actions.gd").write_text('''extends RefCounted
const Loot=preload("res://field/loot.gd")
static func build(book:Array[Dictionary])->Dictionary:
	var entries:Dictionary={}
	for i in book.size():
		var rec:=book[i].duplicate()
		rec["index"]=i
		entries["spell/"+str(rec.name)]=rec
	for id in Loot.ITEMS:
		var item:Array=Loot.ITEMS[id]
		if item[1]=="Материал":continue
		entries["item/"+id]={"name":item[0],"effect":id,"item":id,"description":"Предмет из инвентаря"}
	return entries
static func initial()->Array:
	return ["","","","","","","","","",""]
static func normalize(saved:Variant,entries:Dictionary,hero)->Array:
	var result:=initial()
	if not saved is Array:return result
	for i in mini(10,saved.size()):
		var id:Variant=saved[i]
		if id is String and entries.has(id) and not result.has(id):
			var rec:Dictionary=entries[id]
			if not rec.has("index") or hero.knows(rec):result[i]=id
	return result
''',encoding="utf-8")
edit("field/skill_button.gd",[
('Rect2(177+index*88,453,78,75)','Rect2(144+index*62,466,58,58)'),
('Vector2(26,29),Vector2(52,52)','Vector2(20,21),Vector2(40,40)'),
('Vector2(52,52*clampf','Vector2(40,40*clampf'),
('''	else:
		canvas.draw_string(font,r.position+Vector2(1,44),"◇",HORIZONTAL_ALIGNMENT_CENTER,r.size.x-2,20,Color("#56675c"))''',''),
('str(number),HORIZONTAL_ALIGNMENT_LEFT','str(number%10),HORIZONTAL_ALIGNMENT_LEFT'),
])
edit("field/spellbook.gd",[
('var status:=""','var status:=""\nvar training:=false'),
('func present(profile, entries: Dictionary) -> void:','func present(profile, entries: Dictionary, at_trainer:bool=false) -> void:\n\ttraining=at_trainer'),
('for i in 7:\n\t\tif Slot.bar_rect','for i in 10:\n\t\tif Slot.bar_rect'),
('elif hero.level()>=rec.level and hero.sp>=rec.sp:','elif training and hero.level()>=rec.level and hero.sp>=rec.sp:'),
('elif not available: words(r.position+Vector2(66,49),"Изучить",12,MUTED)','elif not available: words(r.position+Vector2(66,49),"Изучить" if training else "У мастера",12,MUTED)'),
('elif not allowed(chosen): action_text="Ур. %d · %d SP" % [sk.level,sk.sp] if hero.level()<sk.level else "Изучить · %d SP" % sk.sp','elif not allowed(chosen): action_text=("Ур. %d · %d SP" % [sk.level,sk.sp] if hero.level()<sk.level else "Изучить · %d SP" % sk.sp) if training else "Только у мастера"'),
('Rect2(159,413,641,121)','Rect2(130,413,660,121)'),
('for i in 7:\n\t\tvar rec: Dictionary=catalog.get','for i in 10:\n\t\tvar rec: Dictionary=catalog.get'),
])
p=root/"field/spellbook.gd";s=p.read_text(encoding="utf-8")
assert s.count("var ids:=catalog.keys()")==2
s=s.replace("var ids:=catalog.keys()","var ids:=spell_ids()")
s=s.replace("% (ix+1)","% ((ix+1)%10)").replace("[catalog[id].name,to+1]","[catalog[id].name,(to+1)%10]")
p.write_text(s,encoding="utf-8")
append("field/spellbook.gd",'''
func spell_ids()->Array:
	var result:Array=[]
	for id in catalog:
		if catalog[id].has("index"):result.append(id)
	return result
''')
edit("field/floating_panel.gd",[
('signal equip(id: String)','signal equip(id: String)\nsignal hotbar_choose(id:String)\nsignal hotbar_drop(id:String,point:Vector2)'),
('Dress.fit(figure,hero.equipment)','preload("res://ford/looks.gd").fit(figure,hero.appearance)\n\t\tDress.fit(figure,hero.equipment)'),
('var filter:=0','var filter:=0\nvar page:=0'),
('func cell(i: int) -> Rect2:','''func page_ids()->Array:
	var list:=ids()
	page=clampi(page,0,maxi(0,ceili(list.size()/10.0)-1))
	return list.slice(page*10,page*10+10)

func cell(i: int) -> Rect2:'''),
('var list:=ids()\n\tfor i in 10:','var list:=page_ids()\n\tfor i in 10:'),
('var list:=ids()\n\t\t\t\tfor i in list.size():','var list:=page_ids()\n\t\t\t\tfor i in list.size():'),
('draw_line(Vector2(16,247),Vector2(367,247),GOLD)','''draw_line(Vector2(16,247),Vector2(367,247),GOLD)
	box(Rect2(286,46,30,26),Color("#354d3f"),GOLD)
	box(Rect2(338,46,30,26),Color("#354d3f"),GOLD)
	line(Vector2(286,64),"<",15,PAPER,30,HORIZONTAL_ALIGNMENT_CENTER)
	line(Vector2(338,64),">",15,PAPER,30,HORIZONTAL_ALIGNMENT_CENTER)
	line(Vector2(317,64),str(page+1),12,GOLD,21,HORIZONTAL_ALIGNMENT_CENTER)'''),
('line(Vector2(101,281),info[0],19,PAPER)','line(Vector2(101,281),info[0],15,PAPER,265)'),
('line(Vector2(101,326),chance[chosen],13,SOFT)','line(Vector2(101,326),chance.get(chosen,"Стартовое оружие · No Grade"),13,SOFT)'),
('''	var worn:bool=hero.equipment.get(info[1],"")==chosen''','''	box(Rect2(18,336,175,29),Color("#354d3f"),GOLD)
	line(Vector2(19,356),"На панель",13,PAPER,173,HORIZONTAL_ALIGNMENT_CENTER)
	var worn:bool=hero.equipment.get(info[1],"")==chosen'''),
('''							if SLOTS[i]==slot and peer.gear_cell(i).has_point(world-peer.position): equip.emit(drag_item)
			pointer=-99''','''							if SLOTS[i]==slot and peer.gear_cell(i).has_point(world-peer.position): equip.emit(drag_item)
				elif drag_item!="" and not dragging:
					hotbar_drop.emit(drag_item,world)
			pointer=-99'''),
('''		var available:=ids()
		for i in 3:''','''		if Rect2(286,46,30,26).has_point(p) or Rect2(338,46,30,26).has_point(p):
			page+=-1 if p.x<320 else 1
			var list:=page_ids()
			chosen="" if list.is_empty() else list[0]
			refresh()
			return
		var available:=page_ids()
		for i in 3:'''),
('filter=i\n\t\t\t\trefresh()','filter=i\n\t\t\t\tpage=0\n\t\t\t\tchosen=""\n\t\t\t\trefresh()'),
('''		if Rect2(209,345,158,42).has_point(p) and chosen!=""''','''		if Rect2(18,336,175,29).has_point(p) and chosen!="" and Loot.ITEMS[chosen][1]!="Материал":
			hotbar_choose.emit(chosen)
			hide()
			return
		if Rect2(209,345,158,42).has_point(p) and chosen!=""'''),
])
edit("field/hud.gd",[
('signal skill_pressed(slot: int)','''signal skill_pressed(slot: int)
signal autoattack_requested
signal pickup_requested
signal target_requested
signal item_choose(id:String)
signal item_assigned(id:String,slot:int)'''),
('var gateway: Button','var gateway: Button\nvar autoattack:Button\nvar pickup_button:Button\nvar target_button:Button'),
('for i in 7:\n\t\tvar key := SkillButton.new()','for i in 10:\n\t\tvar key := SkillButton.new()'),
('''		slots.append(key)
	var names''','''		slots.append(key)
	autoattack=icon_button("hit","Автоатака")
	place(ui,autoattack,Rect2(866,462,76,66))
	autoattack.pressed.connect(func():autoattack_requested.emit())
	pickup_button=icon_button("pickup","Подобрать добычу")
	place(ui,pickup_button,Rect2(803,469,55,55))
	pickup_button.pressed.connect(func():pickup_requested.emit())
	target_button=icon_button("cycle","Следующая цель")
	place(ui,target_button,Rect2(887,205,55,55))
	target_button.pressed.connect(func():target_requested.emit())
	var names'''),
('bag.peer=sheet','''bag.hotbar_choose.connect(func(id):item_choose.emit(id))
	bag.hotbar_drop.connect(func(id,point):
		var slot:=bar_at(point)
		if slot>=0:item_assigned.emit(id,slot))
	bag.peer=sheet'''),
('func show_book(hero: Careers, catalog: Dictionary) -> void:','func show_book(hero: Careers, catalog: Dictionary, training:bool=false) -> void:'),
('book_editor.present(hero,catalog)','book_editor.present(hero,catalog,training)'),
('status.text = "%s · Ур. %d" % [hero.title(),hero.level()]','status.text = "%s · Ур. %d" % [hero.character_name,hero.level()]'),
])
# Main world scene starts with the new continuous world and the chosen character.
edit("ford/world.gd",[
('const START := Vector2(-5,1.7)','const START := Ground.START\nconst Looks=preload("res://ford/looks.gd")'),
('var city_ground:=Ground.new(true)','var city_ground=ground'),
('var refresh_time := 0.0','''var refresh_time := 0.0
var bridge
var bridge_callback
var player_body:CharacterBody3D
var auto_enabled:=false
var assigning_item:=""
var haste_time:=0.0
var focus_time:=0.0
var hurt_motion:=0.0
var death_wait:=0.0
var autosave_time:=0.0
var trainers:Array[Node3D]=[]
var villagers:Array[Dictionary]=[]
var quality_level:=1
var local_packet:Dictionary={}
var pinch_finger:=-1
var pinch_point:=Vector2.ZERO
var pinch_distance:=0.0'''),
])
section("ford/world.gd","func _ready() -> void:","func update_sound_button()",'''
func _ready() -> void:
	rng.randomize()
	if OS.has_feature("web"):
		bridge=JavaScriptBridge.get_interface("C3Preview")
		if bridge!=null:
			var raw=JSON.parse_string(str(bridge.character()))
			if raw is Dictionary:local_packet=raw
			var opts=JSON.parse_string(str(bridge.settings()))
			if opts is Dictionary:
				quality_level=clampi(int(opts.get("quality",1)),0,2)
				profile.muted=not bool(opts.get("sound",true))
	apply_profile()
	$Landscape.hide()
	Stage.build(self)
	Stage.obstacles(self,ground)
	Stage.decorate(self,ground,quality_level)
	$Sun.shadow_enabled=quality_level>0
	$Sun.directional_shadow_max_distance=36.0 if quality_level<2 else 55.0
	cam.far=180.0
	city_model=preload("res://ford/models/city.glb").instantiate()
	add_child(city_model)
	city_model.position=Vector3(Ground.VILLAGE.x,.02,Ground.VILLAGE.y)
	city_model.rotation.y=PI/2
	city_model.scale=Vector3.ONE*Ground.CITY_SCALE
	for name_ in ["ground","Garden"]:
		var part:=city_model.find_child(name_,true,false) as Node3D
		if part!=null:part.hide()
	town=Ground.village(actor)
	Looks.fit(hero,profile.appearance)
	spells=Skills.book(profile)
	catalog=Actions.build(spells)
	profile.hotbar=Actions.normalize(profile.hotbar,catalog,profile)
	add_child(sound)
	sound.set_muted(profile.muted)
	hp=profile.hp_max();mp=profile.mana_max()
	torso=hero.find_child("Body",true,false)
	for name_ in ["LegL","LegR","ArmL","ArmR"]:
		limbs.append(hero.find_child(name_,true,false))
	for limb in limbs:foot_positions.append(limb.position)
	preload("res://ford/worn.gd").fit(hero,profile.equipment)
	player_body=CharacterBody3D.new()
	player_body.collision_layer=4
	player_body.collision_mask=1|2
	player_body.floor_snap_length=.45
	add_child(player_body)
	var capsule:=CapsuleShape3D.new()
	capsule.radius=.29;capsule.height=1.55
	var shape:=CollisionShape3D.new()
	shape.shape=capsule;shape.position.y=.775
	player_body.add_child(shape)
	player_body.position=Ground.point(actor)+Vector3.UP*.1
	hero.position=player_body.position
	hero.rotation.y=heading
	target_ring=Stage.ring(self,.88,Color("#f9c46a"))
	cursor=Stage.ring(self,.43,Color("#eef2ae"))
	for rec in profile.ground_loot:
		if rec is Dictionary and rec.has("place") and rec.has("items"):spawn_pile(rec)
	build_population()
	build_village()
	add_child(hud)
	hud.shade.hide()
	hud.playing=true
	hud.gateway.text="Мастер класса"
	hud.gateway.pressed.connect(open_trainer)
	for i in 2:
		var key:=hud.button(["−","+"][i])
		key.tooltip_text=["Отдалить мини-карту","Приблизить мини-карту"][i]
		hud.place(hud.ui,key,Rect2(848+i*48,157,44,40))
		hud.ui.move_child(key,hud.desks.get_index())
		key.pressed.connect(hud.radar.change_zoom.bind(-1.0 if i==0 else 1.0))
	hud.skill_pressed.connect(use_slot)
	hud.autoattack_requested.connect(toggle_autoattack)
	hud.pickup_requested.connect(pickup_nearest)
	hud.target_requested.connect(next_target)
	hud.item_assigned.connect(assign_item)
	hud.item_choose.connect(func(id:String):
		assigning_item=id
		hud.feed.text="Выбери ячейку 1–0.")
	hud.swap_requested.connect(func(from:int,to:int):
		var id:String=profile.hotbar[from]
		if id.is_empty():return
		profile.hotbar[from]=profile.hotbar[to]
		profile.hotbar[to]=id
		save_hero();update_ui())
	hud.layout_changed.connect(func():save_hero();update_ui())
	hud.sound_requested.connect(func():
		profile.muted=not profile.muted
		sound.set_muted(profile.muted)
		update_sound_button();save_hero())
	update_sound_button()
	hud.window_requested.connect(open_window)
	hud.careers_pressed.connect(func():hud.show_careers(profile))
	hud.equip_requested.connect(equip_item)
	hud.train_requested.connect(func(i):
		if not near_trainer() or not hud.book_editor.training:
			hud.feed.text="Изучи умение у мастера своего класса."
			return
		if i>=0 and i<spells.size() and profile.learn(spells[i]):
			save_hero();hud.book_editor.queue_redraw();update_ui())
	hud.transfer_requested.connect(func(job):
		if not near_trainer():
			hud.feed.text="Профессия меняется только у мастера."
			return
		if profile.promote(job):
			spells=Skills.book(profile)
			catalog=Actions.build(spells)
			profile.hotbar=Actions.normalize(profile.hotbar,catalog,profile)
			hp=profile.hp_max();mp=profile.mana_max()
			save_hero();hud.shade.hide();update_ui())
	focus=hero.position+Vector3(0,.8,0)
	update_camera()
	hud.feed.text="Где я? Как я сюда попал? Найди мастера и выйди через ворота."
	if not local_packet.get("progress",{}).is_empty():hud.feed.text="С возвращением, "+profile.character_name+"."
	update_ui()
	if bridge!=null:
		bridge_callback=JavaScriptBridge.create_callback(web_command)
		bridge.attach(bridge_callback)
		if local_packet.get("progress",{}).is_empty():start_wakeup()
''')
section("ford/world.gd","func save_hero() -> void:","func _camera_action",'''
func apply_profile()->void:
	profile.race=str(local_packet.get("race","Гном"))
	profile.origin=str(local_packet.get("discipline","Подгорный боец"))
	if not Hero.TREE.has(profile.race) or not Hero.TREE[profile.race].has(profile.origin):
		profile.race="Гном";profile.origin="Подгорный боец"
	profile.character_name=str(local_packet.get("name","Путник"))
	profile.appearance={"race":profile.race,"gender":local_packet.get("gender","male"),"face":local_packet.get("face",0),"hair":local_packet.get("hair",0),"hair_color":local_packet.get("hair_color",0),"skin":local_packet.get("skin",0)}
	var state=local_packet.get("progress",{})
	if not state is Dictionary:state={}
	if state.is_empty():
		var weapon:=starter_weapon(profile.race,profile.mystic())
		profile.inventory={weapon:1}
		profile.equipment={"Оружие":weapon}
		profile.hotbar=Actions.initial()
		actor=START
		return
	var branches:Dictionary=Hero.TREE[profile.race][profile.origin]
	var first:String=str(state.get("first",""))
	var second:String=str(state.get("second",""))
	if branches.has(first):
		profile.first=first
		if branches[first].has(second):profile.second=second
	for key in ["total_xp","kills","sp","adena"]:
		profile.set(key,maxi(0,int(state.get(key,1 if key=="total_xp" else 0))))
	profile.total_xp=clampi(profile.total_xp,1,Hero.Experience.START.back())
	if state.get("learned") is Dictionary:profile.learned=state.learned
	if state.get("inventory") is Dictionary:
		for id in state.inventory:
			if Loot.ITEMS.has(id) and int(state.inventory[id])>0:profile.inventory[id]=clampi(int(state.inventory[id]),1,1000000)
	if state.get("equipment") is Dictionary:
		for slot in state.equipment:
			var id:String=str(state.equipment[slot])
			if Loot.ITEMS.has(id) and Loot.ITEMS[id][1]==slot and profile.inventory.get(id,0)>0:profile.equipment[slot]=id
	if state.get("hotbar") is Array:profile.hotbar=state.hotbar
	var saved:=Vector2(float(local_packet.get("x",START.x)),float(local_packet.get("z",START.y)))
	actor=saved if ground.legal(saved) else START
	var records=state.get("ground_loot",[])
	if records is Array:
		for item in records:
			if not item is Dictionary or not item.get("place") is Array or item.place.size()!=2 or not item.get("items") is Dictionary:continue
			var at:=Vector2(float(item.place[0]),float(item.place[1]))
			if not ground.legal(at):continue
			var record:Dictionary=item.duplicate(true)
			record.place=at
			var valid:=true
			for id in record.items:
				if not Loot.ITEMS.has(id):valid=false
			if valid:profile.ground_loot.append(record)

static func starter_weapon(race:String,mystic:bool)->String:
	if mystic:return "ng_staff"
	return str({"Человек":"ng_sword","Эльф":"ng_sword","Тёмный эльф":"ng_dagger","Орк":"ng_axe","Гном":"ng_hammer"}.get(race,"ng_sword"))

func start_wakeup()->void:
	town_transition=true
	hero.rotation.z=1.3
	hud.veil.modulate.a=1.0
	hud.veil.show()
	var animation:=create_tween()
	animation.tween_property(hud.veil,"modulate:a",0.0,1.3)
	animation.parallel().tween_property(hero,"rotation:z",0.0,1.5)
	animation.tween_callback(func():
		hud.veil.hide()
		town_transition=false
		save_hero())

func web_menu_open()->bool:
	return bridge!=null and bool(bridge.menuOpen())

func web_command(args:Array)->void:
	if not args.is_empty() and str(args[0])=="save":save_hero()

func save_hero()->void:
	if bridge==null or local_packet.is_empty():return
	var state:Dictionary={}
	for key in ["first","second","total_xp","kills","sp","adena","inventory","equipment","learned","hotbar"]:
		state[key]=profile.get(key)
	var loot:Array=[]
	for item in profile.ground_loot:
		var record:Dictionary=item.duplicate(true)
		if record.get("place") is Vector2:
			record.place=[record.place.x,record.place.y]
			loot.append(record)
	state["ground_loot"]=loot
	bridge.save(JSON.stringify(state),actor.x,actor.y)

func open_window(kind:String)->void:
	match kind:
		"Персонаж":hud.show_stats(profile,hp,mp,SPEED)
		"Умения":hud.show_book(profile,catalog,near_trainer())
		"Инвентарь":hud.show_bag(profile)

func equip_item(id:String)->void:
	if profile.toggle_item(id):
		preload("res://ford/worn.gd").fit(hero,profile.equipment)
		hud.sheet.refresh(true);hud.bag.refresh()
		save_hero();update_ui()

func assign_item(id:String,slot:int)->void:
	var key:="item/"+id
	if slot<0 or slot>=10 or not catalog.has(key) or profile.inventory.get(id,0)<=0:return
	var old:=profile.hotbar.find(key)
	if old>=0:profile.hotbar[old]=""
	profile.hotbar[slot]=key
	hud.feed.text="Предмет назначен → "+str((slot+1)%10)
	save_hero();update_ui()

func build_population()->void:
	var seeded:=RandomNumberGenerator.new()
	seeded.seed=19020
	# Fixed ecological groups: passive roots in meadows; wolves in forest;
	# stone creatures among the ruins and quarry, higher-level guards east.
	var clusters: Array=[
		[Vector2(-56,-12),12,2,0],[Vector2(-48,16),12,3,0],[Vector2(-34,-31),10,5,0],
		[Vector2(-8,-19),12,7,1],[Vector2(12,21),12,9,1],[Vector2(26,-39),10,12,1],
		[Vector2(66,-35),12,16,2],[Vector2(83,27),12,20,2],[Vector2(110,-22),10,25,3],
		[Vector2(124,29),12,34,3],[Vector2(136,-62),10,42,3]]
	var occupied:Array[Vector2]=[]
	for cluster in clusters:
		var center:Vector2=cluster[0]
		var count:=0
		for attempt in 220:
			if count>=int(cluster[1]):break
			var p:=center+Vector2(seeded.randf_range(-11,11),seeded.randf_range(-10,10))
			if not ground.legal(p) or Ground.road(p) or Ground.village(p) or absf(p.x-Ground.river(p.y))<5:continue
			var far:=true
			for other in occupied:
				if p.distance_to(other)<2.6:
					far=false;break
			if not far:continue
			occupied.append(p)
			var mob:=Beast.new()
			add_child(mob)
			mob.setup(p,int(cluster[2])+seeded.randi_range(0,2),mobs.size(),int(cluster[3]),ground)
			mobs.append(mob)
			count+=1

func npc_model(race:String,gender:String,p:Vector2,title_:String)->Node3D:
	var npc:=preload("res://ford/models/warden.glb").instantiate() as Node3D
	add_child(npc)
	npc.position=Ground.point(p)
	Looks.fit(npc,{"race":race,"gender":gender,"face":rng.randi_range(0,3),"hair":rng.randi_range(0,3),"hair_color":rng.randi_range(0,3),"skin":rng.randi_range(0,3)})
	npc.rotation.y=1.5
	if not title_.is_empty():
		var tag:=Label3D.new()
		tag.text=title_;tag.font_size=35;tag.pixel_size=.007;tag.outline_size=8
		tag.position.y=2.3;tag.billboard=BaseMaterial3D.BILLBOARD_ENABLED;tag.modulate=Color("#ffe09a")
		npc.add_child(tag)
	return npc

func build_village()->void:
	var points:Array[Vector2]=[Vector2(-87,-8),Vector2(-87,8),Vector2(-92,-7),Vector2(-92,7),Vector2(-96,-8),Vector2(-96,8),Vector2(-101,-8),Vector2(-101,8),Vector2(-104,0)]
	var i:=0
	for race in Hero.TREE:
		for origin in Hero.TREE[race]:
			var p:=points[i]
			i+=1
			if not ground.legal(p):p=Vector2(ground.open_cell(p))
			if not ground.legal(p):p=START+Vector2(0,float(i)*.45)
			var npc:=npc_model(race,"female" if i%2==0 else "male",p,"Мастер · "+str(origin))
			npc.set_meta("origin",origin)
			trainers.append(npc)
	for j in 8:
		var a:=Vector2(-83.0-float(floori(j/4.0))*1.5,float(j%4)*2-3)
		var b:=Vector2(-110.0,float(j%4)*2-3)
		if not ground.legal(a) or not ground.legal(b):continue
		var path:=ground.route(a,b)
		if path.is_empty():continue
		var npc:=npc_model(Hero.TREE.keys()[j%5],"female" if j%2==0 else "male",a,"")
		var body:=npc.find_child("Body",true,false) as Node3D
		villagers.append({"node":npc,"a":a,"b":b,"goal":b,"route":path,"phase":float(j),"body":body})
	npc_model("Человек","male",Vector2(-73,2),"Страж ворот")
	npc_model("Человек","female",Vector2(-76,-2),"Страж ворот")

func update_village(dt:float)->void:
	if actor.distance_to(Ground.VILLAGE)>55:return
	for record in villagers:
		var npc:Node3D=record.node
		var p:=Vector2(npc.position.x,npc.position.z)
		var path:PackedVector2Array=record.route
		if path.is_empty():
			record.goal=record.a if record.goal==record.b else record.b
			path=ground.route(p,record.goal)
		if path.is_empty():continue
		var q:=p.move_toward(path[0],dt*1.35)
		if q.distance_to(path[0])<.08:path.remove_at(0)
		record.route=path
		if q.distance_to(p)>.0001:
			npc.rotation.y=lerp_angle(npc.rotation.y,atan2(q.x-p.x,q.y-p.y),minf(1,dt*7))
			npc.position=Ground.point(q)
		record.phase=float(record.phase)+dt*5
		for index in 4:
			var limb:=npc.find_child(["LegL","LegR","ArmL","ArmR"][index],true,false) as Node3D
			if limb!=null:limb.rotation.x=.24*sin(float(record.phase)+PI*int(index in [1,2]))

func near_trainer()->bool:
	if not town:return false
	for npc in trainers:
		if npc.get_meta("origin")==profile.origin and actor.distance_to(Vector2(npc.position.x,npc.position.z))<=3.2:return true
	return false

func open_trainer()->void:
	if not near_trainer():
		hud.feed.text="Найди мастера: "+profile.origin
		return
	clear_target()
	if not profile.choices().is_empty():hud.show_careers(profile)
	else:hud.show_book(profile,catalog,true)
''')
# Existing camera and ray selection retain mouse/touch support. UI menu blocks movement.
edit("ford/world.gd",[
('if not is_node_ready() or hud.shade.visible or town_transition: return','if not is_node_ready() or hud.shade.visible or town_transition or web_menu_open(): return'),
] if False else [
('''func _process(dt: float) -> void:
	if not is_node_ready() or hud.shade.visible or town_transition: return''','''func _process(dt: float) -> void:
	if not is_node_ready() or hud.shade.visible or web_menu_open(): return'''),
('''func _input(e: InputEvent) -> void:
	if not is_node_ready(): return
	if hud.shade.visible or town_transition: finger=-1; right_drag=false; return''','''func _input(e: InputEvent) -> void:
	if not is_node_ready(): return
	if hud.shade.visible or web_menu_open():
		finger=-1;pinch_finger=-1;right_drag=false
		return
	if e is InputEventScreenTouch and e.pressed and finger>=0 and e.index!=finger and pinch_finger<0:
		pinch_finger=e.index
		pinch_point=e.position
		pinch_distance=maxf(1.0,finger_last.distance_to(pinch_point))
		orbiting=true
		get_viewport().set_input_as_handled()
		return
	if e is InputEventScreenTouch and not e.pressed and e.index==finger and pinch_finger>=0:
		finger=pinch_finger
		finger_last=pinch_point
		finger_origin=pinch_point
		pinch_finger=-1
		orbiting=true
		get_viewport().set_input_as_handled()
		return
	if e is InputEventScreenTouch and not e.pressed and e.index==pinch_finger:
		pinch_finger=-1
		get_viewport().set_input_as_handled()
		return
	if pinch_finger>=0 and e is InputEventScreenDrag and e.index in [finger,pinch_finger]:
		if e.index==finger:finger_last=e.position
		else:pinch_point=e.position
		var gap:=maxf(1.0,finger_last.distance_to(pinch_point))
		wanted_distance=clampf(wanted_distance*pinch_distance/gap,7.0,28.0)
		pinch_distance=gap
		get_viewport().set_input_as_handled()
		return'''),
('''func _unhandled_input(e: InputEvent) -> void:
	if not is_node_ready() or hud.shade.visible or town_transition: return''','''func _unhandled_input(e: InputEvent) -> void:
	if not is_node_ready() or hud.shade.visible or web_menu_open(): return'''),
('if e.keycode>=KEY_1 and e.keycode<=KEY_7: use_slot(e.keycode-KEY_1)','if e.keycode>=KEY_1 and e.keycode<=KEY_9: use_slot(e.keycode-KEY_1)\n\t\tif e.keycode==KEY_0:use_slot(9)'),
('KEY_K: open_window("Умения")','KEY_K: open_window("Умения")\n\t\t\tKEY_SPACE:toggle_autoattack()\n\t\t\tKEY_TAB:next_target()\n\t\t\tKEY_F:pickup_nearest()'),
('func select_screen(screen: Vector2) -> void:\n\tvar best: Beast','''func select_screen(screen: Vector2) -> void:
	if town:
		for npc in trainers:
			if cam.is_position_behind(npc.position):continue
			var head:=cam.unproject_position(npc.position+Vector3.UP*1.6)
			var foot:=cam.unproject_position(npc.position)
			if screen.distance_to((head+foot)*.5)<maxf(20,head.distance_to(foot)*.55):
				if npc.get_meta("origin")==profile.origin and near_trainer():open_trainer()
				else:
					walk_to(Vector2(npc.position.x,npc.position.z))
					hud.feed.text="Подойди к мастеру своего класса."
				return
	var best: Beast'''),
('func clear_target() -> void:\n\ttarget=null','func clear_target() -> void:\n\tauto_enabled=false\n\ttarget=null'),
('hud.feed.text="Цель выбрана · Корневик"','hud.feed.text="Цель выбрана · "+mob.display_name()'),
])
section("ford/world.gd","func use_slot(i: int) -> void:","func flash(id: String)",'''
func pickup_nearest()->void:
	var nearest:Node3D
	var radius:=12.01
	for pile in piles:
		var gap:=actor.distance_to(pile.point)
		if pile.visible and gap<radius:radius=gap;nearest=pile
	if nearest!=null:request_pickup(nearest)
	else:hud.feed.text="Поблизости нет добычи."

func toggle_autoattack()->void:
	if town or death_wait>0 or hud.shade.visible or web_menu_open():return
	if auto_enabled:
		auto_enabled=false
		if pending=="hit":pending="";route.clear()
		hud.feed.text="Автоатака остановлена."
		return
	if target==null or target.hp<=0:
		hud.feed.text="Сначала выбери цель."
		return
	auto_enabled=true
	pending="hit"
	if actor.distance_to(target.flat())<=action_range("hit") and attack_wait<=0:
		var d:=target.flat()-actor
		heading=atan2(d.x,d.y)
		hero.rotation.y=heading
		attack(profile.damage())
		pending=""
	else:plan_chase()

func action_range(id:String)->float:
	if id=="hit":return 5.2 if profile.equipment.get("Оружие","")=="ng_staff" else REACH
	var sk:Dictionary=catalog.get(id,{})
	return 5.8 if sk.get("effect") in ["ranged","drain"] else REACH

func use_slot(i:int)->void:
	if hud.shade.visible or web_menu_open() or death_wait>0 or i<0 or i>=10:return
	if assigning_item!="":
		var chosen:=assigning_item
		assigning_item=""
		assign_item(chosen,i)
		return
	var id:String=profile.hotbar[i]
	if id.is_empty() or not catalog.has(id):return
	if id.begins_with("item/"):
		equip_item(id.trim_prefix("item/"))
		return
	var sk:Dictionary=catalog[id]
	if not profile.knows(sk) or profile.level()<sk.level or cooldowns[sk.index]>0:return
	if mp<sk.mp:
		hud.feed.text="Недостаточно маны."
		return
	if Skills.offensive(sk.effect):
		if town or target==null or target.hp<=0:
			hud.feed.text="Сначала выбери цель."
			return
		pending=id
		cursor.hide()
		if actor.distance_to(target.flat())>action_range(id):plan_chase()
	else:cast(sk)
	update_ui()
''')
section("ford/world.gd","func cast(sk: Dictionary) -> void:","func spawn_pile",'''
func cast(sk:Dictionary)->void:
	if cooldowns[sk.index]>0 or mp<int(sk.mp) or not profile.knows(sk):return
	if Skills.offensive(sk.effect) and (target==null or target.hp<=0):return
	cooldowns[sk.index]=sk.cd
	mp-=int(sk.mp)
	flash("spell/"+str(sk.name))
	hud.feed.text=sk.name
	match sk.effect:
		"guard","heal","renew","haste","focus":
			match sk.effect:
				"guard":shield=7
				"heal":hp=mini(profile.hp_max(),hp+roundi(profile.hp_max()*.3))
				"renew":mp=mini(profile.mana_max(),mp+roundi(profile.mana_max()*.25))
				"haste":haste_time=7
				"focus":focus_time=8
			swing=.30
			sound.effect("ward")
			contact(hero.position+Vector3.UP*.55,"guard")
		"spoil":
			target.spoiled=true
			engaged=true
			target.aggro=true
			sound.effect("ward")
			contact(target.position+Vector3.UP*.35,"spoil")
			float_word(target.position,"Спойл",Color("#f2cd82"))
		_:
			if sk.effect=="stun":target.stun=2
			if sk.effect=="drain":hp=mini(profile.hp_max(),hp+roundi(profile.damage()*.6))
			attack(profile.damage()*(3 if sk.effect=="crush" else 2),"heavy")

func attack(amount:int,kind:String="hit")->void:
	if target==null or target.hp<=0:return
	engaged=true
	target.aggro=true
	swing=.38
	if kind=="hit":
		attack_wait=1.05 if haste_time>0 else 1.5
		if focus_time>0:amount=roundi(amount*1.4)
	sound.effect("hit" if kind=="hit" else "heavy")
	var hit_chance:=clampf(.92+(profile.level()-target.rank)*.026,.55,.98)
	if rng.randf()>hit_chance:
		float_word(target.position,"Промах",Color("#dedfd7"))
		return
	var crit:=kind=="hit" and rng.randf()<.12
	amount=maxi(1,roundi(amount*(1.8 if crit else 1.0)*rng.randf_range(.9,1.1))-target.kind)
	contact(target.position+Vector3.UP*.77,kind)
	float_word(target.position,("Крит! " if crit else "")+"−%d" % amount,Color("#ffb762") if crit else Color("#fff3c4"))
	if not target.hurt(amount):return
	var reward:=Loot.roll(target.kind,target.rank,.04*profile.role_score("Добыча"),target.spoiled,rng)
	reward["place"]=target.flat()
	profile.ground_loot.append(reward)
	spawn_pile(reward)
	var gain:=Loot.xp_for(target.kind,target.rank,profile.level())
	var old_level:=profile.level()
	profile.earn(gain)
	var msg:="+%d EXP · Добыча на земле" % gain
	if profile.level()>old_level:
		hp=profile.hp_max();mp=profile.mana_max()
		msg+=" · Уровень %d!" % profile.level()
	hud.feed.text=msg
	clear_target()
	save_hero();update_ui()
''')
section("ford/world.gd","func _physics_process(dt: float) -> void:","func update_ui()",'''
func _physics_process(dt:float)->void:
	if player_body==null or town_transition:return
	if hud.shade.visible or web_menu_open():
		player_body.velocity=Vector3.ZERO
		hud.stick.reset()
		return
	if death_wait>0:
		death_wait=maxf(0,death_wait-dt)
		hero.rotation.z=lerpf(hero.rotation.z,1.35,minf(1,dt*8))
		if death_wait<=0:
			hero.rotation.z=0
			actor=START
			player_body.position=Ground.point(actor)+Vector3.UP*.1
			player_body.velocity=Vector3.ZERO
			hero.position=player_body.position
			town=true
			hp=profile.hp_max();mp=profile.mana_max()
			hud.feed.text="Ты очнулся у деревенского лекаря."
			save_hero();update_ui()
		return
	var prev:=actor
	var axis:=hud.stick.axis
	if axis.is_zero_approx():
		axis=Input.get_vector("ui_left","ui_right","ui_up","ui_down")
		if axis.is_zero_approx():axis=Vector2(int(Input.is_physical_key_pressed(KEY_D))-int(Input.is_physical_key_pressed(KEY_A)),int(Input.is_physical_key_pressed(KEY_S))-int(Input.is_physical_key_pressed(KEY_W))).limit_length()
	for i in cooldowns.size():cooldowns[i]=maxf(0,cooldowns[i]-dt)
	attack_wait=maxf(0,attack_wait-dt);swing=maxf(0,swing-dt);shield=maxf(0,shield-dt)
	haste_time=maxf(0,haste_time-dt);focus_time=maxf(0,focus_time-dt);hurt_motion=maxf(0,hurt_motion-dt)
	var speed:=SPEED*(1.25 if haste_time>0 else 1.0)
	var desired:=Vector2.ZERO
	if target!=null and target.hp<=0:clear_target()
	if auto_enabled and target!=null and pending=="":pending="hit"
	if not axis.is_zero_approx():
		if target!=null or not route.is_empty() or collecting!=null:clear_target()
		desired=axis.rotated(-yaw)*speed
	elif target!=null and pending!="" and actor.distance_to(target.flat())<=action_range(pending):
		route.clear()
		var d:=target.flat()-actor
		heading=atan2(d.x,d.y)
		if pending.begins_with("spell/"):
			var sk:Dictionary=catalog[pending]
			pending=""
			cast(sk)
		elif attack_wait<=0:
			pending=""
			attack(profile.damage())
	else:
		if target!=null and pending!="" and (route.is_empty() or target_pos.distance_to(target.flat())>1.0):plan_chase()
		while not route.is_empty() and actor.distance_to(route[0])<.30:route.remove_at(0)
		if not route.is_empty():
			var d:=route[0]-actor
			desired=d.normalized()*minf(speed,d.length()/maxf(dt,.001))
		else:cursor.hide()
	var planar:=Vector2(player_body.velocity.x,player_body.velocity.z)
	planar=planar.move_toward(desired,dt*(13.0 if desired.length()>0 else 18.0))
	var next:=ground.slide(actor,planar*dt)
	player_body.velocity.x=(next.x-actor.x)/maxf(dt,.001)
	player_body.velocity.z=(next.y-actor.y)/maxf(dt,.001)
	if not player_body.is_on_floor():player_body.velocity.y-=20.0*dt
	else:player_body.velocity.y=-.15
	player_body.move_and_slide()
	actor=Vector2(player_body.position.x,player_body.position.z)
	if not ground.legal(actor) or player_body.position.y<Ground.height(actor)-1.0:
		actor=prev
		player_body.position=Ground.point(actor)+Vector3.UP*.1
		player_body.velocity=Vector3.ZERO
	hero.position=player_body.position
	var in_village:=Ground.village(actor)
	if in_village!=town:
		town=in_village
		if target!=null or collecting!=null:clear_target()
		hud.feed.text=Ground.sector(actor)+" · "+("Безопасная зона" if town else "Открытый мир")
	if collecting!=null and actor.distance_to(collecting.point)<=1.65:take_pile()
	var in_combat:=false
	for mob in mobs:
		mob.tick(dt,mob==target and engaged,actor)
		if town or mob.hp<=0 or not mob.aggro:continue
		in_combat=true
		if actor.distance_to(mob.flat())<=REACH and mob.stun<=0 and mob.attack_timer<=0:
			mob.attack_timer=1.35 if mob.kind==1 else 1.85
			mob.swing=.35
			if rng.randf()<.10:
				float_word(hero.position,"Уклонение",Color("#c4dedf"))
				continue
			sound.effect("hurt")
			contact(hero.position+Vector3.UP*.91,"hurt")
			hurt_motion=.23
			var damage:=maxi(1,3+mob.rank*2+mob.kind-profile.defense())
			hp-=maxi(1,ceili(damage*(.5 if shield>0 else 1.0)))
			if hp<=0:
				hp=0;clear_target();death_wait=1.5
				for enemy in mobs:enemy.aggro=false
				update_ui();return
	if target!=null:
		target_ring.position=target.position+Vector3.UP*.08
		target_ring.show()
	regen+=dt
	if regen>=1:
		regen-=1
		mp=mini(profile.mana_max(),mp+2)
		if not in_combat:hp=mini(profile.hp_max(),hp+2)
	var motion:=actor-prev
	var moving:=motion.length()>.002
	if moving:
		if swing<=0:heading=atan2(motion.x,motion.y)
		stride+=motion.length()
		if stride>.80:sound.effect("step");stride=fmod(stride,.80)
	hero.rotation.y=lerp_angle(hero.rotation.y,heading,minf(1,dt*12))
	gait_blend=lerpf(gait_blend,1.0 if moving else 0.0,1-exp(-12*dt))
	walk_phase+=motion.length()*PI/.80
	var wave:=sin(walk_phase)
	torso.position.y=(.045*absf(wave)-.025*pow(absf(cos(walk_phase)),8))*gait_blend
	torso.position.x=.035*wave*gait_blend
	torso.rotation.z=.04*wave*gait_blend
	torso.rotation.x=.045*gait_blend+(.18*sin(PI*hurt_motion/.23) if hurt_motion>0 else 0.0)
	torso.rotation.y=.23*sin(PI*swing/.38) if swing>0 else 0.0
	var armed:bool=profile.equipment.get("Оружие","")!=""
	for i in limbs.size():
		var leg_phase:=walk_phase+PI*int(i in [1,2])
		var angle:=sin(leg_phase)*(.49 if i<2 else .38)*gait_blend
		if i>=2 and not moving:angle=-.18 if armed else -.55
		if swing>0 and i==3:angle=-1.60*sin(PI*swing/.38)
		elif swing>0 and i==2:angle=-.65*sin(PI*swing/.38) if not armed else -.30
		limbs[i].rotation.x=angle
		if i<2:limbs[i].position=foot_positions[i]+Vector3.UP*(.115*maxf(0,-cos(leg_phase))*gait_blend)
	update_village(dt)
	autosave_time+=dt
	if autosave_time>=15:
		autosave_time=0
		save_hero()
	refresh_time-=dt
	if refresh_time<=0:
		refresh_time=.15
		update_ui()
''')
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")
s=s[:s.index("func update_ui() -> void:")]+'''
func update_ui()->void:
	hud.refresh(profile,hp,mp,Ground.sector(actor))
	hud.gateway.visible=near_trainer()
	hud.autoattack.visible=not town
	hud.pickup_button.visible=not town
	hud.target_button.visible=not town
	hud.autoattack.modulate=Color("#ffe09b") if auto_enabled else Color.WHITE
	if hud.sheet.visible:
		hud.sheet.stats={"hp":hp,"mp":mp,"str":profile.strength(),"dex":profile.dexterity()}
		hud.sheet.refresh()
	hud.radar.player=actor
	hud.radar.creatures.clear()
	hud.radar.hostile.clear()
	for mob in mobs:
		if mob.hp<=0:continue
		if mob.hostile or mob.aggro:hud.radar.hostile.append(mob.flat())
		else:hud.radar.creatures.append(mob.flat())
	hud.radar.queue_redraw()
	hud.target_name.text="Безопасная деревня" if town else ("Выбери цель" if target==null else "%s · %d · %d/%d" % [target.display_name(),target.rank,target.hp,target.max_hp])
	for i in 10:
		var id:String=profile.hotbar[i]
		var sk:Dictionary=catalog.get(id,{})
		var left:=0.0
		var hint:=""
		if sk.has("index"):
			left=cooldowns[sk.index]
			hint="%d МП" % sk.mp
		elif sk.has("item"):
			hint="×%d" % profile.inventory.get(sk.item,0)
		if left>0:hint="%d с" % ceili(left)
		hud.slots[i].display(sk,hint,left,true,true,id!="" and id==pending)
'''
p.write_text(s,encoding="utf-8")
shutil.copyfile(here/"radar.gd",root/"field/radar.gd")
print("World preview 0.19 source patch applied")
