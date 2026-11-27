"""C3 0.18: display shared server targets in the 3D scene.
Apply after the existing gameplay patches. No local reward or enemy AI path is used.
"""
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

(root/"ford/raid_view.gd").write_text('''extends Node3D
const Ground=preload("res://ford/ground.gd")
const Stage=preload("res://ford/stage.gd")
const Model=preload("res://ford/models/rootling.glb")
var world
var bridge
var actors: Dictionary={}
var data: Dictionary={}
var ring: MeshInstance3D
var selected:=0
var auto_attack:=false
var next_hit:=0.0
var last_serial:=0

func configure(parent) -> void:
	world=parent
	if OS.has_feature("web"): bridge=JavaScriptBridge.get_interface("C3Raid")

func _ready() -> void:
	ring=Stage.ring(self,1.05,Color("#9cdbfc"))
	set_process(bridge!=null)

func reset_selection() -> void:
	selected=0
	auto_attack=false
	if ring!=null: ring.hide()

func create_target(row: Dictionary) -> void:
	var id:=int(row.id)
	var base:=Node3D.new()
	add_child(base)
	base.position=Ground.point(Vector2(float(row.x),float(row.z)))
	var model:=Model.instantiate() as Node3D
	base.add_child(model)
	model.scale=Vector3.ONE*(1.55 if id==2 else 1.2)
	var mark:=Label3D.new()
	mark.name="RaidTag"
	mark.position.y=2.7
	mark.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	mark.font_size=42
	mark.pixel_size=.007
	mark.outline_size=8
	mark.modulate=Color("#b0e1ff")
	base.add_child(mark)
	actors[id]=base

func _process(dt: float) -> void:
	if bridge==null: return
	next_hit=maxf(0,next_hit-dt)
	if world.town or world.town_transition or world.death_wait>0 or not bool(bridge.ready()):
		reset_selection()
		hide()
		return
	show()
	var packet=JSON.parse_string(str(bridge.snapshot()))
	if not packet is Dictionary: return
	var rows=packet.get("mobs",[])
	if not rows is Array: return
	for raw in rows:
		if not raw is Dictionary: continue
		var row: Dictionary=raw
		var id:=int(row.id)
		if not actors.has(id): create_target(row)
		data[id]=row
		var base: Node3D=actors[id]
		base.visible=int(row.hp)>0
		var tag: Label3D=base.get_node("RaidTag")
		tag.text="%s · ОБЩАЯ ЦЕЛЬ\\n%d / %d HP" % [row.name,row.hp,row.max_hp]
	var event=JSON.parse_string(str(bridge.event()))
	if event is Dictionary and int(event.get("serial",0))>last_serial:
		last_serial=int(event.serial)
		if event.has("error"):
			if selected==int(event.mob):
				world.hud.feed.text="Рейд · "+str(event.error)
				if str(event.error) in ["Target respawning","Character unavailable"]: reset_selection()
		elif actors.has(int(event.mob)):
			var victim: Node3D=actors[int(event.mob)]
			world.swing=.38
			world.sound.effect("hit")
			world.contact(victim.position+Vector3.UP*.77,"hit")
			world.float_word(victim.position,"−%d" % int(event.damage),Color("#c8e8ff"))
			if bool(event.kill):
				world.hud.feed.text="Общая победа · +%d рейдового EXP · +%d жетонов" % [event.xp,event.tokens]
				reset_selection()
	if selected==0 or not data.has(selected): return
	var info: Dictionary=data[selected]
	if int(info.hp)<=0:
		reset_selection()
		return
	var current: Node3D=actors[selected]
	ring.position=current.position+Vector3.UP*.08
	ring.show()
	world.hud.target_name.text="%s · %d/%d HP" % [info.name,info.hp,info.max_hp]
	world.hud.autoattack.modulate=Color("#a3e6ff") if auto_attack else Color.WHITE
	if world.web_menu_open() or world.hud.shade.visible:
		auto_attack=false
		return
	if auto_attack and next_hit<=0 and not bool(bridge.busy()):
		var spot:=Vector2(float(info.x),float(info.z))
		var player: Vector2=world.actor
		if player.distance_to(spot)<=2.7:
			var direction:=spot-player
			world.heading=atan2(direction.x,direction.y)
			bridge.hit(selected)
			next_hit=1.65

func try_select(screen: Vector2) -> bool:
	if not visible or world.town or bridge==null or not bool(bridge.ready()): return false
	var nearest:=INF
	var found:=0
	for id in actors:
		var mob: Node3D=actors[id]
		if not mob.visible or world.cam.is_position_behind(mob.position): continue
		var head: Vector2=world.cam.unproject_position(mob.position+Vector3.UP*2.0)
		var foot: Vector2=world.cam.unproject_position(mob.position)
		var width:=maxf(20,head.distance_to(foot)*.55)
		var distance:=screen.distance_to((head+foot)*.5)
		if distance<width and distance<nearest:
			nearest=distance
			found=int(id)
	if found==0: return false
	world.clear_target()
	var spot:=Vector2(float(data[found].x),float(data[found].z))
	var player: Vector2=world.actor
	if player.distance_to(spot)>2.7:
		var point:=spot+(player-spot).normalized()*2.2
		if not world.ground.legal(point): point=spot
		world.walk_to(point)
	selected=found
	world.hud.feed.text="Общая цель · нажми автоатаку. Награды на серверном рейдовом счёте."
	return true

func toggle() -> bool:
	if selected==0: return false
	if world.web_menu_open() or world.hud.shade.visible or world.death_wait>0: return true
	auto_attack=not auto_attack
	if auto_attack:
		next_hit=0
		world.hud.feed.text="Рейдовая автоатака · серверный бой"
	else:
		world.hud.feed.text="Рейдовая автоатака остановлена"
	return true
''',encoding="utf-8")
patch("ford/world.gd",[
('var online_bridge\n','var online_bridge\nvar raid_view\n'),
('\nfunc update_sound_button() -> void:','''	if not online_character.is_empty() and OS.has_feature("web"):
		raid_view=preload("res://ford/raid_view.gd").new()
		raid_view.configure(self)
		add_child(raid_view)

func update_sound_button() -> void:'''),
('func select_screen(screen: Vector2) -> void:\n','func select_screen(screen: Vector2) -> void:\n\tif raid_view!=null and raid_view.try_select(screen): return\n'),
('func clear_target() -> void:\n','func clear_target() -> void:\n\tif raid_view!=null: raid_view.reset_selection()\n'),
('func toggle_autoattack() -> void:\n','func toggle_autoattack() -> void:\n\tif raid_view!=null and raid_view.toggle(): return\n'),
])
patch("project.godot",[('config/version="0.17.0"','config/version="0.18.0"')])
patch("web/shell.html",[
('PRE-ALPHA 0.17 · ONLINE TEST / OFFLINE','PRE-ALPHA 0.18 · ONLINE TEST / OFFLINE'),
('c3-config-0170.js','c3-config-0180.js'),
('c3-online-0170.js','c3-online-0180.js'),
])
# Verify the shared targets fit existing collision geometry even on the original map.
(root/"raid_navigation_test.gd").write_text('''extends SceneTree
const Ground=preload("res://ford/ground.gd")
func _initialize() -> void:
	var nav:=Ground.new()
	for p in [Vector2(-9,3),Vector2(-13,6)]:
		if not nav.legal(p) or nav.route(Vector2(-5,1.7),p).is_empty():
			push_error("Shared target not reachable: "+str(p))
			quit(1)
			return
	print("C3 raid navigation smoke test passed")
	quit(0)
''',encoding="utf-8")
print("C3 0.18 raid client patch complete")
