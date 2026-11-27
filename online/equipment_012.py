"""C3 v0.12: additive equipment/economy patch, after gameplay_011.py."""
from pathlib import Path
import sys,json
root=Path(sys.argv[1])
def patch(file,pairs):
    p=root/file
    s=p.read_text(encoding="utf-8")
    for a,b in pairs:
        if s.count(a)!=1:
            raise RuntimeError(f"{file}: expected one occurrence, got {s.count(a)}: {a[:110]!r}")
        s=s.replace(a,b,1)
    p.write_text(s,encoding="utf-8")

# Retain original IDs so existing cloud inventory remains readable.
items={
 "branch":["Веточка","Материал",0,"",1,4,"branch"],
 "cuirass":["Деревянный нагрудник","Грудь",5,"NG",1,120,"cuirass"],
 "bark":["Пластина коры","Материал",0,"",1,8,"bark"],
 "fang":["Клык волка","Материал",0,"",1,12,"fang"],
 "slate":["Сланцевая руда","Материал",0,"",1,18,"slate"],
 "bracer":["Наручи из коры","Запястья",3,"NG",1,75,"bracer"],
 "knife":["Клык-клинок","Оружие",4,"NG",1,95,"knife"],
 "hammer":["Сланцевый молот","Оружие",7,"NG",1,160,"hammer"],
 "hp_potion":["Зелье здоровья","Расходник",30,"",1,25,"hp_potion"],
 "mp_potion":["Зелье маны","Расходник",20,"",1,30,"mp_potion"],
 "iron_ore":["Железная руда","Материал",0,"",1,25,"slate"],
 "leather":["Выделанная кожа","Материал",0,"",1,20,"bark"],
 "crystal":["Осколок кристалла","Материал",0,"",1,45,"crystal"],
}
grades=[("NG",1,1,1,"Походный"),("D",20,3,18,"Железный"),("C",40,6,85,"Стальной"),("B",52,10,320,"Мифриловый"),("A",61,15,1000,"Лунный"),("S",76,23,3500,"Древний")]
# Existing experience curve caps at 75. S stays visible as a future grade, not obtainable/equippable.
types=[
 ("sword","Клинок","Оружие",8,180),("staff","Посох","Оружие",7,175),("bow","Лук","Оружие",7,170),
 ("chest","Доспех","Грудь",6,145),("helm","Шлем","Голова",3,80),("boots","Сапоги","Ноги",3,80),
 ("gloves","Наручи","Запястья",3,85),("shield","Щит","Щит",4,105),("ring","Кольцо","Кольцо",2,90),
 ("cloak","Плащ","Спина",2,75)]
for grade,lv,power,cost,word in grades:
    for typ,name,slot,bonus,price in types:
        items[grade.lower()+"_"+typ]=[name+" · "+word,slot,bonus*power,grade,lv,price*cost,typ]
assert len(items)==73
loot=root/"field/loot.gd"
s=loot.read_text(encoding="utf-8")
a=s.index("const ITEMS :=")
b=s.index("# resource",a)
s=s[:a]+"const ITEMS := "+json.dumps(items,ensure_ascii=False,indent=2)+"\n"+s[b:]
s=s.replace('return {"adena":rng.randi_range(t[4]*rank,t[5]*rank),"items":bag}', '''# Additional independent drops; higher tiers only at appropriate monster levels.
	if rng.randf()<.12: bag["hp_potion"]=1
	if rng.randf()<.07: bag["mp_potion"]=1
	if rng.randf()<.13: bag[["leather","leather","iron_ore"][kind]]=1
	if spoiled and rng.randf()<.35: bag["crystal"]=1
	if rng.randf()<.025:
		var grade: String="ng"
		for gate in [[20,"d"],[40,"c"],[52,"b"],[61,"a"],[76,"s"]]:
			if rank>=gate[0]: grade=gate[1]
		var options: Array=["sword","staff","bow","chest","helm","boots","gloves","shield","ring","cloak"]
		bag[grade+"_"+str(options[rng.randi_range(0,options.size()-1)])]=1
	return {"adena":rng.randi_range(t[4]*rank,t[5]*rank),"items":bag}''')
s+='''
static func price(id: String) -> int:
	return int(ITEMS[id][5]) if ITEMS.has(id) else 0

static func sell_price(id: String) -> int:
	return maxi(1,floori(price(id)*.40)) if ITEMS.has(id) else 0

static func requirement(id: String) -> int:
	return int(ITEMS[id][4]) if ITEMS.has(id) else 999

static func grade_color(id: String) -> Color:
	var colors: Dictionary={"NG":"#d6d5bd","D":"#9acf8d","C":"#83c8eb","B":"#bf9ce6","A":"#eeab78","S":"#f2d579"}
	return Color(colors.get(ITEMS.get(id,["","","","",""])[3],"#b8c2b5"))
'''
loot.write_text(s,encoding="utf-8")

# Original vector art for new item categories.
art=root/"field/art/icons"
shapes={
"sword":'<path d="M15 49L45 14 53 10 50 21 24 53Z" fill="#c6d9df" stroke="#516878" stroke-width="2"/><path d="M12 43l18 13" stroke="#d4ae70" stroke-width="6"/><path d="M18 50L9 60" stroke="#76543d" stroke-width="6"/>',
"staff":'<path d="M15 60L43 17" stroke="#9e7046" stroke-width="7"/><path d="M36 19L43 5 54 12 55 25 43 31Z" fill="#89c8d1" stroke="#d2efef" stroke-width="2"/>',
"bow":'<path d="M17 7Q63 30 17 58" fill="none" stroke="#be9361" stroke-width="6"/><path d="M17 7L17 58M7 32H53" stroke="#d9d4bf" stroke-width="2"/><path d="M54 32l-9-5v10z" fill="#d2dbe0"/>',
"chest":'<path d="M10 19L22 9 32 16 42 9 54 19 47 35 44 31 44 56 20 56 20 31 17 35Z" fill="#8d9fa3" stroke="#d8c8a4" stroke-width="2"/><path d="M21 39H43M21 46H43" stroke="#52696f" stroke-width="3"/>',
"helm":'<path d="M12 36Q12 10 32 8Q52 10 52 36L49 53 39 53 39 38 25 38 25 53 15 53Z" fill="#a5b4bd" stroke="#d9c9a8" stroke-width="2"/><path d="M18 31H46M32 9V35" stroke="#52636c" stroke-width="3"/>',
"boots":'<path d="M14 9H29L27 43 38 50V57H8V48L14 38ZM39 9H54L52 43 61 50V57H34V48L39 38Z" fill="#a08063" stroke="#d5b68c" stroke-width="2"/>',
"gloves":'<path d="M11 12L27 9 31 36 23 55 9 50 15 31Z M36 9L52 12 49 31 55 50 41 55 33 36Z" fill="#9eaeb1" stroke="#d9c9a8" stroke-width="2"/><path d="M11 30L30 35M34 35L53 30" stroke="#9e7750" stroke-width="4"/>',
"shield":'<path d="M12 15L32 7 52 15V37Q46 51 32 58Q18 51 12 37Z" fill="#758e9c" stroke="#d4b77a" stroke-width="3"/><path d="M32 14V49M19 30H45" stroke="#d4b77a" stroke-width="4"/>',
"ring":'<ellipse cx="32" cy="38" rx="17" ry="17" fill="none" stroke="#d1ac69" stroke-width="8"/><path d="M21 18L32 7 43 18 32 28Z" fill="#81c6b5" stroke="#e0e7ce" stroke-width="2"/>',
"cloak":'<path d="M23 10H41L54 56Q32 61 10 56Z" fill="#657b84" stroke="#cdb58c" stroke-width="2"/><path d="M25 14L21 53M39 14L43 53" stroke="#43565d" stroke-width="3"/>',
"hp_potion":'<path d="M25 7H39V20Q54 30 51 45Q48 56 32 56Q16 56 13 45Q10 30 25 20Z" fill="#bd5450" stroke="#f4d0b1" stroke-width="2"/><path d="M23 8H41V15H23Z" fill="#b68e64"/><path d="M20 31Q15 41 23 47" fill="none" stroke="#f7ad96" stroke-width="3"/>',
"mp_potion":'<path d="M25 7H39V20Q54 30 51 45Q48 56 32 56Q16 56 13 45Q10 30 25 20Z" fill="#518ebc" stroke="#bce3f2" stroke-width="2"/><path d="M23 8H41V15H23Z" fill="#b68e64"/><path d="M20 31Q15 41 23 47" fill="none" stroke="#b8e4ed" stroke-width="3"/>',
"crystal":'<path d="M17 28L29 6 46 18 53 39 32 58 13 46Z" fill="#9fc7c9" stroke="#d4ece7" stroke-width="2"/><path d="M29 6L32 58 46 18 17 28 53 39" stroke="#7097a4" stroke-width="2" fill="none"/>'
}
for key,shape in shapes.items():
    (art/("gear_"+key+".svg")).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><rect x="1" y="1" width="62" height="62" rx="8" fill="#283a37" stroke="#998363"/>'+shape+'</svg>',encoding="utf-8")
patch("field/icon_library.gd",[
('const TEXTURES := {','const Loot=preload("res://field/loot.gd")\nconst TEXTURES := {\n'+''.join('\t"gear_'+k+'":preload("res://field/art/icons/gear_'+k+'.svg"),\n' for k in shapes)),
('return TEXTURES.get(id,TEXTURES.locked)','''if TEXTURES.has(id): return TEXTURES[id]
	if Loot.ITEMS.has(id):
		var category: String=Loot.ITEMS[id][6]
		return TEXTURES.get("gear_"+category,TEXTURES.get(category,TEXTURES.locked))
	return TEXTURES.locked'''),
])
patch("field/careers.gd",[
('return role_score("Щит")*3 + equipped_bonus("Грудь") + equipped_bonus("Запястья")','''var result:=role_score("Щит")*3
	for slot in ["Голова","Грудь","Запястья","Ноги","Щит","Кольцо","Спина"]: result+=equipped_bonus(slot)
	return result'''),
('if slot == "Материал":','if slot in ["Материал","Расходник"]:'),
('else:\n\t\tequipment[slot]=id\n\treturn true','else:\n\t\tif level()<Loot.requirement(id): return false\n\t\tequipment[slot]=id\n\treturn true'),
])
# Prices and inventory transactions, no changes to saved data format.
p=root/"field/careers.gd"
s=p.read_text(encoding="utf-8")+'''
func buy_item(id: String) -> bool:
	if not Loot.ITEMS.has(id) or Loot.ITEMS[id][1]=="Материал" or level()<Loot.requirement(id): return false
	var cost:=Loot.price(id)
	if cost<=0 or adena<cost: return false
	adena-=cost
	inventory[id]=int(inventory.get(id,0))+1
	return true

func sell_item(id: String) -> bool:
	if not Loot.ITEMS.has(id) or inventory.get(id,0)<=0: return false
	if equipment.values().has(id) and inventory[id]<=1: return false
	inventory[id]=int(inventory[id])-1
	if inventory[id]<=0: inventory.erase(id)
	adena+=Loot.sell_price(id)
	return true

func consume(id: String) -> bool:
	if id not in ["hp_potion","mp_potion"] or inventory.get(id,0)<=0: return false
	inventory[id]=int(inventory[id])-1
	if inventory[id]<=0: inventory.erase(id)
	return true
'''
p.write_text(s,encoding="utf-8")
# Bag pagination and grade details. Keep drag/drop and tap-to-slot from 0.11.
patch("field/floating_panel.gd",[
('var filter:=0','var filter:=0\nvar page:=0'),
('if (filter==1 and material) or (filter==2 and not material): continue','''if (filter==1 and Loot.ITEMS[id][1] in ["Материал","Расходник"]) or (filter==2 and not material): continue'''),
('func cell(i: int) -> Rect2:','''func page_ids() -> Array:
	var list:=ids()
	page=clampi(page,0,maxi(0,ceili(list.size()/10.0)-1))
	return list.slice(page*10,page*10+10)

func cell(i: int) -> Rect2:'''),
('var list:=ids()\n\tfor i in 10:','var list:=page_ids()\n\tfor i in 10:'),
('GOLD if id!="" and chosen==id else Color("#4d604f")','GOLD if id!="" and chosen==id else (Loot.grade_color(id) if id!="" else Color("#4d604f"))'),
('draw_line(Vector2(16,247),Vector2(367,247),GOLD)','''draw_line(Vector2(16,247),Vector2(367,247),GOLD)
	box(Rect2(287,46,29,25),Color("#354d3f"),GOLD)
	box(Rect2(338,46,29,25),Color("#354d3f"),GOLD)
	line(Vector2(287,63),"<",15,PAPER,29,HORIZONTAL_ALIGNMENT_CENTER)
	line(Vector2(338,63),">",15,PAPER,29,HORIZONTAL_ALIGNMENT_CENTER)
	line(Vector2(317,63),str(page+1),12,GOLD,21,HORIZONTAL_ALIGNMENT_CENTER)'''),
('line(Vector2(101,281),info[0],19,PAPER)','line(Vector2(101,281),info[0],14,Loot.grade_color(chosen),265)'),
('line(Vector2(101,305),info[1],14,GOLD)','line(Vector2(101,305),info[1]+(" · "+info[3]+" · Ур. "+str(info[4]) if info[3]!="" else ""),14,GOLD)'),
('line(Vector2(101,326),chance[chosen],13,SOFT)','line(Vector2(101,326),chance.get(chosen,"Продажа: "+str(Loot.sell_price(chosen))+" аден"),13,SOFT)'),
('var worn:bool=hero.equipment.get(info[1],"")==chosen','''if info[1]=="Расходник":
		line(Vector2(17,374),"+%d %s" % [info[2],"ОЗ" if chosen=="hp_potion" else "МП"],16,GOLD)
		box(Rect2(209,345,158,42),Color("#415746"),GOLD)
		line(Vector2(211,372),"Применить",16,PAPER,154,HORIZONTAL_ALIGNMENT_CENTER)
		return
	var worn:bool=hero.equipment.get(info[1],"")==chosen'''),
('line(Vector2(211,372),"Снять" if worn else "Надеть",16,PAPER,154,HORIZONTAL_ALIGNMENT_CENTER)','line(Vector2(211,372),"Снять" if worn else ("Нужен ур. "+str(info[4]) if hero.level()<info[4] else "Надеть"),14,PAPER,154,HORIZONTAL_ALIGNMENT_CENTER)'),
('var list:=ids()\n\t\t\t\tfor i in list.size():','var list:=page_ids()\n\t\t\t\tfor i in list.size():'),
('var available:=ids()\n\t\tfor i in 3:','''if Rect2(287,46,29,25).has_point(p) or Rect2(338,46,29,25).has_point(p):
			page+=-1 if p.x<320 else 1
			var visible_ids:=page_ids()
			chosen="" if visible_ids.is_empty() else visible_ids[0]
			refresh()
			return
		var available:=page_ids()
		for i in 3:'''),
('filter=i\n\t\t\t\trefresh()','filter=i\n\t\t\t\tpage=0\n\t\t\t\tchosen=""\n\t\t\t\trefresh()'),
])
# Grade badge in hotbar.
patch("field/skill_button.gd",[
('const Icons=preload("res://field/icon_library.gd")','const Icons=preload("res://field/icon_library.gd")\nconst Loot=preload("res://field/loot.gd")'),
('canvas.draw_texture_rect(Icons.for_skill(sk),image_r,false)','''canvas.draw_texture_rect(Icons.for_skill(sk),image_r,false)
		if sk.has("item"):
			var id: String=sk.item
			if Loot.ITEMS.has(id) and Loot.ITEMS[id][3]!="":
				canvas.draw_string(font,r.position+Vector2(r.size.x-21,13),Loot.ITEMS[id][3],HORIZONTAL_ALIGNMENT_RIGHT,19,10,Loot.grade_color(id))'''),
])
# Original visible equipment on the existing animated body and limb pivots.
(root/"ford/worn.gd").write_text('''extends RefCounted
const Loot=preload("res://field/loot.gd")
const Looks=preload("res://ford/looks.gd")

static func remove_layer(parent: Node3D,name_: String) -> Node3D:
	if parent==null: return null
	var old:=parent.get_node_or_null(name_)
	if old!=null: parent.remove_child(old);old.queue_free()
	var node:=Node3D.new()
	node.name=name_
	parent.add_child(node)
	return node

static func tint(id: String) -> Color:
	if id in ["cuirass","bracer","hammer"]: return Color("#a87950")
	return Loot.grade_color(id).darkened(.25)

static func fit(model: Node3D,gear: Dictionary) -> void:
	var body:=model.find_child("Body",true,false) as Node3D
	if body==null: return
	var outfit:=remove_layer(body,"Outfit")
	var chest: String=gear.get("Грудь","")
	if chest!="":
		var color:=tint(chest)
		for i in 5:
			var x: float=(i-2)*.14
			Looks.piece(outfit,Vector3(x,1.18,.27-.026*absf(i-2)),Vector3(.14,.43-.035*absf(i-2),.09),color)
		Looks.piece(outfit,Vector3(0,1.18,-.265),Vector3(.60,.43,.09),color.darkened(.1))
		Looks.piece(outfit,Vector3(0,1.02,.34),Vector3(.58,.065,.045),color.lightened(.3))
	var helm: String=gear.get("Голова","")
	if helm!="":
		var color:=tint(helm)
		Looks.piece(outfit,Vector3(0,1.99,0),Vector3(.54,.28,.51),color,true)
		for side in [-1,1]: Looks.piece(outfit,Vector3(side*.24,1.80,.01),Vector3(.09,.30,.43),color)
	var cloak: String=gear.get("Спина","")
	if cloak!="":
		Looks.piece(outfit,Vector3(0,.98,-.38),Vector3(.64,.83,.09),tint(cloak))
	for name_ in ["ArmL","ArmR","LegL","LegR"]:
		var joint:=model.find_child(name_,true,false) as Node3D
		if joint==null: continue
		var layer:=remove_layer(joint,"EquipmentVisual")
		if name_.begins_with("Leg"):
			var boots: String=gear.get("Ноги","")
			if boots!="":
				Looks.piece(layer,Vector3(0,-.55,0),Vector3(.27,.34,.28),tint(boots))
				Looks.piece(layer,Vector3(0,-.72,.085),Vector3(.29,.16,.38),tint(boots),true)
			continue
		var cuffs: String=gear.get("Запястья","")
		if cuffs!="": Looks.piece(layer,Vector3(0,-.34,0),Vector3(.27,.20,.27),tint(cuffs))
		if name_=="ArmL":
			var shield: String=gear.get("Щит","")
			if shield!="":
				Looks.piece(layer,Vector3(-.14,-.27,.14),Vector3(.55,.65,.14),tint(shield),true)
				Looks.piece(layer,Vector3(-.14,-.27,.23),Vector3(.15,.16,.10),Color("#c5ad7b"),true)
			continue
		var weapon: String=gear.get("Оружие","")
		if weapon=="" or not Loot.ITEMS.has(weapon): continue
		var type_: String=Loot.ITEMS[weapon][6]
		var color:=tint(weapon)
		Looks.piece(layer,Vector3(0,-.52,.17),Vector3(.10,.12,.20),Color("#76583c"))
		if type_=="staff":
			Looks.piece(layer,Vector3(0,-.52,.48),Vector3(.09,.09,1.14),Color("#8c6844"))
			Looks.piece(layer,Vector3(0,-.52,1.06),Vector3(.20,.20,.24),color.lightened(.3),true)
		elif type_=="bow":
			for i in 5:
				var ang: float=(i-2)*.36
				var segment:=Looks.piece(layer,Vector3(0,-.52+sin(ang)*.68,.22+cos(ang)*.32),Vector3(.07,.24,.08),Color("#ac8055"))
				segment.rotation.x=ang
			Looks.piece(layer,Vector3(0,-.52,.43),Vector3(.025,.92,.025),Color("#ddd2b0"))
		elif type_=="hammer":
			Looks.piece(layer,Vector3(0,-.52,.45),Vector3(.10,.10,.65),Color("#886645"))
			Looks.piece(layer,Vector3(0,-.52,.81),Vector3(.36,.34,.23),color)
		else:
			var length:=.40 if type_=="knife" else .85
			Looks.piece(layer,Vector3(0,-.52,.29),Vector3(.31,.09,.08),Color("#b79d66"))
			Looks.piece(layer,Vector3(0,-.52,.32+length*.5),Vector3(.12,.06,length),color.lightened(.25))
''',encoding="utf-8")
# Merchant UI using existing scrollable Godot panel. Merchant location clear of buildings/trainers.
patch("ford/world.gd",[
('var assigning_item:=""','var assigning_item:=""\nvar merchant: Node3D\nvar market_button: Button\nvar market_grade:="NG"\nvar market_selling:=false\nvar potion_wait:=0.0'),
('build_trainers()\n\tadd_child(hud)','build_trainers()\n\tbuild_merchant()\n\tadd_child(hud)'),
('hud.trainer_requested.connect(open_trainer)','''hud.trainer_requested.connect(open_trainer)
	market_button=hud.button("Торговец · магазин")
	hud.place(hud.ui,market_button,Rect2(650,315,295,47))
	hud.ui.move_child(market_button,hud.desks.get_index())
	market_button.hide()
	market_button.pressed.connect(open_market)
	hud.ui.resized.connect(layout_market)
	layout_market()'''),
('for trainer in trainers: trainer.visible=town','for trainer in trainers: trainer.visible=town\n\tmerchant.visible=town'),
('''	hud.equip_requested.connect(func(id): 
		if profile.toggle_item(id):
			preload("res://ford/worn.gd").fit(hero,profile.equipment)
			hud.sheet.refresh(true)
			hud.bag.refresh()
			save_hero()
			update_ui())''','''	hud.equip_requested.connect(use_item)'''),
('''		var item:=id.trim_prefix("item/")
		if profile.toggle_item(item):
			preload("res://ford/worn.gd").fit(hero,profile.equipment)
			hud.sheet.refresh(true)
			hud.bag.refresh()
			save_hero()
			update_ui()
		else: hud.feed.text="Предмет недоступен для использования."
		return''','''		use_item(id.trim_prefix("item/"))
		return'''),
('attack_wait=maxf(0,attack_wait-dt)','attack_wait=maxf(0,attack_wait-dt)\n\tpotion_wait=maxf(0,potion_wait-dt)'),
('hud.trainer_button.visible=near_trainer()','hud.trainer_button.visible=near_trainer()\n\tmarket_button.visible=near_merchant() and not near_trainer()'),
('elif sk.has("item"): hint="×%d" % profile.inventory.get(sk.item,0)','elif sk.has("item"):\n\t\t\thint="×%d" % profile.inventory.get(sk.item,0)\n\t\t\tif sk.item in ["hp_potion","mp_potion"]: left=potion_wait'),
])
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")+'''
func use_item(id: String) -> void:
	if not Loot.ITEMS.has(id) or death_wait>0: return
	if id in ["hp_potion","mp_potion"]:
		if potion_wait>0:
			hud.feed.text="Зелья · ещё %.1f с" % potion_wait
			return
		if (id=="hp_potion" and hp>=profile.hp_max()) or (id=="mp_potion" and mp>=profile.mana_max()):
			hud.feed.text="Показатель уже полный."
			return
		if not profile.consume(id): return
		if id=="hp_potion": hp=mini(profile.hp_max(),hp+int(Loot.ITEMS[id][2]))
		else: mp=mini(profile.mana_max(),mp+int(Loot.ITEMS[id][2]))
		potion_wait=8.0
		sound.effect("ward")
		contact(hero.position+Vector3.UP*.55,"guard")
	else:
		if profile.level()<Loot.requirement(id):
			hud.feed.text="Требуется уровень "+str(Loot.requirement(id))
			return
		if not profile.toggle_item(id):
			hud.feed.text="Предмет недоступен для использования."
			return
		preload("res://ford/worn.gd").fit(hero,profile.equipment)
		hud.sheet.refresh(true)
	hud.bag.refresh()
	save_hero()
	update_ui()

func build_merchant() -> void:
	merchant=preload("res://ford/models/warden.glb").instantiate() as Node3D
	add_child(merchant)
	merchant.position=Ground.point(Vector2(180,25))
	Looks.fit(merchant,"Человек","female",1)
	var tag:=Label3D.new()
	tag.text="Торговка · Экипировка"
	tag.position.y=2.3
	tag.font_size=38
	tag.pixel_size=.007
	tag.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	tag.modulate=Color("#efcf8b")
	merchant.add_child(tag)
	merchant.visible=town

func layout_market() -> void:
	market_button.position=Vector2(650,315)+(hud.ui.size-Vector2(960,540)).max(Vector2.ZERO)

func near_merchant() -> bool:
	return town and merchant!=null and actor.distance_to(Vector2(merchant.position.x,merchant.position.z))<=4.5

func open_market() -> void:
	if not near_merchant(): return
	clear_target()
	var rows: VBoxContainer=hud.show_panel("Торговец · "+str(profile.adena)+" аден")
	var tabs:=HBoxContainer.new()
	rows.add_child(tabs)
	for mode in ["Купить","Продать"]:
		var tab: Button=hud.button(mode)
		tab.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		tabs.add_child(tab)
		tab.pressed.connect(func():
			market_selling=mode=="Продать"
			open_market())
	if not market_selling:
		var grades:=HBoxContainer.new()
		rows.add_child(grades)
		for grade in ["NG","D","C","B","A","S","Зелья"]:
			var tab: Button=hud.button(grade)
			tab.add_theme_font_size_override("font_size",13)
			tab.size_flags_horizontal=Control.SIZE_EXPAND_FILL
			grades.add_child(tab)
			tab.pressed.connect(func():
				market_grade=grade
				open_market())
	var count:=0
	for key in Loot.ITEMS:
		var id: String=key
		var item: Array=Loot.ITEMS[id]
		if market_selling:
			if profile.inventory.get(id,0)<1: continue
		else:
			if item[1]=="Материал": continue
			if market_grade=="Зелья":
				if item[1]!="Расходник": continue
			elif item[3]!=market_grade: continue
		count+=1
		var row:=HBoxContainer.new()
		rows.add_child(row)
		var icon:=TextureRect.new()
		icon.texture=hud.Icons.get_icon(id)
		icon.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.custom_minimum_size=Vector2(41,41)
		row.add_child(icon)
		var description: Label=hud.label(str(item[0])+"\\n"+str(item[1])+" · "+str(item[2])+" · Ур. "+str(item[4]),13,Loot.grade_color(id))
		description.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		row.add_child(description)
		var price: int=Loot.sell_price(id) if market_selling else Loot.price(id)
		var action: Button=hud.button(("Продать " if market_selling else "Купить ")+str(price))
		action.add_theme_font_size_override("font_size",13)
		action.disabled=(profile.equipment.values().has(id) and profile.inventory.get(id,0)<=1) if market_selling else (profile.level()<item[4] or profile.adena<price)
		row.add_child(action)
		action.pressed.connect(func():
			if not near_merchant(): return
			var ok: bool=profile.sell_item(id) if market_selling else profile.buy_item(id)
			if ok:
				save_hero()
				hud.bag.refresh()
				update_ui()
				open_market.call_deferred())
	if count==0: rows.add_child(hud.label("Нет предметов для продажи",16))

'''
p.write_text(s,encoding="utf-8")
# Versioned Web assets.
patch("project.godot",[('config/version="0.11.0"','config/version="0.12.0"')])
patch("web/shell.html",[
('PRE-ALPHA 0.11 · ONLINE TEST / OFFLINE','PRE-ALPHA 0.12 · ONLINE TEST / OFFLINE'),
('c3-config-0110.js','c3-config-0120.js'),
('c3-online-0110.js','c3-online-0120.js'),
])
# Build-time smoke test: no database writes or player accounts.
(root/"equipment_test.gd").write_text('''extends SceneTree
const Hero=preload("res://field/careers.gd")
const Loot=preload("res://field/loot.gd")
func _initialize() -> void:
	var h:=Hero.new()
	h.race="Гном"
	h.origin="Подгорный боец"
	h.adena=1000
	if not h.buy_item("ng_sword") or h.adena!=820 or not h.toggle_item("ng_sword"):
		push_error("Shop/equip smoke test failed");quit(1);return
	if h.buy_item("d_sword") or h.sell_item("ng_sword"):
		push_error("Level or equipped-item protection failed");quit(1);return
	if not h.toggle_item("ng_sword") or not h.sell_item("ng_sword") or h.adena!=892:
		push_error("Sell transaction failed");quit(1);return
	if not h.buy_item("hp_potion") or not h.consume("hp_potion") or h.consume("hp_potion"):
		push_error("Potion transaction failed");quit(1);return
	var rng:=RandomNumberGenerator.new()
	rng.seed=1234
	for i in 300:
		var reward:=Loot.roll(i%3,3,0,false,rng)
		for id in reward.items:
			if not Loot.ITEMS.has(id) or Loot.requirement(id)>3:
				push_error("Invalid low-level drop");quit(1);return
	print("C3 equipment smoke test passed")
	quit(0)
''',encoding="utf-8")
print("C3 v0.12 equipment patch complete")


# Potions use their actual cooldown; material IDs stay compatible with old saves.
patch("field/actions.gd",[
('entries["item/"+id]={"name":item[0],"effect":id,"item":id,"description":"Предмет из инвентаря"}','entries["item/"+id]={"name":item[0],"effect":id,"item":id,"description":"Предмет из инвентаря","cd":8.0 if item[1]=="Расходник" else 0.0}'),
])
# Correct ranged reach to reflect equipped bows/staves.
patch("ford/world.gd",[
('if id=="hit": return 5.2 if profile.mystic() else (4.8 if profile.role_score("Дальний бой")>0 else REACH)','''if id=="hit":
		var weapon: String=profile.equipment.get("Оружие","")
		var style: String=Loot.ITEMS[weapon][6] if Loot.ITEMS.has(weapon) else ""
		if style=="bow": return 4.8
		if style=="staff": return 5.2
		return 5.2 if profile.mystic() else (4.8 if profile.role_score("Дальний бой")>0 else REACH)'''),
])
