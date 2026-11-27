extends CharacterBody3D
const MODEL=preload("res://ford/models/rootling.glb")
const Ground=preload("res://ford/ground.gd")
const Looks=preload("res://ford/looks.gd")
const NAMES:=["Корневик","Вересковый волк","Сланцевик","Каменный страж"]
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
var attack_timer:=0.0
var aggro:=false
var hostile:=false
var limbs:Array[Node3D]=[]
var contacts:Array[Vector3]=[]
var torso:Node3D
var label:Label3D
var nav
var shape_node:CollisionShape3D

func setup(p:Vector2,level_:int,index:int,species:int=0,navigation=null)->void:
	home=p;rank=level_;kind=species;nav=navigation
	hostile=kind!=0
	max_hp=26+rank*7+kind*12
	hp=max_hp
	phase=index*1.71
	position=Ground.point(p)+Vector3.UP*.08
	collision_layer=2
	collision_mask=1|2|4
	floor_snap_length=.45
	shape_node=CollisionShape3D.new()
	var shape:=CapsuleShape3D.new()
	shape.radius=.32 if kind<2 else .46
	shape.height=1.0 if kind<2 else 1.65
	shape_node.shape=shape
	shape_node.position.y=shape.height*.5
	add_child(shape_node)
	if kind==0:
		var model:=MODEL.instantiate()
		add_child(model)
		torso=model.find_child("Body",true,false) as Node3D
		for n in ["FrontL","FrontR","BackL","BackR"]:
			limbs.append(model.find_child(n,true,false) as Node3D)
	else:
		torso=Node3D.new()
		add_child(torso)
		var color:=Color("#887e70") if kind==1 else (Color("#75838a") if kind==2 else Color("#646956"))
		if kind==1:
			Looks.piece(torso,Vector3(0,.66,0),Vector3(.62,.60,1.26),color,true)
			Looks.piece(torso,Vector3(0,.86,.64),Vector3(.48,.52,.56),color.lightened(.13),true)
			Looks.piece(torso,Vector3(0,.73,.96),Vector3(.33,.25,.38),Color("#49413a"),true)
			for side in [-1,1]:
				var ear:=Looks.piece(torso,Vector3(side*.17,1.13,.63),Vector3(.14,.28,.13),color.darkened(.2))
				ear.rotation.z=-side*.22
				Looks.piece(torso,Vector3(side*.15,.91,.85),Vector3(.075,.075,.075),Color("#efbd62"),true)
			var tail:=Looks.piece(torso,Vector3(0,.81,-.77),Vector3(.17,.17,.67),color.darkened(.15),true)
			tail.rotation.x=.45
		else:
			Looks.piece(torso,Vector3(0,.96,0),Vector3(.90,.91,.68),color,true)
			Looks.piece(torso,Vector3(0,1.57,.02),Vector3(.60,.54,.55),color.lightened(.12),true)
			for side in [-1,1]:
				Looks.piece(torso,Vector3(side*.14,1.60,.27),Vector3(.10,.08,.08),Color("#eeb462"))
			Looks.piece(torso,Vector3(0,1.0,.37),Vector3(.16,.24,.08),Color("#cba261"),true)
		for i in 4:
			var limb:=Node3D.new()
			torso.add_child(limb)
			limb.position=Vector3((-.29 if i%2==0 else .29)*(1.55 if kind>=2 and i<2 else 1.0),.55 if kind==1 or i>=2 else 1.18,.39 if i<2 and kind==1 else (-.39 if kind==1 else 0.0))
			Looks.piece(limb,Vector3(0,-.25,0),Vector3(.17,.54,.19) if kind==1 else Vector3(.37,.60,.36),color)
			limbs.append(limb)
	for limb in limbs:contacts.append(limb.position)
	label=Label3D.new()
	label.position.y=1.8 if kind<2 else 2.15
	label.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size=35;label.pixel_size=.007;label.outline_size=7
	label.modulate=Color("#f3a18a") if hostile else Color("#f0dfb7")
	add_child(label)
	update_label()

func display_name()->String:return NAMES[kind]

func update_label()->void:
	label.text="%s · %d\n%d/%d" % [display_name(),rank,hp,max_hp]

func flat()->Vector2:return Vector2(position.x,position.z)

func tick(dt:float,engaged:bool,player:Vector2)->void:
	if hp<=0:
		respawn-=dt
		if respawn>14.1:
			rotation.z=lerpf(rotation.z,1.35,minf(1,dt*9))
		else:hide()
		if respawn<=0:
			hp=max_hp;spoiled=false;stun=0;aggro=false;attack_timer=0;rotation.z=0;velocity=Vector3.ZERO
			position=Ground.point(home)+Vector3.UP*.08
			shape_node.disabled=false
			update_label()
		return
	var previous:=flat()
	var gap:=previous.distance_to(player)
	visible=gap<58
	if gap>65 and not aggro:return
	phase+=dt
	stun=maxf(0,stun-dt);swing=maxf(0,swing-dt);hit_flash=maxf(0,hit_flash-dt);attack_timer=maxf(0,attack_timer-dt)
	if not Ground.village(player) and home.distance_to(player)<12 and (engaged or (hostile and gap<4.2)):aggro=true
	if aggro and (Ground.village(player) or home.distance_to(player)>15):
		aggro=false;hp=max_hp;spoiled=false;update_label()
	var goal:=home+Vector2(1.45*cos(phase*.42),1.25*sin(phase*.39))
	var speed:=.75
	if aggro:
		goal=player
		speed=2.65 if kind==1 else 1.7
	var desired:=Vector2.ZERO
	if stun<=0 and (not aggro or gap>1.45):
		var direction:=previous.direction_to(goal)
		if previous.distance_to(goal)>.12:desired=direction*speed
	var movement:=Vector2(velocity.x,velocity.z).move_toward(desired,dt*6.0)
	var next:=previous+movement*dt
	if nav!=null:next=nav.slide(previous,movement*dt)
	velocity.x=(next.x-previous.x)/maxf(dt,.001)
	velocity.z=(next.y-previous.y)/maxf(dt,.001)
	if not is_on_floor():velocity.y-=18.0*dt
	else:velocity.y=-.15
	move_and_slide()
	var motion:=flat()-previous
	var face:=player-flat() if aggro else motion
	if face.length_squared()>.0001:rotation.y=lerp_angle(rotation.y,atan2(face.x,face.y),minf(1,dt*8))
	cycle+=motion.length()*8.3
	var walking:=clampf(motion.length()/maxf(dt*.68,.001),0,1)
	torso.position.y=.024*sin(phase*2.1)+walking*.045*absf(sin(cycle))
	torso.rotation.z=.064*sin(cycle)*walking
	torso.rotation.x=-.29*sin(PI*swing/.35) if swing>0 else .04*walking
	torso.scale=Vector3.ONE*(1+.04*hit_flash/.16)
	for i in limbs.size():
		var angle:=cycle+PI*int(i in [1,2])
		limbs[i].rotation.x=.38*sin(angle)*walking
		if kind>=2 and i<2 and swing>0:limbs[i].rotation.x=-1.25*sin(PI*swing/.35)
		limbs[i].position=contacts[i]+Vector3.UP*.09*maxf(0,-cos(angle))*walking

func hurt(amount:int)->bool:
	aggro=true;hit_flash=.16
	hp=maxi(0,hp-amount)
	update_label()
	if hp==0:
		respawn=15.0;aggro=false;velocity=Vector3.ZERO
		shape_node.set_deferred("disabled",true)
	return hp==0
