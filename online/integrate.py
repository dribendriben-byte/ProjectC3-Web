"""Apply optional v0.10 online adapter AFTER the v0.9.1 Web patch.
Usage: python3 online/integrate.py <Godot project directory>
Requires an actual configured Supabase project; do not deploy before testing.
"""
from pathlib import Path
import sys
root = Path(sys.argv[1])
def replace_once(text, old, new):
    if text.count(old)!=1:
        raise ValueError(f"Expected one match for {old!r}; got {text.count(old)}")
    return text.replace(old,new,1)
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")
s=replace_once(s,'var refresh_time := 0.0','''var refresh_time := 0.0
var online_bridge
var online_character: Dictionary = {}
var online_elapsed := 0.0
var online_save_elapsed := 0.0
var online_avatars: Dictionary = {}
var online_goals: Dictionary = {}''')
s=replace_once(s,'\tprofile.restore()\n','''	if OS.has_feature("web"):
		online_bridge=JavaScriptBridge.get_interface("C3Online")
		if online_bridge!=null:
			var raw=JSON.parse_string(str(online_bridge.character()))
			if raw is Dictionary:
				online_character=raw
	if online_character.is_empty():
		profile.restore()
	else:
		apply_online_profile()
''')
s=replace_once(s,'\tcity_model.hide()\n','''	city_model.hide()
	if not online_character.is_empty():
		town=online_character.get("region","field")=="town"
		ground=city_ground if town else field_ground
		var saved_point:=Vector2(float(online_character.get("x",-5)),float(online_character.get("z",1.7)))
		actor=saved_point if ground.legal(saved_point) else (Vector2(180,34.5) if town else START)
		city_model.visible=town
		hero.position=Ground.point(actor)
''')
s=replace_once(s,'\tadd_child(hud)\n','\tadd_child(hud)\n\thud.radar.town=town\n\tfor pile in piles: pile.visible=not town\n')
s=replace_once(s,'func save_hero() -> void:\n\tif profile.store_character()!=OK: hud.feed.text="Не удалось записать сохранение."','''func save_hero() -> void:
	if not online_character.is_empty():
		send_online_save()
	elif profile.store_character()!=OK:
		hud.feed.text="Не удалось записать сохранение."

func apply_online_profile() -> void:
	var r: String=online_character.get("race","Гном")
	var o: String=online_character.get("discipline","Подгорный боец")
	if not Hero.TREE.has(r) or not Hero.TREE[r].has(o): return
	profile.race=r
	profile.origin=o
	var state=online_character.get("progress",{})
	if not state is Dictionary: return
	var first: String=str(state.get("first",""))
	var second: String=str(state.get("second",""))
	if Hero.TREE[r][o].has(first):
		profile.first=first
		if Hero.TREE[r][o][first].has(second): profile.second=second
	for key in ["total_xp","kills","sp","adena"]:
		profile.set(key,maxi(0,int(state.get(key,1 if key=="total_xp" else 0))))
	profile.total_xp=mini(profile.total_xp,Hero.Experience.START.back())
	for key in ["learned","inventory","equipment"]:
		if state.get(key) is Dictionary: profile.set(key,state[key])
	if state.get("hotbar") is Array: profile.hotbar=state.hotbar
	profile.muted=bool(state.get("muted",false))
	for item in state.get("ground_loot",[]):
		if item is Dictionary and item.get("place") is Array and item.place.size()==2 and item.get("items") is Dictionary:
			var record: Dictionary=item.duplicate(true)
			record.place=Vector2(float(item.place[0]),float(item.place[1]))
			profile.ground_loot.append(record)

func send_online_save() -> void:
	if online_bridge==null or online_character.is_empty() or town_transition: return
	var state: Dictionary={}
	for key in ["first","second","total_xp","kills","sp","adena","learned","inventory","equipment","hotbar","muted"]:
		state[key]=profile.get(key)
	var loot: Array=[]
	for item in profile.ground_loot:
		var record: Dictionary=item.duplicate(true)
		if record.get("place") is Vector2:
			record.place=[record.place.x,record.place.y]
			loot.append(record)
	state.ground_loot=loot
	online_bridge.save(JSON.stringify(state),"town" if town else "field",actor.x,actor.y)

func online_process(dt: float) -> void:
	if online_character.is_empty() or online_bridge==null: return
	if bool(online_bridge.blocked()):
		get_tree().paused=true
		return
	online_elapsed+=dt
	online_save_elapsed+=dt
	if online_save_elapsed>=12.0:
		online_save_elapsed=0.0
		send_online_save()
	if online_elapsed>=2.0:
		online_elapsed=0.0
		if not town_transition: online_bridge.tick("town" if town else "field",actor.x,actor.y,wrapf(heading,-PI,PI))
		var peers=JSON.parse_string(str(online_bridge.peers()))
		var seen: Dictionary={}
		if peers is Array:
			for row in peers:
				if not row is Dictionary: continue
				var id: String=str(row.get("id",""))
				if id.is_empty(): continue
				var point:=Vector2(float(row.get("x",0)),float(row.get("z",0)))
				if (point.x>100)!=town: continue
				seen[id]=true
				if not online_avatars.has(id):
					var avatar:=preload("res://ford/models/warden.glb").instantiate() as Node3D
					add_child(avatar)
					avatar.position=Ground.point(point)
					var tag:=Label3D.new()
					tag.text=str(row.get("name",""))
					tag.position=Vector3(0,2.05,0)
					tag.font_size=40
					tag.pixel_size=.008
					tag.billboard=BaseMaterial3D.BILLBOARD_ENABLED
					tag.modulate=Color("#a4ecff")
					tag.outline_size=6
					avatar.add_child(tag)
					online_avatars[id]=avatar
				online_goals[id]=Ground.point(point)
				online_avatars[id].rotation.y=float(row.get("heading",0))
		for id in online_avatars.keys():
			if not seen.has(id):
				online_avatars[id].queue_free()
				online_avatars.erase(id)
				online_goals.erase(id)
	for id in online_avatars:
		var avatar: Node3D=online_avatars[id]
		var destination: Vector3=online_goals[id]
		avatar.position=avatar.position.lerp(destination,1.0-exp(-5.0*dt))
''')
s=replace_once(s,'func _process(dt: float) -> void:\n\tif not is_node_ready() or hud.shade.visible or town_transition: return','''func _process(dt: float) -> void:
	if not is_node_ready(): return
	online_process(dt)
	if hud.shade.visible or town_transition: return''')
p.write_text(s,encoding="utf-8")
# HTML must load config and bridge before the existing main game handler.
p=root/"web/shell.html"
s=p.read_text(encoding="utf-8")
s=replace_once(s,'<script src="$GODOT_URL"></script>','''<script src="c3-config.js"></script>
<script src="c3-online.js"></script>
<script src="$GODOT_URL"></script>''')
s=replace_once(s,'PRE-ALPHA 0.9.1 · SINGLE PLAYER','PRE-ALPHA 0.10 · ONLINE TEST / OFFLINE')
p.write_text(s,encoding="utf-8")
print("Online adapter applied")


# v0.10.1: settings and reliable explicit exit handshake with browser.
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")
s=replace_once(s,'var online_bridge\n','var online_bridge\nvar menu_callback\n')
s=replace_once(s,'\tapply_quality(2)\n','''	apply_quality(2)
	if online_bridge!=null:
		menu_callback=JavaScriptBridge.create_callback(web_menu_command)
		online_bridge.attachMenu(menu_callback,profile.muted,quality_level)
''')
s=replace_once(s,'\tonline_process(dt)\n\tif hud.shade.visible or town_transition: return','''	online_process(dt)
	if web_menu_open() or hud.shade.visible or town_transition: return''')
s=replace_once(s,'func _input(e: InputEvent) -> void:\n\tif not is_node_ready(): return','''func _input(e: InputEvent) -> void:
	if not is_node_ready(): return
	if web_menu_open():
		finger=-1
		pinch_finger=-1
		right_drag=false
		turning=0
		get_viewport().set_input_as_handled()
		return''')
s=replace_once(s,'func _unhandled_input(e: InputEvent) -> void:\n\tif not is_node_ready() or hud.shade.visible or town_transition: return','''func _unhandled_input(e: InputEvent) -> void:
	if not is_node_ready() or web_menu_open() or hud.shade.visible or town_transition: return''')
s=replace_once(s,'func _physics_process(dt: float) -> void:\n\tif hud.shade.visible or town_transition: return','''func _physics_process(dt: float) -> void:
	if web_menu_open() or hud.shade.visible or town_transition: return''')
s+='''
func web_menu_open() -> bool:
	return online_bridge!=null and bool(online_bridge.menuOpen())

func web_menu_command(args: Array) -> void:
	if args.is_empty() or online_bridge==null: return
	var command: String=str(args[0])
	match command:
		"save":
			if town_transition:
				online_bridge.menuAck(false,"Дождись завершения перехода между локациями.")
			elif not online_character.is_empty():
				if bool(online_bridge.blocked()):
					online_bridge.menuAck(false,"Доступ к персонажу прекращён.")
				else:
					send_online_save()
					online_bridge.menuAck(true,"")
			else:
				var result: int=profile.store_character()
				online_bridge.menuAck(result==OK,"Не удалось сохранить локальный прогресс." if result!=OK else "")
		"sound":
			if args.size()<2: return
			profile.muted=bool(args[1])
			sound.set_muted(profile.muted)
			update_sound_button()
			save_hero()
		"quality":
			if args.size()<2: return
			apply_quality(clampi(int(args[1]),0,2))
'''
p.write_text(s,encoding="utf-8")
p=root/"web/shell.html"
s=p.read_text(encoding="utf-8")
s=replace_once(s,'PRE-ALPHA 0.10 · ONLINE TEST / OFFLINE','PRE-ALPHA 0.10.1 · ONLINE TEST / OFFLINE')
p.write_text(s,encoding="utf-8")
