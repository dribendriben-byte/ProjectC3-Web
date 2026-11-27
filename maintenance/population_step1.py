"""Small, reversible population update. Apply ONLY to a known-good alpha source tree."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"ford/world.gd"
s=p.read_text(encoding="utf-8")
anchor="\tadd_child(hud)\n"
if s.count(anchor)!=1 or "func add_extra_population_step1" in s:
    raise RuntimeError("Unknown or already patched world source")
if "var field_ground" not in s or "var mobs:" not in s:
    raise RuntimeError("Existing navigation or creature list missing")
s=s.replace(anchor,"\tadd_extra_population_step1()\n"+anchor,1)
s+='''
# Preserve the existing scene, terrain, enemy AI, saves, quests and accounts.
# New low-level packs are scattered across both riverbanks; no spawn on the road.
func add_extra_population_step1() -> void:
	var points: Array[Vector2] = [
		Vector2(-7,-8),Vector2(-11,-9),Vector2(-15,-8),Vector2(-18,-11),
		Vector2(-18,10),Vector2(-13,9),Vector2(-9,11),Vector2(-5,9),
		Vector2(5,-9),Vector2(8,-12),Vector2(12,-11),Vector2(17,-11),
		Vector2(18,9),Vector2(15,12),Vector2(9,12),Vector2(5,8),
		Vector2(-17,5),Vector2(-7,6),Vector2(19,1)]
	var added := 0
	for point in points:
		if added>=16: break
		if point.distance_to(START)<5.0 or absf(point.y)<3.0: continue
		var safe := true
		for offset in [Vector2.ZERO,Vector2(.8,0),Vector2(-.8,0),Vector2(0,.8),Vector2(0,-.8)]:
			if not field_ground.legal(point+offset):
				safe=false
				break
		if not safe or field_ground.route(START,point).is_empty(): continue
		for existing in mobs:
			if existing.home.distance_to(point)<2.8:
				safe=false
				break
		if not safe: continue
		var creature := Beast.new()
		add_child(creature)
		var level_: int=1 if point.x<0 else (2 if point.x<12 else 3)
		creature.setup(point,level_,mobs.size())
		creature.add_to_group("c3_population_step1")
		mobs.append(creature)
		added+=1
	print("C3 population step 1: ",added," additional creatures")
'''
p.write_text(s,encoding="utf-8")
(root/"population_step1_test.gd").write_text('''extends SceneTree
func _initialize()->void:
	call_deferred("run_test")
func run_test()->void:
	var world=preload("res://ford/ford.tscn").instantiate()
	root.add_child(world)
	await process_frame
	var extras:=get_nodes_in_group("c3_population_step1")
	if extras.size()<10 or extras.size()>16:
		push_error("Unexpected extra population: "+str(extras.size()))
		quit(1)
		return
	for mob in extras:
		if not world.field_ground.legal(mob.home) or world.field_ground.route(world.START,mob.home).is_empty():
			push_error("Unreachable extra spawn")
			quit(1)
			return
		for other in world.mobs:
			if other!=mob and mob.home.distance_to(other.home)<2.8:
				push_error("Crowded spawn")
				quit(1)
				return
	print("C3 population smoke test passed")
	quit(0)
''',encoding="utf-8")
print("Small population patch applied; no changes to login, saves, battle or map bounds.")
