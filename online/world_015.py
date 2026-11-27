"""C3 0.15: expand the existing landscape and add three PvE zones."""
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

# Use existing GLB terrain and obstacle geometry, not an empty plane.
patch("ford/ground.gd",[
    ("const LIMIT := Vector2(20,14)","const LIMIT := Vector2(40,30)"),
    ("Rect2i(-40,-28,81,57)","Rect2i(-80,-60,161,121)"),
    ("for x in range(-40,41):","for x in range(-80,81):"),
    ("for y in range(-28,29):","for y in range(-60,61):"),
])
(root/"ford/frontier.gd").write_text('''extends RefCounted
const Ground=preload("res://ford/ground.gd")
const Looks=preload("res://ford/looks.gd")
const SPAWNS=[
	[Vector2(23,-8),6,1],[Vector2(26,-12),8,1],[Vector2(31,-8),10,1],
	[Vector2(34,-14),12,1],[Vector2(26,-18),14,1],[Vector2(35,-20),16,1],
	[Vector2(24,8),12,2],[Vector2(29,11),15,2],[Vector2(34,9),18,2],
	[Vector2(27,19),20,2],[Vector2(34,19),22,2],[Vector2(37,24),25,2],
	[Vector2(10,19),20,2],[Vector2(14,22),24,2],[Vector2(17,26),28,2],
	[Vector2(21,26),32,2],[Vector2(23,29),36,2],[Vector2(12,28),40,2]]
const BOSS_POS=Vector2(38,15)
static func sector(p: Vector2) -> String:
	if p.y>=17 and p.x>=5: return "Сланцевый карьер"
	if p.x>=20 and p.y>=3: return "Руины Серого Дозора"
	if p.x>=20 and p.y<3: return "Вересковый лес"
	return "Травяной брод"

static func signpost(root: Node3D,p: Vector2,name_: String,color: Color) -> void:
	var marker:=Node3D.new()
	root.add_child(marker)
	marker.position=Ground.point(p)
	Looks.piece(marker,Vector3(0,.8,0),Vector3(.13,1.6,.13),Color("#8c6845"))
	Looks.piece(marker,Vector3(0,1.42,0),Vector3(1.7,.45,.12),Color("#9a7955"))
	var label:=Label3D.new()
	label.text=name_
	label.font_size=42
	label.pixel_size=.007
	label.position.y=2.0
	label.outline_size=8
	label.modulate=color
	label.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	marker.add_child(label)

static func dress(root: Node3D,nav) -> void:
	for entry in [[Vector2(21,-3),"Вересковый лес · 6–16",Color("#bbdf9f")],[Vector2(22,5),"Серый Дозор · 12–25",Color("#d5c6a9")],[Vector2(10,17),"Карьер · 20–40",Color("#c1d9e8")]]:
		if nav.legal(entry[0]): signpost(root,entry[0],entry[1],entry[2])
	# Ruin fragments and quarry deposits are set outside the walkable paths.
	for p in [Vector2(37,13),Vector2(39,13),Vector2(37,17),Vector2(39,17)]:
		var column:=Node3D.new()
		root.add_child(column)
		column.position=Ground.point(p)
		Looks.piece(column,Vector3(0,.95,0),Vector3(.54,1.9,.54),Color("#777e82"))
		Looks.piece(column,Vector3(0,1.96,0),Vector3(.74,.16,.74),Color("#aaa99a"))
	for p in [Vector2(9,24),Vector2(15,29),Vector2(25,27)]:
		var stone:=Node3D.new()
		root.add_child(stone)
		stone.position=Ground.point(p)
		for j in 3:
			var crystal:=Looks.piece(stone,Vector3(j*.25-.25,.35,0),Vector3(.22,.7+j*.14,.25),Color("#79a5b6"),true)
			crystal.rotation.z=(j-1)*.27
''',encoding="utf-8")
patch("ford/creature.gd",[
("var kind:=0","var kind:=0\nvar elite:=false"),
('label.text="%s · %d\\n%d/%d" % [NAMES[kind],rank,hp,max_hp]','label.text="%s · %d\\n%d/%d" % [display_name(),rank,hp,max_hp]'),
("respawn=12+kind*4;aggro=false","respawn=180.0 if elite else 12.0+kind*4;aggro=false"),
("if respawn>11.5+kind*4:","if respawn>(179.5 if elite else 11.5+kind*4):"),
])
p=root/"ford/creature.gd"
s=p.read_text(encoding="utf-8")+'''
func display_name() -> String:
	return "Страж Серого Дозора · ЭЛИТА" if elite else NAMES[kind]

func make_elite() -> void:
	elite=true
	max_hp*=4
	hp=max_hp
	scale=Vector3.ONE*1.35
	label.position.y=2.9
	label.modulate=Color("#ffd275")
	update_label()
'''
p.write_text(s,encoding="utf-8")
# Larger map keeps radar centered on the actor at higher zoom.
patch("field/radar.gd",[
("else Vector2(40,28)","else Vector2(80,60)"),
("for i in range(-14,14):","for i in range(-30,30):"),
])
patch("ford/world.gd",[
('const Forge=preload("res://field/forge.gd")','const Forge=preload("res://field/forge.gd")\nconst Frontier=preload("res://ford/frontier.gd")'),
('build_trainers()\n\tbuild_merchant()','build_frontier()\n\tbuild_trainers()\n\tbuild_merchant()'),
('Beast.NAMES[mob.kind]','mob.display_name()'),
('Beast.NAMES[target.kind]','target.display_name()'),
('hud.refresh(profile,hp,mp,"Вересковый Град" if town else "Травяной брод")','hud.refresh(profile,hp,mp,"Вересковый Град" if town else Frontier.sector(actor))'),
('var gain := Loot.xp_for(target.kind,target.rank,profile.level())','var gain := Loot.xp_for(target.kind,target.rank,profile.level())*(3 if target.elite else 1)'),
('reward["adena"]=maxi(1,roundi(int(reward.adena)*penalty))','''reward["adena"]=maxi(1,roundi(int(reward.adena)*penalty))
	if target.elite:
		reward["adena"]*=3
		reward.items["enchant_weapon"]=1
		reward.items["crystal"]=int(reward.items.get("crystal",0))+2'''),
])
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")+'''
func build_frontier() -> void:
	Frontier.dress(self,field_ground)
	for entry in Frontier.SPAWNS:
		var p: Vector2=entry[0]
		if not field_ground.legal(p): continue
		var mob:=Beast.new()
		add_child(mob)
		mob.setup(p,int(entry[1]),mobs.size(),int(entry[2]),field_ground)
		mobs.append(mob)
	if field_ground.legal(Frontier.BOSS_POS):
		var boss:=Beast.new()
		add_child(boss)
		boss.setup(Frontier.BOSS_POS,25,mobs.size(),2,field_ground)
		boss.make_elite()
		mobs.append(boss)
'''
p.write_text(s,encoding="utf-8")
(root/"frontier_test.gd").write_text('''extends SceneTree
const Ground=preload("res://ford/ground.gd")
const Frontier=preload("res://ford/frontier.gd")
func _initialize() -> void:
	var nav:=Ground.new()
	var start:=Vector2(-5,1.7)
	for entry in Frontier.SPAWNS:
		var p: Vector2=entry[0]
		if not nav.legal(p) or nav.route(start,p).is_empty():
			push_error("Unreachable frontier spawn "+str(p));quit(1);return
	if not nav.legal(Frontier.BOSS_POS) or nav.route(start,Frontier.BOSS_POS).is_empty() or nav.legal(Vector2(41,0)):
		push_error("Frontier boundary or elite route invalid");quit(1);return
	print("C3 frontier smoke test passed")
	quit(0)
''',encoding="utf-8")
print("C3 v0.15 frontier patch complete")
