extends RefCounted
const Looks=preload("res://ford/looks.gd")

static func fit(model:Node3D,gear:Dictionary)->void:
	var body:=model.find_child("Body",true,false) as Node3D
	if body==null:return
	var outfit:=Looks.layer(body,"Outfit")
	if gear.get("Грудь","")!="":
		for i in 5:
			var x:float=(i-2)*.14
			Looks.piece(outfit,Vector3(x,1.18,.27-.018*absf(i-2)),Vector3(.14,.45,.08),Color("#a98a60").darkened((i%2)*.10))
	var right:=model.find_child("ArmR",true,false) as Node3D
	var left:=model.find_child("ArmL",true,false) as Node3D
	if right==null or left==null:return
	for arm in [right,left]:
		var cuff:=Looks.layer(arm,"Cuff")
		if gear.get("Запястья","")!="":Looks.piece(cuff,Vector3(0,-.35,0),Vector3(.27,.19,.27),Color("#a88960"))
	# Original GLB has a baked-in weapon. Looks.fit replaces that mesh;
	# only this independently equipped object is attached to ArmR.
	var grip:=Looks.layer(right,"WeaponGrip")
	grip.position=Vector3(0,-.52,.04)
	grip.rotation.x=.40
	var id:String=gear.get("Оружие","")
	if id=="":return
	var metal:=Color("#c1cbd0")
	var handle:=Color("#634a32")
	var brass:=Color("#c5a36b")
	Looks.piece(grip,Vector3(0,0,0),Vector3(.085,.085,.22),handle)
	Looks.piece(grip,Vector3(0,0,-.12),Vector3(.13,.11,.06),brass,true)
	if id=="ng_staff":
		Looks.piece(grip,Vector3(0,0,.36),Vector3(.08,.08,1.24),handle)
		Looks.piece(grip,Vector3(0,0,.98),Vector3(.19,.18,.16),brass)
		Looks.piece(grip,Vector3(0,0,1.1),Vector3(.22,.21,.26),Color("#80b8cc"),true)
	elif id in ["ng_hammer","hammer"]:
		Looks.piece(grip,Vector3(0,0,.30),Vector3(.09,.09,.63),handle)
		Looks.piece(grip,Vector3(0,0,.64),Vector3(.37,.30,.23),metal)
		Looks.piece(grip,Vector3(0,0,.64),Vector3(.39,.09,.25),brass)
	elif id=="ng_axe":
		Looks.piece(grip,Vector3(0,0,.32),Vector3(.085,.085,.72),handle)
		var axe:=Looks.piece(grip,Vector3(.14,0,.65),Vector3(.36,.085,.33),metal)
		axe.rotation.y=.20
		Looks.piece(grip,Vector3(-.12,0,.65),Vector3(.13,.09,.14),brass)
	else:
		var length:=.39 if id in ["ng_dagger","knife"] else .82
		Looks.piece(grip,Vector3(0,0,.12),Vector3(.29,.08,.075),brass)
		Looks.piece(grip,Vector3(0,0,.17+length*.5),Vector3(.115,.047,length),metal)
		var tip:=Looks.piece(grip,Vector3(0,0,.17+length),Vector3(.084,.045,.13),metal.lightened(.13),true)
		tip.rotation.y=.15
