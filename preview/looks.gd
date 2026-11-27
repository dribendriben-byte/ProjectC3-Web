extends RefCounted
const COLORS={
	"Человек":["#e2b797","#cc9c77","#ad7754","#80523c"],
	"Эльф":["#f0d7bc","#d5ae8d","#b68d68","#977150"],
	"Тёмный эльф":["#aab0c4","#8c91ab","#6f748e","#555a72"],
	"Орк":["#a0af78","#82915c","#687448","#485b39"],
	"Гном":["#e0b48d","#c28c65","#a36d50","#785039"]}
const HAIR:=["#362a26","#805039","#d3b075","#d8d9d2"]
const OUTFIT:={"Человек":"#55788e","Эльф":"#5c8560","Тёмный эльф":"#6f608a","Орк":"#876044","Гном":"#a67c48"}

static func piece(root:Node3D,p:Vector3,s:Vector3,tint:Color,round_:bool=false)->MeshInstance3D:
	var mesh:PrimitiveMesh
	if round_:
		var ball:=SphereMesh.new()
		ball.radius=.5
		ball.height=1.0
		ball.radial_segments=9
		ball.rings=5
		mesh=ball
	else:
		var cube:=BoxMesh.new()
		cube.size=Vector3.ONE
		mesh=cube
	var mat:=StandardMaterial3D.new()
	mat.albedo_color=tint
	mat.roughness=.83
	mesh.material=mat
	var node:=MeshInstance3D.new()
	node.mesh=mesh
	root.add_child(node)
	node.position=p
	node.scale=s
	return node

static func taper(root:Node3D,p:Vector3,top:float,bottom:float,h:float,tint:Color,depth:float=1.0)->MeshInstance3D:
	var mesh:=CylinderMesh.new()
	mesh.top_radius=top;mesh.bottom_radius=bottom;mesh.height=h;mesh.radial_segments=9
	var mat:=StandardMaterial3D.new()
	mat.albedo_color=tint;mat.roughness=.88
	mesh.material=mat
	var node:=MeshInstance3D.new()
	node.mesh=mesh
	root.add_child(node)
	node.position=p;node.scale.z=depth
	return node

static func layer(parent:Node3D,name_:String,clear_mesh:bool=false)->Node3D:
	var old:=parent.get_node_or_null(name_)
	if old!=null:
		parent.remove_child(old)
		old.queue_free()
	if clear_mesh and parent is MeshInstance3D: parent.mesh=null
	var node:=Node3D.new()
	node.name=name_
	parent.add_child(node)
	return node

static func fit(model:Node3D,appearance:Dictionary)->void:
	var race:String=appearance.get("race","Человек")
	if not COLORS.has(race): race="Человек"
	var female:bool=appearance.get("gender","male")=="female"
	var face:=clampi(int(appearance.get("face",0)),0,3)
	var hairstyle:=clampi(int(appearance.get("hair",0)),0,3)
	var hair:=Color(HAIR[clampi(int(appearance.get("hair_color",0)),0,3)])
	var skin:=Color(COLORS[race][clampi(int(appearance.get("skin",0)),0,3)])
	var cloth:=Color(OUTFIT[race])
	var leather:=Color("#514138")
	var trim:=Color("#c1ab80")
	var proportion:Dictionary={"Человек":Vector3(.94,1.08,.94),"Эльф":Vector3(.81,1.15,.84),"Тёмный эльф":Vector3(.84,1.12,.86),"Орк":Vector3(1.23,1.16,1.19),"Гном":Vector3(1.07,.83,1.05)}
	model.scale=proportion[race]
	if female: model.scale*=Vector3(.91,1.02,.92)
	var body:=model.find_child("Body",true,false) as Node3D
	if body==null:return
	var torso:=layer(body,"NewBody",true)
	taper(torso,Vector3(0,1.16,0),.34,.265,.58,cloth,.78)
	taper(torso,Vector3(0,.87,0),.265,.33,.23,cloth.darkened(.15),.79)
	taper(torso,Vector3(0,1.0,0),.29,.29,.1,leather,.8)
	piece(torso,Vector3(0,1.0,.24),Vector3(.12,.10,.045),trim)
	piece(torso,Vector3(0,1.25,.25),Vector3(.06,.35,.04),trim)
	for side in [-1,1]:
		var lapel:=piece(torso,Vector3(side*.14,1.36,.22),Vector3(.085,.20,.045),trim)
		lapel.rotation.z=side*.45
		piece(torso,Vector3(side*.31,1.42,.0),Vector3(.22,.19,.31),cloth.lightened(.12),true)
	taper(torso,Vector3(0,1.52,0),.12,.14,.19,skin,.93)
	var widths:Array[float]=[.43,.48,.39,.45]
	var heights:Array[float]=[.48,.46,.54,.51]
	var w:=widths[face]
	piece(torso,Vector3(0,1.77,.015),Vector3(w,heights[face],.42),skin,true)
	piece(torso,Vector3(0,1.66,.05),Vector3(w*.72,.24,.34),skin,true)
	piece(torso,Vector3(0,1.75,.237),Vector3(.08,.11,.08),skin.lightened(.07),true)
	for side in [-1,1]:
		var eye_x:float=side*w*.24
		piece(torso,Vector3(eye_x,1.81,.211),Vector3(.084,.041,.035),Color("#eee9df"),true)
		piece(torso,Vector3(eye_x,1.81,.232),Vector3(.034,.034,.017),Color("#455f65"),true)
		var brow:=piece(torso,Vector3(eye_x,1.86,.215),Vector3(.095,.023,.027),hair)
		brow.rotation.z=side*[.04,.16,-.10,.10][face]
		var elf:bool=race in ["Эльф","Тёмный эльф"]
		var ear:=piece(torso,Vector3(side*(w*.5+.035),1.8,0),Vector3(.12,.28,.11) if elf else Vector3(.10,.15,.10),skin,true)
		if elf:ear.rotation.z=-side*.64
	piece(torso,Vector3(0,1.67,.218),Vector3(.10,.021,.023),skin.darkened(.35))
	piece(torso,Vector3(0,1.96,-.01),Vector3(w*1.12,.22,.46),hair,true)
	piece(torso,Vector3(0,1.83,-.16),Vector3(w*.99,.37,.22),hair,true)
	match hairstyle:
		1:
			var fringe:=piece(torso,Vector3(-.12,1.92,.17),Vector3(.23,.18,.16),hair,true)
			fringe.rotation.z=.45
		2:
			for side in [-1,1]:piece(torso,Vector3(side*w*.42,1.64,-.11),Vector3(.14,.55,.23),hair,true)
			piece(torso,Vector3(0,1.43,-.25),Vector3(w,.72,.19),hair,true)
		3:
			piece(torso,Vector3(0,1.99,-.17),Vector3(.30,.19,.30),hair,true)
			piece(torso,Vector3(0,1.67,-.29),Vector3(.18,.37,.19),hair,true)
	if race=="Гном" and not female:
		piece(torso,Vector3(0,1.56,.18),Vector3(w*.81,.38,.26),hair,true)
		piece(torso,Vector3(0,1.7,.23),Vector3(.29,.085,.10),hair,true)
	if race=="Орк":
		for side in [-1,1]:
			var tusk:=taper(torso,Vector3(side*.115,1.69,.23),.009,.036,.14,Color("#eee3c5"))
			tusk.rotation.z=-side*.13
	for name_ in ["LegL","LegR","ArmL","ArmR"]:
		var joint:=model.find_child(name_,true,false) as Node3D
		if joint==null:continue
		var limb:=layer(joint,"NewLimb",true)
		if name_.begins_with("Leg"):
			taper(limb,Vector3(0,-.17,0),.14,.11,.37,cloth.darkened(.24),.83)
			taper(limb,Vector3(0,-.51,0),.11,.135,.34,leather,.94)
			piece(limb,Vector3(0,-.70,.07),Vector3(.29,.16,.37),leather,true)
		else:
			taper(limb,Vector3(0,-.14,0),.123,.103,.31,cloth,.93)
			taper(limb,Vector3(0,-.37,0),.096,.089,.22,skin,.93)
			# Closed hand with thumb, centered exactly on the weapon socket.
			piece(limb,Vector3(0,-.52,.04),Vector3(.19,.21,.18),skin,true)
			piece(limb,Vector3(-.075 if name_=="ArmR" else .075,-.48,.10),Vector3(.075,.12,.08),skin,true)
