extends RefCounted
const Ground=preload("res://ford/ground.gd")

static func material(color:Color)->StandardMaterial3D:
	var m:=StandardMaterial3D.new()
	m.albedo_color=color
	m.roughness=1.0
	return m

static func box(root:Node3D,p:Vector3,s:Vector3,color:Color)->MeshInstance3D:
	var b:=BoxMesh.new()
	b.size=s
	b.material=material(color)
	var node:=MeshInstance3D.new()
	node.mesh=b
	root.add_child(node)
	node.position=p
	return node

static func triangle(st:SurfaceTool,a:Vector3,b:Vector3,c:Vector3,tint:Color)->void:
	var normal:Vector3=(c-a).cross(b-a).normalized()
	for v in [a,b,c]:
		st.set_color(tint)
		st.set_normal(normal)
		st.add_vertex(v)

static func ground_tint(p:Vector2)->Color:
	if Ground.road(p): return Color("#aa9271").lerp(Color("#c5ae85"),.5+.5*sin(p.x*.5)*cos(p.y*.6))
	if Ground.village(p): return Color("#8c9472")
	var base:=Color("#748d55")
	if p.x>92: base=Color("#858876")
	elif p.x>42 and p.y< -23: base=Color("#777f69")
	elif p.x>42: base=Color("#83916c")
	elif p.x> -24: base=Color("#607e48")
	return base.lerp(base.lightened(.20),.5+.5*sin(p.x*.25)*cos(p.y*.29))

static func build(root:Node3D)->void:
	var env_node:=WorldEnvironment.new()
	var env:=Environment.new()
	var sky:=Sky.new()
	var sky_mat:=ProceduralSkyMaterial.new()
	sky_mat.sky_top_color=Color("#6f9cb9")
	sky_mat.sky_horizon_color=Color("#d3dfd1")
	sky_mat.ground_bottom_color=Color("#748768")
	sky_mat.ground_horizon_color=Color("#d3dfd1")
	sky.sky_material=sky_mat
	env.sky=sky
	env.background_mode=Environment.BG_SKY
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color=Color("#d6e0cb")
	env.ambient_light_energy=.82
	env.fog_enabled=true
	env.fog_light_color=Color("#bccdc1")
	env.fog_density=.009
	env_node.environment=env
	root.add_child(env_node)
	var terrain:=SurfaceTool.new()
	terrain.begin(Mesh.PRIMITIVE_TRIANGLES)
	for z in range(-90,90,2):
		for x in range(-150,150,2):
			var a:=Ground.point(Vector2(x,z))
			var b:=Ground.point(Vector2(x+2,z))
			var c:=Ground.point(Vector2(x+2,z+2))
			var d:=Ground.point(Vector2(x,z+2))
			var tint:=ground_tint(Vector2(x+1,z+1))
			triangle(terrain,a,b,c,tint)
			triangle(terrain,a,c,d,tint)
	var mat:=StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo=true
	mat.vertex_color_is_srgb=true
	mat.cull_mode=BaseMaterial3D.CULL_DISABLED
	mat.roughness=1
	terrain.set_material(mat)
	var land:=MeshInstance3D.new()
	land.mesh=terrain.commit()
	root.add_child(land)
	# Real static collision mesh for the continuous terrain.
	land.create_trimesh_collision()
	var stream:=SurfaceTool.new()
	stream.begin(Mesh.PRIMITIVE_TRIANGLES)
	var water:=StandardMaterial3D.new()
	water.albedo_color=Color("#4f8391")
	water.roughness=.31
	water.cull_mode=BaseMaterial3D.CULL_DISABLED
	stream.set_material(water)
	for z in range(-90,90,2):
		var x:=Ground.river(z)
		var xx:=Ground.river(z+2)
		for v in [Vector3(x-2.9,-.22,z),Vector3(x+2.9,-.22,z),Vector3(xx+2.9,-.22,z+2),Vector3(x-2.9,-.22,z),Vector3(xx+2.9,-.22,z+2),Vector3(xx-2.9,-.22,z+2)]:
			stream.set_normal(Vector3.UP)
			stream.add_vertex(v)
	var river:=MeshInstance3D.new()
	river.mesh=stream.commit()
	root.add_child(river)
	for z in [-43.0,0.0,43.0]:
		var x:=Ground.river(z)
		# Low rails delineate crossings without blocking the road.
		for side in [-1,1]:
			box(root,Vector3(x,.66,z+side*2.7),Vector3(8.7,.15,.13),Color("#8b6445"))
			for dx in [-4.0,0.0,4.0]:
				box(root,Vector3(x+dx,.49,z+side*2.7),Vector3(.17,.8,.17),Color("#8b6445"))

static func obstacles(root:Node3D,nav)->void:
	for b in nav.blocks:
		var body:=StaticBody3D.new()
		root.add_child(body)
		body.position=Ground.point(Vector2(float(b[0]),float(b[1])))+Vector3.UP*1.6
		var shape:=BoxShape3D.new()
		shape.size=Vector3(float(b[2])*2,3.2,float(b[3])*2)
		var collision:=CollisionShape3D.new()
		collision.shape=shape
		body.add_child(collision)

static func multi(root:Node3D,mesh:Mesh,positions:Array[Transform3D])->void:
	if positions.is_empty(): return
	var mm:=MultiMesh.new()
	mm.transform_format=MultiMesh.TRANSFORM_3D
	mm.mesh=mesh
	mm.instance_count=positions.size()
	for i in positions.size(): mm.set_instance_transform(i,positions[i])
	var node:=MultiMeshInstance3D.new()
	node.multimesh=mm
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(node)

static func decorate(root:Node3D,nav,quality:int)->void:
	var rng:=RandomNumberGenerator.new()
	rng.seed=19019
	var trunks:Array[Transform3D]=[]
	var crowns:Array[Transform3D]=[]
	var rocks:Array[Transform3D]=[]
	var grass:Array[Transform3D]=[]
	for i in 550:
		var p:=Vector2(rng.randf_range(-145,145),rng.randf_range(-84,84))
		if p.x<-65 or Ground.road(p) or not nav.legal(p) or absf(p.x-Ground.river(p.y))<5: continue
		if p.x>92 and rng.randf()<.75: continue
		var scale_:=rng.randf_range(.8,2.1)
		var at:=Ground.point(p)
		trunks.append(Transform3D(Basis.IDENTITY.scaled(Vector3(scale_*.85,scale_,scale_*.85)),at+Vector3.UP*1.15*scale_))
		crowns.append(Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*scale_),at+Vector3.UP*2.7*scale_))
	for i in 160:
		var p:=Vector2(rng.randf_range(-140,145),rng.randf_range(-85,85))
		if Ground.village(p) or Ground.road(p) or not nav.legal(p): continue
		var sc:=rng.randf_range(.2,.8)
		rocks.append(Transform3D(Basis(Vector3.UP,rng.randf()*TAU).scaled(Vector3(sc,sc*.6,sc*.82)),Ground.point(p)+Vector3.UP*sc*.2))
	for i in (1700 if quality==2 else (1050 if quality==1 else 420)):
		var p:=Vector2(rng.randf_range(-145,145),rng.randf_range(-85,85))
		if Ground.village(p) or Ground.road(p) or not nav.legal(p): continue
		var sc:=rng.randf_range(.12,.45)
		grass.append(Transform3D(Basis(Vector3.UP,rng.randf()*TAU).scaled(Vector3(sc,sc*2,sc)),Ground.point(p)+Vector3.UP*sc*.8))
	var trunk:=CylinderMesh.new()
	trunk.top_radius=.12;trunk.bottom_radius=.18;trunk.height=2.3;trunk.radial_segments=6;trunk.material=material(Color("#765d42"))
	var crown:=SphereMesh.new()
	crown.radius=1.08;crown.height=2.8;crown.radial_segments=7;crown.rings=4;crown.material=material(Color("#527449"))
	var rock:=SphereMesh.new()
	rock.radius=1.0;rock.height=1.5;rock.radial_segments=7;rock.rings=3;rock.material=material(Color("#92998a"))
	var tuft:=PrismMesh.new()
	tuft.size=Vector3(.7,1.1,.20);tuft.material=material(Color("#8da467"))
	multi(root,trunk,trunks);multi(root,crown,crowns);multi(root,rock,rocks);multi(root,tuft,grass)
	for entry in [[Vector2(-66,5),"Поля Рассвета"],[Vector2(-24,5),"Вересковый лес"],[Vector2(50,-5),"Руины / карьер"],[Vector2(94,5),"Каменные пустоши"]]:
		var p:Vector2=entry[0]
		var at:=Ground.point(p)
		box(root,at+Vector3.UP*.8,Vector3(.15,1.6,.15),Color("#725638"))
		box(root,at+Vector3.UP*1.55,Vector3(2.0,.48,.12),Color("#9a7951"))
		var tag:=Label3D.new()
		tag.text=str(entry[1]);tag.font_size=42;tag.pixel_size=.007;tag.outline_size=8
		tag.billboard=BaseMaterial3D.BILLBOARD_ENABLED;tag.modulate=Color("#ffe6b3")
		root.add_child(tag);tag.position=at+Vector3.UP*2.05

static func ring(root:Node3D,radius:float,color:Color)->MeshInstance3D:
	var mesh:=TorusMesh.new()
	mesh.inner_radius=radius-.045
	mesh.outer_radius=radius
	mesh.rings=28
	mesh.ring_segments=5
	var mat:=StandardMaterial3D.new()
	mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color=color
	mesh.material=mat
	var node:=MeshInstance3D.new()
	node.mesh=mesh
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(node)
	node.hide()
	return node
