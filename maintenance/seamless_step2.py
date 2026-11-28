"""Step 2: connect the original field and original city without moving either.
Apply to a successful alpha build, after the optional population step.
No auth, inventory, combat, NPC, or save format replacement.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
def unique(s,a,b):
    if s.count(a)!=1: raise RuntimeError(f"Expected single source anchor {a[:90]!r}, got {s.count(a)}")
    return s.replace(a,b,1)
def section(s,start,end,body):
    a=s.index(start); b=s.index(end,a+len(start))
    return s[:a]+body+"\n\n"+s[b:]

(root/"ford/connected_ground.gd").write_text('''extends RefCounted
const Ground=preload("res://ford/ground.gd")
const STEP:=.5
const CORNERS: Array[Vector2]=[Vector2(18,0),Vector2(110,0),Vector2(110,44),Vector2(180,44),Vector2(180,38)]
var field
var city
var grid:=AStarGrid2D.new()

func _init(field_nav,city_nav)->void:
	field=field_nav
	city=city_nav
	grid.region=Rect2i(-80,-80,534,179)
	grid.cell_size=Vector2.ONE*STEP
	grid.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.update()
	for y in range(grid.region.position.y,grid.region.end.y):
		for x in range(grid.region.position.x,grid.region.end.x):
			var cell:=Vector2i(x,y)
			grid.set_point_solid(cell,not legal(Vector2(cell)*STEP))

static func in_city(p:Vector2)->bool:
	return p.x>=134 and p.x<=226 and absf(p.y)<=39

static func on_road(p:Vector2)->bool:
	return (p.x>=18 and p.x<=113 and absf(p.y)<=3) or (absf(p.x-110)<=3 and p.y>=-3 and p.y<=47) or (p.x>=107 and p.x<=183 and absf(p.y-44)<=3) or (absf(p.x-180)<=2.4 and p.y>=38 and p.y<=47)

func legal(p:Vector2)->bool:
	# In the old map rectangles the existing collision rules remain authoritative.
	if in_city(p): return city.legal(p)
	var min_p:=Vector2(field.grid.region.position)*STEP
	var max_p:=Vector2(field.grid.region.end-Vector2i.ONE)*STEP
	if p.x>=min_p.x and p.x<=max_p.x and p.y>=min_p.y and p.y<=max_p.y:
		return field.legal(p)
	if not on_road(p):return false
	# Two original Garden tree trunks lie in the road strip. Canopies remain intact.
	for tree in [Vector2(111.7,9.25),Vector2(134.2,44.6)]:
		if p.distance_to(tree)<.8:return false
	for b in field.blocks:
		if absf(float(b[0])-p.x)<float(b[2])+.22 and absf(float(b[1])-p.y)<float(b[3])+.22:return false
	for b in city.blocks:
		if absf(float(b[0])-p.x)<float(b[2])+.22 and absf(float(b[1])-p.y)<float(b[3])+.22:return false
	return true

func open_cell(p:Vector2)->Vector2i:
	var original:=Vector2i((p/STEP).round())
	var best:=original
	var distance:=INF
	for dy in range(-1,2):
		for dx in range(-1,2):
			var q:=original+Vector2i(dx,dy)
			if not grid.region.has_point(q) or grid.is_point_solid(q):continue
			var d:=p.distance_squared_to(Vector2(q)*STEP)
			if d<distance:distance=d;best=q
	return best

func route(a:Vector2,b:Vector2)->PackedVector2Array:
	if not legal(b):return []
	var start:=open_cell(a)
	var end:=open_cell(b)
	if not grid.region.has_point(start) or not grid.region.has_point(end) or grid.is_point_solid(start) or grid.is_point_solid(end):return []
	var trail:=grid.get_point_path(start,end)
	if trail.is_empty():return trail
	if trail.size()>1 and a.distance_to(trail[0])<.09:trail.remove_at(0)
	trail.append(b)
	return trail

static func road_mesh(root:Node3D,field_nav)->void:
	# Existing GLB ground and city stay visible. Add a thin road surface and a
	# wider green shoulder over the gap, following the original height function.
	var old_edge:=float(field_nav.grid.region.end.x-1)*STEP
	var start_x:=old_edge-.75
	var mat:=StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo=true
	mat.vertex_color_is_srgb=true
	mat.roughness=1
	mat.cull_mode=BaseMaterial3D.CULL_DISABLED
	var st:=SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_material(mat)
	for x in range(floori(start_x),184):
		for z in range(-5,48):
			var p:=Vector2(x+.5,z+.5)
			if in_city(p):continue
			var is_road:=on_road(p)
			var shoulder:bool=(p.x>=start_x and p.x<=115 and absf(p.y)<=5) or (absf(p.x-110)<=5 and p.y>=-5 and p.y<=49) or (p.x>=105 and p.x<=185 and absf(p.y-44)<=5)
			if not is_road and not shoulder:continue
			if p.x<start_x:continue
			var tint:=Color("#ae9874") if is_road else Color("#768c58")
			tint=tint.lerp(tint.lightened(.12),.5+.5*sin(p.x*1.7+p.y*.9))
			var a:=Ground.point(Vector2(x,z))+Vector3.UP*.045
			var b:=Ground.point(Vector2(x+1,z))+Vector3.UP*.045
			var c:=Ground.point(Vector2(x+1,z+1))+Vector3.UP*.045
			var d:=Ground.point(Vector2(x,z+1))+Vector3.UP*.045
			for v in [a,b,c,a,c,d]:
				st.set_color(tint)
				st.set_normal(Vector3.UP)
				st.add_vertex(v)
	var mesh:=MeshInstance3D.new()
	mesh.name="ContinuousRoad"
	mesh.mesh=st.commit()
	root.add_child(mesh)
''',encoding="utf-8")

p=root/"ford/ground.gd"
s=p.read_text(encoding="utf-8")
# Smooth the original height discontinuity only beyond the old farming area.
s=unique(s,'if p.x>100: return .05','if p.x>100: return .05\n\tif p.x>70: return lerpf(.32,.05,(p.x-70.0)/30.0)')
p.write_text(s,encoding="utf-8")

p=root/"ford/world.gd";s=p.read_text(encoding="utf-8")
s=unique(s,'const Ground = preload("res://ford/ground.gd")','const Ground = preload("res://ford/ground.gd")\nconst ConnectedGround=preload("res://ford/connected_ground.gd")')
# In the base project ground uses inferred static type Ground. Keep old field and city
# instances for the existing enemy and trainer code, but actor uses duck-typed nav.
s=unique(s,'var ground := Ground.new()','var ground=Ground.new()')
# Initialize after city instantiation but before any loaded position validation.
s=unique(s,'\tcity_model.hide()\n','\tcity_model.show()\n\tground=ConnectedGround.new(field_ground,city_ground)\n\tConnectedGround.road_mesh(self,field_ground)\n')
s=s.replace('ground=city_ground if town else field_ground','')
# Remove blank assignment lines if they had indentation; all later calls use unified nav.
s=s.replace('city_model.visible=town','city_model.show()')
s=s.replace('for pile in piles: pile.visible=not town','for pile in piles: pile.show()')
# Both regions are permanently present. Proximity checks still govern interaction.
for old,new in [
    ('npc.visible=town','npc.show()'),
    ('merchant.visible=town','merchant.show()'),
    ('smith.visible=town','smith.show()'),
    ('npc.visible=in_town==town','npc.show()'),
]:
    s=s.replace(old,new)
# Keep the saved-point validation on the combined ground, not the old region.
# Region selection is derived from coordinates after a valid restore.
s=unique(s,'\t\tactor=saved_point if ground.legal(saved_point) else (Vector2(180,34.5) if town else START)','\t\tactor=saved_point if ground.legal(saved_point) else (Vector2(180,34.5) if town else START)\n\t\ttown=ConnectedGround.in_city(actor)')

# Existing save restore path validates coordinates through unified navigation.
# Keep the original fallback and existing region flags. No new region enum.
s=section(s,'func travel_city()','func layout_camera_buttons', '''func travel_city() -> void:
	if town_transition or hud.shade.visible:return
	# The button is now a walking destination, not a teleport.
	var destination:=Vector2(-5,1.7) if town else Vector2(180,34.5)
	walk_to(destination)
	hud.feed.text="Следуй по дороге через южные ворота."

func update_continuous_region() -> void:
	var now_town:=ConnectedGround.in_city(actor)
	hud.radar.road_mode=ConnectedGround.on_road(actor) and not now_town and not field_ground.legal(actor)
	if now_town==town:return
	town=now_town
	hud.radar.town=town
	# A walking route must survive a region crossing; clear only combat state.
	target=null
	pending=""
	collecting=null
	engaged=false
	target_ring.hide()
	hud.feed.text="Вересковый Град · Безопасная зона" if town else "Южные ворота · Открытая дорога"
	update_ui()
	save_hero()''')
# Keep normal movement and its path. No fade, actor relocation or camera reset.
s=unique(s,'\tif collecting!=null and actor.distance_to(collecting.point)<=1.65: take_pile()','\tupdate_continuous_region()\n\tif collecting!=null and actor.distance_to(collecting.point)<=1.65: take_pile()')
# Preserve town flag in older cloud data, but use position as truth after restore.
anchor='\tadd_child(hud)\n'
s=unique(s,anchor,'\ttown=ConnectedGround.in_city(actor)\n'+anchor)
# In older builds this button was visible near the old teleport. Keep it as a
# walking aid only and don't change independent trainer buttons.
s=re.sub(r'(?m)^(\s*)hud\.gateway\.visible=actor\.distance_to\(Vector2\(180,36\) if town else START\)<6$',r'\1hud.gateway.visible=true',s)
s=s.replace('hud.gateway.text="К Травяному броду" if town else "В Вересковый Град"','hud.gateway.text="Путь к заставе" if town else "Дорога в город"')
s=s.replace('hud.refresh(profile,hp,mp,"Вересковый Град" if town else "Травяной брод")','hud.refresh(profile,hp,mp,"Вересковый Град" if town else ("Южная дорога" if ConnectedGround.on_road(actor) and not field_ground.legal(actor) else "Травяной брод"))')
# Death retains original respawn behavior, and fixes the region before autosaving.
s=s.replace('\t\t\tactor=START\n\t\t\thero.position=Ground.point(actor)','\t\t\tactor=START\n\t\t\ttown=ConnectedGround.in_city(actor)\n\t\t\thud.radar.town=town\n\t\t\thero.position=Ground.point(actor)')

s=s.replace('if (point.x>100)!=town: continue','if ConnectedGround.in_city(point)!=town: continue')
# Explicitly avoid retaining a stale autoattack when entering a safe zone.
if "var auto_enabled:=" in s:
    s=unique(s,"\ttown=now_town\n\thud.radar.town=town","\ttown=now_town\n\tauto_enabled=false\n\thud.radar.town=town")
# Initialize radar immediately for saves on the road.
s=unique(s,'\thud.radar.player=actor','\thud.radar.road_mode=ConnectedGround.on_road(actor) and not town and not field_ground.legal(actor)\n\thud.radar.player=actor')
# The unified navigator is duck-typed, so route results need explicit types.
s,n=re.subn(r'(?m)^([ \t]*var path)\s*:=\s*(ground\.route\([^\n]*\))',r'\1: PackedVector2Array = \2',s)
if n<1: raise RuntimeError("Expected route type annotation")
for required in ["func layout_camera_buttons(", "func apply_quality(", "func _camera_action("]:
    if required not in s: raise RuntimeError("Existing UI function removed: "+required)
p.write_text(s,encoding="utf-8")

p=root/"field/radar.gd";s=p.read_text(encoding="utf-8")
s=unique(s,'var town:=false','var town:=false\nvar road_mode:=false')
s=re.sub(r'(?m)^func _draw\(\) -> void:\n', '''func _draw() -> void:
	if road_mode:
		draw_rect(Rect2(Vector2.ZERO,size),Color("#526348"))
		var road:=PackedVector2Array()
		for p in [Vector2(18,0),Vector2(110,0),Vector2(110,44),Vector2(180,44),Vector2(180,38)]:
			road.append(road_point(p))
		draw_polyline(road,Color("#d6bd8b"),4,true)
		draw_circle(road_point(Vector2(180,38)),4,Color("#85b9ba"))
		draw_circle(road_point(player),3.7,Color("#fff0b3"))
		draw_rect(Rect2(Vector2.ZERO,size),Color("#aaab83"),false,1)
		return
''',s,count=1)
s+='''
func road_point(p:Vector2)->Vector2:
	return (p-Vector2(10,-10))/Vector2(180,65)*size
'''
p.write_text(s,encoding="utf-8")
(root/"seamless_step2_test.gd").write_text('''extends SceneTree
const Ground=preload("res://ford/ground.gd")
const Connected=preload("res://ford/connected_ground.gd")
func _initialize()->void:
	call_deferred("run_test")
func fail(message:String)->void:
	push_error(message)
	quit(1)
func run_test()->void:
	var nav:=Connected.new(Ground.new(),Ground.new(true))
	var a:=Vector2(-5,1.7)
	var b:=Vector2(180,34.5)
	var route:=nav.route(a,b)
	if route.is_empty() or nav.route(b,a).is_empty():
		fail("City or field disconnected")
		return
	for p in route:
		if not nav.legal(p):
			fail("Route uses blocked coordinate "+str(p))
			return
	var world=preload("res://ford/ford.tscn").instantiate()
	root.add_child(world)
	await process_frame
	if not world.city_model.visible or world.get_node_or_null("ContinuousRoad")==null:
		fail("Original city or road not visible")
		return
	if get_nodes_in_group("c3_population_step1").size()<10:
		fail("Combined build lost the population update")
		return
	if world.trainers.size()!=9 or not world.merchant.visible or not world.smith.visible:
		fail("Original city services not visible")
		return
	for npc in world.trainers+world.quest_npcs:
		if not npc.visible:
			fail("Original NPC hidden")
			return
	# Start near the existing gate to exercise actual physics traversal, not a teleport.
	world.actor=Vector2(180,37.5)
	world.hero.position=Ground.point(world.actor)
	world.update_continuous_region()
	world.walk_to(Vector2(180,45))
	var previous:Vector2=world.actor
	var crossed:=false
	for i in 200:
		await physics_frame
		var point:Vector2=world.actor
		if point.distance_to(previous)>.35 or world.town_transition:
			fail("Movement jumped or triggered a scene transition")
			return
		if not world.town and point.y>39:crossed=true
		previous=point
	if not crossed or world.actor.distance_to(Vector2(180,45))>.65 or not world.city_model.visible:
		fail("Could not walk out of city")
		return
	world.walk_to(Vector2(180,37.5))
	for i in 200:
		await physics_frame
		var point:Vector2=world.actor
		if point.distance_to(previous)>.35 or world.town_transition:
			fail("Return movement jumped")
			return
		previous=point
	if not world.town or world.actor.distance_to(Vector2(180,37.5))>.65:
		fail("Could not walk back into city")
		return
	# Cross the second boundary, between the original field and added road.
	world.clear_target()
	world.actor=Vector2(39,0)
	world.hero.position=Ground.point(world.actor)
	world.update_continuous_region()
	world.walk_to(Vector2(46,0))
	previous=world.actor
	for i in 200:
		await physics_frame
		var point:Vector2=world.actor
		if point.distance_to(previous)>.35 or world.town_transition:
			fail("Field to road movement jumped")
			return
		previous=point
	if world.actor.distance_to(Vector2(46,0))>.65 or not world.hud.radar.road_mode:
		fail("Field to road crossing failed")
		return
	world.walk_to(Vector2(39,0))
	for i in 200:
		await physics_frame
	if world.actor.distance_to(Vector2(39,0))>.65 or world.hud.radar.road_mode:
		fail("Road to field crossing failed")
		return
	print("C3 seamless step 2 smoke test passed")
	quit(0)
''',encoding="utf-8")
print("Seamless candidate applied to original alpha")
