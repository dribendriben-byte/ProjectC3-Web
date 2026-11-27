"""C3 0.13: crafting, enchant, charges, separate spoil loot. Apply after equipment_012.py."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def patch(file,pairs):
    p=root/file
    s=p.read_text(encoding="utf-8")
    for a,b in pairs:
        if s.count(a)!=1:
            raise RuntimeError(f"{file}: expected one occurrence, got {s.count(a)}: {a[:110]!r}")
        s=s.replace(a,b,1)
    p.write_text(s,encoding="utf-8")
def append(file,content):
    p=root/file
    p.write_text(p.read_text(encoding="utf-8")+"\n"+content,encoding="utf-8")

patch("field/loot.gd",[
('const ITEMS := {','''const ITEMS := {
	"soulshot":["Soulshot","Расходник",0,"",1,5,"soulshot"],
	"spiritshot":["Spiritshot","Расходник",0,"",1,7,"spiritshot"],
	"enchant_weapon":["Свиток заточки оружия","Материал",0,"",1,220,"enchant_weapon"],
	"enchant_armor":["Свиток заточки брони","Материал",0,"",1,160,"enchant_armor"],
	"recipe_ng":["Рецепты походного снаряжения","Материал",0,"",1,80,"recipe_ng"],
	"recipe_d":["Рецепты железного снаряжения","Материал",0,"",20,250,"recipe_d"],
	"recipe_c":["Рецепты стального снаряжения","Материал",0,"",40,750,"recipe_c"],'''),
('''	if rng.randf()<.12: bag["hp_potion"]=1''','''	if rng.randf()<.18: bag["soulshot"]=rng.randi_range(2,5)
	if rng.randf()<.13: bag["spiritshot"]=rng.randi_range(2,4)
	if rng.randf()<.025: bag["recipe_ng"]=1
	if rank>=20 and rng.randf()<.02: bag["recipe_d"]=1
	if rank>=40 and rng.randf()<.015: bag["recipe_c"]=1
	if rng.randf()<.008: bag["enchant_weapon"]=1
	if rng.randf()<.012: bag["enchant_armor"]=1
	if rng.randf()<.12: bag["hp_potion"]=1'''),
])
append("field/loot.gd",'''
static func spoil_roll(kind: int,rank: int,bonus: int,rng: RandomNumberGenerator) -> Dictionary:
	var bag: Dictionary={}
	var materials: Array=["bark","fang","slate"]
	bag[materials[kind]]=rng.randi_range(1,2)+mini(bonus,2)
	if rng.randf()<.45: bag[["leather","leather","iron_ore"][kind]]=1
	if rng.randf()<.12+bonus*.04: bag["crystal"]=1
	if rng.randf()<.05: bag["recipe_ng"]=1
	if rank>=20 and rng.randf()<.06: bag["recipe_d"]=1
	if rank>=40 and rng.randf()<.05: bag["recipe_c"]=1
	if rng.randf()<.025: bag["enchant_armor"]=1
	return {"adena":0,"items":bag,"spoil_only":true}
''')
icons={
 "soulshot":'<path d="M32 6L53 30 32 57 11 30Z" fill="#dbba63" stroke="#f8e9ae" stroke-width="2"/><path d="M32 15L39 29 32 48 25 29Z" fill="#fff1bc"/>',
 "spiritshot":'<path d="M32 6L53 30 32 57 11 30Z" fill="#639ace" stroke="#c6edff" stroke-width="2"/><path d="M32 15L39 29 32 48 25 29Z" fill="#dcf6ff"/>',
 "enchant_weapon":'<rect x="13" y="9" width="38" height="46" rx="4" fill="#d0bc93" stroke="#e9dcc2"/><path d="M21 43L43 19M23 32L32 41" stroke="#b65f4c" stroke-width="4"/>',
 "enchant_armor":'<rect x="13" y="9" width="38" height="46" rx="4" fill="#d0bc93" stroke="#e9dcc2"/><path d="M23 22L32 17 41 22V35L32 44 23 35Z" fill="#7998a1" stroke="#495e6d" stroke-width="2"/>',
 "recipe_ng":'<path d="M14 9H50V55H14Z" fill="#d5bc8d"/><path d="M21 20H43M21 29H43M21 38H36" stroke="#735c40" stroke-width="3"/><circle cx="42" cy="45" r="7" fill="#967b54"/>',
 "recipe_d":'<path d="M14 9H50V55H14Z" fill="#d5bc8d"/><path d="M21 20H43M21 29H43M21 38H36" stroke="#735c40" stroke-width="3"/><circle cx="42" cy="45" r="7" fill="#76a86c"/>',
 "recipe_c":'<path d="M14 9H50V55H14Z" fill="#d5bc8d"/><path d="M21 20H43M21 29H43M21 38H36" stroke="#735c40" stroke-width="3"/><circle cx="42" cy="45" r="7" fill="#5687b0"/>',
}
for key,shape in icons.items():
    (root/"field/art/icons"/("gear_"+key+".svg")).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect x="1" y="1" width="62" height="62" rx="8" fill="#283a37" stroke="#998363"/>'+shape+'</svg>',encoding="utf-8")
patch("field/icon_library.gd",[
('const TEXTURES := {','const TEXTURES := {\n'+''.join('\t"gear_'+k+'":preload("res://field/art/icons/gear_'+k+'.svg"),\n' for k in icons)),
])
# Recipes and safe enchant are a separate game module.
(root/"field/forge.gd").write_text('''extends RefCounted
const Loot=preload("res://field/loot.gd")
const RECIPE_GRADES:=["NG","D","C"]
const CAP:=6
const CHANCES: Array[float]=[1.0,1.0,1.0,.65,.50,.35]

static func recipe(id: String) -> Dictionary:
	if not Loot.ITEMS.has(id): return {}
	var item: Array=Loot.ITEMS[id]
	var grade: String=item[3]
	if not grade in RECIPE_GRADES or id.begins_with("ng_")==false and id.begins_with("d_")==false and id.begins_with("c_")==false: return {}
	var factor: int=[1,4,10][RECIPE_GRADES.find(grade)]
	var materials: Dictionary
	if item[1]=="Оружие":
		materials={"branch":3*factor,"iron_ore":3*factor,"fang":2*factor}
	elif item[1]=="Кольцо":
		materials={"iron_ore":2*factor,"crystal":factor}
	else:
		materials={"bark":3*factor,"leather":2*factor,"iron_ore":factor}
	return {"materials":materials,"fee":roundi(Loot.price(id)*.22),"grade":grade}

static func can_craft(hero,id: String) -> bool:
	var r:=recipe(id)
	if r.is_empty() or hero.level()<Loot.requirement(id): return false
	if not hero.recipes.has(r.grade): return false
	if r.grade!="NG" and hero.role_score("Оружейник")<=0: return false
	if hero.adena<r.fee: return false
	for mat in r.materials:
		if int(hero.inventory.get(mat,0))<int(r.materials[mat]): return false
	return true

static func craft(hero,id: String) -> bool:
	if not can_craft(hero,id): return false
	var r:=recipe(id)
	hero.adena-=int(r.fee)
	for mat in r.materials:
		hero.inventory[mat]=int(hero.inventory[mat])-int(r.materials[mat])
		if hero.inventory[mat]<=0: hero.inventory.erase(mat)
	hero.inventory[id]=int(hero.inventory.get(id,0))+1
	return true

static func learn_recipe(hero,id: String) -> bool:
	var grade: String={"recipe_ng":"NG","recipe_d":"D","recipe_c":"C"}.get(id,"")
	if grade=="" or hero.recipes.has(grade) or hero.level()<Loot.requirement(id): return false
	if grade!="NG" and hero.role_score("Оружейник")<=0: return false
	if not hero.consume_one(id): return false
	hero.recipes.append(grade)
	return true

static func enchant_level(hero,id: String) -> int:
	return clampi(int(hero.enchants.get(id,0)),0,CAP)

static func scroll(id: String) -> String:
	if not Loot.ITEMS.has(id) or Loot.ITEMS[id][3]=="": return ""
	return "enchant_weapon" if Loot.ITEMS[id][1]=="Оружие" else "enchant_armor"

static func enchant_fee(id: String) -> int:
	return maxi(20,roundi(Loot.price(id)*.12))

static func enchant_chance(hero,id: String) -> float:
	var current:=enchant_level(hero,id)
	return CHANCES[current] if current<CAP else 0.0

static func can_enchant(hero,id: String) -> bool:
	var needed:=scroll(id)
	return needed!="" and int(hero.inventory.get(id,0))>0 and hero.level()>=Loot.requirement(id) and enchant_level(hero,id)<CAP and int(hero.inventory.get(needed,0))>0 and hero.adena>=enchant_fee(id)

static func enchant(hero,id: String,rng: RandomNumberGenerator) -> int:
	if not can_enchant(hero,id): return -1
	var chance:=enchant_chance(hero,id)
	if not hero.consume_one(scroll(id)): return -1
	hero.adena-=enchant_fee(id)
	if rng.randf()>chance: return 0
	hero.enchants[id]=enchant_level(hero,id)+1
	return 1

static func bonus(hero,id: String) -> int:
	var level_:=enchant_level(hero,id)
	if level_<=0 or not Loot.ITEMS.has(id): return 0
	return level_*maxi(1,roundi(float(Loot.ITEMS[id][2])*.12))
''',encoding="utf-8")
patch("field/careers.gd",[
('const Loot = preload("res://field/loot.gd")','const Loot = preload("res://field/loot.gd")\nconst Forge=preload("res://field/forge.gd")'),
('var muted := false','var muted := false\nvar recipes: Array=[]\nvar enchants: Dictionary={}\nvar soul_enabled:=false\nvar spirit_enabled:=false'),
('return int(Loot.ITEMS[id][2]) if Loot.ITEMS.has(id) else 0','return int(Loot.ITEMS[id][2])+Forge.bonus(self,id) if Loot.ITEMS.has(id) else 0'),
('"muted","ground_loot"]','"muted","ground_loot","recipes","enchants","soul_enabled","spirit_enabled"]'),
('muted = bool(file.get_value("hero","muted",false))','''muted = bool(file.get_value("hero","muted",false))
		var saved_recipes=file.get_value("hero","recipes",[])
		var saved_enchants=file.get_value("hero","enchants",{})
		recipes=saved_recipes if saved_recipes is Array else []
		enchants=saved_enchants if saved_enchants is Dictionary else {}
		soul_enabled=bool(file.get_value("hero","soul_enabled",false))
		spirit_enabled=bool(file.get_value("hero","spirit_enabled",false))'''),
('if equipment.values().has(id) and inventory[id]<=1: return false','if (equipment.values().has(id) or Forge.enchant_level(self,id)>0) and inventory[id]<=1: return false'),
])
append("field/careers.gd",'''
func consume_one(id: String) -> bool:
	if not Loot.ITEMS.has(id) or inventory.get(id,0)<=0: return false
	inventory[id]=int(inventory[id])-1
	if inventory[id]<=0: inventory.erase(id)
	return true
''')
# State additions are optional, preserving earlier saves.
patch("ford/world.gd",[
('const Looks=preload("res://ford/looks.gd")','const Looks=preload("res://ford/looks.gd")\nconst Forge=preload("res://field/forge.gd")'),
('var market_grade:="NG"','var market_grade:="NG"\nvar smith: Node3D\nvar smith_button: Button\nvar sweep_button: Button\nvar forge_mode:="Крафт"\nvar forge_grade:="NG"\nvar forge_feedback:=""'),
('''	profile.muted=bool(state.get("muted",false))''','''	profile.muted=bool(state.get("muted",false))
	if state.get("recipes") is Array: profile.recipes=state.recipes
	if state.get("enchants") is Dictionary: profile.enchants=state.enchants
	profile.soul_enabled=bool(state.get("soul_enabled",false))
	profile.spirit_enabled=bool(state.get("spirit_enabled",false))'''),
('["first","second","total_xp","kills","sp","adena","learned","inventory","equipment","hotbar","muted"]','["first","second","total_xp","kills","sp","adena","learned","inventory","equipment","hotbar","muted","recipes","enchants","soul_enabled","spirit_enabled"]'),
('build_merchant()\n\tadd_child(hud)','build_merchant()\n\tbuild_smith()\n\tadd_child(hud)'),
('''	layout_market()''','''	layout_market()
	smith_button=hud.button("Кузнец · крафт / заточка")
	hud.place(hud.ui,smith_button,Rect2(650,315,295,47))
	hud.ui.move_child(smith_button,hud.desks.get_index())
	smith_button.pressed.connect(open_forge)
	sweep_button=hud.button("Сбор спойла")
	sweep_button.add_theme_font_size_override("font_size",12)
	hud.place(hud.ui,sweep_button,Rect2(816,267,130,42))
	hud.ui.move_child(sweep_button,hud.desks.get_index())
	sweep_button.pressed.connect(sweep_nearest)
	hud.ui.resized.connect(layout_forge)
	layout_forge()
	smith_button.hide()
	sweep_button.hide()'''),
('merchant.visible=town\n\tground=city_ground','merchant.visible=town\n\tsmith.visible=town\n\tground=city_ground'),
('''		"spoil":
			target.spoiled=true
			engaged=true
			sound.effect("ward")
			contact(target.position+Vector3.UP*.35,"spoil")
			float_word(target.position,"Спойл",Color("#f2cd82"))''','''		"spoil":
			if target==null or target.hp<=0 or target.spoiled: return
			engaged=true
			target.aggro=true
			sound.effect("ward")
			contact(target.position+Vector3.UP*.35,"spoil")
			var chance:=clampf(.78+.035*(profile.level()-target.rank)+.04*profile.role_score("Добыча"),.25,.95)
			target.spoiled=rng.randf()<chance
			float_word(target.position,"Спойл успешен" if target.spoiled else "Спойл не удался",Color("#f2cd82"))
			hud.feed.text="После победы нажми Сбор спойла." if target.spoiled else "Спойл не удался."'''),
('''	sound.effect("hit" if kind=="hit" else "heavy")
	var hit_chance''','''	var charge: String="spiritshot" if profile.mystic() else "soulshot"
	var enabled: bool=profile.spirit_enabled if charge=="spiritshot" else profile.soul_enabled
	if enabled and profile.consume_one(charge):
		amount=roundi(amount*(1.7 if charge=="spiritshot" else 1.5))
		float_word(hero.position,"Spiritshot" if charge=="spiritshot" else "Soulshot",Color("#a3daff") if charge=="spiritshot" else Color("#ffdb84"))
		contact(hero.position+Vector3.UP*.65,"guard")
		hud.bag.refresh()
	elif enabled:
		if charge=="spiritshot": profile.spirit_enabled=false
		else: profile.soul_enabled=false
	sound.effect("hit" if kind=="hit" else "heavy")
	var hit_chance'''),
('''	var reward := Loot.roll(target.kind,target.rank,.04*profile.role_score("Добыча"),target.spoiled,rng)
	reward["place"]=target.flat()
	profile.ground_loot.append(reward)
	spawn_pile(reward)''','''	var reward := Loot.roll(target.kind,target.rank,.04*profile.role_score("Добыча"),false,rng)
	reward["place"]=target.flat()
	profile.ground_loot.append(reward)
	spawn_pile(reward)
	if target.spoiled:
		var extra:=Loot.spoil_roll(target.kind,target.rank,profile.role_score("Добыча"),rng)
		extra["place"]=target.flat()
		profile.ground_loot.append(extra)
		spawn_pile(extra)'''),
('''		if pile.visible and gap<radius: radius=gap; nearest=pile
	if nearest: request_pickup(nearest)''','''		if pile.visible and not pile.reward.get("spoil_only",false) and gap<radius: radius=gap; nearest=pile
	if nearest: request_pickup(nearest)'''),
('''func request_pickup(pile: Node3D) -> void:
	clear_target()''','''func request_pickup(pile: Node3D, sweeping: bool=false) -> void:
	if pile.reward.get("spoil_only",false) and not sweeping:
		hud.feed.text="Нажми Сбор спойла для этой добычи."
		return
	clear_target()'''),
('''	var msg:="Подобрано · %d аден" % pile.reward.adena''','''	var msg:="Собран спойл" if pile.reward.get("spoil_only",false) else "Подобрано · %d аден" % pile.reward.adena'''),
('''	market_button.visible=near_merchant() and not near_trainer()''','''	smith_button.visible=near_smith()
	market_button.visible=near_merchant() and not near_trainer() and not near_smith()
	hud.trainer_button.visible=near_trainer() and not near_smith()
	sweep_button.visible=not town and has_spoil_nearby()'''),
('''			if sk.item in ["hp_potion","mp_potion"]: left=potion_wait''','''			if sk.item in ["hp_potion","mp_potion"]: left=potion_wait
			elif sk.item in ["soulshot","spiritshot"]:
				var on: bool=profile.soul_enabled if sk.item=="soulshot" else profile.spirit_enabled
				if on: hint="ON · "+str(profile.inventory.get(sk.item,0))'''),
('''	if id in ["hp_potion","mp_potion"]:
		if potion_wait>0:''','''	if id in ["soulshot","spiritshot"]:
		if profile.inventory.get(id,0)<=0:
			hud.feed.text="Нет зарядов."
			return
		if id=="soulshot":
			profile.soul_enabled=not profile.soul_enabled
			profile.spirit_enabled=false
		else:
			profile.spirit_enabled=not profile.spirit_enabled
			profile.soul_enabled=false
		hud.feed.text=str(Loot.ITEMS[id][0])+(" · ВКЛ" if profile.soul_enabled or profile.spirit_enabled else " · ВЫКЛ")
	elif id in ["hp_potion","mp_potion"]:
		if potion_wait>0:'''),
('''	if market_grade=="Зелья":
				if item[1]!="Расходник": continue''','''	if market_grade=="Зелья":
				if id not in ["hp_potion","mp_potion","soulshot","spiritshot"]: continue'''),
])
# Save shot consumption on attacks without waiting for a kill (periodic autosave also applies).
# All transactions remain character-local in this closed alpha.
append("ford/world.gd",'''
func has_spoil_nearby() -> bool:
	for pile in piles:
		if pile.visible and pile.reward.get("spoil_only",false) and actor.distance_to(pile.point)<=12.0: return true
	return false

func sweep_nearest() -> void:
	if town or death_wait>0 or hud.shade.visible or web_menu_open(): return
	var nearest: Node3D
	var radius:=12.01
	for pile in piles:
		var gap:=actor.distance_to(pile.point)
		if pile.visible and pile.reward.get("spoil_only",false) and gap<radius:
			radius=gap
			nearest=pile
	if nearest!=null: request_pickup(nearest,true)
	else: hud.feed.text="Поблизости нет спойла."

func build_smith() -> void:
	smith=preload("res://ford/models/warden.glb").instantiate() as Node3D
	add_child(smith)
	var spot:=Vector2(180,12)
	for option in [Vector2(180,12),Vector2(180,10),Vector2(180,14),Vector2(182,12)]:
		if city_ground.legal(option):
			spot=option
			break
	smith.position=Ground.point(spot)
	Looks.fit(smith,"Гном","male",2)
	var tag:=Label3D.new()
	tag.text="Кузнец · Горн"
	tag.position.y=2.3
	tag.font_size=38
	tag.pixel_size=.007
	tag.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	tag.modulate=Color("#efcf8b")
	smith.add_child(tag)
	smith.visible=town

func layout_forge() -> void:
	var extra: Vector2=(hud.ui.size-Vector2(960,540)).max(Vector2.ZERO)
	smith_button.position=Vector2(650,315)+extra
	sweep_button.position=Vector2(816+extra.x,267)

func near_smith() -> bool:
	return town and smith!=null and actor.distance_to(Vector2(smith.position.x,smith.position.z))<=3.5

func forge_line(rows: VBoxContainer,title: String,detail: String,button_text: String,enabled: bool,callback: Callable) -> void:
	var row:=HBoxContainer.new()
	rows.add_child(row)
	var column:=VBoxContainer.new()
	column.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	row.add_child(column)
	column.add_child(hud.label(title,15))
	var info:=hud.label(detail,12,Color("#d5c7a6"))
	info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	column.add_child(info)
	var button: Button=hud.button(button_text)
	button.add_theme_font_size_override("font_size",13)
	button.disabled=not enabled
	row.add_child(button)
	button.pressed.connect(callback)

func after_forge(message: String) -> void:
	forge_feedback=message
	save_hero()
	hud.bag.refresh()
	hud.sheet.refresh(true)
	update_ui()
	open_forge.call_deferred()

func open_forge() -> void:
	if not near_smith(): return
	clear_target()
	var rows: VBoxContainer=hud.show_panel("Кузнец · "+str(profile.adena)+" аден")
	var tabs:=HBoxContainer.new()
	rows.add_child(tabs)
	for mode in ["Крафт","Рецепты","Заточка"]:
		var tab: Button=hud.button(mode)
		tab.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		tabs.add_child(tab)
		tab.pressed.connect(func():
			forge_mode=mode
			forge_feedback=""
			open_forge.call_deferred())
	if forge_feedback!="": rows.add_child(hud.label(forge_feedback,15,Color("#f4d396")))
	if forge_mode=="Рецепты":
		rows.add_child(hud.label("NG доступен всем; D/C — мастеровым гномам.",14))
		for id in ["recipe_ng","recipe_d","recipe_c"]:
			var grade: String={"recipe_ng":"NG","recipe_d":"D","recipe_c":"C"}[id]
			var enabled: bool=profile.inventory.get(id,0)>0 and not profile.recipes.has(grade) and profile.level()>=Loot.requirement(id) and (grade=="NG" or profile.role_score("Оружейник")>0)
			forge_line(rows,str(Loot.ITEMS[id][0]),"В сумке: "+str(profile.inventory.get(id,0))+(" · изучен" if profile.recipes.has(grade) else " · выпадает с монстров"),"Изучить",enabled,func():
				if near_smith() and Forge.learn_recipe(profile,id): after_forge("Рецепты "+grade+" изучены."))
	elif forge_mode=="Крафт":
		var grades:=HBoxContainer.new()
		rows.add_child(grades)
		for grade in Forge.RECIPE_GRADES:
			var tab: Button=hud.button(grade)
			grades.add_child(tab)
			tab.pressed.connect(func():
				forge_grade=grade
				open_forge.call_deferred())
		if not profile.recipes.has(forge_grade): rows.add_child(hud.label("Сначала изучи рецепт во вкладке Рецепты.",14))
		for key in Loot.ITEMS:
			var id: String=key
			var r:=Forge.recipe(id)
			if r.is_empty() or r.grade!=forge_grade: continue
			var detail:=str(r.fee)+" аден · "
			for mat in r.materials:
				detail+=str(Loot.ITEMS[mat][0])+" "+str(profile.inventory.get(mat,0))+"/"+str(r.materials[mat])+"; "
			forge_line(rows,str(Loot.ITEMS[id][0]),detail,"Создать",Forge.can_craft(profile,id),func():
				if near_smith() and Forge.craft(profile,id): after_forge("Создано: "+str(Loot.ITEMS[id][0])))
	else:
		rows.add_child(hud.label("+1–3: 100%. Затем 65/50/35%. Вещь сохраняется.",14))
		for key in profile.inventory:
			var id: String=key
			var scroll:=Forge.scroll(id)
			if scroll=="": continue
			var plus:=Forge.enchant_level(profile,id)
			var chance:=roundi(100*Forge.enchant_chance(profile,id))
			var detail: String="Шанс "+str(chance)+"% · "+str(Forge.enchant_fee(id))+" аден · свитков "+str(profile.inventory.get(scroll,0))
			forge_line(rows,str(Loot.ITEMS[id][0])+" +"+str(plus),detail,"Заточить",Forge.can_enchant(profile,id),func():
				if not near_smith(): return
				var result:=Forge.enchant(profile,id,rng)
				if result>=0: after_forge("Успех! +"+str(Forge.enchant_level(profile,id)) if result==1 else "Неудача. Предмет сохранён."))
''')
patch("field/floating_panel.gd",[
('const Dress=preload("res://ford/worn.gd")','const Dress=preload("res://ford/worn.gd")\nconst Forge=preload("res://field/forge.gd")'),
('line(Vector2(101,281),info[0],14,Loot.grade_color(chosen),265)','line(Vector2(101,281),info[0]+(" +"+str(Forge.enchant_level(hero,chosen)) if Forge.enchant_level(hero,chosen)>0 else ""),14,Loot.grade_color(chosen),265)'),
('''		line(Vector2(17,374),"+%d %s" % [info[2],"ОЗ" if chosen=="hp_potion" else "МП"],16,GOLD)''','''		var description: String="+%d %s" % [info[2],"ОЗ" if chosen=="hp_potion" else "МП"]
		if chosen in ["soulshot","spiritshot"]:
			var enabled: bool=hero.soul_enabled if chosen=="soulshot" else hero.spirit_enabled
			description="Автозаряд: "+("ВКЛ" if enabled else "ВЫКЛ")
		line(Vector2(17,374),description,14,GOLD)'''),
('var diff:int=-info[2] if worn else info[2]-hero.equipped_bonus(info[1])','var strength: int=int(info[2])+Forge.bonus(hero,chosen)\n\tvar diff:int=-strength if worn else strength-hero.equipped_bonus(info[1])'),
('''		if hero.equipment.values().has(id): line(r.position+Vector2(3,14),"◆",11,GOLD)''','''		if Forge.enchant_level(hero,id)>0: line(r.position+Vector2(3,14),"+"+str(Forge.enchant_level(hero,id)),11,GOLD)
		elif hero.equipment.values().has(id): line(r.position+Vector2(3,14),"◆",11,GOLD)'''),
])
patch("ford/pile.gd",[
('gold.albedo_color=Color("#eac268")','gold.albedo_color=Color("#78b3dc") if record.get("spoil_only",false) else Color("#eac268")'),
('''	var ids:Array=record.items.keys()''','''	if record.get("spoil_only",false):
		var tag:=Label3D.new()
		tag.text="СПОЙЛ"
		tag.position.y=.95
		tag.billboard=BaseMaterial3D.BILLBOARD_ENABLED
		tag.font_size=35
		tag.pixel_size=.006
		tag.modulate=Color("#a2d8ff")
		add_child(tag)
	var ids:Array=record.items.keys()'''),
])
patch("field/skills.gd",[
('Помечает живую цель. Победа даёт дополнительный ресурс.','Попытка спойла живой цели. После победы отдельно собери спойл.'),
])
patch("project.godot",[('config/version="0.12.0"','config/version="0.13.0"')])
patch("web/shell.html",[
('PRE-ALPHA 0.12 · ONLINE TEST / OFFLINE','PRE-ALPHA 0.13 · ONLINE TEST / OFFLINE'),
('c3-config-0120.js','c3-config-0130.js'),
('c3-online-0120.js','c3-online-0130.js'),
])
(root/"crafting_test.gd").write_text('''extends SceneTree
const Hero=preload("res://field/careers.gd")
const Forge=preload("res://field/forge.gd")
const Loot=preload("res://field/loot.gd")
func _initialize() -> void:
	var h:=Hero.new()
	h.race="Гном"
	h.origin="Подгорный боец"
	h.adena=1000
	h.inventory={"recipe_ng":1,"branch":3,"iron_ore":3,"fang":2,"enchant_weapon":3,"soulshot":2}
	if Forge.can_craft(h,"ng_sword") or not Forge.learn_recipe(h,"recipe_ng") or not Forge.craft(h,"ng_sword"):
		push_error("Craft/recipe failed");quit(1);return
	if Forge.craft(h,"ng_sword") or Forge.can_craft(h,"d_sword") or h.inventory.has("branch"):
		push_error("Craft validation failed");quit(1);return
	var rng:=RandomNumberGenerator.new()
	rng.seed=1234
	for i in 3:
		if Forge.enchant(h,"ng_sword",rng)!=1:
			push_error("Safe enchant failed");quit(1);return
	if Forge.enchant_level(h,"ng_sword")!=3 or Forge.enchant(h,"ng_sword",rng)!=-1 or h.sell_item("ng_sword"):
		push_error("Enchanted item protection failed");quit(1);return
	if not h.toggle_item("ng_sword") or h.equipped_bonus("Оружие")<=Loot.ITEMS.ng_sword[2]:
		push_error("Enchant stat bonus failed");quit(1);return
	if not h.consume_one("soulshot") or h.inventory.soulshot!=1:
		push_error("Charge consumption failed");quit(1);return
	for i in 30:
		var reward:=Loot.spoil_roll(i%3,3,1,rng)
		if not reward.spoil_only or reward.items.is_empty() or reward.adena!=0:
			push_error("Spoil reward failed");quit(1);return
	print("C3 crafting smoke test passed")
	quit(0)
''',encoding="utf-8")
print("C3 0.13 patch complete")
