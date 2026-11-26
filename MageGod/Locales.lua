local _, ns = ...

-- English first; the Spanish client overwrites what it has
local L = {
	PREFIX = "|cff3fc7ebMageGod:|r ",
	SUBTITLE = "Quality of life for mages",
	YARDS = "yd",
	METERS = "m",
	NOT_IN_COMBAT = "not in combat: try again when the fight is over.",
	OTHER_CLASS = "only for a mage: on this character it stays hidden.",
	UNLOCKED = "displays unlocked: drag them where you want them. /magegod lock when you're done.",
	LOCKED = "displays locked.",

	-- Reminders
	BUFFS_NAME = "Missing buffs",
	FOOD_NAME = "Food and scrolls",
	FOOD_MISSING = "No XP from food",
	CLICK_CAST = "Click: cast it",
	CLICK_PICK_ARMOR = "Click: pick the armor to put on",
	CLICK_USE = "Click: use it",
	CLICK_FOOD = "Click: your XP food",
	CLICK_EAT = "Click: eat it",
	NO_XP_FOOD = "No XP food in your bags",
	WELL_FED = "Well Fed",
	FOOD_STOCK = "XP food in your bags: %s",
	IMBUE_MISSING = "Weapon not imbued",
	FAMILIAR_MISSING = "No familiar",
	DECIPHER = "Decipher a scroll",
	CLICK_DECIPHER = "Click: decipher it. It can backfire and turn you into a sheep for 8 seconds; the scroll isn't lost.",
	OPEN_BUNDLE = "Open your Bundle of Scrolls",
	COMPREHENSION = "Comprehension", -- the skill, as the game names it
	BARRIER_NAME = "Barrier",
	MANA_NAME = "Mana regen",
	MANA_LABEL = "MP5",
	BUFFS_REPORT = "armor: %s; intellect: %s; mana gem: %s; food buff: %s.",
	BUFFS_SEEN = "buffs on you: %s",
	BUFFS_HIDDEN = "the game hides your buffs in combat: try again out of it.",
	BUFF_LEFT = "%s, %s left",
	BUFF_ON = "%s, no end",
	BUFF_NONE = "none",
	BUFF_UNKNOWN = "not seen yet",
	BUFF_NOT_KNOWN = "not learned",
	GEM_HAVE = "%s (you have %d)",
	GEM_NONE = "no conjure spell learned",
	FOOD_ON = "yes",
	FOOD_OFF = "no",
	FOOD_MAX_LEVEL = "no (no XP to gain at your level)",

	-- Range
	RANGE = {
		melee = "Melee",
		nova = "Nova range",
		ranged = "In range",
		far = "Max range",
		out = "Out of range",
	},
	RANGE_NO_TARGET = "no target.",
	RANGE_REPORT = "%s at %d-%d yd; %s reaches %d yd and says %s.",
	RANGE_STEPS = "range checks: ",
	RANGE_LOADING = "(some range items not loaded yet)",
	RANGE_YES = "yes",
	RANGE_NO = "no",
	UNITS_SET = "range in %s.",
	THREAT = "AGGRO %d%%",
	THREAT_PULLED = "YOU HAVE AGGRO!",
	THREAT_NAME = "Aggro",

	-- Missile Barrage
	MISSILES_NAME = "Missile Barrage lightning",
	MISSILES_WATCHING = "lightning for %s: watching spells %s.",
	MISSILES_NOT_READY = "the lightning isn't set up yet: the addon builds it out of combat.",
	MISSILES_REFUSED = "the game didn't take the lightning's animations, so it won't show.",

	-- Blink
	PULSE_NAME = "Blink ready",

	-- Options
	TAB_BUFFS = "Reminders",
	TAB_RANGE = "Range",
	TAB_THREAT = "Aggro",
	TAB_PROCS = "Procs",
	-- Talent reset price, under the class trainer's window
	SEC_RESPEC = "Class trainer",
	OPT_RESPEC = "When the talent reset price drops, under your trainer's window",
	RESPEC_HINT = "Blizzard doesn't publish it: players report a step up with each reset (1, 5, 10, then 5 g more up to 50 g) and a step down for each week since the last one. The price the trainer asks is the real one.",
	RESPEC_TITLE = "Talent reset",
	RESPEC_CLASS = "Class talents",
	RESPEC_LEGACY = "Legacy talents",
	RESPEC_LAST = "Last one %s ago, for %s",
	RESPEC_NOW = "Now: %s",
	RESPEC_NOW_ABOUT = "Now: about %s",
	RESPEC_DROPS = "Drops to %s %s (in %s)",
	RESPEC_LOWEST = "It's at its lowest",
	RESPEC_ASKED = "The trainer asked %s, %s ago",
	RESPEC_UNKNOWN = "%s doesn't know when you last reset yet: it writes it down the next time you pay for one.",
	RESPEC_TODAY = "today at %s",
	RESPEC_TOMORROW = "tomorrow at %s",
	RESPEC_ON = "on %s at %s",
	RESPEC_WEEKDAYS = { "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" },
	RESPEC_MINUTES = "%d min",
	RESPEC_HOURS = "%d h",
	RESPEC_DAYS = "%d days",
	OPT_MISSILES = "Purple lightning around you while %s is up",
	OPT_MISSILES_SIZE = "Size (%)",
	OPT_MISSILES_X = "Left or right",
	OPT_MISSILES_Y = "Down or up",
	OPT_MISSILES_GAP = "Space between the two sides",
	OPT_MISSILES_ALPHA = "Strength of the strike as it procs (%)",
	OPT_MISSILES_CALM = "Strength afterwards, while it lasts (%)",
	OPT_MISSILES_TIMER = "The seconds it has left, under it",
	OPT_MISSILES_TIMER_SIZE = "Size of the number",
	OPT_MISSILES_COLOR = "Lightning colour",
	OPT_MISSILES_TEST = "See how it looks",
	OPT_PULSE_ALSO = "Also when %s is back",
	KICK_NAME = "Interrupt",
	OPT_KICK = "%s ready while your target casts",
	OPT_DEBUFFS = "%s and %s on your target, with stacks and seconds, beside its nameplate",
	PROCS_NAME = "Clearcasting, Heating Up and Fingers of Frost",
	PROCS_WATCHING = "%s: watching spells %s.",
	PROCS_NOT_READY = "%s isn't set up yet: the addon builds it out of combat.",
	PROCS_REFUSED = "the game didn't take the animations for %s, so they won't show.",
	PROCS_NO_TALENT = "%s: not watched, you don't have %s.",
	OPT_PROC_CLEARCASTING = "A circle of arcane light at your feet with %s (talent %s)",
	OPT_PROC_HEATING = "Embers rising on both sides of you with %s (talent %s)",
	OPT_PROC_FINGERS = "A snowflake by each hand with %s (talent %s)",
	OPT_PROC_COLOR = "Colour",
	OPT_PROC_TEST = "Try this one",
	SEC_PROCS_LOOK = "Clearcasting, Heating Up and Fingers of Frost: how they look",
	OPT_PROCS_SIZE = "Their size (%)",
	OPT_PROCS_X = "Their place: left or right",
	OPT_PROCS_Y = "Their place: down or up",
	OPT_PROCS_GAP = "Space between the embers on each side",
	OPT_PROCS_ALPHA = "Their strength as they proc (%)",
	OPT_PROCS_CALM = "Their strength afterwards, while they last (%)",
	OPT_PROCS_TIMER = "The seconds they have left",
	OPT_PROCS_TIMER_SIZE = "Size of their number",
	PROCS_HINT = "Each one only shows with its talent: Clearcasting (Arcane Concentration) makes your next damage spell free, Heating Up takes 25% off your next Pyroblast's cast for each charge, and Fingers of Frost makes your next 2 spells treat the target as Frozen. A burst as each procs, then a calmer version while it lasts. The game itself shows them, so they work in combat too; changes made in a fight wait until it's over. You can also drag them with Move displays.",
	TRY = "Try it",
	OPT_PULSE = "Its icon big in the middle each time %s is ready again",
	OPT_PULSE_SIZE = "Size",
	OPT_PULSE_ALPHA = "Strength (%)",
	OPT_PULSE_COLOR = "Colour of the shine behind it",
	PULSE_HINT = "It pops up and fades in under a second. In combat Forever hides how long a cooldown has left, but not whether it's running, so it shows in fights too. You can drag it with the Move displays button.",
	MISSILES_HINT = "Your next Arcane Missiles are free and fire faster. A big strike as it procs, then calmer lightning while it lasts. The game itself shows it, so it works in combat too; changes made in a fight wait until it's over. You can also drag it with the Move displays button.",
	SEC_BUFFS = "Your buffs",
	OPT_BUFFS_ON = "Remind me of the buffs I'm missing",
	OPT_ARMOR = "Armor",
	OPT_ARMOR_CHOICE = "Which armor",
	ARMOR_AUTO = "The last one you cast",
	ARMOR_FROST = "%s or %s",
	OPT_INTELLECT = "%s (or %s)",
	OPT_MAGIC = "Also remind me of",
	MAGIC_NONE = "Nothing else",
	OPT_WARN_TIME = "Warn before it ends (minutes)",
	OPT_IN_COMBAT = "Also in combat (all of them up top)",
	OPT_CLICK = "Click a reminder to cast it (out of combat)",
	SEC_GEMS = "Mana gems",
	OPT_GEMS_ON = "Remind me to conjure my mana gem",
	OPT_GEMS_ALL = "Every gem I know, not just the best one",
	SEC_GATHER = "Gathering tracking",
	SEC_REAGENTS = "Reagents",
	SEC_GROUP = "Group, gear and bags",
	OPT_GROUP_BUFFS = "In a group, who is missing your %s (a click casts it on them)",
	OPT_REPAIR = "Remind me when my gear wears out or my bags fill up",
	OPT_REPAIR_LOW = "Gear under (%)",
	OPT_REPAIR_BAGS = "Free bag slots, at most",
	OPT_REAGENTS = "Remind me when my reagents run low (runes, Arcane Powder, Light Feathers), unless I have %s",
	OPT_GATHER = "Herbalism or Mining: remind me to turn on %s or %s out in the world",
	SEC_FOOD = "Food",
	OPT_FOOD_ON = "A small reminder when I'm not Well Fed (+5% XP from kills)",
	SEC_SCROLLS = "Scrolls (Comprehension)",
	OPT_IMBUE = "Remind me to imbue my weapon when I carry a scroll for it",
	OPT_FAMILIAR = "Remind me to call my familiar when I carry its scroll",
	OPT_DECIPHER = "Remind me to decipher the scrolls I carry, and to open my Bundle of Scrolls",
	SCROLLS_HINT = "They show beside the chat with the food one, out of combat. Click one to use the scroll.",
	SEC_BARRIER = "Shields",
	OPT_BARRIER = "A bar with what's left of your shield: %s, %s, %s or %s",
	OPT_SHIELD_COLOR = "Colour of %s",
	OPT_BARRIER_POTIONS = "Protection potions too, in their school's colour",
	OPT_BARRIER_WIDTH = "Width",
	OPT_BARRIER_HEIGHT = "Height",
	OPT_BARRIER_TEXT = "Show how much it still absorbs",
	OPT_BARRIER_TIME = "Show the seconds it has left",
	OPT_BARRIER_ICON = "The shield's icon beside it",
	OPT_BARRIER_COLOR = "Its colour",
	BARRIER_HINT = "A priest's Power Word: Shield shows too, out of combat. The game only gives the total of every shield on you: with two at once the bar shows both, in the colour of the last one. Move it over the game's own bars with the Move displays button.",
	SEC_MANA = "Mana regeneration",
	WAND_NAME = "Wand",
	SEC_WAND = "Wand",
	OPT_WAND = "A bar with when your wand's next shot comes",
	OPT_WAND_WIDTH = "Wand bar width",
	OPT_WAND_HEIGHT = "Wand bar height",
	OPT_WAND_TIME = "The seconds to the next shot",
	OPT_WAND_ICON = "Your wand's icon beside it",
	OPT_WAND_COLOR = "Wand bar colour",
	OPT_WAND_TEST = "See it shooting",
	OPT_MANA = "A bar for the five-second rule: when your mana comes back",
	OPT_MANA_TEXT = "Show the seconds left, and what each tick gives",
	OPT_MANA_TICKS = "Then fill it up to each tick (every 2 seconds)",
	OPT_MANA_LABEL = "MP5 beside it: grey while waiting, green while it comes back",
	OPT_MANA_WAIT_COLOR = "Its colour while you wait",
	OPT_MANA_REGEN_COLOR = "Its colour while your mana comes back",
	MANA_HINT = "A spell that costs mana stops your Spirit regen for 5 seconds, and each one starts them again. Grey: waiting. Blue: your mana is coming back. Wands cost no mana.",
	SEC_DISTANCE = "Distance",
	OPT_RANGE_ON = "Show the range to your target",
	OPT_ONLY_COMBAT = "Only in combat",
	OPT_SHOW_STATE = "Show the state under the number",
	OPT_FAR = "Glow in the last 5 yards of your reach",
	OPT_RANGE_SPELL = "Spell that measures it",
	RANGE_SPELL_AUTO = "The last one you cast",
	SEC_LOOK = "Look",
	OPT_DISPLAY = "Show",
	DISPLAY = { number = "One number (32 yd)", bracket = "Between two checks (30-35 yd)" },
	OPT_UNITS = "Units",
	UNITS = { yards = "Yards", meters = "Metres" },
	OPT_FONT = "Font",
	FONTS = { fredoka = "Fredoka", changa = "Changa", game = "The game's" },
	OPT_STYLE = "Style",
	STYLE = { text = "Number", icon = "Colour square", both = "Both" },
	OPT_POSITION = "Where",
	POSITION = { plate = "On the target's nameplate", free = "Where I put it" },
	OPT_PLATE_SIDE = "Side of the nameplate",
	PLATE_SIDE = { top = "Above", bottom = "Below", left = "Left", right = "Right" },
	OPT_PLATE_GAP = "Distance from the nameplate",
	OPT_SIZE = "Size",
	PREVIEW_HINT = "Click a state to change its colour",
	SEC_THREAT = "Aggro in groups",
	OPT_THREAT = "Warn me before I pull aggro off the tank",
	OPT_THREAT_PCT = "From (% of the tank's threat)",
	THREAT_HINT = "Solo you always have the aggro, so this only shows in a group.",
	UNLOCK = "Move displays",
	LOCK = "Lock displays",
	OPT_MINIMAP_BUTTON = "Minimap button",

	-- Minimap button
	TIP_LEFT = "Left click: options",
	TIP_RIGHT_UNLOCK = "Right click: move the displays",
	TIP_RIGHT_LOCK = "Right click: lock the displays",
	TIP_DRAG = "Drag: move this button",
	TIP_GEM = "%s: %d",

	HELP = {
		"|cff3fc7ebMageGod|r commands:",
		"  /magegod  - options (or click the minimap button)",
		"  /magegod unlock | lock  - move the displays",
		"  /magegod meters | yards  - the range in metres or yards",
		"  /magegod range  - what each range check says about your target",
		"  /magegod buffs  - what the addon sees of your buffs",
		"  /magegod lightning  - try the Missile Barrage lightning",
		"  /magegod procs  - try Clearcasting, Heating Up and Fingers of Frost",
		"  /magegod wand  - try the wand's swing timer",
		"  /magegod blink  - try the pulse for Blink ready",
		"  /magegod respec  - when the talent reset price drops",
		"  /magegod button  - show or hide the minimap button",
	},
}

if GetLocale() == "esES" or GetLocale() == "esMX" then
	L.SUBTITLE = "Mejoras para magos"
	L.NOT_IN_COMBAT = "no en combate: vuelve a probar cuando acabe la pelea."
	L.OTHER_CLASS = "solo para un mago: en este personaje no se muestra."
	L.UNLOCKED = "avisos desbloqueados: arrástralos donde quieras. /magegod bloquear cuando acabes."
	L.LOCKED = "avisos bloqueados."

	L.BUFFS_NAME = "Bufos que faltan"
	L.FOOD_NAME = "Comida y pergaminos"
	L.FOOD_MISSING = "Sin exp de comida"
	L.CLICK_CAST = "Clic: lanzarlo"
	L.CLICK_PICK_ARMOR = "Clic: elegir qué armadura ponerte"
	L.CLICK_USE = "Clic: usarlo"
	L.CLICK_FOOD = "Clic: tu comida de exp"
	L.CLICK_EAT = "Clic: comerla"
	L.NO_XP_FOOD = "No llevas comida de exp"
	L.WELL_FED = "Bien alimentado"
	L.FOOD_STOCK = "comida de exp en tus bolsas: %s"
	L.IMBUE_MISSING = "Arma sin imbuir"
	L.FAMILIAR_MISSING = "Sin familiar"
	L.DECIPHER = "Descifrar un pergamino"
	L.CLICK_DECIPHER = "Clic: descifrarlo. Puede salir mal y convertirte en oveja 8 segundos; el pergamino no se pierde."
	L.OPEN_BUNDLE = "Abrir el paquete de pergaminos"
	L.COMPREHENSION = "Comprensión"
	L.BARRIER_NAME = "Barrera"
	L.MANA_NAME = "Regen. de maná"
	L.BUFFS_REPORT = "armadura: %s; intelecto: %s; gema de maná: %s; bufo de comida: %s."
	L.BUFFS_SEEN = "bufos que llevas: %s"
	L.BUFFS_HIDDEN = "el juego esconde tus bufos en combate: vuelve a probar fuera de él."
	L.BUFF_LEFT = "%s, le quedan %s"
	L.BUFF_ON = "%s, sin final"
	L.BUFF_NONE = "sin poner"
	L.BUFF_UNKNOWN = "aún sin ver"
	L.BUFF_NOT_KNOWN = "sin aprender"
	L.GEM_HAVE = "%s (llevas %d)"
	L.GEM_NONE = "ningún hechizo de conjurar aprendido"
	L.FOOD_ON = "sí"
	L.FOOD_OFF = "no"
	L.FOOD_MAX_LEVEL = "no (a tu nivel ya no ganas experiencia)"

	L.RANGE = {
		melee = "Cuerpo a cuerpo",
		nova = "Alcance de Nova",
		ranged = "A distancia",
		far = "Al límite",
		out = "Fuera de alcance",
	}
	L.RANGE_NO_TARGET = "no tienes objetivo."
	L.RANGE_REPORT = "%s a %d-%d yd; %s llega a %d yd y dice %s."
	L.RANGE_STEPS = "comprobaciones: "
	L.RANGE_LOADING = "(faltan por cargar algunos objetos de distancia)"
	L.RANGE_YES = "sí"
	L.RANGE_NO = "no"
	L.UNITS_SET = "distancia en %s."
	L.THREAT = "AGRO %d%%"
	L.THREAT_PULLED = "¡TIENES EL AGRO!"
	L.THREAT_NAME = "Agro"

	L.MISSILES_NAME = "Rayos de Misiles Arcanos"
	L.MISSILES_WATCHING = "rayos de %s: vigilando los hechizos %s."
	L.MISSILES_NOT_READY = "los rayos aún no están montados: el addon los monta fuera de combate."
	L.MISSILES_REFUSED = "el juego no aceptó las animaciones de los rayos, así que no saldrán."

	L.PULSE_NAME = "Traslación lista"

	L.TAB_BUFFS = "Recordatorios"
	L.TAB_RANGE = "Distancia"
	L.TAB_THREAT = "Agro"
	L.TAB_PROCS = "Procs"
	L.SEC_RESPEC = "Instructor de clase"
	L.OPT_RESPEC = "Cuándo baja el precio de reiniciar talentos, bajo la ventana del instructor"
	L.RESPEC_HINT = "Blizzard no lo publica: los jugadores cuentan que sube un escalón con cada reinicio (1, 5, 10 y luego 5 g más hasta 50 g) y baja uno por cada semana desde el último. El precio que pide el instructor es el real."
	L.RESPEC_TITLE = "Reinicio de talentos"
	L.RESPEC_CLASS = "Talentos de clase"
	L.RESPEC_LEGACY = "Talentos de legado"
	L.RESPEC_LAST = "El último, hace %s, por %s"
	L.RESPEC_NOW = "Ahora: %s"
	L.RESPEC_NOW_ABOUT = "Ahora: unos %s"
	L.RESPEC_DROPS = "Baja a %s %s (en %s)"
	L.RESPEC_LOWEST = "Ya está en lo más bajo"
	L.RESPEC_ASKED = "El instructor te pidió %s hace %s"
	L.RESPEC_UNKNOWN = "%s aún no sabe cuándo reiniciaste por última vez: lo apunta la próxima vez que pagues uno."
	L.RESPEC_TODAY = "hoy a las %s"
	L.RESPEC_TOMORROW = "mañana a las %s"
	L.RESPEC_ON = "el %s a las %s"
	L.RESPEC_WEEKDAYS = { "domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado" }
	L.RESPEC_MINUTES = "%d min"
	L.RESPEC_HOURS = "%d h"
	L.RESPEC_DAYS = "%d días"
	L.OPT_MISSILES = "Rayos morados a tu alrededor mientras dure %s"
	L.OPT_MISSILES_SIZE = "Tamaño (%)"
	L.OPT_MISSILES_X = "Izquierda o derecha"
	L.OPT_MISSILES_Y = "Abajo o arriba"
	L.OPT_MISSILES_GAP = "Separación entre los dos lados"
	L.OPT_MISSILES_ALPHA = "Intensidad del relámpago al salir (%)"
	L.OPT_MISSILES_CALM = "Intensidad después, mientras dura (%)"
	L.OPT_MISSILES_TIMER = "Los segundos que le quedan, debajo"
	L.OPT_MISSILES_TIMER_SIZE = "Tamaño del número"
	L.OPT_MISSILES_COLOR = "Color de los rayos"
	L.OPT_MISSILES_TEST = "Ver cómo queda"
	L.OPT_PULSE_ALSO = "También cuando vuelve %s"
	L.KICK_NAME = "Interrupción"
	L.OPT_KICK = "%s listo mientras tu objetivo lanza algo"
	L.OPT_DEBUFFS = "%s y %s en tu objetivo, con cargas y segundos, junto a su placa"
	L.PROCS_NAME = "Clearcasting, Heating Up y Fingers of Frost"
	L.PROCS_WATCHING = "%s: vigilando los hechizos %s."
	L.PROCS_NOT_READY = "%s aún no está montado: el addon lo monta fuera de combate."
	L.PROCS_REFUSED = "el juego no aceptó las animaciones de %s, así que no saldrán."
	L.PROCS_NO_TALENT = "%s: no se vigila, no tienes %s."
	L.OPT_PROC_CLEARCASTING = "Un círculo de luz arcana a tus pies con %s (talento %s)"
	L.OPT_PROC_HEATING = "Brasas subiendo a ambos lados con %s (talento %s)"
	L.OPT_PROC_FINGERS = "Un copo de hielo junto a cada mano con %s (talento %s)"
	L.OPT_PROC_COLOR = "Color"
	L.OPT_PROC_TEST = "Probar este"
	L.SEC_PROCS_LOOK = "Clearcasting, Heating Up y Fingers of Frost: cómo se ven"
	L.OPT_PROCS_SIZE = "Su tamaño (%)"
	L.OPT_PROCS_X = "Su sitio: izquierda o derecha"
	L.OPT_PROCS_Y = "Su sitio: abajo o arriba"
	L.OPT_PROCS_GAP = "Separación entre las brasas de cada lado"
	L.OPT_PROCS_ALPHA = "Su intensidad al salir (%)"
	L.OPT_PROCS_CALM = "Su intensidad después, mientras duran (%)"
	L.OPT_PROCS_TIMER = "Los segundos que les quedan"
	L.OPT_PROCS_TIMER_SIZE = "Tamaño de su número"
	L.PROCS_HINT = "Cada uno sale solo con su talento: Clearcasting (Arcane Concentration) hace gratis tu próximo hechizo de daño, Heating Up quita un 25 % al lanzamiento de tu próximo Pyroblast por cada carga y Fingers of Frost hace que tus 2 próximos hechizos traten al objetivo como congelado. Un estallido al salir cada uno y después una versión más tranquila mientras dura. Los muestra el propio juego, así que también salen en combate; lo que cambies en una pelea se aplica al acabar. También puedes arrastrarlos con Mover avisos."
	L.TRY = "Probar"
	L.OPT_PULSE = "Su icono en grande en el centro cada vez que vuelve %s"
	L.OPT_PULSE_SIZE = "Tamaño"
	L.OPT_PULSE_ALPHA = "Intensidad (%)"
	L.OPT_PULSE_COLOR = "Color del destello de detrás"
	L.PULSE_HINT = "Aparece de golpe y se desvanece en menos de un segundo. En combate Forever esconde cuánto le falta a un hechizo, pero no si está en reutilización, así que también sale en las peleas. Puedes arrastrarlo con el botón Mover avisos."
	L.MISSILES_HINT = "Tus próximos Proyectiles Arcanos no gastan maná y van más rápidos. Un gran relámpago al salir y después rayos más tranquilos mientras dura. Los muestra el propio juego, así que también salen en combate; lo que cambies en una pelea se aplica al acabar. También puedes arrastrarlos con el botón Mover avisos."
	L.SEC_BUFFS = "Tus bufos"
	L.OPT_BUFFS_ON = "Recordarme los bufos que me faltan"
	L.OPT_ARMOR = "Armadura"
	L.OPT_ARMOR_CHOICE = "Qué armadura"
	L.ARMOR_AUTO = "La última que te pusiste"
	L.ARMOR_FROST = "%s o %s"
	L.OPT_INTELLECT = "%s (o %s)"
	L.OPT_MAGIC = "Recordarme también"
	L.MAGIC_NONE = "Nada más"
	L.OPT_WARN_TIME = "Avisar antes de que se acabe (minutos)"
	L.OPT_IN_COMBAT = "También en combate (todos arriba)"
	L.OPT_CLICK = "Hacer clic en un recordatorio para lanzarlo (fuera de combate)"
	L.SEC_GEMS = "Gemas de maná"
	L.OPT_GEMS_ON = "Recordarme conjurar mi gema de maná"
	L.OPT_GEMS_ALL = "Todas las gemas que sé hacer, no solo la mejor"
	L.SEC_GATHER = "Rastreo de recolección"
	L.SEC_REAGENTS = "Reactivos"
	L.SEC_GROUP = "Grupo, equipo y bolsas"
	L.OPT_GROUP_BUFFS = "En grupo, quién no tiene tu %s (con un clic se lo lanzas)"
	L.OPT_REPAIR = "Avisarme cuando se me gaste el equipo o se me llenen las bolsas"
	L.OPT_REPAIR_LOW = "Equipo por debajo de (%)"
	L.OPT_REPAIR_BAGS = "Huecos libres en las bolsas, como mucho"
	L.OPT_REAGENTS = "Avisarme cuando me queden pocos reactivos (runas, Polvo arcano, Plumas ligeras), salvo si tengo %s"
	L.OPT_GATHER = "Herboristería o Minería: recordarme poner %s o %s fuera de mazmorras"
	L.SEC_FOOD = "Comida"
	L.OPT_FOOD_ON = "Un aviso pequeño cuando no llevo Bien alimentado (+5% de exp por muerte)"
	L.SEC_SCROLLS = "Pergaminos (Comprensión)"
	L.OPT_IMBUE = "Recordarme imbuir el arma cuando llevo un pergamino para ella"
	L.OPT_FAMILIAR = "Recordarme llamar a mi familiar cuando llevo su pergamino"
	L.OPT_DECIPHER = "Recordarme descifrar los pergaminos que llevo y abrir el paquete de pergaminos"
	L.SCROLLS_HINT = "Salen junto al chat con el de la comida, fuera de combate. Haz clic en uno para usar el pergamino."
	L.SEC_BARRIER = "Escudos"
	L.OPT_BARRIER = "Una barra con lo que le queda a tu escudo: %s, %s, %s o %s"
	L.OPT_SHIELD_COLOR = "Color de %s"
	L.OPT_BARRIER_POTIONS = "También las pociones de protección, del color de su escuela"
	L.OPT_BARRIER_WIDTH = "Ancho"
	L.OPT_BARRIER_HEIGHT = "Alto"
	L.OPT_BARRIER_TEXT = "Mostrar cuánto absorbe todavía"
	L.OPT_BARRIER_TIME = "Mostrar los segundos que le quedan"
	L.OPT_BARRIER_ICON = "El icono del escudo al lado"
	L.OPT_BARRIER_COLOR = "Su color"
	L.BARRIER_HINT = "El Palabra de poder: escudo de un sacerdote también sale, fuera de combate. El juego solo da el total de todos los escudos que llevas: con dos a la vez la barra muestra los dos, del color del último. Ponla encima de las barras del juego con el botón Mover avisos."
	L.SEC_MANA = "Regeneración de maná"
	L.WAND_NAME = "Varita"
	L.SEC_WAND = "Varita"
	L.OPT_WAND = "Una barra con cuándo sale el próximo disparo de la varita"
	L.OPT_WAND_WIDTH = "Ancho de la barra de la varita"
	L.OPT_WAND_HEIGHT = "Alto de la barra de la varita"
	L.OPT_WAND_TIME = "Los segundos hasta el próximo disparo"
	L.OPT_WAND_ICON = "El icono de tu varita al lado"
	L.OPT_WAND_COLOR = "Color de la barra de la varita"
	L.OPT_WAND_TEST = "Verla disparando"
	L.OPT_MANA = "Una barra para la regla de los 5 segundos: cuándo vuelve tu maná"
	L.OPT_MANA_TEXT = "Mostrar los segundos que faltan y lo que da cada tick"
	L.OPT_MANA_TICKS = "Después, llenarla hasta cada tick (cada 2 segundos)"
	L.OPT_MANA_LABEL = "MP5 al lado: gris mientras esperas, verde mientras vuelve"
	L.OPT_MANA_WAIT_COLOR = "Su color mientras esperas"
	L.OPT_MANA_REGEN_COLOR = "Su color mientras vuelve el maná"
	L.MANA_HINT = "Un hechizo que gasta maná corta la regeneración del Espíritu 5 segundos, y cada uno los vuelve a empezar. Gris: esperando. Azul: el maná vuelve. La varita no gasta maná."
	L.SEC_DISTANCE = "Distancia"
	L.OPT_RANGE_ON = "Mostrar la distancia a tu objetivo"
	L.OPT_ONLY_COMBAT = "Solo en combate"
	L.OPT_SHOW_STATE = "Mostrar el estado debajo del número"
	L.OPT_FAR = "Brillar en las últimas 5 yardas de tu alcance"
	L.OPT_RANGE_SPELL = "Hechizo que la mide"
	L.RANGE_SPELL_AUTO = "El último que lanzaste"
	L.SEC_LOOK = "Aspecto"
	L.OPT_DISPLAY = "Mostrar"
	L.DISPLAY = { number = "Un número (32 yd)", bracket = "Entre dos comprobaciones (30-35 yd)" }
	L.OPT_UNITS = "Unidades"
	L.UNITS = { yards = "Yardas", meters = "Metros" }
	L.OPT_FONT = "Letra"
	L.FONTS = { fredoka = "Fredoka", changa = "Changa", game = "La del juego" }
	L.OPT_STYLE = "Estilo"
	L.STYLE = { text = "Número", icon = "Cuadrado de color", both = "Los dos" }
	L.OPT_POSITION = "Dónde"
	L.POSITION = { plate = "En la placa del objetivo", free = "Donde yo la ponga" }
	L.OPT_PLATE_SIDE = "Lado de la placa"
	L.PLATE_SIDE = { top = "Encima", bottom = "Debajo", left = "Izquierda", right = "Derecha" }
	L.OPT_PLATE_GAP = "Separación de la placa"
	L.OPT_SIZE = "Tamaño"
	L.PREVIEW_HINT = "Haz clic en un estado para cambiar su color"
	L.SEC_THREAT = "Agro en grupo"
	L.OPT_THREAT = "Avisarme antes de quitarle el agro al tanque"
	L.OPT_THREAT_PCT = "Desde (% de la amenaza del tanque)"
	L.THREAT_HINT = "Solo siempre tienes tú el agro, así que esto solo sale en grupo."
	L.UNLOCK = "Mover avisos"
	L.LOCK = "Bloquear avisos"
	L.OPT_MINIMAP_BUTTON = "Botón del minimapa"

	L.TIP_LEFT = "Clic izquierdo: opciones"
	L.TIP_RIGHT_UNLOCK = "Clic derecho: mover los avisos"
	L.TIP_RIGHT_LOCK = "Clic derecho: bloquear los avisos"
	L.TIP_DRAG = "Arrastrar: mover este botón"

	L.HELP = {
		"Comandos de |cff3fc7ebMageGod|r:",
		"  /magegod  - opciones (o clic en el botón del minimapa)",
		"  /magegod desbloquear | bloquear  - mover los avisos",
		"  /magegod metros | yardas  - la distancia en metros o en yardas",
		"  /magegod rango  - qué dice cada comprobación de distancia de tu objetivo",
		"  /magegod bufos  - lo que el addon ve de tus bufos",
		"  /magegod rayos  - probar los rayos del proc de Proyectiles Arcanos",
		"  /magegod procs  - probar Clearcasting, Heating Up y Fingers of Frost",
		"  /magegod varita  - probar la barra de la varita",
		"  /magegod traslacion  - probar el aviso de Traslación lista",
		"  /magegod talentos  - cuándo baja el precio de reiniciar talentos",
		"  /magegod boton  - mostrar u ocultar el botón del minimapa",
	}
end

ns.L = L
