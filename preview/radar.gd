extends Control
const Ground=preload("res://ford/ground.gd")
var town:=false
var player:=Vector2.ZERO
var creatures:=PackedVector2Array()
var hostile:=PackedVector2Array()
var zoom:=3.5

func change_zoom(direction:float)->void:
	zoom=clampf(zoom*pow(1.35,direction),1.0,7.0)
	queue_redraw()

func mapped(p:Vector2)->Vector2:
	var extent:=Vector2(300,180)
	var span:=extent/(2.0*zoom)
	var center:=player.clamp(-extent*.5+span,extent*.5-span)
	return ((p-center)/extent*zoom+Vector2(.5,.5))*size

func segment(a:Vector2,b:Vector2,tint:Color,width:float)->void:
	var p:=mapped(a)
	var q:=mapped(b)
	var rect:=Rect2(Vector2(2,2),size-Vector2(4,4))
	var points:Array[Vector2]=[]
	if rect.has_point(p):points.append(p)
	if rect.has_point(q):points.append(q)
	var corners:Array[Vector2]=[rect.position,Vector2(rect.end.x,rect.position.y),rect.end,Vector2(rect.position.x,rect.end.y)]
	for i in 4:
		var hit=Geometry2D.segment_intersects_segment(p,q,corners[i],corners[(i+1)%4])
		if hit is Vector2:points.append(hit)
	if points.size()>=2:draw_line(points[0],points[1],tint,width,true)

func dot(p:Vector2,r:float,c:Color)->void:
	var m:=mapped(p)
	if Rect2(Vector2(r,r),size-Vector2(r*2,r*2)).has_point(m):draw_circle(m,r,c)

func _draw()->void:
	draw_rect(Rect2(Vector2.ZERO,size),Color("#53694b"))
	for i in range(-90,90,3):
		segment(Vector2(Ground.river(i),i),Vector2(Ground.river(i+3),i+3),Color("#739fa2"),minf(4*zoom,12))
	segment(Vector2(-150,0),Vector2(150,0),Color("#c4ad79"),2.6)
	for z in [-43,43]:segment(Vector2(10,z),Vector2(145,z),Color("#c4ad79"),1.8)
	for x in [10,105]:segment(Vector2(x,-43),Vector2(x,43),Color("#c4ad79"),1.8)
	var corners:Array[Vector2]=[Vector2(-120,-28),Vector2(-72,-28),Vector2(-72,28),Vector2(-120,28)]
	for i in 4:segment(corners[i],corners[(i+1)%4],Color("#ddc494"),1.8)
	for p in creatures:dot(p,1.5,Color("#e6bc7e"))
	for p in hostile:dot(p,1.7,Color("#e88373"))
	dot(player,3.2,Color("#fff0b3"))
	draw_rect(Rect2(Vector2.ZERO,size),Color("#aab38e"),false,1)
