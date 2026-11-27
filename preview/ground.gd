extends RefCounted

const STEP:=1.0
const LIMIT:=Vector2(150,90)
const VILLAGE:=Vector2(-96,0)
const START:=Vector2(-85.2,0)
const CITY_SCALE:=.60
var grid:=AStarGrid2D.new()
var blocks:Array=[]
var town:=false

static func river(z:float)->float:
	return 42.0+5.0*sin(z*.037)

static func bridge(z:float)->bool:
	return absf(z)<4.0 or absf(z-43.0)<3.0 or absf(z+43.0)<3.0

static func village(p:Vector2)->bool:
	return absf(p.x-VILLAGE.x)<24.0 and absf(p.y)<28.0

static func road(p:Vector2)->bool:
	return absf(p.y)<3.1 or (p.x>5 and (absf(p.y-43)<2.7 or absf(p.y+43)<2.7)) or (absf(p.x-10)<2.8 and absf(p.y)<46) or (absf(p.x-105)<2.6 and absf(p.y)<46)

static func height(p:Vector2)->float:
	var flatness:=smoothstep(-66.0,-48.0,p.x)
	var rolling:float=(.62+.57*sin(p.x*.055)*cos(p.y*.062)+.33*sin(p.y*.13)+.18*cos(p.x*.17+p.y*.09))*flatness
	if road(p): rolling*=.35
	var gap:=absf(p.x-river(p.y))
	if gap<5.5 and not bridge(p.y):
		rolling=lerpf(-1.05,rolling,smoothstep(2.4,5.5,gap))
	elif gap<4.4 and bridge(p.y):
		rolling=lerpf(.29,rolling,smoothstep(2.4,4.4,gap))
	return rolling+.02

static func point(p:Vector2)->Vector3:
	return Vector3(p.x,height(p),p.y)

static func sector(p:Vector2)->String:
	if village(p): return "Деревня Пробуждения"
	if p.x< -24: return "Поля Рассвета"
	if p.x<40: return "Вересковый лес"
	if p.y< -23: return "Руины Дозора"
	if p.x>92: return "Каменные пустоши"
	return "Сланцевый карьер"

func _init(_city:bool=false)->void:
	# Original city's south gate is rotated east. Transform its authored obstacle list.
	var source=JSON.parse_string(FileAccess.get_file_as_string("res://ford/models/city_blocks.json"))
	if source is Array:
		for b in source:
			blocks.append([VILLAGE.x+float(b[1])*CITY_SCALE,-(float(b[0])-180.0)*CITY_SCALE,float(b[3])*CITY_SCALE,float(b[2])*CITY_SCALE])
	# Wall runs with wide open east/west gates; no invisible loading boundary.
	for side in [-1,1]:
		blocks.append([VILLAGE.x,side*27.5,23.5,.65])
		for wing in [-1,1]:
			blocks.append([VILLAGE.x+side*24.0,wing*15.0,.65,12.0])
	grid.region=Rect2i(-150,-90,301,181)
	grid.cell_size=Vector2.ONE*STEP
	grid.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.update()
	for y in range(-90,91):
		if bridge(y): continue
		var center:=river(y)
		for x in range(floori(center-3.1),ceili(center+3.1)+1):
			if absf(float(x)-center)<3.1: grid.set_point_solid(Vector2i(x,y),true)
	for b in blocks:
		for x in range(ceili(float(b[0])-float(b[2])-.40),floori(float(b[0])+float(b[2])+.40)+1):
			for y in range(ceili(float(b[1])-float(b[3])-.40),floori(float(b[1])+float(b[3])+.40)+1):
				var id:=Vector2i(x,y)
				if grid.region.has_point(id): grid.set_point_solid(id,true)

func legal(p:Vector2)->bool:
	if absf(p.x)>LIMIT.x-.5 or absf(p.y)>LIMIT.y-.5: return false
	if absf(p.x-river(p.y))<3.0 and not bridge(p.y): return false
	for b in blocks:
		if absf(float(b[0])-p.x)<float(b[2])+.32 and absf(float(b[1])-p.y)<float(b[3])+.32: return false
	return true

func open_cell(p:Vector2)->Vector2i:
	var original:=Vector2i((p/STEP).round())
	var best:=original
	var distance:=INF
	for dy in range(-2,3):
		for dx in range(-2,3):
			var q:=original+Vector2i(dx,dy)
			if not grid.region.has_point(q) or grid.is_point_solid(q): continue
			var d:float=p.distance_squared_to(Vector2(q)*STEP)
			if d<distance:
				distance=d
				best=q
	return best

func route(a:Vector2,b:Vector2)->PackedVector2Array:
	if not legal(b): return PackedVector2Array()
	var start:=open_cell(a)
	var end:=open_cell(b)
	if not grid.region.has_point(start) or not grid.region.has_point(end) or grid.is_point_solid(start) or grid.is_point_solid(end): return PackedVector2Array()
	var trail:=grid.get_point_path(start,end)
	if trail.is_empty(): return trail
	if trail.size()>1 and a.distance_to(trail[0])<.25: trail.remove_at(0)
	trail.append(b)
	return trail

func slide(p:Vector2,delta:Vector2)->Vector2:
	if legal(p+delta): return p+delta
	var q:=p
	if legal(q+Vector2(delta.x,0)): q.x+=delta.x
	if legal(q+Vector2(0,delta.y)): q.y+=delta.y
	return q
