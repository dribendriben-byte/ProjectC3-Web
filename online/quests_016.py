"""C3 0.16: quest NPCs, journal, repeatable and chain quests."""
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

(root/"field/quests.gd").write_text('''extends RefCounted
const Loot=preload("res://field/loot.gd")
const Experience=preload("res://field/experience.gd")
# npc, title, dialogue, min level, prerequisite, kill kind, min monster level, goal, reward, repeatable
const DATA={
	"ford_intro":{"npc":"guard","title":"Первый дозор","text":"За бродом ожили корни. Докажи, что дорога снова безопасна.","level":1,"requires":"","kind":0,"rank":1,"count":3,"xp":100,"adena":60,"items":{"hp_potion":2},"repeat":false},
	"ford_hunt":{"npc":"guard","title":"Лесная тропа","text":"Патруль потерял следы у восточной тропы. Убей пять волков.","level":3,"requires":"ford_intro","kind":1,"rank":1,"count":5,"xp":250,"adena":100,"items":{"soulshot":5},"repeat":false},
	"forest_wolves":{"npc":"scout","title":"Опасная чаща","text":"Волки в восточном лесу охотятся на путников. Нам нужно расчистить путь.","level":6,"requires":"ford_hunt","kind":1,"rank":6,"count":6,"xp":1600,"adena":300,"items":{"hp_potion":3},"repeat":false},
	"forest_patrol":{"npc":"scout","title":"Патруль леса","text":"Каждый новый патруль уменьшает опасность на дороге.","level":6,"requires":"forest_wolves","kind":1,"rank":6,"count":8,"xp":900,"adena":160,"items":{"leather":2},"repeat":true},
	"ruin_watch":{"npc":"captain","title":"Серый Дозор","text":"Каменные создания заняли руины. Вернись после шести побед.","level":12,"requires":"forest_wolves","kind":2,"rank":12,"count":6,"xp":4500,"adena":750,"items":{"recipe_ng":1},"repeat":false},
	"elite_watch":{"npc":"captain","title":"Последний страж","text":"В руинах пробудился древний страж. Победи его и доложи мне.","level":20,"requires":"ruin_watch","kind":2,"rank":25,"count":1,"xp":18000,"adena":1500,"items":{"enchant_weapon":1},"repeat":false,"elite":true},
	"quarry_stone":{"npc":"miner","title":"Каменная жила","text":"Карьер снова опасен. Разгони сланцевиков у старых залежей.","level":20,"requires":"ruin_watch","kind":2,"rank":20,"count":8,"xp":12000,"adena":900,"items":{"iron_ore":5},"repeat":false},
	"quarry_repeat":{"npc":"miner","title":"Работа старателя","text":"Расчисти карьер для следующей смены.","level":20,"requires":"quarry_stone","kind":2,"rank":20,"count":10,"xp":6000,"adena":400,"items":{"slate":3,"iron_ore":2},"repeat":true}
}
static func status(hero,id: String) -> String:
	if not DATA.has(id): return "locked"
	var q: Dictionary=DATA[id]
	var record: Dictionary=hero.quests.get(id,{})
	if record.get("state")=="active":
		return "ready" if int(record.get("count",0))>=q.count else "active"
	if record.get("state")=="done" and not q.repeat: return "done"
	if hero.level()<q.level: return "locked"
	if q.requires!="" and int(hero.quests.get(q.requires,{}).get("completed",0))<1: return "locked"
	return "available"

static func accept(hero,id: String) -> bool:
	if status(hero,id)!="available": return false
	var completed: int=int(hero.quests.get(id,{}).get("completed",0))
	hero.quests[id]={"state":"active","count":0,"completed":completed}
	return true

static func on_kill(hero,kind: int,rank: int,elite: bool) -> Array[String]:
	var changed: Array[String]=[]
	for id in DATA:
		if status(hero,id)!="active": continue
		var q: Dictionary=DATA[id]
		if kind!=q.kind or rank<q.rank or (q.get("elite",false) and not elite): continue
		hero.quests[id]["count"]=mini(q.count,int(hero.quests[id].get("count",0))+1)
		changed.append(id)
	return changed

static func claim(hero,id: String) -> bool:
	if status(hero,id)!="ready": return false
	var q: Dictionary=DATA[id]
	var completed: int=int(hero.quests[id].get("completed",0))+1
	# State is set before reward; repeatable quests require explicit fresh acceptance.
	hero.quests[id]={"state":"done","count":q.count,"completed":completed}
	hero.total_xp=mini(Experience.START.back(),hero.total_xp+int(q.xp))
	hero.sp+=maxi(1,roundi(q.xp*.06))
	hero.adena+=int(q.adena)
	for item in q.items:
		if Loot.ITEMS.has(item): hero.inventory[item]=int(hero.inventory.get(item,0))+int(q.items[item])
	return true

static func description(hero,id: String) -> String:
	var q: Dictionary=DATA[id]
	var count: int=int(hero.quests.get(id,{}).get("count",0))
	var result: String="%d/%d · Ур. %d · %d EXP · %d аден" % [count,q.count,q.level,q.xp,q.adena]
	if q.requires!="" and int(hero.quests.get(q.requires,{}).get("completed",0))<1: result+=" · после «"+str(DATA[q.requires].title)+"»"
	if q.repeat: result+=" · повторяемое"
	return result
''',encoding="utf-8")
patch("field/careers.gd",[
("var recipes: Array=[]","var recipes: Array=[]\nvar quests: Dictionary={}"),
('"soul_enabled","spirit_enabled"]','"soul_enabled","spirit_enabled","quests"]'),
('spirit_enabled=bool(file.get_value("hero","spirit_enabled",false))','''spirit_enabled=bool(file.get_value("hero","spirit_enabled",false))
		var saved_quests=file.get_value("hero","quests",{})
		quests=saved_quests if saved_quests is Dictionary else {}'''),
])
patch("ford/world.gd",[
('const Frontier=preload("res://ford/frontier.gd")','const Frontier=preload("res://ford/frontier.gd")\nconst Quests=preload("res://field/quests.gd")'),
('var smith: Node3D','var smith: Node3D\nvar quest_npcs: Array[Node3D]=[]\nvar quest_button: Button\nvar journal_button: Button'),
('profile.spirit_enabled=bool(state.get("spirit_enabled",false))','''profile.spirit_enabled=bool(state.get("spirit_enabled",false))
	if state.get("quests") is Dictionary: profile.quests=state.quests'''),
('"recipes","enchants","soul_enabled","spirit_enabled"]','"recipes","enchants","soul_enabled","spirit_enabled","quests"]'),
('build_smith()\n\tadd_child(hud)','build_smith()\n\tbuild_quest_npcs()\n\tadd_child(hud)'),
('sweep_button.hide()\n','''sweep_button.hide()
	quest_button=hud.button("Задания · диалог")
	hud.place(hud.ui,quest_button,Rect2(650,315,295,47))
	hud.ui.move_child(quest_button,hud.desks.get_index())
	quest_button.pressed.connect(open_nearby_quests)
	quest_button.hide()
	journal_button=hud.button("Квесты · J")
	journal_button.add_theme_font_size_override("font_size",13)
	hud.place(hud.ui,journal_button,Rect2(15,124,112,38))
	hud.ui.move_child(journal_button,hud.desks.get_index())
	journal_button.pressed.connect(open_journal)
	hud.ui.resized.connect(layout_quests)
	layout_quests()
'''),
('smith.visible=town\n\tground=city_ground','''smith.visible=town
	for npc in quest_npcs: npc.visible=bool(npc.get_meta("in_town"))==town
	ground=city_ground'''),
('KEY_F: pickup_nearest()','KEY_F: pickup_nearest()\n\t\t\tKEY_J: open_journal()'),
('func select_screen(screen: Vector2) -> void:\n\tif town:','''func select_screen(screen: Vector2) -> void:
	for npc in quest_npcs:
		if not npc.visible or cam.is_position_behind(npc.position): continue
		var top:=cam.unproject_position(npc.position+Vector3.UP*1.6)
		var bottom:=cam.unproject_position(npc.position)
		if screen.distance_to((top+bottom)*.5)<maxf(22,top.distance_to(bottom)*.48):
			var p:=Vector2(npc.position.x,npc.position.z)
			if actor.distance_to(p)<=3.4: open_quest_npc(npc)
			else:
				walk_to(p)
				hud.feed.text="Подойди для разговора."
			return
	if town:'''),
('profile.earn(gain)\n\tvar msg','''profile.earn(gain)
	var changed:=Quests.on_kill(profile,target.kind,target.rank,target.elite)
	var msg'''),
('hud.feed.text=msg\n\tclear_target()','''if not changed.is_empty():
		var qid: String=changed[0]
		msg+=" · "+str(Quests.DATA[qid].title)+" "+str(profile.quests[qid].count)+"/"+str(Quests.DATA[qid].count)
	hud.feed.text=msg
	clear_target()'''),
('sweep_button.visible=not town and has_spoil_nearby()','''sweep_button.visible=not town and has_spoil_nearby()
	var npc:=nearby_quest_npc()
	quest_button.visible=npc!=null
	if npc!=null:
		quest_button.text="Задания · "+str(npc.get_meta("display"))
		smith_button.hide()
		market_button.hide()
		hud.trainer_button.hide()
	refresh_quest_markers()'''),
])
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")+'''
func build_quest_npcs() -> void:
	for entry in [["guard","Дозорный Рен",Vector2(-5,3),false,"Человек"],["scout","Следопыт Эйра",Vector2(24,-3),false,"Эльф"],["captain","Капитан Арден",Vector2(180,30),true,"Человек"],["miner","Старатель Брин",Vector2(10,17),false,"Гном"]]:
		var in_town: bool=entry[3]
		var nav=city_ground if in_town else field_ground
		var p: Vector2=entry[2]
		if not nav.legal(p): continue
		var npc:=preload("res://ford/models/warden.glb").instantiate() as Node3D
		add_child(npc)
		npc.position=Ground.point(p)
		Looks.fit(npc,entry[4],"female" if entry[0]=="scout" else "male",1)
		npc.set_meta("quest_id",entry[0])
		npc.set_meta("display",entry[1])
		npc.set_meta("in_town",in_town)
		var tag:=Label3D.new()
		tag.name="QuestTag"
		tag.font_size=42
		tag.pixel_size=.007
		tag.position.y=2.35
		tag.billboard=BaseMaterial3D.BILLBOARD_ENABLED
		tag.outline_size=8
		npc.add_child(tag)
		npc.visible=in_town==town
		quest_npcs.append(npc)

func refresh_quest_markers() -> void:
	for npc in quest_npcs:
		var marker: Label3D=npc.get_node("QuestTag")
		var prefix: String=""
		var tint:=Color("#d5dacd")
		for id in Quests.DATA:
			if Quests.DATA[id].npc!=npc.get_meta("quest_id"): continue
			var state:=Quests.status(profile,id)
			if state=="ready":
				prefix="? "
				tint=Color("#ffdb75")
				break
			if state=="available":
				prefix="! "
				tint=Color("#ffdb75")
		marker.text=prefix+str(npc.get_meta("display"))
		marker.modulate=tint

func nearby_quest_npc() -> Node3D:
	var nearest: Node3D
	var gap:=3.4
	for npc in quest_npcs:
		if not npc.visible: continue
		var d:=actor.distance_to(Vector2(npc.position.x,npc.position.z))
		if d<gap:
			gap=d
			nearest=npc
	return nearest

func layout_quests() -> void:
	quest_button.position=Vector2(650,315)+(hud.ui.size-Vector2(960,540)).max(Vector2.ZERO)

func open_nearby_quests() -> void:
	var npc:=nearby_quest_npc()
	if npc!=null: open_quest_npc(npc)

func open_quest_npc(npc: Node3D) -> void:
	if not npc.visible or actor.distance_to(Vector2(npc.position.x,npc.position.z))>3.4: return
	clear_target()
	var rows: VBoxContainer=hud.show_panel(str(npc.get_meta("display")))
	for id in Quests.DATA:
		var q: Dictionary=Quests.DATA[id]
		if q.npc!=npc.get_meta("quest_id"): continue
		var state:=Quests.status(profile,id)
		if state=="done": continue
		rows.add_child(hud.label(q.title,19,Color("#eecf8d")))
		var text:=hud.label(q.text,14)
		text.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
		rows.add_child(text)
		rows.add_child(hud.label(Quests.description(profile,id),13))
		var action: Button=hud.button("Принять" if state=="available" else ("Получить награду" if state=="ready" else ("Выполняется" if state=="active" else "Пока недоступно")))
		action.disabled=state not in ["available","ready"]
		rows.add_child(action)
		action.pressed.connect(func():
			if not npc.visible or actor.distance_to(Vector2(npc.position.x,npc.position.z))>3.4: return
			var old_level:=profile.level()
			var ok:=Quests.claim(profile,id) if state=="ready" else Quests.accept(profile,id)
			if ok:
				if profile.level()>old_level:
					hp=profile.hp_max()
					mp=profile.mana_max()
				hud.feed.text=("Награда получена: " if state=="ready" else "Задание принято: ")+str(q.title)
				save_hero()
				update_ui()
				hud.bag.refresh()
				open_quest_npc.call_deferred(npc))
	var close:=hud.button("Закрыть")
	rows.add_child(close)
	close.pressed.connect(func(): hud.shade.hide())

func open_journal() -> void:
	if town_transition or web_menu_open(): return
	clear_target()
	var rows: VBoxContainer=hud.show_panel("Журнал заданий")
	var count:=0
	for id in Quests.DATA:
		var state:=Quests.status(profile,id)
		if state not in ["active","ready"]: continue
		var q: Dictionary=Quests.DATA[id]
		count+=1
		rows.add_child(hud.label(q.title,19,Color("#eecf8d")))
		var text:=hud.label(Quests.description(profile,id),14)
		text.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
		rows.add_child(text)
		var giver: String={"guard":"Дозорный Рен · Застава","scout":"Следопыт Эйра · Лес","captain":"Капитан Арден · Город","miner":"Старатель Брин · Карьер"}[q.npc]
		rows.add_child(hud.label(("Готово! Вернись: " if state=="ready" else "Выдал: ")+giver,13))
	if count==0: rows.add_child(hud.label("Нет активных заданий. Найди NPC с !",16))
	var close:=hud.button("Закрыть")
	rows.add_child(close)
	close.pressed.connect(func(): hud.shade.hide())
'''
p.write_text(s,encoding="utf-8")
patch("project.godot",[('config/version="0.14.0"','config/version="0.16.0"')])
patch("web/shell.html",[
('PRE-ALPHA 0.14 · ONLINE TEST / OFFLINE','PRE-ALPHA 0.16 · ONLINE TEST / OFFLINE'),
('c3-config-0140.js','c3-config-0160.js'),
('c3-online-0140.js','c3-online-0160.js'),
])
(root/"quests_test.gd").write_text('''extends SceneTree
const Hero=preload("res://field/careers.gd")
const Q=preload("res://field/quests.gd")
func _initialize() -> void:
	var h:=Hero.new()
	h.race="Гном"
	h.origin="Подгорный боец"
	if not Q.accept(h,"ford_intro") or Q.accept(h,"ford_intro") or Q.claim(h,"ford_intro"):
		push_error("Quest accept validation");quit(1);return
	Q.on_kill(h,1,1,false)
	if h.quests.ford_intro.count!=0:
		push_error("Wrong monster counted");quit(1);return
	for i in 3: Q.on_kill(h,0,1,false)
	if Q.status(h,"ford_intro")!="ready" or not Q.claim(h,"ford_intro") or Q.claim(h,"ford_intro") or Q.accept(h,"ford_intro"):
		push_error("Quest claim validation");quit(1);return
	if h.adena!=60 or h.kills!=0 or int(h.inventory.get("hp_potion",0))!=2:
		push_error("Quest reward failed");quit(1);return
	h.total_xp=Hero.Experience.START[19]
	h.quests["forest_wolves"]={"state":"done","count":6,"completed":1}
	if not Q.accept(h,"forest_patrol"):
		push_error("Repeatable quest failed");quit(1);return
	for i in 8: Q.on_kill(h,1,6,false)
	if not Q.claim(h,"forest_patrol") or not Q.accept(h,"forest_patrol") or h.quests.forest_patrol.count!=0:
		push_error("Repeatable reset failed");quit(1);return
	print("C3 quest smoke test passed")
	quit(0)
''',encoding="utf-8")
print("C3 v0.16 quests patch complete")
