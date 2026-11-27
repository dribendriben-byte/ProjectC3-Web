"""C3 v0.14: advanced class skills and class-master progression."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def patch(file,pairs):
    p=root/file
    s=p.read_text(encoding="utf-8")
    for a,b in pairs:
        if s.count(a)!=1:
            raise RuntimeError(f"{file}: expected one occurrence, got {s.count(a)}: {a[:110]!r}")
        s=s.replace(a,b,1)
    p.write_text(s,encoding="utf-8")

# Use existing persistent profession and learned-skill names; no character migration required.
patch("field/skills.gd",[
('''	"renew":[0,20.0,"Восстанавливает 25% максимальной маны."]''','''	"renew":[0,20.0,"Восстанавливает 25% максимальной маны."],
	"pierce":[12,8.0,"Дальний мощный удар (2,6× базового урона)."],
	"barrier":[12,24.0,"На 12 с уменьшает входящий урон вдвое."],
	"mend":[15,18.0,"Восстанавливает 50% максимального здоровья."],
	"surge":[10,25.0,"На 12 с усиливает автоатаку и ускоряет движение."]'''),
('static func book(hero) -> Array[Dictionary]:','''# Three additional learned abilities per existing second profession.
const SECOND := {
	"Бастион":["Крепость/barrier","Удар бастиона/crush","Последний рубеж/mend"],
	"Сумрачный щит":["Печать щита/stun","Ночной заслон/barrier","Кровавая клятва/drain"],
	"Дуэлянт":["Двойной разрез/crush","Темп дуэли/surge","Вызов клинка/stun"],
	"Копейщик":["Выпад копья/pierce","Стальной натиск/crush","Круг копий/guard"],
	"Следопыт":["Стрела следа/pierce","Лесной привал/mend","Тропа ветра/surge"],
	"Стрелок":["Орлиный выстрел/pierce","Залп/crush","Хладнокровие/focus"],
	"Огневед":["Солнечное копьё/pierce","Пламя земли/crush","Дыхание огня/surge"],
	"Костепевец":["Костяной заслон/barrier","Песнь праха/drain","Могильный зов/stun"],
	"Зверовод":["Зов стаи/pierce","Дикая ярость/surge","Тёплый очаг/mend"],
	"Целитель":["Большое исцеление/mend","Купол света/barrier","Светлый источник/renew"],
	"Провидец":["Знак грядущего/focus","Круг защиты/barrier","Пророчество жизни/mend"],
	"Лунный щит":["Лунная крепость/barrier","Серебряный таран/stun","Прилив жизни/mend"],
	"Певец клинка":["Песнь рассвета/surge","Серебряный взмах/crush","Звон стали/guard"],
	"Лесной охотник":["Охота на добычу/pierce","Лесной покров/guard","Бегущий ветер/surge"],
	"Лунный лучник":["Лунное копьё/pierce","Свет звезды/focus","Серебряный залп/crush"],
	"Ледяной голос":["Копьё инея/pierce","Холодный плен/stun","Зимний купол/barrier"],
	"Хозяин ручья":["Речной поток/pierce","Живая вода/mend","Прилив маны/renew"],
	"Хранитель росы":["Жемчужная роса/mend","Покров леса/barrier","Родник силы/renew"],
	"Рыцарь затмения":["Щит затмения/barrier","Клятва тьмы/drain","Приговор ночи/crush"],
	"Танцор стали":["Танец сумерек/surge","Вихрь стали/crush","Шаг призрака/stun"],
	"Тень ущелья":["Укол из тени/pierce","Тёмный ритм/surge","Кровавая метка/drain"],
	"Сумрачный лучник":["Стрела полуночи/pierce","Теневой залп/crush","Зоркость/focus"],
	"Глас бури":["Копьё грома/pierce","Раскат/stun","Грозовой вихрь/crush"],
	"Призыватель мглы":["Печать мглы/barrier","Ночной поток/drain","Тёмный источник/renew"],
	"Хранитель сумерек":["Ночное исцеление/mend","Купол сумерек/barrier","Звёздный источник/renew"],
	"Сокрушитель":["Разлом земли/crush","Неистовый натиск/surge","Каменный панцирь/barrier"],
	"Костолом":["Ломающий удар/crush","Тотем бури/surge","Громовая ладонь/stun"],
	"Вождь духов":["Защита предков/barrier","Великий тотем/surge","Воля духов/mend"],
	"Глашатай":["Глас предков/pierce","Песнь жизни/mend","Ритуал источника/renew"],
	"Искатель жил":["Глубинный спойл/spoil","Удар старателя/crush","Стойкость гор/mend"],
	"Рунный кузнец":["Рунный молот/crush","Крепость горна/barrier","Жар кузницы/surge"]
}

static func book(hero) -> Array[Dictionary]:'''),
('''	if FIRST.has(hero.first):
		_append(list,FIRST[hero.first],[20,28,36])
	return list''','''	if FIRST.has(hero.first):
		_append(list,FIRST[hero.first],[20,28,36])
	if SECOND.has(hero.second):
		_append(list,SECOND[hero.second],[40,52,64])
	return list'''),
('''		28: return 4500
		_: return 10000''','''		28: return 4500
		36: return 10000
		40: return 16000
		52: return 32000
		64: return 64000
		_: return 10000'''),
('return effect in ["strike","ranged","crush","drain","stun","spoil"]','return effect in ["strike","ranged","crush","drain","stun","spoil","pierce"]'),
])

# Existing skill art by effect, and clearer role descriptions for advanced careers.
patch("field/icon_library.gd",[
('const TEXTURES := {','''const TEXTURES := {
	"pierce":preload("res://field/art/icons/ranged.svg"),
	"barrier":preload("res://field/art/icons/guard.svg"),
	"mend":preload("res://field/art/icons/heal.svg"),
	"surge":preload("res://field/art/icons/haste.svg"),'''),
])
patch("field/careers.gd",[
('return 42 + int(BONUSES[race][0]) + (level()-1)*5 + (8 if first != "" else 0)','return 42 + int(BONUSES[race][0]) + (level()-1)*5 + (8 if first != "" else 0) + role_score("Щит")*12'),
('return (40 if mystic() else 26) + level()*2','return (40 if mystic() else 26) + level()*2 + role_score("Восстановление")*10'),
('return equipped_bonus("Оружие") + strength() + role_score("Оружейник")*2 + (4 if first != "" else 0) + (8 if second != "" else 0)','return equipped_bonus("Оружие") + strength() + role_score("Оружейник")*2 + role_score("Натиск")*3 + role_score("Дальний бой")*2 + (4 if first != "" else 0) + (8 if second != "" else 0)'),
])
p=root/"field/careers.gd"
s=p.read_text(encoding="utf-8")
s+='''
func role_summary() -> String:
	var labels: Array[String]=[]
	for role in ROLES:
		var points:=role_score(role)
		if points>0: labels.append(str(role)+" "+str(points))
	if labels.is_empty(): return "Стартовая дисциплина"
	return " · ".join(labels)
'''
p.write_text(s,encoding="utf-8")
# The original HUD can display 10 skill cards in two rows. Explicitly cap click search to 10.
patch("field/spellbook.gd",[
('words(Vector2(110,77),"%s  ·  %d SP" % [hero.title(),hero.sp],14,GOLD)','words(Vector2(110,77),"%s  ·  %d SP  ·  Ур. %d" % [hero.title(),hero.sp,hero.level()],14,GOLD)'),
('words(Vector2(52,334),sk.name,19,GOLD)','words(Vector2(52,334),"%s · %d МП · %.0f с" % [sk.name,sk.mp,sk.cd] if sk.has("index") else sk.name,17,GOLD)'),
])
# Promotion is offered only by a matching city master, with explicit confirmation.
patch("field/hud.gd",[
('func show_careers(hero: Careers) -> void:','func show_careers(hero: Careers, at_trainer: bool=false) -> void:'),
('''	box.add_child(label(hero.title(),30))
	var branches: Dictionary = Careers.TREE[hero.race][hero.origin]''','''	box.add_child(label(hero.title(),26))
	box.add_child(label(hero.role_summary(),14,GOLD))
	var branches: Dictionary = Careers.TREE[hero.race][hero.origin]'''),
('''	if not hero.choices().is_empty():
		box.add_child(label("Выбери профессию",16,GOLD))''','''	if hero.first.is_empty():
		box.add_child(label("Первая профессия · уровень 20",14,GOLD))
	elif hero.second.is_empty():
		box.add_child(label("Вторая профессия · уровень 40",14,GOLD))
	else:
		box.add_child(label("Вторая профессия получена. Умения: 40 / 52 / 64.",14,GOLD))
	if not hero.choices().is_empty() and not at_trainer:
		box.add_child(label("Для смены профессии найди своего мастера в городе.",14,GOLD))
	if not hero.choices().is_empty() and at_trainer:
		box.add_child(label("Выбери профессию · выбор постоянный",16,GOLD))'''),
('''			b.pressed.connect(func(): transfer_requested.emit(c))''','''			b.pressed.connect(func(): confirm_profession(hero,str(c)))'''),
])
p=root/"field/hud.gd"
s=p.read_text(encoding="utf-8")
s+='''
func confirm_profession(hero: Careers,choice: String) -> void:
	var rows:=show_panel("Новая профессия")
	rows.add_child(label("Выбрать: "+choice+"?",22,GOLD))
	rows.add_child(label("Выбор постоянный. Старые умения и прогресс сохраняются.",15))
	var yes:=button("Подтвердить")
	rows.add_child(yes)
	yes.pressed.connect(func(): transfer_requested.emit(choice))
	var no:=button("Назад")
	rows.add_child(no)
	no.pressed.connect(func(): show_careers(hero,true))
'''
p.write_text(s,encoding="utf-8")

patch("ford/world.gd",[
('var cooldowns: Array[float] = [0,0,0,0,0,0,0]','var cooldowns: Array[float] = [0,0,0,0,0,0,0,0,0,0]'),
('hud.careers_pressed.connect(func(): hud.show_careers(profile))','hud.careers_pressed.connect(func(): hud.show_careers(profile,near_trainer()))'),
('''	hud.transfer_requested.connect(func(job):
		if profile.promote(job):
			spells=Skills.book(profile)
			catalog=Actions.build(spells)
			save_hero()
			hud.shade.hide()
			update_ui())''','''	hud.transfer_requested.connect(func(job):
		if not near_trainer():
			hud.feed.text="Профессия меняется только у мастера твоего класса."
			return
		var previous_hp:=profile.hp_max()
		var previous_mp:=profile.mana_max()
		if profile.promote(job):
			spells=Skills.book(profile)
			catalog=Actions.build(spells)
			profile.hotbar=Actions.normalize(profile.hotbar,catalog,profile)
			hp=mini(profile.hp_max(),hp+maxi(0,profile.hp_max()-previous_hp))
			mp=mini(profile.mana_max(),mp+maxi(0,profile.mana_max()-previous_mp))
			save_hero()
			hud.shade.hide()
			hud.feed.text="Новая профессия: "+profile.title()+" · изучи умения у мастера."
			update_ui())'''),
('return 5.8 if sk.get("effect") in ["ranged","drain"] else REACH','return 5.8 if sk.get("effect") in ["ranged","drain","pierce"] else REACH'),
('''func cast(sk: Dictionary) -> void:
	cooldowns[sk.index]=sk.cd
	mp-=int(sk.mp)''','''func cast(sk: Dictionary) -> void:
	if not profile.knows(sk) or profile.level()<sk.level or mp<int(sk.mp) or cooldowns[sk.index]>0: return
	if Skills.offensive(sk.effect) and (target==null or target.hp<=0): return
	cooldowns[sk.index]=sk.cd
	mp-=int(sk.mp)'''),
('''		"heal":
			hp=mini(profile.hp_max(),hp+roundi(profile.hp_max()*.3))''','''		"mend":
			hp=mini(profile.hp_max(),hp+roundi(profile.hp_max()*.5))
			sound.effect("ward")
			contact(hero.position+Vector3.UP*.55,"guard")
		"barrier":
			shield=12.0
			sound.effect("ward")
			contact(hero.position+Vector3.UP*.55,"guard")
		"surge":
			haste_time=12.0
			focus_time=12.0
			sound.effect("ward")
			contact(hero.position+Vector3.UP*.55,"guard")
		"pierce":
			attack(roundi(profile.damage()*2.6),"heavy")
		"heal":
			hp=mini(profile.hp_max(),hp+roundi(profile.hp_max()*.3))'''),
('''	hud.show_book(profile,catalog,true)
''','''	if not profile.choices().is_empty():
		hud.show_careers(profile,true)
	else:
		hud.show_book(profile,catalog,true)
'''),
])
# A profession choice must not prevent a player from learning available older abilities.
patch("ford/world.gd",[
('''		"Умения": hud.show_book(profile,catalog)''','''		"Умения": hud.show_book(profile,catalog,near_trainer())'''),
])
patch("project.godot",[('config/version="0.13.0"','config/version="0.14.0"')])
patch("web/shell.html",[
('PRE-ALPHA 0.13 · ONLINE TEST / OFFLINE','PRE-ALPHA 0.14 · ONLINE TEST / OFFLINE'),
('c3-config-0130.js','c3-config-0140.js'),
('c3-online-0130.js','c3-online-0140.js'),
])
# Check every existing profession branch, legal promotions, learning and persistence of skill names.
(root/"classes_test.gd").write_text('''extends SceneTree
const Hero=preload("res://field/careers.gd")
const Skills=preload("res://field/skills.gd")
const Actions=preload("res://field/actions.gd")
func _initialize() -> void:
	var count:=0
	var seen: Dictionary={}
	for race in Hero.TREE:
		for origin in Hero.TREE[race]:
			for first in Hero.TREE[race][origin]:
				for advanced in Hero.TREE[race][origin][first]:
					var h:=Hero.new()
					h.race=race
					h.origin=origin
					if h.promote(first) or Skills.book(h).size()!=4:
						push_error("Premature promotion");quit(1);return
					h.total_xp=Hero.Experience.START[19]
					h.sp=1000000
					var starter: Dictionary=Skills.book(h)[0]
					if not h.learn(starter) or not h.promote(first) or h.promote(advanced):
						push_error("First promotion invalid");quit(1);return
					if Skills.book(h).size()!=7:
						push_error("First profession skill count");quit(1);return
					h.total_xp=Hero.Experience.START[39]
					if not h.promote(advanced) or not h.knows(starter):
						push_error("Second promotion or starter preservation failed");quit(1);return
					var skills:=Skills.book(h)
					if skills.size()!=10 or skills[7].level!=40 or skills[8].level!=52 or skills[9].level!=64 or h.learn(skills[9]):
						push_error("Advanced skills invalid");quit(1);return
					if not h.learn(skills[7]) or h.learn(skills[7]):
						push_error("Skill training validation");quit(1);return
					h.total_xp=Hero.Experience.START[63]
					if not h.learn(skills[8]) or not h.learn(skills[9]):
						push_error("Advanced skill progression");quit(1);return
					for i in range(7,10):
						var n: String=skills[i].name
						if seen.has(n):
							push_error("Duplicate advanced skill");quit(1);return
						seen[n]=true
					var entries:=Actions.build(skills)
					var bar:=Actions.initial()
					bar[9]="spell/"+str(skills[9].name)
					if Actions.normalize(bar,entries,h)[9]!=bar[9]:
						push_error("Tenth slot advanced skill validation");quit(1);return
					count+=1
	if count!=Skills.SECOND.size() or seen.size()!=count*3:
		push_error("Unmapped advanced professions");quit(1);return
	print("C3 class smoke test passed: ",count," professions, ",seen.size()," advanced skills")
	quit(0)
''',encoding="utf-8")
print("C3 v0.14 class patch complete")
