extends SceneTree
const Ground=preload("res://ford/ground.gd")
const World=preload("res://ford/world.gd")
const Hero=preload("res://field/careers.gd")
const Actions=preload("res://field/actions.gd")
const Loot=preload("res://field/loot.gd")
const Worn=preload("res://ford/worn.gd")

func _initialize()->void:
	call_deferred("run_test")

func fail(message:String)->void:
	push_error(message)
	quit(1)

func run_test()->void:
	var nav:=Ground.new()
	if not nav.legal(Ground.START):
		fail("Village spawn blocked")
		return
	for p in [Vector2(-71,0),Vector2(-60,0),Vector2(0,0),Vector2(60,0),Vector2(140,0),Vector2(60,-43),Vector2(60,43)]:
		if not nav.legal(p) or nav.route(Ground.START,p).is_empty():
			fail("Disconnected continuous terrain: "+str(p))
			return
	var class_count:=0
	for race in Hero.TREE:
		var list:Array=Hero.TREE[race].keys()
		for i in list.size():
			var weapon:=World.starter_weapon(race,i==1)
			if not Loot.ITEMS.has(weapon) or Loot.ITEMS[weapon][1]!="Оружие":
				fail("Invalid starter weapon")
				return
			class_count+=1
	if class_count!=9 or Actions.initial().size()!=10:
		fail("Class/slot count")
		return
	var world:=preload("res://ford/ford.tscn").instantiate()
	root.add_child(world)
	await process_frame
	if world.mobs.size()<100 or world.trainers.size()!=9 or world.villagers.size()<6:
		fail("Population missing")
		return
	if not world.town or not world.player_body is CharacterBody3D:
		fail("Physical village spawn")
		return
	var grip:=world.hero.find_child("WeaponGrip",true,false) as Node3D
	if grip==null or grip.get_parent().name!="ArmR" or grip.get_child_count()==0:
		fail("Weapon not attached to right hand")
		return
	var weapon:String=world.profile.equipment.get("Оружие","")
	if not world.profile.toggle_item(weapon):
		fail("Weapon unequip")
		return
	Worn.fit(world.hero,world.profile.equipment)
	grip=world.hero.find_child("WeaponGrip",true,false) as Node3D
	if grip==null or grip.get_child_count()!=0:
		fail("Weapon remained visible after unequip")
		return
	world.walk_to(Vector2(-67,0))
	for i in 480:
		await physics_frame
	if world.actor.x< -71.5 or world.town or not world.city_model.visible:
		fail("Could not walk out of village on continuous terrain: "+str(world.actor))
		return
	print("C3 world preview smoke test passed")
	quit(0)
