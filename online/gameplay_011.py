from pathlib import Path
import sys
root=Path(sys.argv[1])
def patch(file, pairs):
    p=root/file
    s=p.read_text(encoding="utf-8")
    for a,b in pairs:
        if s.count(a)!=1:
            raise RuntimeError(f"{file}: expected one occurrence, got {s.count(a)}: {a[:110]!r}")
        s=s.replace(a,b,1)
    p.write_text(s,encoding="utf-8")
    print("C3 0.11 patched",file)

# Ten slots: migrate old bars without deleting learned skills/items.
(root/"field/actions.gd").write_text('''extends RefCounted
const Loot=preload("res://field/loot.gd")
static func build(book: Array[Dictionary]) -> Dictionary:
	var entries: Dictionary={}
	for i in book.size():
		var record := book[i].duplicate()
		record["index"]=i
		entries["spell/"+str(record.name)]=record
	for id in Loot.ITEMS:
		var item: Array=Loot.ITEMS[id]
		entries["item/"+id]={"name":item[0],"effect":id,"item":id,"description":"Предмет из инвентаря"}
	return entries

static func initial() -> Array:
	return ["","","","","","","","","",""]

static func normalize(saved: Variant, entries: Dictionary, hero) -> Array:
	var result := initial()
	if not saved is Array: return result
	for i in mini(10,saved.size()):
		var id: Variant=saved[i]
		if id is String and entries.has(id) and not result.has(id):
			var rec: Dictionary=entries[id]
			if not rec.has("index") or hero.knows(rec): result[i]=id
	return result
''',encoding="utf-8")
patch("field/skill_button.gd",[
('Rect2(177+index*88,453,78,75)','Rect2(144+index*64,466,60,60)'),
('var image_r:=Rect2(r.get_center()-Vector2(26,29),Vector2(52,52))','var image_r:=Rect2(r.get_center()-Vector2(21,22),Vector2(42,42))'),
('Vector2(52,52*clampf','Vector2(42,42*clampf'),
('''	else:
		var c := r.get_center()
		var d := Vector2(7,0)
		var diamond := PackedVector2Array([c-d,c-Vector2(0,7),c+d,c+Vector2(0,7),c-d])
		canvas.draw_polyline(diamond,Color("#56675c"),1.5,true)''',''),
('str(number),HORIZONTAL_ALIGNMENT_LEFT','str(number%10),HORIZONTAL_ALIGNMENT_LEFT'),
])
patch("field/careers.gd",[
('return sk.level==1 or learned.has(sk.name)','return learned.has(sk.name)'),
])
patch("field/spellbook.gd",[
('var status:=""','var status:=""\nvar training:=false'),
('func present(profile, entries: Dictionary) -> void:','func present(profile, entries: Dictionary, at_trainer: bool=false) -> void:\n\ttraining=at_trainer'),
('for i in 7:\n\t\tif Slot.bar_rect','for i in 10:\n\t\tif Slot.bar_rect'),
('elif hero.level()>=rec.level and hero.sp>=rec.sp:','elif training and hero.level()>=rec.level and hero.sp>=rec.sp:'),
('"Книга умений",27,PAPER','"Мастер класса" if training else "Книга умений",27,PAPER'),
('elif not available: words(r.position+Vector2(66,49),"Изучить",12,MUTED)','elif not available: words(r.position+Vector2(66,49),"Изучить" if training else "У мастера",12,MUTED)'),
('elif not allowed(chosen): action_text="Ур. %d · %d SP" % [sk.level,sk.sp] if hero.level()<sk.level else "Изучить · %d SP" % sk.sp','elif not allowed(chosen): action_text=("Ур. %d · %d SP" % [sk.level,sk.sp] if hero.level()<sk.level else "Изучить · %d SP" % sk.sp) if training else "Только у мастера"'),
('Rect2(159,413,641,121)','Rect2(130,413,660,121)'),
('for i in 7:\n\t\tvar rec: Dictionary=catalog.get','for i in 10:\n\t\tvar rec: Dictionary=catalog.get'),
('Slot.paint(self,Slot.bar_rect(i),i+1,rec','Slot.paint(self,Slot.bar_rect(i),i+1,rec'),
] if False else [
('var status:=""','var status:=""\nvar training:=false'),
('func present(profile, entries: Dictionary) -> void:','func present(profile, entries: Dictionary, at_trainer: bool=false) -> void:\n\ttraining=at_trainer'),
('for i in 7:\n\t\tif Slot.bar_rect','for i in 10:\n\t\tif Slot.bar_rect'),
('elif hero.level()>=rec.level and hero.sp>=rec.sp:','elif training and hero.level()>=rec.level and hero.sp>=rec.sp:'),
('"Книга умений",27,PAPER','"Мастер класса" if training else "Книга умений",27,PAPER'),
('elif not available: words(r.position+Vector2(66,49),"Изучить",12,MUTED)','elif not available: words(r.position+Vector2(66,49),"Изучить" if training else "У мастера",12,MUTED)'),
('elif not allowed(chosen): action_text="Ур. %d · %d SP" % [sk.level,sk.sp] if hero.level()<sk.level else "Изучить · %d SP" % sk.sp','elif not allowed(chosen): action_text=("Ур. %d · %d SP" % [sk.level,sk.sp] if hero.level()<sk.level else "Изучить · %d SP" % sk.sp) if training else "Только у мастера"'),
('Rect2(159,413,641,121)','Rect2(130,413,660,121)'),
('for i in 7:\n\t\tvar rec: Dictionary=catalog.get','for i in 10:\n\t\tvar rec: Dictionary=catalog.get'),
])
# Item drag from bag directly to the real, adaptively placed slots.
patch("field/floating_panel.gd",[
('signal equip(id: String)','signal equip(id: String)\nsignal hotbar_drop(id: String, point: Vector2)'),
('elif drag_item!="" and peer.visible and peer.get_rect().has_point(world):','elif drag_item!="" and peer.visible and peer.get_rect().has_point(world):'),
('''							if SLOTS[i]==slot and peer.gear_cell(i).has_point(world-peer.position): equip.emit(drag_item)
			pointer=-99''','''							if SLOTS[i]==slot and peer.gear_cell(i).has_point(world-peer.position): equip.emit(drag_item)
				elif drag_item!="" and not dragging:
					hotbar_drop.emit(drag_item,world)
			pointer=-99'''),
])
patch("field/hud.gd",[
('signal skill_pressed(slot: int)','signal skill_pressed(slot: int)\nsignal item_assigned(id: String, slot: int)\nsignal autoattack_requested\nsignal pickup_requested\nsignal target_requested\nsignal trainer_requested'),
('var gateway: Button','var gateway: Button\nvar autoattack: Button\nvar pickup_button: Button\nvar target_button: Button\nvar trainer_button: Button'),
('for i in 7:\n\t\tvar key := SkillButton.new()','for i in 10:\n\t\tvar key := SkillButton.new()'),
('''		slots.append(key)
	var names''','''		slots.append(key)
	autoattack=icon_button("hit","Автоатака")
	place(ui,autoattack,Rect2(866,462,76,66))
	autoattack.pressed.connect(func(): autoattack_requested.emit())
	pickup_button=icon_button("pickup","Подобрать добычу")
	place(ui,pickup_button,Rect2(804,468,54,54))
	pickup_button.pressed.connect(func(): pickup_requested.emit())
	target_button=icon_button("cycle","Следующая цель")
	place(ui,target_button,Rect2(866,205,54,54))
	target_button.pressed.connect(func(): target_requested.emit())
	trainer_button=button("Мастер класса · изучить")
	place(ui,trainer_button,Rect2(650,315,295,47))
	trainer_button.hide()
	trainer_button.pressed.connect(func(): trainer_requested.emit())
	var names'''),
('bag.peer=sheet','bag.hotbar_drop.connect(func(id,point):\n\t\tvar slot:=bar_at(point)\n\t\tif slot>=0: item_assigned.emit(id,slot))\n\tbag.peer=sheet'),
('gateway.position = Vector2(650 + extra.x,372 + extra.y)','''gateway.position = Vector2(650 + extra.x,372 + extra.y)
	autoattack.position=Vector2(866+extra.x,462+extra.y)
	pickup_button.position=Vector2(804+extra.x,468+extra.y)
	target_button.position=Vector2(866+extra.x,205)
	trainer_button.position=Vector2(650+extra.x,315+extra.y)'''),
('func show_book(hero: Careers, catalog: Dictionary) -> void:','func show_book(hero: Careers, catalog: Dictionary, training: bool=false) -> void:'),
('book_editor.present(hero,catalog)','book_editor.present(hero,catalog,training)'),
])
# Radar zoom is centered on hero and clipped to the map, never the game camera.
(root/"field/radar.gd").write_text('''extends Control
const Ground=preload("res://ford/ground.gd")
var town:=false
var player:=Vector2.ZERO
var creatures:=PackedVector2Array()
var hostile:=PackedVector2Array()
var zoom:=1.0

func change_zoom(direction: float) -> void:
	zoom=clampf(zoom*pow(1.35,direction),1.0,4.0)
	queue_redraw()

func mapped(p: Vector2) -> Vector2:
	var center:=Vector2(180,0) if town else Vector2.ZERO
	var extent:=Vector2(94,80) if town else Vector2(40,28)
	if zoom>1.01:
		var span:=extent/(2.0*zoom)
		center=player.clamp(center-extent*.5+span,center+extent*.5-span)
	return ((p-center)/extent*zoom+Vector2(.5,.5))*size

func segment(a: Vector2,b: Vector2,tint: Color,width: float) -> void:
	var p:=mapped(a)
	var q:=mapped(b)
	var rect:=Rect2(Vector2(2,2),size-Vector2(4,4))
	var points: Array[Vector2]=[]
	if rect.has_point(p): points.append(p)
	if rect.has_point(q): points.append(q)
	var corners: Array[Vector2]=[rect.position,Vector2(rect.end.x,rect.position.y),rect.end,Vector2(rect.position.x,rect.end.y)]
	for i in 4:
		var hit=Geometry2D.segment_intersects_segment(p,q,corners[i],corners[(i+1)%4])
		if hit is Vector2: points.append(hit)
	if points.size()>=2: draw_line(points[0],points[1],tint,width,true)

func dot(p: Vector2,r: float,c: Color) -> void:
	var m:=mapped(p)
	if Rect2(Vector2(r,r),size-Vector2(r*2,r*2)).has_point(m): draw_circle(m,r,c)

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO,size),Color("#526348"))
	if town:
		for x in [-33,-18,0,18,33]: segment(Vector2(180+x,-38),Vector2(180+x,38),Color("#b9a880"),2)
		for z in [-21,3,17,30]: segment(Vector2(135,z),Vector2(225,z),Color("#b9a880"),2)
		dot(Vector2(180,2),3,Color("#85b9ba"))
		dot(Vector2(180,37),3,Color("#eac784"))
	else:
		for i in range(-14,14):
			segment(Vector2(Ground.river(i),i),Vector2(Ground.river(i+1),i+1),Color("#739fa2"),minf(8*zoom,12))
		segment(Vector2(-3,0),Vector2(3,0),Color("#ccad75"),4)
		for p in creatures: dot(p,2,Color("#e6b479"))
		for p in hostile: dot(p,2.4,Color("#f08270"))
	dot(player,3.4,Color("#fff0b3"))
	draw_rect(Rect2(Vector2.ZERO,size),Color("#aaab83"),false,1)
''',encoding="utf-8")
# Low-poly race silhouettes using original rig and additional original geometry.
(root/"ford/looks.gd").write_text('''extends RefCounted
static func piece(parent: Node3D, at: Vector3, extent: Vector3, tint: Color, ball: bool=false) -> MeshInstance3D:
	var mesh: PrimitiveMesh
	if ball:
		var sphere:=SphereMesh.new()
		sphere.radius=.5
		sphere.height=1.0
		sphere.radial_segments=8
		sphere.rings=4
		mesh=sphere
	else:
		var cube:=BoxMesh.new()
		cube.size=Vector3.ONE
		mesh=cube
	var mat:=StandardMaterial3D.new()
	mat.albedo_color=tint
	mat.roughness=1.0
	mesh.material=mat
	var part:=MeshInstance3D.new()
	part.mesh=mesh
	parent.add_child(part)
	part.position=at
	part.scale=extent
	return part

static func taper(parent: Node3D, at: Vector3, top: float, bottom: float, height: float, tint: Color, depth: float=1.0) -> MeshInstance3D:
	var mesh:=CylinderMesh.new()
	mesh.top_radius=top
	mesh.bottom_radius=bottom
	mesh.height=height
	mesh.radial_segments=8
	var material:=StandardMaterial3D.new()
	material.albedo_color=tint
	material.roughness=1.0
	mesh.material=material
	var part:=MeshInstance3D.new()
	part.mesh=mesh
	parent.add_child(part)
	part.position=at
	part.scale.z=depth
	return part

static func layer(parent: Node3D, tag: String) -> Node3D:
	var old:=parent.get_node_or_null(tag)
	if old!=null:
		parent.remove_child(old)
		old.queue_free()
	if parent is MeshInstance3D: parent.mesh=null
	var result:=Node3D.new()
	result.name=tag
	parent.add_child(result)
	return result

static func fit(model: Node3D,race: String,gender: String,style: int=0) -> void:
	var body:=model.find_child("Body",true,false) as Node3D
	if body==null: return
	var detail:=layer(body,"RaceDetails")
	var proportions: Dictionary={"Человек":Vector3(.92,1.12,.91),"Эльф":Vector3(.77,1.22,.81),"Тёмный эльф":Vector3(.82,1.18,.83),"Орк":Vector3(1.23,1.20,1.16),"Гном":Vector3(1.08,.85,1.05)}
	var skins: Dictionary={"Человек":Color("#d6aa83"),"Эльф":Color("#e2bea1"),"Тёмный эльф":Color("#8c7c9e"),"Орк":Color("#819069"),"Гном":Color("#c79a77")}
	var outfits: Dictionary={"Человек":Color("#42637a"),"Эльф":Color("#526f4c"),"Тёмный эльф":Color("#504361"),"Орк":Color("#80543d"),"Гном":Color("#936c3f")}
	var trim: Color=Color("#b9aa89")
	var skin: Color=skins.get(race,skins["Человек"])
	var cloth: Color=outfits.get(race,outfits["Человек"])
	cloth=cloth.lightened(float(clampi(style,0,3))*.055)
	var leather:=Color("#513a2e")
	var hair_colors: Array[Color]=[Color("#46302b"),Color("#c1a06e"),Color("#8c4b35"),Color("#d4d2c9")]
	var hair: Color=hair_colors[clampi(style,0,3)]
	if race=="Тёмный эльф": hair=hair.lightened(.3)
	var female:=gender=="female"
	model.scale=proportions.get(race,Vector3.ONE)
	if female: model.scale*=Vector3(.91,1.02,.92)
	# Torso, layered cloth, belt and shoulders. The original joints remain animated.
	taper(detail,Vector3(0,1.15,0),.37,.28,.61,cloth,.72)
	taper(detail,Vector3(0,.88,0),.27,.39,.27,cloth.darkened(.13),.79)
	taper(detail,Vector3(0,.98,0),.30,.30,.095,leather,.8)
	piece(detail,Vector3(0,.98,.25),Vector3(.12,.10,.045),trim)
	piece(detail,Vector3(0,1.25,.25),Vector3(.07,.34,.045),trim.darkened(.12))
	for side in [-1,1]:
		var lapel:=piece(detail,Vector3(side*.15,1.39,.22),Vector3(.10,.24,.055),trim)
		lapel.rotation.z=side*.50
		piece(detail,Vector3(side*.32,1.42,.01),Vector3(.27,.20,.38),cloth.lightened(.18),true)
	# The skirt panels move with the torso, leaving boots/feet separately articulated.
	if female:
		taper(detail,Vector3(0,.76,0),.28,.43,.43,cloth,.82)
		piece(detail,Vector3(0,.64,-.29),Vector3(.64,.37,.075),cloth.darkened(.15))
	else:
		piece(detail,Vector3(0,.86,.27),Vector3(.25,.30,.09),cloth.darkened(.12))
	if race in ["Эльф","Тёмный эльф"]:
		piece(detail,Vector3(0,1.13,-.29),Vector3(.58,.68,.09),cloth.darkened(.20))
	elif race=="Орк":
		for side in [-1,1]:
			piece(detail,Vector3(side*.33,1.43,.04),Vector3(.32,.23,.41),Color("#8c7761"),true)
	# Bare, expressive head; no shared helmet.
	taper(detail,Vector3(0,1.51,0),.12,.15,.17,skin,.94)
	piece(detail,Vector3(0,1.77,.015),Vector3(.45,.51,.44),skin,true)
	piece(detail,Vector3(0,1.69,.06),Vector3(.33,.25,.35),skin,true)
	piece(detail,Vector3(0,1.75,.237),Vector3(.08,.11,.08),skin.lightened(.06),true)
	for side in [-1,1]:
		piece(detail,Vector3(side*.106,1.81,.215),Vector3(.087,.043,.033),Color("#eee5d4"),true)
		piece(detail,Vector3(side*.106,1.81,.239),Vector3(.039,.039,.018),Color("#394745"),true)
		var brow:=piece(detail,Vector3(side*.109,1.864,.212),Vector3(.103,.024,.027),hair)
		brow.rotation.z=side*.10
		var ear:=piece(detail,Vector3(side*(.29 if race in ["Эльф","Тёмный эльф"] else .22),1.80,.0),Vector3(.14,.31,.12) if race in ["Эльф","Тёмный эльф"] else Vector3(.10,.15,.10),skin,true)
		if race in ["Эльф","Тёмный эльф"]: ear.rotation.z=-side*.64
	piece(detail,Vector3(0,1.67,.218),Vector3(.11,.022,.025),skin.darkened(.30))
	piece(detail,Vector3(0,1.975,-.01),Vector3(.48,.22,.46),hair,true)
	piece(detail,Vector3(0,1.84,-.16),Vector3(.44,.38,.20),hair,true)
	if female or race in ["Эльф","Тёмный эльф"]:
		for side in [-1,1]:
			piece(detail,Vector3(side*.19,1.67,-.11),Vector3(.14,.53,.24),hair,true)
		piece(detail,Vector3(0,1.49,-.25),Vector3(.46,.69,.19),hair,true)
	elif style%2==1:
		var lock:=piece(detail,Vector3(-.14,1.96,.13),Vector3(.20,.20,.25),hair,true)
		lock.rotation.z=.35
	if race=="Гном" and not female:
		piece(detail,Vector3(0,1.59,.18),Vector3(.34,.36,.25),hair,true)
		piece(detail,Vector3(0,1.70,.23),Vector3(.31,.09,.11),hair,true)
	elif race=="Орк":
		for side in [-1,1]:
			var tusk:=taper(detail,Vector3(side*.12,1.69,.225),0.012,.045,.15,Color("#eee0b9"),.8)
			tusk.rotation.z=-side*.12
	# Separate meshes on the existing four animation pivots.
	for side in ["LegL","LegR","ArmL","ArmR"]:
		var joint:=model.find_child(side,true,false) as Node3D
		if joint==null: continue
		var gear:=layer(joint,"RaceSkin")
		if side.begins_with("Leg"):
			taper(gear,Vector3(0,-.20,0),.14,.11,.40,cloth.darkened(.24),.83)
			taper(gear,Vector3(0,-.56,.015),.12,.14,.33,leather,.95)
			piece(gear,Vector3(0,-.735,.07),Vector3(.29,.15,.37),leather,true)
			piece(gear,Vector3(0,-.42,.13),Vector3(.22,.07,.07),trim.darkened(.28))
		else:
			taper(gear,Vector3(0,-.15,0),.125,.105,.30,cloth,.91)
			taper(gear,Vector3(0,-.40,0),.10,.09,.22,skin,.88)
			piece(gear,Vector3(0,-.53,.015),Vector3(.19,.20,.19),skin,true)
			if not female or race=="Орк":
				taper(gear,Vector3(0,-.33,0),.115,.115,.15,leather,.95)
''',encoding="utf-8")
# Use actual 3D models with distinct silhouettes for three enemy families.
(root/"ford/creature.gd").write_text('''extends Node3D
const MODEL=preload("res://ford/models/rootling.glb")
const Ground=preload("res://ford/ground.gd")
const Looks=preload("res://ford/looks.gd")
const NAMES:=["Корневик","Вересковый волк","Сланцевик"]
var kind:=0
var rank:=1
var hp:=33
var max_hp:=33
var home:=Vector2.ZERO
var spoiled:=false
var stun:=0.0
var respawn:=0.0
var phase:=0.0
var cycle:=0.0
var swing:=0.0
var hit_flash:=0.0
var aggro:=false
var hostile:=false
var attack_timer:=0.0
var limbs: Array[Node3D]=[]
var contacts: Array[Vector3]=[]
var torso: Node3D
var label: Label3D
var navigation

func setup(p: Vector2,level: int,index: int,species: int=0,nav=null) -> void:
	home=p
	rank=level
	kind=species
	navigation=nav
	hostile=kind!=0
	max_hp=26+level*7+kind*12
	hp=max_hp
	phase=index*1.71
	position=Ground.point(p)
	if kind==0:
		var model:=MODEL.instantiate()
		add_child(model)
		torso=model.find_child("Body",true,false)
		for name_ in ["FrontL","FrontR","BackL","BackR"]:
			limbs.append(model.find_child(name_,true,false))
	else:
		torso=Node3D.new()
		add_child(torso)
		var color:=Color("#8b8578") if kind==1 else Color("#747c89")
		if kind==1:
			Looks.piece(torso,Vector3(0,.65,0),Vector3(.65,.61,1.24),color,true)
			Looks.piece(torso,Vector3(0,.84,.64),Vector3(.48,.52,.57),color.lightened(.12),true)
			Looks.piece(torso,Vector3(0,.72,.95),Vector3(.35,.25,.38),Color("#4f4944"),true)
			for side in [-1,1]:
				var ear:=Looks.piece(torso,Vector3(side*.17,1.13,.61),Vector3(.16,.29,.15),color.darkened(.2))
				ear.rotation.z=-side*.23
				Looks.piece(torso,Vector3(side*.15,.9,.86),Vector3(.07,.07,.07),Color("#efbd62"),true)
			var tail:=Looks.piece(torso,Vector3(0,.82,-.75),Vector3(.16,.16,.65),color.darkened(.15),true)
			tail.rotation.x=.45
		else:
			Looks.piece(torso,Vector3(0,.97,0),Vector3(.95,.91,.69),color,true)
			Looks.piece(torso,Vector3(0,1.56,.02),Vector3(.61,.55,.55),color.lightened(.12),true)
			for side in [-1,1]: Looks.piece(torso,Vector3(side*.14,1.59,.27),Vector3(.10,.08,.08),Color("#f0af57"))
			Looks.piece(torso,Vector3(0,1.0,.37),Vector3(.17,.24,.08),Color("#dfa65a"),true)
		for i in 4:
			var limb:=Node3D.new()
			torso.add_child(limb)
			limb.position=Vector3((-.29 if i%2==0 else .29)*(1.6 if kind==2 and i<2 else 1.0),.55 if kind==1 or i>=2 else 1.18,.39 if i<2 and kind==1 else (-.39 if kind==1 else 0.0))
			Looks.piece(limb,Vector3(0,-.25,0),Vector3(.17,.54,.19) if kind==1 else Vector3(.38,.60,.36),color)
			limbs.append(limb)
	for limb in limbs: contacts.append(limb.position)
	label=Label3D.new()
	label.position.y=1.8 if kind!=2 else 2.15
	label.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size=35
	label.pixel_size=.007
	label.outline_size=7
	label.modulate=Color("#f29b84") if hostile else Color("#f0dfb7")
	add_child(label)
	update_label()

func update_label() -> void:
	label.text="%s · %d\\n%d/%d" % [NAMES[kind],rank,hp,max_hp]

func flat() -> Vector2:
	return Vector2(position.x,position.z)

func tick(dt: float,engaged: bool,player: Vector2) -> void:
	if hp<=0:
		respawn-=dt
		if respawn<=0:
			hp=max_hp;spoiled=false;stun=0;aggro=false;attack_timer=0;position=Ground.point(home);update_label();show()
		return
	var previous:=flat()
	phase+=dt
	stun=maxf(0,stun-dt)
	swing=maxf(0,swing-dt)
	hit_flash=maxf(0,hit_flash-dt)
	attack_timer=maxf(0,attack_timer-dt)
	if (engaged or (hostile and previous.distance_to(player)<3.2)) and home.distance_to(player)<8: aggro=true
	if aggro and home.distance_to(player)>9.0: aggro=false;hp=max_hp;spoiled=false;update_label()
	var goal:=home+Vector2(.72*cos(phase*.72),.64*sin(phase*.58))
	var speed:=.68
	if aggro:
		goal=player
		speed=2.35 if kind==1 else 1.45
	if stun<=0 and (not aggro or previous.distance_to(player)>1.24):
		var next:=previous.move_toward(goal,speed*dt)
		if navigation==null or navigation.legal(next): position=Ground.point(next)
	var motion:=flat()-previous
	var face:=player-flat() if aggro else motion
	if face.length_squared()>.000001: rotation.y=lerp_angle(rotation.y,atan2(face.x,face.y),minf(1,dt*7))
	cycle+=motion.length()*8.3
	var walking:=clampf(motion.length()/maxf(dt*.68,.001),0,1)
	torso.position.y=.024*sin(phase*2.1)+walking*.045*absf(sin(cycle))
	torso.rotation.z=.064*sin(cycle)*walking
	torso.rotation.x=-.29*sin(PI*swing/.35) if swing>0 else .04*walking
	torso.scale=Vector3.ONE*(1.0+.045*hit_flash/.16)
	for i in limbs.size():
		var angle:=cycle+PI*int(i in [1,2])
		limbs[i].rotation.x=.38*sin(angle)*walking
		if kind==2 and i<2 and swing>0: limbs[i].rotation.x=-1.25*sin(PI*swing/.35)
		limbs[i].position=contacts[i]+Vector3.UP*.09*maxf(0,-cos(angle))*walking

func hurt(amount: int) -> bool:
	aggro=true
	hit_flash=.16
	hp=maxi(0,hp-amount)
	update_label()
	if hp==0:
		respawn=12+kind*4;aggro=false;hide()
	return hp==0
''',encoding="utf-8")


patch("field/spellbook.gd",[
('var ids:=catalog.keys()','var ids:=spell_ids()'), # card_at
]) if False else None
p=root/"field/spellbook.gd"
s=p.read_text(encoding="utf-8")
assert s.count("var ids:=catalog.keys()")==2
s=s.replace("var ids:=catalog.keys()","var ids:=spell_ids()")
s+='''
func spell_ids() -> Array:
	var result: Array=[]
	for id in catalog:
		if catalog[id].has("index"): result.append(id)
	return result
'''
p.write_text(s,encoding="utf-8")
patch("field/careers.gd",[
('var race := ""','var gender:="male"\nvar appearance:=0\nvar race := ""'),
])
patch("field/floating_panel.gd",[
('Dress.fit(figure,hero.equipment)','preload("res://ford/looks.gd").fit(figure,hero.race,hero.gender,hero.appearance)\n\t\tDress.fit(figure,hero.equipment)'),
])
patch("ford/world.gd",[
('const REACH := 1.52','const REACH := 1.52\nconst Looks=preload("res://ford/looks.gd")'),
('var attack_wait := 0.0','var attack_wait := 0.0\nvar auto_enabled:=false\nvar haste_time:=0.0\nvar focus_time:=0.0\nvar hurt_motion:=0.0\nvar death_wait:=0.0\nvar trainers: Array[Node3D]=[]'),
('spells=Skills.book(profile)\n\tcatalog=Actions.build(spells)','''if not online_character.is_empty():
		profile.gender=str(online_character.get("gender","male"))
		profile.appearance=int(online_character.get("appearance",0))
	Looks.fit(hero,profile.race,profile.gender,profile.appearance)
	spells=Skills.book(profile)
	if profile.hotbar.size()==7:
		for sk in spells:
			if sk.level==1 and profile.hotbar.has("spell/"+str(sk.name)): profile.learned[sk.name]=true
	catalog=Actions.build(spells)'''),
('''	for i in homes.size():
		var mob := Beast.new()
		add_child(mob)
		mob.setup(homes[i],1+floori(i/3.0),i)
		mobs.append(mob)''','''	homes.append_array([Vector2(8,7),Vector2(14,-8),Vector2(17,5)])
	for i in homes.size():
		var mob := Beast.new()
		add_child(mob)
		var species:=0 if i<5 else (1 if i<9 else 2)
		mob.setup(homes[i],1+floori(i/3.0),i,species,field_ground)
		mobs.append(mob)
	build_trainers()'''),
('key.tooltip_text=["Отдалить","Приблизить"][i]','key.tooltip_text=["Отдалить мини-карту","Приблизить мини-карту"][i]'),
('key.pressed.connect(_camera_action.bind(i+2))','key.pressed.connect(hud.radar.change_zoom.bind(-1.0 if i==0 else 1.0))'),
('hud.skill_pressed.connect(use_slot)','''hud.skill_pressed.connect(use_slot)
	hud.autoattack_requested.connect(toggle_autoattack)
	hud.pickup_requested.connect(pickup_nearest)
	hud.target_requested.connect(next_target)
	hud.trainer_requested.connect(open_trainer)
	hud.item_assigned.connect(func(id: String,slot: int):
		var key: String="item/"+id
		if not catalog.has(key) or profile.inventory.get(id,0)<=0: return
		var old:=profile.hotbar.find(key)
		if old>=0: profile.hotbar[old]=""
		profile.hotbar[slot]=key
		save_hero()
		update_ui())'''),
('if profile.learn(spells[i]): save_hero(); hud.book_editor.queue_redraw()','''if not near_trainer() or not hud.book_editor.training:
			hud.feed.text="Умения изучаются у мастера твоего класса."
			return
		if i>=0 and i<spells.size() and profile.learn(spells[i]):
			save_hero()
			hud.book_editor.queue_redraw()
			update_ui()'''),
('hud.feed.text="Выбери Корневика, затем нажми удар на панели."','hud.feed.text="Выбери цель, затем нажми отдельную кнопку атаки."'),
('city_model.visible=town\n\tground=city_ground if town else field_ground','city_model.visible=town\n\tfor trainer in trainers: trainer.visible=town\n\tground=city_ground if town else field_ground'),
('if e.keycode>=KEY_1 and e.keycode<=KEY_7: use_slot(e.keycode-KEY_1)','if e.keycode>=KEY_1 and e.keycode<=KEY_9: use_slot(e.keycode-KEY_1)\n\t\tif e.keycode==KEY_0: use_slot(9)'),
('KEY_K: open_window("Умения")','KEY_K: open_window("Умения")\n\t\t\tKEY_SPACE: toggle_autoattack()\n\t\t\tKEY_TAB: next_target()\n\t\t\tKEY_F: pickup_nearest()'),
('func select_screen(screen: Vector2) -> void:\n\tvar best: Beast','''func select_screen(screen: Vector2) -> void:
	if town:
		for trainer in trainers:
			if cam.is_position_behind(trainer.position): continue
			var head:=cam.unproject_position(trainer.position+Vector3.UP*1.6)
			var foot:=cam.unproject_position(trainer.position)
			if screen.distance_to((head+foot)*.5)<maxf(25,head.distance_to(foot)*.55):
				if trainer.get_meta("discipline")==profile.origin and near_trainer():
					open_trainer()
				else:
					walk_to(Vector2(trainer.position.x,trainer.position.z)+Vector2(0,1.6))
					hud.feed.text="Подойди к мастеру своего класса."
				return
	var best: Beast'''),
('target=null\n\tpending=""','target=null\n\tauto_enabled=false\n\tpending=""'),
('hud.feed.text="Цель выбрана · Корневик"','hud.feed.text="Цель выбрана · "+Beast.NAMES[mob.kind]'),
('''func use_slot(i: int) -> void:
	if hud.shade.visible or i<0 or i>=7: return
	var id: String=profile.hotbar[i]
	if id.is_empty():
		hud.show_book(profile,catalog)
		return
	if id=="cycle":
		next_target()
		hud.slots[i].flash_cast()
		return
	if id=="pickup":
		var nearest:Node3D
		var radius:=12.01
		for pile in piles:
			var gap:=actor.distance_to(pile.point)
			if pile.visible and gap<radius: radius=gap; nearest=pile
		if nearest: request_pickup(nearest); flash("pickup")
		else: hud.feed.text="Поблизости нет добычи."
		return
	var sk: Dictionary=catalog[id]''','''func pickup_nearest() -> void:
	var nearest:Node3D
	var radius:=12.01
	for pile in piles:
		var gap:=actor.distance_to(pile.point)
		if pile.visible and gap<radius: radius=gap; nearest=pile
	if nearest: request_pickup(nearest)
	else: hud.feed.text="Поблизости нет добычи."

func toggle_autoattack() -> void:
	if town or death_wait>0 or hud.shade.visible or web_menu_open(): return
	if auto_enabled:
		auto_enabled=false
		if pending=="hit": pending="";route.clear()
		hud.feed.text="Автоатака остановлена."
		update_ui()
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
	else: plan_chase()
	update_ui()

func action_range(id: String) -> float:
	if id=="hit": return 5.2 if profile.mystic() else (4.8 if profile.role_score("Дальний бой")>0 else REACH)
	var sk: Dictionary=catalog.get(id,{})
	return 5.8 if sk.get("effect") in ["ranged","drain"] else REACH

func use_slot(i: int) -> void:
	if hud.shade.visible or web_menu_open() or death_wait>0 or i<0 or i>=10: return
	var id: String=profile.hotbar[i]
	if id.is_empty(): return
	if not catalog.has(id): return
	if id.begins_with("item/"):
		var item:=id.trim_prefix("item/")
		if profile.toggle_item(item):
			preload("res://ford/worn.gd").fit(hero,profile.equipment)
			hud.sheet.refresh(true)
			hud.bag.refresh()
			save_hero()
			update_ui()
		else: hud.feed.text="Предмет недоступен для использования."
		return
	var sk: Dictionary=catalog[id]'''),
('if actor.distance_to(target.flat())>REACH: plan_chase()','if actor.distance_to(target.flat())>action_range(id): plan_chase()'),
('''		"guard":
			shield=7''','''		"heal":
			hp=mini(profile.hp_max(),hp+roundi(profile.hp_max()*.3))
			sound.effect("ward")
			contact(hero.position+Vector3.UP*.55,"guard")
		"renew":
			mp=mini(profile.mana_max(),mp+roundi(profile.mana_max()*.25))
			sound.effect("ward")
		"haste":
			haste_time=7
			sound.effect("ward")
		"focus":
			focus_time=8
			sound.effect("ward")
		"guard":
			shield=7'''),
('''		_:
			if sk.effect=="stun": target.stun=2
			attack(profile.damage()*(3 if sk.effect=="crush" else 2),"stun" if sk.effect=="stun" else "heavy")''','''		_:
			if target==null: return
			if sk.effect=="stun": target.stun=2
			if sk.effect=="drain": hp=mini(profile.hp_max(),hp+roundi(profile.damage()*.6))
			attack(profile.damage()*(3 if sk.effect=="crush" else 2),"stun" if sk.effect=="stun" else "heavy")'''),
('''	engaged=true
	sound.effect("hit" if kind=="hit" else "heavy")
	contact(target.position+Vector3.UP*.77,kind)
	swing=.38
	attack_wait=1.02
	float_word(target.position,"−%d" % amount,Color("#fff3c4"))
	if not target.hurt(amount): return
	var reward := Loot.roll(0,target.rank,.04*profile.role_score("Добыча"),target.spoiled,rng)''','''	if target==null or target.hp<=0: return
	engaged=true
	target.aggro=true
	swing=.38
	if kind=="hit":
		attack_wait=1.05 if haste_time>0 else 1.5
		if focus_time>0: amount=roundi(amount*1.4)
	sound.effect("hit" if kind=="hit" else "heavy")
	var hit_chance:=clampf(.91+float(profile.dexterity()-10)*.002+float(profile.level()-target.rank)*.025,.55,.98)
	if rng.randf()>hit_chance:
		float_word(target.position,"Промах",Color("#dfdfda"))
		return
	var critical:=kind=="hit" and rng.randf()<clampf(.10+profile.dexterity()*.003,.1,.25)
	amount=maxi(1,roundi(amount*(1.8 if critical else 1.0)*rng.randf_range(.9,1.1))-target.kind*2)
	contact(target.position+Vector3.UP*.77,kind)
	float_word(target.position,("Крит! " if critical else "")+"−%d" % amount,Color("#ffb762") if critical else Color("#fff3c4"))
	if not target.hurt(amount): return
	var reward := Loot.roll(target.kind,target.rank,.04*profile.role_score("Добыча"),target.spoiled,rng)'''),
('Loot.xp_for(0,target.rank,profile.level())','Loot.xp_for(target.kind,target.rank,profile.level())'),
('''	if wheel!=null: wheel.rotate_x(dt*.45)
	var prev := actor''','''	if death_wait>0:
		death_wait=maxf(0,death_wait-dt)
		hero.rotation.z=lerpf(hero.rotation.z,1.25,dt*7)
		if death_wait<=0:
			hero.rotation.z=0
			actor=START
			hero.position=Ground.point(actor)
			hp=profile.hp_max()
			mp=profile.mana_max()
			hud.feed.text="Стража вернула тебя к заставе."
			save_hero()
		return
	if wheel!=null: wheel.rotate_x(dt*.45)
	var prev := actor'''),
('shield=maxf(0,shield-dt)\n\tif not axis.is_zero_approx():','''shield=maxf(0,shield-dt)
	haste_time=maxf(0,haste_time-dt)
	focus_time=maxf(0,focus_time-dt)
	hurt_motion=maxf(0,hurt_motion-dt)
	if auto_enabled and target!=null and pending=="": pending="hit"
	var speed:=SPEED*(1.25 if haste_time>0 else 1.0)
	if not axis.is_zero_approx():'''),
('var delta := axis.rotated(-yaw)*SPEED*dt','var delta := axis.rotated(-yaw)*speed*dt'),
('actor.distance_to(target.flat())<=REACH:\n\t\troute.clear()','actor.distance_to(target.flat())<=action_range(pending):\n\t\troute.clear()'),
('''		elif attack_wait<=0:
			flash("hit")
			pending=""
			attack(profile.damage())''','''		elif attack_wait<=0:
			pending=""
			attack(profile.damage())'''),
('var travel := dt*SPEED','var travel := dt*speed'),
('''	if not town:
		for mob in mobs: mob.tick(dt,mob==target and engaged,actor)
	if target!=null:
		target_ring.position=target.position+Vector3.UP*.08
		target_ring.show()
		if engaged and actor.distance_to(target.flat())<=REACH and target.stun<=0:
			hurt_wait-=dt
			if hurt_wait<=0:
				target.swing=.35
				sound.effect("hurt")
				contact(hero.position+Vector3.UP*.91,"hurt")
				hurt_wait=1.55
				var damage := maxi(1,3+target.rank*2-profile.defense())
				hp-=maxi(1,ceili(damage*(.5 if shield>0 else 1.0)))
				if hp<=0:
					clear_target()
					actor=START
					hp=profile.hp_max()
					mp=profile.mana_max()
					hud.feed.text="Стража вернула тебя к заставе."''','''	if not town:
		var in_combat:=false
		for mob in mobs:
			mob.tick(dt,mob==target and engaged,actor)
			if mob.hp<=0 or not mob.aggro: continue
			in_combat=true
			if actor.distance_to(mob.flat())<=REACH and mob.stun<=0 and mob.attack_timer<=0:
				mob.attack_timer=1.35 if mob.kind==1 else 1.85
				mob.swing=.35
				if rng.randf()<.12:
					float_word(hero.position,"Уклонение",Color("#c4dedf"))
					continue
				sound.effect("hurt")
				contact(hero.position+Vector3.UP*.91,"hurt")
				hurt_motion=.22
				var damage:=maxi(1,3+mob.rank*2+mob.kind-profile.defense())
				hp-=maxi(1,ceili(damage*(.5 if shield>0 else 1.0)))
				if hp<=0:
					hp=0
					clear_target()
					for enemy in mobs: enemy.aggro=false
					death_wait=1.1
					update_ui()
					return
		if not in_combat and target==null: engaged=false
	if target!=null:
		target_ring.position=target.position+Vector3.UP*.08
		target_ring.show()'''),
('torso.rotation.x=.045*gait_blend','torso.rotation.x=.045*gait_blend+.18*sin(PI*hurt_motion/.22) if hurt_motion>0 else .045*gait_blend\n\tif swing>0: torso.rotation.y=.27*sin(PI*swing/.38)\n\telse: torso.rotation.y=0'),
('if i==3 and swing>0: v=-1.65*sin(PI*swing/.38)','if swing>0 and i==3: v=-1.65*sin(PI*swing/.38)\n\t\tif swing>0 and i==2 and profile.mystic(): v=-1.35*sin(PI*swing/.38)'),
('''	hud.radar.creatures.clear()
	for mob in mobs:
		if mob.hp>0: hud.radar.creatures.append(mob.flat())''','''	hud.radar.creatures.clear()
	hud.radar.hostile.clear()
	for mob in mobs:
		if mob.hp>0:
			if mob.hostile or mob.aggro: hud.radar.hostile.append(mob.flat())
			else: hud.radar.creatures.append(mob.flat())'''),
('''		hud.target_name.text="Выбери Корневика" if target==null else "Корневик · Ур. %d · %d/%d" % [target.rank,target.hp,target.max_hp]
	for i in 7:''','''		hud.target_name.text="Выбери цель" if target==null else "%s · Ур. %d · %d/%d" % [Beast.NAMES[target.kind],target.rank,target.hp,target.max_hp]
	hud.autoattack.modulate=Color("#ffe09b") if auto_enabled else Color.WHITE
	hud.autoattack.visible=not town
	hud.pickup_button.visible=not town
	hud.target_button.visible=not town
	hud.trainer_button.visible=near_trainer()
	for i in 10:'''),
('elif id=="hit": left=attack_wait','elif sk.has("item"): hint="×%d" % profile.inventory.get(sk.item,0)'),
])
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")
s+='''
func build_trainers() -> void:
	var ix:=0
	var spots: Array[Vector2]=[Vector2(169,6),Vector2(174,6),Vector2(180,6),Vector2(186,6),Vector2(191,6),Vector2(169,17),Vector2(175,17),Vector2(185,17),Vector2(191,17)]
	for race in Hero.TREE:
		for discipline in Hero.TREE[race]:
			var spot:=spots[ix]
			ix+=1
			if not city_ground.legal(spot):
				for offset in [Vector2(0,2),Vector2(0,-2),Vector2(2,0),Vector2(-2,0)]:
					if city_ground.legal(spot+offset): spot+=offset;break
			var npc:=preload("res://ford/models/warden.glb").instantiate() as Node3D
			add_child(npc)
			npc.position=Ground.point(spot)
			npc.set_meta("discipline",discipline)
			Looks.fit(npc,race,"male",ix%4)
			var tag:=Label3D.new()
			tag.text="Мастер: "+str(discipline)
			tag.position.y=2.3
			tag.font_size=38
			tag.pixel_size=.007
			tag.billboard=BaseMaterial3D.BILLBOARD_ENABLED
			tag.modulate=Color("#ffdc91")
			npc.add_child(tag)
			npc.visible=town
			trainers.append(npc)

func near_trainer() -> bool:
	if not town: return false
	for npc in trainers:
		if npc.get_meta("discipline")==profile.origin and actor.distance_to(Vector2(npc.position.x,npc.position.z))<=3.0: return true
	return false

func open_trainer() -> void:
	if not near_trainer():
		hud.feed.text="Найди в городе мастера: "+profile.origin
		return
	clear_target()
	hud.show_book(profile,catalog,true)
'''
p.write_text(s,encoding="utf-8")
# Death pose for enemies before hiding and respawn.
patch("ford/creature.gd",[
('''		respawn-=dt
		if respawn<=0:
			hp=max_hp;spoiled=false;stun=0;aggro=false;attack_timer=0;position=Ground.point(home);update_label();show()
		return''','''		respawn-=dt
		if respawn>11.5+kind*4:
			rotation.z=lerpf(rotation.z,1.4,dt*9)
		else: hide()
		if respawn<=0:
			rotation.z=0
			hp=max_hp;spoiled=false;stun=0;aggro=false;attack_timer=0;position=Ground.point(home);update_label();show()
		return'''),
('respawn=12+kind*4;aggro=false;hide()','respawn=12+kind*4;aggro=false'),
])
patch("project.godot",[
('config/version="0.9.1"','config/version="0.11.0"'),
])
patch("web/shell.html",[
('PRE-ALPHA 0.10.2 · ONLINE TEST / OFFLINE','PRE-ALPHA 0.11 · ONLINE TEST / OFFLINE'),
('1–7 — умения','1–0 — предметы и умения'),
])


# Touch-friendly alternative to drag: select item, then tap destination slot.
patch("field/floating_panel.gd",[
('signal hotbar_drop(id: String, point: Vector2)','signal hotbar_drop(id: String, point: Vector2)\nsignal hotbar_choose(id: String)'),
('''	line(Vector2(101,326),chance[chosen],13,SOFT)
	if info[1]=="Материал":''','''	line(Vector2(101,326),chance[chosen],13,SOFT)
	box(Rect2(18,336,175,29),Color("#354d3f"),GOLD)
	line(Vector2(19,356),"На панель",13,PAPER,173,HORIZONTAL_ALIGNMENT_CENTER)
	if info[1]=="Материал":'''),
('''		if Rect2(209,345,158,42).has_point(p) and chosen!=""''','''		if Rect2(18,336,175,29).has_point(p) and chosen!="":
			hotbar_choose.emit(chosen)
			hide()
			return
		if Rect2(209,345,158,42).has_point(p) and chosen!=""'''),
])
patch("field/hud.gd",[
('signal item_assigned(id: String, slot: int)','signal item_assigned(id: String, slot: int)\nsignal item_choose(id: String)'),
('bag.hotbar_drop.connect(func(id,point):','bag.hotbar_choose.connect(func(id): item_choose.emit(id))\n\tbag.hotbar_drop.connect(func(id,point):'),
])
patch("ford/world.gd",[
('var auto_enabled:=false','var auto_enabled:=false\nvar assigning_item:=""'),
('''	hud.item_assigned.connect(func(id: String,slot: int):
		var key: String="item/"+id
		if not catalog.has(key) or profile.inventory.get(id,0)<=0: return
		var old:=profile.hotbar.find(key)
		if old>=0: profile.hotbar[old]=""
		profile.hotbar[slot]=key
		save_hero()
		update_ui())''','''	hud.item_assigned.connect(assign_item)
	hud.item_choose.connect(func(id: String):
		assigning_item=id
		hud.feed.text="Выбери ячейку 1–0 для предмета.")'''),
('''	var id: String=profile.hotbar[i]
	if id.is_empty(): return''','''	if not assigning_item.is_empty():
		var chosen:=assigning_item
		assigning_item=""
		assign_item(chosen,i)
		return
	var id: String=profile.hotbar[i]
	if id.is_empty(): return'''),
('''	if not town:
		var in_combat:=false
		for mob in mobs:''','''	var in_combat:=false
	if not town:
		for mob in mobs:'''),
('if not engaged: hp=mini(profile.hp_max(),hp+2)','if not in_combat and not engaged: hp=mini(profile.hp_max(),hp+2)'),
])
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")
s+='''
func assign_item(id: String,slot: int) -> void:
	var key: String="item/"+id
	if slot<0 or slot>=10 or not catalog.has(key) or profile.inventory.get(id,0)<=0: return
	var old:=profile.hotbar.find(key)
	if old>=0: profile.hotbar[old]=""
	profile.hotbar[slot]=key
	hud.feed.text=str(catalog[key].name)+" → "+str((slot+1)%10)
	save_hero()
	update_ui()
'''
p.write_text(s,encoding="utf-8")
# New exported assets prevent stale browser code.
patch("web/shell.html",[
('c3-config-0102.js','c3-config-0110.js'),
('c3-online-0102.js','c3-online-0110.js'),
])

patch("ford/world.gd",[
('''					add_child(avatar)
					avatar.position=Ground.point(point)''','''					add_child(avatar)
					Looks.fit(avatar,str(row.get("race","Человек")),"male",0)
					avatar.position=Ground.point(point)'''),
])
patch("field/skills.gd",[
('Атака с расстояния до 220.','Атака с расстояния до 5,8 м.'),
])
p=root/"field/spellbook.gd"
s=p.read_text(encoding="utf-8").replace("% (ix+1)","% ((ix+1)%10)").replace("[catalog[id].name,to+1]","[catalog[id].name,(to+1)%10]")
p.write_text(s,encoding="utf-8")
