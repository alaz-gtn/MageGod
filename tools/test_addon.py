"""Loads the addon against a mocked WoW API (LuaJIT = Lua 5.1) and checks its behaviour.

Usage: python -I test_addon.py <MageGod folder> [enUS|esES]
Needs: pip install lupa
"""
import re
import sys
from pathlib import Path

from lupa.luajit21 import LuaRuntime

ADDON = Path(sys.argv[1])
LOCALE = sys.argv[2] if len(sys.argv) > 2 else "enUS"
lua = LuaRuntime(unpack_returned_tuples=True)

printed = []
lua.globals().py_print = lambda *a: printed.append(" ".join(str(x) for x in a))
lua.globals().LOCALE = LOCALE

lua.execute(r'''
print = function(...) local t = {} for i = 1, select("#", ...) do t[#t+1] = tostring((select(i, ...))) end py_print(table.concat(t, " ")) end
format = string.format; strlower = string.lower; max = math.max; min = math.min; abs = math.abs; floor = math.floor; ceil = math.ceil
strtrim = function(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end
wipe = function(t) for k in pairs(t) do t[k] = nil end return t end
GetLocale = function() return LOCALE end
-- A value the game hides from addons
SECRET = {}
-- A hidden value that still carries what it hides, for the game's own setters to use
function Hidden(v) return { hidden = v } end
local function Unwrap(v) if type(v) == "table" and v.hidden ~= nil then return v.hidden end return v end
issecretvalue = function(v) return v == SECRET or (type(v) == "table" and v.hidden ~= nil) end

SPELLS = {
  [168] = "Frost Armor", [7300] = "Frost Armor", [7301] = "Frost Armor",
  [7302] = "Ice Armor", [7320] = "Ice Armor", [10219] = "Ice Armor", [10220] = "Ice Armor",
  [6117] = "Mage Armor", [22782] = "Mage Armor", [22783] = "Mage Armor",
  [1459] = "Arcane Intellect", [1460] = "Arcane Intellect", [10157] = "Arcane Intellect",
  [23028] = "Arcane Brilliance",
  [604] = "Dampen Magic", [1008] = "Amplify Magic",
  [759] = "Conjure Mana Agate", [3552] = "Conjure Mana Jade", [10053] = "Conjure Mana Citrine", [10054] = "Conjure Mana Ruby",
  [19705] = "Well Fed",
  [116] = "Frostbolt", [133] = "Fireball", [5143] = "Arcane Missiles",
  [11426] = "Ice Barrier", [13033] = "Ice Barrier", [1463] = "Mana Shield",
  [1953] = "Blink",
  [400588] = "Missile Barrage", [400589] = "Missile Barrage", [401736] = "Missile Barrage", [467409] = "Missile Barrage",
}
-- How far each spell reaches
REACH = { Frostbolt = 30, Fireball = 35, ["Arcane Missiles"] = 30 }

-- Game state the tests change
G = { class = "MAGE", level = 20, known = {}, auras = {}, auraTimes = {}, secret = false, combat = false,
      now = 100, timers = {}, target = nil, dist = 27, secretRange = false, uncached = {}, items = {},
      group = false, threat = nil, plate = nil, speed = {}, cursor = { 0, 100 }, dead = false, bags = {},
      epoch = 1000000, mainHand = nil, weaponEnchant = false, mana = 1000, manaMax = 1000, secretMana = false,
      tipsLoading = false }
-- Your mana, and what each spell costs (Shoot, the wand, nothing)
MANA_COSTS = { [116] = 25, [133] = 30, [5019] = 0 }
UnitPower = function() if G.secretMana then return Hidden(G.mana) end return G.mana end
UnitPowerMax = function() return G.manaMax end
-- A screen pixel is half a UI unit here
PixelUtil = { GetPixelToUIUnitFactor = function() return 0.5 end }
C_CurveUtil = { CreateCurve = function()
  local c = { points = {} }
  function c:SetType() end
  function c:AddPoint(x, y) table.insert(self.points, { x, y }) end
  return c
end }
local function EvalCurve(c, x)
  local p = c.points
  if x <= p[1][1] then return p[1][2] end
  for i = 2, #p do if x <= p[i][1] then local a, b = p[i - 1], p[i] return a[2] + (b[2] - a[2]) * (x - a[1]) / (b[1] - a[1]) end end
  return p[#p][2]
end
UnitPowerPercent = function(_, _, _, curve)
  local share = G.mana / G.manaMax
  local v = curve and EvalCurve(curve, share) or share
  if G.secretMana then return Hidden(v) end
  return v
end
time = function() return G.epoch end
-- Weapons by item: their subclass (staff 10, dagger 15)
WEAPONS = { [900] = 10, [901] = 15 }
GetInventoryItemID = function(_, slot) if slot == 16 then return G.mainHand end end
GetWeaponEnchantInfo = function() return G.weaponEnchant end
FAMILIAR_SPELLS = { [275069] = "Rat Familiar", [277483] = "Frog Familiar", [277493] = "Cat Familiar" }
-- Food in the bags: by bag, { itemID, count }; what each one's tooltip says
NUM_BAG_SLOTS = 4
FOODS = { [700] = "Roast Raptor", [701] = "Freshly Baked Bread", [702] = "Spiced Wolf Meat",
  [703] = "Roasted Boar Meat", [704] = "Smoked Bear Meat" }
ITEM_SPELL_TRIGGER_ONUSE = "Use:"
FOOD_TIPS = {
  [700] = "Use: Restores 1392 health over 27 sec. If you spend at least 10 seconds eating you will become well fed and gain 12 Stamina and Spirit for 15 min.",
  [701] = "Use: Restores 552 health over 24 sec. Must remain seated while eating.",
  [702] = "Use: Restores 294 health over 21 sec. If you spend at least 10 seconds eating you will become well fed and gain 6 Stamina and Spirit for 15 min.",
  -- As Forever words it
  [703] = "Use: Restores 58 health over 18 sec.  Must remain seated while eating.  If you spend at least 10 sec eating, you will become well fed and gain 1 Strength for 15 min.  Additionally, experience gained from kills is increased by 5%. (1 Sec Cooldown)",
  [704] = "Use: Restores 294 health over 21 sec. If you spend at least 10 sec eating, you will become well fed and gain 6 Stamina and Spirit for 15 min.",
}
C_Container = {
  GetContainerNumSlots = function(bag) return G.bags[bag] and #G.bags[bag] or 0 end,
  GetContainerItemInfo = function(bag, slot) local it = G.bags[bag] and G.bags[bag][slot] if it then return { itemID = it[1], stackCount = it[2] } end end,
}
C_TooltipInfo = { GetBagItem = function(bag, slot)
  local it = G.bags[bag] and G.bags[bag][slot]
  if not it then return end
  TIP_LOOKS = (TIP_LOOKS or 0) + 1
  -- Before the game has loaded what the item does, only its name
  if G.tipsLoading then return { lines = { { leftText = FOODS[it[1]] } } } end
  return { lines = { { leftText = FOODS[it[1]] }, { leftText = FOOD_TIPS[it[1]] } } }
end }

UnitClass = function() return "Class", G.class end
UnitLevel = function() return G.level end
GetMaxPlayerLevel = function() return 60 end
UnitRace = function() return "Human", "Human" end
GetTime = function() return G.now end
IsPlayerSpell = function(id) return G.known[id] or false end
local function KnownByName(name) for id in pairs(G.known) do if G.known[id] and SPELLS[id] == name then return true end end end
PASSIVE = {}
C_Spell = {
  GetSpellName = function(id) return SPELLS[id] end,
  IsSpellPassive = function(id) return PASSIVE[id] or false end,
  GetSpellTexture = function(id) return id end,
  GetSpellInfo = function(name) if KnownByName(name) then return { name = name, maxRange = REACH[name] } end end,
  GetSpellPowerCost = function(id) local c = MANA_COSTS[id] if c then return { { type = 0, cost = c, costPerSec = 0 } } end return {} end,
  IsSpellInRange = function(spell)
    if G.secretRange then return SECRET end
    if REACH[spell] and KnownByName(spell) then return G.dist <= REACH[spell] end
  end,
}
C_UnitAuras = { GetAuraDataByIndex = function(_, i)
  if G.secret then return SECRET end
  local name = G.auras[i] if not name then return end
  local t = G.auraTimes[name]
  return { name = name, expirationTime = t and t[1] or 0, duration = t and t[2] or 0, spellId = t and t[3] } end }
C_Secrets = { ShouldAurasBeSecret = function() return G.secret end }
-- Spell cooldowns, by spell: what C_Spell.GetSpellCooldown hands over
COOLDOWNS = {}
C_Spell.GetSpellCooldown = function(id) return COOLDOWNS[id] end
C_Spell.GetSpellCooldownDuration = function(id)
  local cd = COOLDOWNS[id]
  return { IsZero = function() if cd and cd.secretZero then return SECRET end return not (cd and cd.isActive and not cd.gcd) end }
end
C_NamePlate = { GetNamePlateForUnit = function() return G.plate end }
UnitExists = function(u) if u == "target" then return G.target ~= nil end return true end
UnitCanAttack = function() return G.target and G.target.hostile end
UnitIsDead = function() return false end
UnitIsDeadOrGhost = function() return G.dead end
UnitOnTaxi = function() return false end
UnitAffectingCombat = function() return G.combat end
InCombatLockdown = function() return G.combat end
CheckInteractDistance = function(_, i) if G.secretRange then return SECRET end return G.dist <= (i == 3 and 8 or 28) end
GetUnitSpeed = function(u) return G.speed[u] or 0 end
IsInGroup = function() return G.group end
UnitGetTotalAbsorbs = function() return G.absorb end
UnitDetailedThreatSituation = function() if G.threat then return G.threat[1], G.threat[2], G.threat[3], G.threat[4] end end
C_Item = {
  GetItemInfo = function(id) if ITEM_YARDS[id] then return "range item" end end,
  IsItemDataCachedByID = function(id) return not G.uncached[id] end,
  IsItemInRange = function(id)
    if G.secretRange then return SECRET end
    if G.uncached[id] or not ITEM_YARDS[id] then return nil end
    return G.dist <= ITEM_YARDS[id]
  end,
  RequestLoadItemDataByID = function() end,
  GetItemCount = function(id) return G.items[id] or 0 end,
  GetItemNameByID = function(id) return FOODS[id] or "gem " .. id end,
  GetItemIconByID = function(id) return id * 10 end,
  GetItemSpell = function(id) return FAMILIAR_SPELLS[id] end,
  GetItemInfoInstant = function(id) local w = WEAPONS[id] if w then return id, "t", "s", "", 0, 2, w end
    if FOODS[id] then return id, "t", "s", "", 0, 0, 5 end return id, "t", "s", "", 0, 15, 0 end,
}
ITEM_YARDS = {}
function BuildItemYards(ns) for _, step in ipairs(ns.RANGE_ITEMS) do for _, id in ipairs(step[2]) do ITEM_YARDS[id] = step[1] end end end
function Uncache(ns, yards) for _, step in ipairs(ns.RANGE_ITEMS) do if step[1] == yards then for _, id in ipairs(step[2]) do G.uncached[id] = true end end end end
C_Timer = { After = function(t, f) table.insert(G.timers, f) end, NewTicker = function() return { Cancel = function() end } end }
function RunTimers() local t = G.timers G.timers = {} for _, f in ipairs(t) do f() end end
GetCursorPosition = function() return G.cursor[1], G.cursor[2] end

-- Frames and textures: the methods the tests look at keep their state, the rest do nothing
local function Texture() local t = { shown = true } setmetatable(t, { __index = function(_, k) return function(self, ...)
  if k == "SetShown" then self.shown = (...) and true or false
  elseif k == "Hide" then self.shown = false elseif k == "Show" then self.shown = true
  elseif k == "IsShown" then return self.shown
  elseif k == "SetTexture" then self.tex = ... elseif k == "SetDesaturated" then self.desat = ...
  elseif k == "SetColorTexture" or k == "SetTextColor" or k == "SetVertexColor" then self.color = { ... }
  elseif k == "SetText" then self.text = ... elseif k == "GetStringWidth" then return #tostring(self.text or "") * 6
  elseif k == "SetFormattedText" then
    local args = { ... }
    for i = 2, #args do if issecretvalue(args[i]) then self.hiddenText = true end args[i] = Unwrap(args[i]) end
    self.text = format(unpack(args))
  elseif k == "SetFont" then self.font = { ... }
  elseif k == "SetFontObject" then local o = ... self.fontObject = o self.font = o and o.font self.color = nil
  elseif k == "GetTextColor" then if rawget(self, "color") then return unpack(self.color) end
  elseif k == "SetPoint" then self.points = rawget(self, "points") or {} table.insert(self.points, { ... })
  elseif k == "ClearAllPoints" then self.points = {}
  elseif k == "GetText" then return self.text
  elseif k == "CreateAnimationGroup" then return CreateFrame("Frame") end
end end }) return t end
NAMED = {}
function CreateFrame(kind, name, parent, template)
  local f = { scripts = {}, events = {}, kind = kind, parent = parent, template = template, shown = true, attrs = {}, width = 100 }
  setmetatable(f, { __index = function(_, k)
    if k:match("^Create") then return function() return CreateFrame("Frame") end end
    if k:match("^%u") then return function() end end
  end })
  function f:SetScript(n, fn) self.scripts[n] = fn end
  function f:GetScript(n) return self.scripts[n] end
  function f:RegisterEvent(e) self.events[e] = true end
  function f:RegisterUnitEvent(e) self.events[e] = true end
  function f:UnregisterEvent(e) self.events[e] = nil end
  function f:CreateTexture() return Texture() end
  function f:CreateFontString() return Texture() end
  function f:SetAlpha(a) self.alpha = Unwrap(a) self.hiddenAlpha = issecretvalue(a) end
  function f:SetStatusBarColor(...) self.barColor = { ... } end
  function f:SetShown(v) self.shown = v and true or false end
  function f:Hide() self.shown = false end function f:Show() self.shown = true end
  function f:IsShown() return self.shown end
  function f:IsVisible() return self.shown end
  function f:SetChecked(v) self.checked = v and true or false end
  function f:GetChecked() return self.checked end
  function f:GetFrameLevel() return 1 end
  function f:GetParent() return self.parent end
  function f:SetPoint(...) self.point = { ... } end
  function f:GetPoint() local p = self.point return p[1], p[2], p[3], p[4], p[5] end
  function f:SetSize(w, h) self.width, self.height = w, h end
  function f:SetWidth(w) self.width = w end
  function f:SetHeight(h) self.height = h end
  function f:HookScript(n, fn) self.hooks = self.hooks or {} self.hooks[n] = fn end
  function f:GetWidth() return self.width end
  function f:GetHeight() return self.height end
  function f:GetCenter() return 0, 0 end
  function f:GetEffectiveScale() return 1 end
  function f:SetText(t) self.text = t end
  function f:GetText() return self.text end
  function f:SetValue(v) self.value = Unwrap(v) self.hiddenValue = issecretvalue(v) end
  function f:SetMinMaxValues(a, b) self.minmax = { Unwrap(a), Unwrap(b) } end
  function f:SetAttribute(k, v) self.attrs[k] = v end
  function f:GetAttribute(k) return self.attrs[k] end
  function f:GetLeft() return 300 end
  function f:GetBottom() return 500 end
  function f:SetScale(s) self.scale = s end
  function f:Play() self.playing = true end
  function f:Stop() self.playing = false end
  -- Forever's aura container: one slot, whose button the addon dresses; the game plays what it's given
  if kind == "AuraContainer" then
    function f:SetEnabled(v) self.enabled = v end
    function f:SetUnit(u) self.unit = u end
    function f:AddAuraSlot(key, filter, options)
      self.slot = { key = key, filter = filter, options = options }
      local button = CreateFrame("Button", nil, self)
      button.shownAnims, button.assignedAnims = {}, {}
      function button:AddAuraShownAnimation(g) table.insert(self.shownAnims, g) end
      function button:AddAuraAssignedAnimation(g) table.insert(self.assignedAnims, g) end
      function button:SetDurationText(text, opts) self.durationText = { text = text, options = opts } end
      self.button = button
      options.initializeFrame(button)
    end
  end
  FRAMES = FRAMES or {} table.insert(FRAMES, f)
  if name then NAMED[name] = f end
  return f
end
-- Font objects: one per name, the last font set on it counts
FONT_OBJECTS = {}
function CreateFont(name)
  local f = { name = name }
  function f:SetFont(...) self.font = { ... } end
  function f:GetFont() return unpack(self.font) end
  FONT_OBJECTS[name] = f
  return f
end
UIParent = CreateFrame("Frame")
Minimap = CreateFrame("Frame")
ChatFrame1 = CreateFrame("Frame")
Minimap.width = 140
GameFontNormal = { GetFont = function() return "font" end }
UISpecialFrames = {}
CustomAuraContainerAuraProcessingPolicy = { None = 0 }
Enum = { NumericRuleFormatRounding = { Up = 2 } }
C_StringUtil = { CreateNumericRuleFormatter = function()
  return { SetBreakpoints = function(self, rules) self.rules = rules end }
end }
ColorPickerFrame = { SetupColorPickerAndShow = function(self, info) COLOR_INFO = info end, GetColorRGB = function() return 0, 0, 1 end }
SOUNDKIT = { IG_MAINMENU_OPTION_CHECKBOX_ON = 1 }
PlaySound = function() end
TOOLTIP = {}
GameTooltip = { SetOwner = function() TOOLTIP = {} end, AddLine = function(_, s) table.insert(TOOLTIP, s) end, Show = function() end }
GameTooltip_Hide = function() end
SlashCmdList = {}

-- The reminder icons showing, in order
function ShownIcons(parent)
  local t = {}
  for _, f in ipairs(FRAMES) do if f.parent == parent and f.shown and f.icon then t[#t + 1] = f end end
  return t
end
function Same(a, b) return rawequal(a, b) end
function Fire(event, ...) for _, f in ipairs(FRAMES) do if f.events[event] and f.scripts.OnEvent then f.scripts.OnEvent(f, event, ...) end end end
''')

load = lua.eval('function(src, name) return assert(loadstring(src, "@" .. name)) end')
ns = lua.table()
toc = Path(ADDON, "MageGod.toc").read_text(encoding="utf-8")
for fname in re.findall(r"^(\w+\.lua)$", toc, re.M):
    load(Path(ADDON, fname).read_text(encoding="utf-8"), fname)("MageGod", ns)

G = lua.globals()
S = G.G  # the game state
G.BuildItemYards(ns)
L = ns.L
es = LOCALE in ("esES", "esMX")
fails = []


def check(cond, msg):
    print(("OK   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


def slash(arg):
    printed.clear()
    G.SlashCmdList.MAGEGOD(arg)
    return list(printed)


def know(*ids, on=True):
    for i in ids:
        S.known[i] = on
    G.Fire("SPELLS_CHANGED")


def auras(**times):
    """auras(name=(seconds left, duration[, spell id])) puts those buffs on you"""
    S.auras = lua.table(*[n.replace("_", " ") for n in times])
    S.auraTimes = lua.table()
    for n, (left, *rest) in times.items():
        S.auraTimes[n.replace("_", " ")] = lua.table(S.now + left if left else 0, *rest)
    G.Fire("UNIT_AURA", "player")


row = G.NAMED["MageGodBuffs"]
food = G.NAMED["MageGodFood"]


def icons():
    return [(i.icon.tex, bool(i.icon.desat), i.text.text) for i in G.ShownIcons(row).values()] if row.shown else []


# ---------------------------------------------------------------- Login: a level 20 mage
S.known = lua.table()
for i in (168, 1459, 116, 133, 5143):
    S.known[i] = True
G.Fire("ADDON_LOADED", "MageGod")
G.Fire("PLAYER_LOGIN")
db = G.MageGodDB
check(db.buffs.enabled and db.range.enabled and db.gems.enabled and db.food.enabled, "settings filled in from the defaults")
check(icons() == [(168, True, ""), (1459, True, "")],
      f"no buffs on: Frost Armor and Arcane Intellect, grey: {icons()}")


def extras():
    if not food.shown:
        return []
    return [(r.text.text, r.attrs["type"], r.attrs["macrotext"] or r.attrs["item"] or r.attrs["spell"])
            for r in G.ShownIcons(food).values()]


check(extras() == [(L.FOOD_MISSING, None, None)], f"and the small food reminder, nothing to click: {extras()}")
check(food.point[1] == "LEFT" and G.Same(food.point[2], G.ChatFrame1) and food.point[3] == "RIGHT",
      "it sits beside the chat until you move it")
db.positions.food = lua.table("CENTER", "CENTER", 10, 20)
ns.PlaceFrame(food)
check(food.point[1] == "CENTER" and G.Same(food.point[2], G.UIParent) and food.point[4] == 10, "moved: where you put it")
db.positions.food = None
ns.PlaceFrame(food)
out = slash("")
check(G.NAMED["MageGodOptions"] is not None and G.NAMED["MageGodOptions"].shown, "/magegod opens the options")
slash("")

# ---------------------------------------------------------------- Buffs on, and running out
auras(Frost_Armor=(1700, 1800), Arcane_Intellect=(3500, 3600), Well_Fed=(800, 900))
check(icons() == [] and not row.shown and not food.shown, "armor, intellect and Well Fed on: nothing")
S.now = S.now + 3420  # intellect has 80 s left, the armor has run out
auras(Arcane_Intellect=(80, 3600), Well_Fed=(800, 900))
check(icons() == [(168, True, "")], f"armor gone: up top, grey: {icons()}")
check(extras() == [("Arcane Intellect  1:20", "spell", "Arcane Intellect")],
      f"intellect in its last 2 minutes: beside the chat with its time, a click casts it again: {extras()}")
header = list(G.ShownIcons(food).values())[0]
check(header.height == 30 and header.attrs["unit"] == "player" and not header.icon.desat, "bigger than the food rows, on you, in colour")
check(tuple(round(c, 2) for c in header.text.color.values()) == (0.45, 0.85, 1) and header.back.color[4] == 0.8
      and header.stripe.color[1] == 0.25 and header.edge.color[1] == 0.25,
      "mage look: a dark bar with a blue stripe, the icon in a blue frame, light blue text")
check(header.text.font[1] == "Fonts\\ARIALN.TTF" and header.text.font[2] == 16, f"in the game's thin narrow font: {list(header.text.font.values())}")
db.buffs.warnMinutes = 1
ns.UpdateBuffs()
check(icons() == [(168, True, "")] and extras() == [], "warning only in the last minute: intellect not yet")
db.buffs.warnMinutes = 2
auras(Frost_Armor=(1800, 1800), Arcane_Intellect=(3600, 3600), Well_Fed=(800, 900))
check(icons() == [], "both cast again: nothing")
check(ns.BuffState("armor")[1] == "frost", "the addon knows which armor is on")

# ---------------------------------------------------------------- In combat Forever hides your buffs
S.combat, S.secret = True, True
G.Fire("PLAYER_REGEN_DISABLED")
G.Fire("UNIT_AURA", "player")
check(icons() == [], "in combat, buffs hidden: still known to be on")
S.now = S.now + 1750  # the armor has 50 s left
ns.UpdateBuffs()
check(icons() == [] and not food.shown, "in combat nothing shows, not even what's running out")
db.buffs.combat = True
ns.UpdateBuffs()
check(icons() == [(168, False, "0:50")], f"with 'also in combat' on, the armor's time counted from what was seen, up top: {icons()}")
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 168)
check(icons() == [], "Frost Armor cast in combat: taken as on, for its 30 minutes")
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", G.SECRET)
check(icons() == [], "a hidden spell id is left alone")
S.now = S.now + 1750
ns.UpdateBuffs()
check(icons() == [(168, False, "0:50"), (1459, False, "1:40")],
      f"and runs out again, with the intellect from before the fight in its last minutes too: {icons()}")
db.buffs.combat = False
ns.UpdateBuffs()
check(icons() == [], "turned off again: nothing in combat")
check(not food.shown, "no food reminder in combat")
S.combat, S.secret = False, False
auras(Frost_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
G.Fire("PLAYER_REGEN_ENABLED")
check(icons() == [], "out of combat the buffs are read again")

# ---------------------------------------------------------------- Which armor
auras(Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
know(7302)  # Ice Armor learned
check(icons() == [(7302, True, "")], f"with Ice Armor learned it's the one to put on: {icons()}")
know(6117)  # Mage Armor learned
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 6117)
check(db.lastArmor == "mage" and icons() == [], "Mage Armor cast: any armor will do")
auras(Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
check(icons() == [(6117, True, "")], "it wears off: Mage Armor, the last one you cast")
db.buffs.armorChoice = "frost"
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
check(icons() == [(7302, True, "")], "Frost or Ice Armor chosen, Mage Armor on: Ice Armor")
db.buffs.armorChoice = "mage"
ns.UpdateBuffs()
check(icons() == [], "Mage Armor chosen and on: nothing")
db.buffs.armorChoice = "auto"
db.buffs.armor = False
auras(Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
check(icons() == [], "the armor reminder can be turned off")
db.buffs.armor = True

# Arcane Intellect: Brilliance counts, and casting it on someone else doesn't
auras(Mage_Armor=(1800, 1800), Arcane_Brilliance=(3000, 3600), Well_Fed=(800, 900))
check(icons() == [], "Arcane Brilliance counts as Arcane Intellect")
auras(Mage_Armor=(1800, 1800), Well_Fed=(800, 900))
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 1459)
check(icons() == [(1459, True, "")], "Arcane Intellect cast on someone else out of combat: still missing on you")
db.buffs.magic = "dampen"
ns.UpdateBuffs()
check(len(icons()) == 1, "Dampen Magic chosen but not learned: no reminder")
know(604)
check(icons() == [(1459, True, ""), (604, True, "")], f"learned: it shows too: {icons()}")
db.buffs.magic = "none"

# Clicking a reminder casts it, out of combat
cast = G.NAMED["MageGodCast"]


def casters():
    return [(b.attrs["type"], b.attrs["spell"], b.attrs["unit"]) for b in G.ShownIcons(cast).values()] if cast.shown else []


G.ShownIcons = lua.eval('''function(parent)
  local t = {}
  for _, f in ipairs(FRAMES) do if f.parent == parent and f.shown and (f.icon or f.template) then t[#t + 1] = f end end
  return t
end''')
auras(Mage_Armor=(1800, 1800), Well_Fed=(800, 900))
check(casters() == [("spell", "Arcane Intellect", "player")],
      f"the intellect reminder is a button that casts it on you: {casters()}")
check(G.Same(cast.parent, G.UIParent) and cast.point[3] == "BOTTOMLEFT" and cast.point[4] == 300,
      "the buttons sit over the icons, but apart from them")
auras(Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
check(casters() == [("spell", "Mage Armor", "player")], f"and the armor one: {casters()}")
G.Fire("PLAYER_REGEN_DISABLED")  # the game says so before it locks the buttons
check(not cast.shown and icons() == [], "a fight starts: the buttons go, and the reminders with them")
S.combat = True
ns.UpdateBuffs()
check(not cast.shown, "and they can't come back in combat")
S.combat = False
G.Fire("PLAYER_REGEN_ENABLED")
check(cast.shown, "back after it")
db.buffs.click = False
ns.UpdateBuffs()
check(not cast.shown, "clicking can be turned off")
db.buffs.click = True
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
check(not cast.shown, "nothing missing: no buttons")

# ---------------------------------------------------------------- Mana gems
S.level = 38
know(759, 3552)  # Agate and Jade
check(icons() == [(3552, True, "")], f"Jade learned, none in the bags: conjure Mana Jade: {icons()}")
check(casters() == [("spell", "Conjure Mana Jade", "player")], "a click conjures it")
db.gems.all = True
ns.UpdateBuffs()
check(icons() == [(3552, True, ""), (759, True, "")], "every gem you know: Jade and Agate")
S["items"][5513] = 1
G.Fire("BAG_UPDATE_DELAYED")
check(icons() == [(759, True, "")], "Jade in the bags: only Agate left")
db.gems.all = False
ns.UpdateBuffs()
check(icons() == [], "only the best one: nothing to conjure")
S["items"][5513] = 0
S.combat = True
G.Fire("PLAYER_REGEN_DISABLED")
check(icons() == [], "no gem reminder in combat")
S.combat = False
G.Fire("PLAYER_REGEN_ENABLED")
check(icons() == [(3552, True, "")], "and back after it")
db.gems.enabled = False
ns.UpdateBuffs()
check(icons() == [], "gems can be turned off")
db.gems.enabled = True
S["items"][5513] = 1

# ---------------------------------------------------------------- Food
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600))
check(food.shown and icons() == [], "no Well Fed: only the small reminder")

# Its list of the XP food in your bags
menu = G.NAMED["MageGodFoodMenu"]


def click(button):
    for down in (True, False):  # the game clicks on the way down and up
        if button.hooks and button.hooks["OnClick"]:
            button.hooks["OnClick"](button, "LeftButton", down)


def menu_rows():
    return [(r.text.text, r.attrs["type"], r.attrs["item"]) for r in G.ShownIcons(menu).values()] if menu.shown else []


S.bags = lua.table_from({0: lua.table_from([lua.table(700, 5), lua.table(701, 10), lua.table(702, 2), lua.table(702, 1)])})
G.Fire("BAG_UPDATE_DELAYED")
food_row = next(r for r in G.ShownIcons(food).values() if r.isFood)
click(food_row)
check(menu_rows() == [("Roast Raptor  x5", "item", "item:700"), ("Spiced Wolf Meat  x3", "item", "item:702")],
      f"a click on the food row: your food that makes you Well Fed, not the bread: {menu_rows()}")
check(G.Same(menu.point[2], food_row) and menu.point[3] == "TOPRIGHT", "beside the row")
looks = G.TIP_LOOKS
G.Fire("BAG_UPDATE_DELAYED")
check(G.TIP_LOOKS == looks, "each food's tooltip read only once")
entry = list(G.ShownIcons(menu).values())[0]
click(entry)
check(not menu.shown, "you pick one: the game eats it and the list goes")
click(food_row)
click(food_row)
check(not menu.shown, "the row opens and closes it")
S.bags = lua.table_from({0: lua.table_from([lua.table(701, 10)])})
G.Fire("BAG_UPDATE_DELAYED")
click(food_row)
check(menu_rows() == [(L.NO_XP_FOOD, None, None)], f"none in the bags: it says so: {menu_rows()}")
# At login the game may not have loaded what a food does yet: it isn't written off for good
S.tipsLoading = True
S.bags = lua.table_from({0: lua.table_from([lua.table(703, 57)])})
G.Fire("BAG_UPDATE_DELAYED")
check(menu_rows() == [(L.NO_XP_FOOD, None, None)], f"its text not loaded yet: not on the list ({menu_rows()})")
S.tipsLoading = False
G.Fire("BAG_UPDATE_DELAYED")
check(menu_rows() == [("Roasted Boar Meat  x57", "item", "item:703")], f"and once it is, there it is: {menu_rows()}")
# Should Forever name the buff otherwise, "well fed" in the food's text and on the buff still count
G.SPELLS[19705] = "Fed Up"
G.Fire("SPELLS_CHANGED")
S.bags = lua.table_from({0: lua.table_from([lua.table(704, 3)])})
G.Fire("BAG_UPDATE_DELAYED")
check(menu_rows() == [("Smoked Bear Meat  x3", "item", "item:704")], f"another buff name: the food still counts: {menu_rows()}")
S.bags = lua.table_from({0: lua.table_from([lua.table(701, 10)])})
G.Fire("BAG_UPDATE_DELAYED")
G.Fire("PLAYER_REGEN_DISABLED")
check(not menu.shown, "a fight starts: the list goes")
G.Fire("PLAYER_REGEN_ENABLED")
click(food_row)
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
check(not menu.shown and not food.shown, "Well Fed: the row and its list go, whatever the game calls it")
G.SPELLS[19705] = "Well Fed"
G.Fire("SPELLS_CHANGED")
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600))
S.bags = lua.table()
G.Fire("BAG_UPDATE_DELAYED")
S.level = 60
ns.UpdateBuffs()
check(not food.shown, "at level 60 there's no XP to gain: no food reminder")
S.level = 38
db.food.enabled = False
ns.UpdateBuffs()
check(not food.shown, "it can be turned off")
db.food.enabled = True
S.dead = True
ns.UpdateBuffs()
check(not food.shown and icons() == [], "dead: no reminders")
S.dead = False
out = slash("bufos" if es else "buffs")
print("     /magegod buffs:", out)
check(len(out) == 3 and "Mage Armor" in out[0] and "Arcane Intellect" in out[0] and "Conjure Mana Jade" in out[0]
      and out[1] == L.PREFIX + L.FOOD_STOCK % L.BUFF_NONE and "Mage Armor" in out[2], "/magegod buffs says what it sees")
S.bags = lua.table_from({0: lua.table_from([lua.table(703, 57), lua.table(701, 10)])})
out = slash("bufos" if es else "buffs")
check(out[1] == L.PREFIX + L.FOOD_STOCK % "Roasted Boar Meat x57", f"and your XP food: {out[1]}")
S.bags = lua.table()
S.secret = True
out = slash("buffs")
check(len(out) == 3 and out[2] == L.PREFIX + L.BUFFS_HIDDEN, "and that the game hides them in combat")
S.secret = False
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))

# ---------------------------------------------------------------- Range
rng = G.NAMED["MageGodRange"]
S.target = lua.table(hostile=True)
yd = L.YARDS
db.range.display = "bracket"


def range_at(dist):
    S.dist = dist
    ns.UpdateRange()
    return f"{rng.text.text} {rng.unit.text}" if rng.shown else None


def colour():
    return tuple(round(c, 2) for c in rng.text.color.values())[:3]


check(range_at(3) == f"0-5 {yd}" and colour() == (1, 0.2, 0.2), f"3 yd: on you, red ({rng.text.text})")
check(range_at(8) == f"5-8 {yd}" and colour() == (1, 0.82, 0), f"8 yd: Frost Nova range, yellow ({rng.text.text})")
check(range_at(18) == f"15-20 {yd}" and colour() == (0.3, 1, 0.3) and not rng.glow.shown, f"18 yd: in range, green ({rng.text.text})")
check(range_at(27) == f"25-28 {yd}" and colour() == (0.45, 0.8, 1) and rng.glow.shown,
      f"27 yd: the last 5 yards of Frostbolt's 30, glowing ({rng.text.text})")
check(range_at(33) == f"30-35 {yd}" and colour() == (0.6, 0.6, 0.6) and not rng.glow.shown, f"33 yd: out of range, grey ({rng.text.text})")
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 133)
check(db.range.lastSpell == "fireball" and range_at(33) == f"30-35 {yd}" and colour() == (0.45, 0.8, 1),
      "Fireball cast: the range follows its 35 yards")
check(range_at(37) == f"35-40 {yd}" and colour() == (0.6, 0.6, 0.6), "37 yd: out of Fireball's reach")
db.range.spell = "frostbolt"
check(range_at(33) == f"30-35 {yd}" and colour() == (0.6, 0.6, 0.6), "Frostbolt chosen in the options: 33 yd is out again")
db.range.spell = "auto"
G.Uncache(ns, 5)
G.Uncache(ns, 10)
G.Fire("PLAYER_LOGIN")  # the steps are built again
check(range_at(7) is not None and colour() == (1, 0.82, 0), f"without the 5 and 10 yard items, 8 yards stands in ({rng.text.text})")
S.uncached = lua.table()
G.Fire("PLAYER_LOGIN")
S.secretRange = True
check(range_at(20) is None, "the game hides the range: nothing shown")
S.secretRange = False
db.range.display = "number"
check(range_at(18) is not None and rng.text.text.isdigit(), f"one number: {rng.text.text}")
db.range.onlyCombat = True
check(range_at(18) is None, "only in combat: nothing out of it")
db.range.onlyCombat = False
out = slash("rango" if es else "range")
check(len(out) == 2 and "Fireball" in out[0] and "35" in out[0], f"/magegod range: {out}")
out = slash("meters")
check(db.range.units == "meters" and range_at(18) is not None and rng.unit.text == L.METERS, "metres")
slash("yards")

# ---------------------------------------------------------------- Aggro
thr = G.NAMED["MageGodThreat"]
S.threat = lua.table(False, 1, 95, 95)
ns.UpdateThreat()
check(not thr.shown, "solo: you always have the aggro, nothing to say")
S.group = True
ns.UpdateThreat()
check(thr.shown and thr.text.text == L.THREAT % 95, f"in a group at 95%: {thr.text.text}")
S.threat = lua.table(False, 1, 80, 80)
ns.UpdateThreat()
check(not thr.shown, "80%: below the 90% line")
S.threat = lua.table(True, 3, 100, 130)
ns.UpdateThreat()
check(thr.shown and thr.text.text == L.THREAT_PULLED, "you pulled it")
S.threat = lua.table(G.SECRET, G.SECRET, G.SECRET, G.SECRET)
ns.UpdateThreat()
check(not thr.shown, "hidden threat: nothing")
S.threat = None
S.group = False

# ---------------------------------------------------------------- The barrier
bar = G.NAMED["MageGodBarrier"]
status = next(f for f in G.FRAMES.values() if f.kind == "StatusBar" and G.Same(f.parent, bar))
know(11426)
S.absorb = 0
ns.UpdateBuffs()
check(not bar.shown, "no shield: no bar")
S.absorb = 431
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900), Ice_Barrier=(60, 60))
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 11426)
G.RunTimers()
check(bar.shown and list(status.minmax.values()) == [0, 431] and status.value == 431 and bar.text.text == "431"
      and bar.time.text == "60", f"Ice Barrier cast: a full bar with what it absorbs and its minute ({bar.text.text}, {bar.time.text}s)")
check(bar.icon.tex == 11426, "with its icon")
S.absorb = 200
S.now = S.now + 15
G.Fire("UNIT_ABSORB_AMOUNT_CHANGED", "player")
check(status.value == 200 and bar.text.text == "200" and bar.time.text == "45", "hits taken: 200 left, 45 s")
S.absorb = 0
G.Fire("UNIT_ABSORB_AMOUNT_CHANGED", "player")
check(not bar.shown, "broken: the bar goes")
# In combat Forever hides how much it absorbs: the game fills the bar in itself
S.combat, S.secret = True, True
G.Fire("PLAYER_REGEN_DISABLED")
S.absorb = G.Hidden(500)
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 13033)
G.RunTimers()
check(bar.shown and list(status.minmax.values()) == [0, 500] and status.hiddenValue and bar.text.hiddenText
      and bar.text.text == "500" and bar.time.text == "60", "in combat, hidden: the bar and its number still show it")
S.absorb = G.Hidden(120)
G.Fire("UNIT_ABSORB_AMOUNT_CHANGED", "player")
check(status.value == 120 and bar.text.text == "120", "and go down with it")
S.now = S.now + 61
ns.UpdateBuffs()
check(not bar.shown, "after its minute it goes")
S.combat, S.secret = False, False
G.Fire("PLAYER_REGEN_ENABLED")
S.absorb = 300
G.Fire("UNIT_ABSORB_AMOUNT_CHANGED", "player")
check(bar.shown and list(status.minmax.values()) == [0, 300], "a shield you didn't cast (a priest's), readable: it shows too")
S.absorb = 350
G.Fire("UNIT_ABSORB_AMOUNT_CHANGED", "player")
check(list(status.minmax.values()) == [0, 350], "a bigger one on top: the bar grows")
db.barrier.width, db.barrier.height = 250, 20
ns.RefreshAll()
check(bar.width == 250 and bar.height == 20, f"its size is yours to set: {bar.width}x{bar.height}")
bedge = [list(pt.values()) for pt in bar.edge.points.values()]
check(bedge == [["TOPLEFT", -0.5, 0.5], ["BOTTOMRIGHT", 0.5, -0.5]] and list(bar.edge.color.values()) == [0, 0, 0, 1],
      f"like the mana bar: a black edge one screen pixel thin: {bedge}")
check(list(status.barColor.values()) == [0.52, 0.78, 0.92], f"a flat frost fill: {list(status.barColor.values())}")
check(bar.text.font[1] == "Fonts\\ARIALN.TTF" and bar.text.font[2] == 18 and bar.time.font[1] == "Fonts\\ARIALN.TTF",
      f"its thin letters: {list(bar.text.font.values())}")
btag_edge = [list(pt.values()) for pt in bar.tagEdge.points.values()]
btag_point = list(bar.tag.point.values())
check(btag_point[0] == "RIGHT" and G.Same(btag_point[1], bar) and btag_point[2:] == ["LEFT", -0.5, 0]
      and bar.tag.width == 20 and bar.tag.height == 20 and bar.tag.shown and btag_edge == bedge, "the shield's icon on a square tag against its left end, the same edge")
db.barrier.icon = False
db.barrier.color = lua.table(r=1, g=0.5, b=0)
ns.RefreshAll()
check(not bar.tag.shown and list(status.barColor.values()) == [1, 0.5, 0], "the icon can go, and the colour is yours")
db.barrier.icon = True
db.barrier.color = lua.table(r=0.52, g=0.78, b=0.92)
ns.RefreshAll()
db.barrier.text, db.barrier.time = False, False
ns.UpdateBarrier()
check(bar.text.text == "" and bar.time.text == "", "the number and the seconds can go")
db.barrier.text, db.barrier.time = True, True
db.barrier.enabled = False
ns.UpdateBarrier()
check(not bar.shown, "and the whole bar")
db.barrier.enabled = True
S.absorb = 0
ns.UpdateBarrier()

# ---------------------------------------------------------------- The five-second rule
mana = G.NAMED["MageGodMana"]


def later(seconds):
    S.now = S.now + seconds
    ns.UpdateMana()


def mana_to(value):
    S.mana = value
    G.Fire("UNIT_POWER_UPDATE", "player", "MANA")


def bar_color():
    return tuple(round(c, 2) for c in mana.barColor.values())


def label_color():
    return tuple(round(c, 2) for c in mana.label.color.values())


ns.UpdateMana()
check(not mana.shown, "full mana: no bar")
S.manaMax = 2000
S.mana = 900
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 116)
G.Fire("UNIT_POWER_UPDATE", "player", "MANA")
check(not mana.shown, "out of combat it stays out of the way")
G.Fire("PLAYER_REGEN_DISABLED")
check(mana.shown, "in a fight it shows")
G.Fire("PLAYER_REGEN_ENABLED")
check(not mana.shown, "and goes when the fight ends")
db.mana.onlyCombat = False
ns.UpdateMana()
check(mana.shown and bar_color() == (0.45, 0.5, 0.62) and mana.value == 1 and mana.text.text == "5.0",
      f"a Frostbolt: grey, five seconds to wait ({mana.value}, {mana.text.text})")
check(mana.label.text == "MP5" and mana.tag.shown and label_color() == (0.75, 0.75, 0.75), "MP5 beside it, in grey")
later(2)
check(abs(mana.value - 0.6) < 1e-9 and mana.text.text == "3.0", f"two seconds on: three to go ({mana.text.text})")
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 5019)
check(mana.text.text == "3.0", "a wand shot costs no mana: it doesn't start them again")
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 133)
check(mana.text.text == "5.0", "a Fireball does")
later(5)
check(bar_color() == (0.38, 0.56, 0.7) and mana.value == 1 and mana.text.text == "",
      f"after them: blue, the mana comes back ({bar_color()})")
check(label_color() == (0.3, 1, 0.3), "and MP5 goes green")
db.mana.label = False
ns.UpdateMana()
check(not mana.tag.shown, "MP5 can go")
db.mana.label = True
mana_to(915)
check(mana.value == 0 and mana.text.text == "+15", f"a tick: what it gave, and the bar starts again ({mana.text.text})")
later(1)
check(abs(mana.value - 0.5) < 1e-9, "filling up to the next one, two seconds on")
S.now = S.now + 0.5
mana_to(1015)
check(mana.text.text == "+15" and abs(mana.value - 0.75) < 1e-9, "a potion off the beat isn't a tick")
S.now = S.now + 0.5
mana_to(1030)
check(mana.value == 0 and mana.text.text == "+15", "the next tick, on the beat")
S.now = S.now + 0.1
mana_to(1040)
check(mana.text.text == "+25" and abs(mana.value - 0.05) < 1e-9, "a drink in the same tick: one tick with both")
S.now = S.now + 0.9
mana_to(1045)
S.now = S.now + 2
mana_to(1060)
check(mana.value == 0 and mana.text.text == "+15", "two gains off the beat two seconds apart: the beat moved")
db.mana.ticks = False
ns.UpdateMana()
check(mana.value == 1, "without the ticks, a full blue bar while it comes back")
db.mana.ticks = True
db.mana.text = False
ns.UpdateMana()
check(mana.text.text == "", "the numbers can go")
db.mana.text = True
mana_to(2000)
check(not mana.shown, "full again: the bar goes")
# In a fight Forever may hide your mana: the game hides the bar at full itself
S.combat, S.secretMana = True, True
G.Fire("PLAYER_REGEN_DISABLED")
S.mana = 1500
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 116)
G.Fire("UNIT_POWER_UPDATE", "player", "MANA")
check(mana.shown and mana.hiddenAlpha and mana.alpha == 1 and mana.text.text == "5.0", "hidden mana: the wait still shows")
S.mana = 2000
later(6)
check(mana.hiddenAlpha and mana.alpha == 0, "and at full mana the game makes it see-through")
S.combat, S.secretMana = False, False
G.Fire("PLAYER_REGEN_ENABLED")
check(not mana.shown and mana.alpha == 1, "out of the fight, full: hidden as usual")
db.mana.width, db.mana.height = 220, 12
ns.RefreshAll()
check(mana.width == 220 and mana.height == 12, f"its size is yours to set: {mana.width}x{mana.height}")
edge = [list(pt.values()) for pt in mana.edge.points.values()]
check(edge == [["TOPLEFT", -0.5, 0.5], ["BOTTOMRIGHT", 0.5, -0.5]] and list(mana.edge.color.values()) == [0, 0, 0, 1],
      f"a black edge one screen pixel thin: {edge}")
tag_edge = [list(pt.values()) for pt in mana.tagEdge.points.values()]
tag_point = list(mana.tag.point.values())
check(tag_point[0] == "RIGHT" and G.Same(tag_point[1], mana) and tag_point[2:] == ["LEFT", -0.5, 0]
      and mana.tag.width == 26 and mana.tag.height == 12
      and tag_edge == edge, f"MP5 on a dark tag against the bar's left end, the same edge: {mana.tag.width}x{mana.tag.height}")
db.mana.enabled = False
mana_to(1500)
check(not mana.shown, "and it can be turned off")
db.mana.enabled = True
db.mana.onlyCombat = True
S.manaMax = 1000
mana_to(1000)

# ---------------------------------------------------------------- Forever's mage scrolls
S.mainHand = 900  # a staff
S["items"][277485] = 2  # Scroll of Imbue Frost, for staves
S["items"][275069] = 2  # Scroll of Rat Familiar
G.Fire("BAG_UPDATE_DELAYED")
imbue_macro = "/use item:277485\n/use 16"
check(extras() == [(L.IMBUE_MISSING, "macro", imbue_macro), (L.FAMILIAR_MISSING, "item", "item:275069")],
      f"scrolls you carry and haven't used: imbue the staff, call the familiar: {extras()}")
rows = list(G.ShownIcons(food).values())
check(rows[0].icon.tex == 2774850 and not rows[0].icon.desat and rows[1].icon.tex == 2750690, "each with its scroll's icon")
check(rows[0].width == rows[1].width == food.width and rows[1].point[3] == -24,
      f"stacked bars, all as long as the longest: {rows[0].width}, {rows[1].width}")
S.weaponEnchant = True
ns.UpdateBuffs()
check(extras() == [(L.FAMILIAR_MISSING, "item", "item:275069")], "the weapon already imbued: only the familiar")
S.weaponEnchant = False
S.mainHand = 901  # a dagger
ns.UpdateBuffs()
check(extras() == [(L.FAMILIAR_MISSING, "item", "item:275069")], "a dagger in hand: the staff scroll is no use")
S["items"][277488] = 1  # Scroll of Imbue Iceknife, for daggers
G.Fire("BAG_UPDATE_DELAYED")
check(extras()[0] == (L.IMBUE_MISSING, "macro", "/use item:277488\n/use 16"), "with a dagger scroll: that one")
S.mainHand = 900  # the staff again: its scroll
G.Fire("BAG_UPDATE_DELAYED")
S["items"][275069] = 1  # the familiar used
G.Fire("BAG_UPDATE_DELAYED")
check(extras() == [(L.IMBUE_MISSING, "macro", imbue_macro)] and db.lastFamiliar == 275069
      and db.scrollUsed.familiar == S.epoch, f"a familiar scroll used: no reminder for its hour: {extras()}")
S.epoch = S.epoch + 3601
ns.UpdateBuffs()
check(len(extras()) == 2, "an hour later it's back")
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900), Rat_Familiar=(3000, 3600))
check(len(extras()) == 1, "the familiar's buff on you: no reminder either")
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900))
S["items"][277493] = 1  # a Cat Familiar too: the rat is the one you use
G.Fire("BAG_UPDATE_DELAYED")
check(extras()[1] == (L.FAMILIAR_MISSING, "item", "item:275069"), "the familiar you used last, while you carry it")
S["items"][275069] = 0
G.MerchantFrame = G.CreateFrame("Frame")
G.Fire("BAG_UPDATE_DELAYED")
check(extras()[1] == (L.FAMILIAR_MISSING, "item", "item:277493") and db.scrollUsed.familiar < S.epoch - 3000,
      "the rat sold at a vendor: not used, and the cat now")
G.MerchantFrame = None
S["items"][277485] = 1  # the imbue used
G.Fire("BAG_UPDATE_DELAYED")
check(extras() == [(L.FAMILIAR_MISSING, "item", "item:277493")] and db.lastImbue == 277485, "the imbue used: its hour")
S.epoch = S.epoch + 3601
G.Fire("PLAYER_REGEN_DISABLED")
check(not food.shown, "a fight starts: the rows go, before the game locks them")
S.combat = True
ns.UpdateBuffs()
check(not food.shown, "and stay away in combat")
S.combat = False
G.Fire("PLAYER_REGEN_ENABLED")
check(len(extras()) == 2, "back after it")
db.scrolls.imbue, db.scrolls.familiar = False, False
ns.UpdateBuffs()
check(extras() == [], "both can be turned off")
db.scrolls.imbue, db.scrolls.familiar = True, True
for item in (277485, 277488, 275069, 277493):
    S["items"][item] = 0
G.Fire("BAG_UPDATE_DELAYED")
check(extras() == [], "no scrolls in the bags: nothing")

# ---------------------------------------------------------------- Moving the displays
ns.SetUnlocked(True)
check(len(icons()) == 2 and food.shown and rng.shown and thr.shown and bar.shown and mana.shown,
      "unlocked: samples of everything to drag")
check(mana.text.text == "3.2" and bar_color() == (0.45, 0.5, 0.62), "the mana bar's sample is a wait")
check(not cast.shown, "the cast buttons stay out of the way")
check([r[0] for r in extras()] == ["Arcane Intellect  1:35", L.FOOD_MISSING, L.IMBUE_MISSING, L.FAMILIAR_MISSING],
      f"the running out, food and scroll samples: {extras()}")
check(all(f.mover.shown for f in ns.movers.values()), "each with its handle")
ns.SetUnlocked(False)
check(icons() == [] and not food.shown and not thr.shown and not bar.shown and not mana.shown, "locked: back to what's real")
S.combat = True
out = slash("unlock")
check(not ns.unlocked and out[0] == L.PREFIX + L.NOT_IN_COMBAT, "not in combat")
S.combat = False

# ---------------------------------------------------------------- Options
win, pages = ns.OptionsWindow()
page = {p.key: p for p in pages.values()}
check(set(page.keys()) == {"buffs", "range", "procs", "threat"}, f"pages: {list(page.keys())}")
ns.ShowOptionsPage("buffs")
controls = {c.setting: c for c in page["buffs"].controls.values()}
armor = controls[L.OPT_ARMOR_CHOICE]
check(armor.text == L.ARMOR_AUTO, f"armor choice: {armor.text}")
armor.scripts.OnClick(armor)
check(db.buffs.armorChoice == "frost" and "Frost Armor" in armor.text and "Ice Armor" in armor.text, f"next: {armor.text}")
armor.scripts.OnClick(armor)
armor.scripts.OnClick(armor)
check(db.buffs.armorChoice == "auto", "and round again")
gems_all = controls[L.OPT_GEMS_ALL]
gems_all.checked = True
gems_all.scripts.OnClick(gems_all)
check(db.gems.all, "the gems switch works")
gems_all.checked = False
gems_all.scripts.OnClick(gems_all)
width = controls[L.OPT_BARRIER_WIDTH]
check(width is not None and controls[L.OPT_CLICK] is not None, "the barrier's width and the click option are there")
check(controls[L.OPT_BARRIER_ICON] is not None and controls[L.OPT_BARRIER_COLOR] is not None, "and its icon and colour")
check(controls[L.OPT_IMBUE] is not None and controls[L.OPT_FAMILIAR] is not None, "and the scroll ones")
ticks = controls[L.OPT_MANA_TICKS]
ticks.checked = False
ticks.scripts.OnClick(ticks)
check(not db.mana.ticks and controls[L.OPT_MANA] is not None, "the mana bar's options are there and work")
ticks.checked = True
ticks.scripts.OnClick(ticks)
regen = controls[L.OPT_MANA_REGEN_COLOR]
regen.scripts.OnClick(regen)
G.COLOR_INFO.swatchFunc()
check(tuple(db.mana.colors.regen[k] for k in "rgb") == (0, 0, 1), "its colours are yours to pick")
G.COLOR_INFO.cancelFunc()
check(tuple(round(db.mana.colors.regen[k], 2) for k in "rgb") == (0.38, 0.56, 0.7), "or to put back")
check(controls[L.OPT_MANA_WAIT_COLOR] is not None, "the waiting one too")
ns.ShowOptionsPage("range")
rcontrols = {c.setting: c for c in page["range"].controls.values()}
spell = rcontrols[L.OPT_RANGE_SPELL]
spell.scripts.OnClick(spell)
check(db.range.spell == "frostbolt" and spell.text == "Frostbolt", f"range spell: {spell.text}")
db.range.spell = "auto"
check(all(L.RANGE[s] in rcontrols for s in ("melee", "nova", "ranged", "far", "out")), "a preview sample for each state")
ns.ShowOptionsPage("threat")
check(any(c.setting == L.OPT_THREAT for c in page["threat"].controls.values()), "the aggro page")
win.Hide(win)

# ---------------------------------------------------------------- Missile Barrage: purple lightning
S.secret = False
S.combat = False
MEDIA = "Interface\\AddOns\\MageGod\\media\\"


def boxes():
    return [f for f in G.FRAMES.values() if f.kind == "AuraContainer"]


def watched(b):
    return sorted(b.slot.options.candidateFilters.includeSpellIDs.keys())


state = ns.MissilesState()
box = state.container
check(len(boxes()) == 1 and G.Same(box, boxes()[0]), "an aura container for Missile Barrage, built at login")
check(box.slot.filter == "HELPFUL" and box.unit == "player" and box.enabled, "it watches your buffs")
check(watched(box) == [400589, 401736, 467409], f"Forever's Missile Barrage buffs, not the passive that procs them: {watched(box)}")
button = box.button
check(len(button.shownAnims) == 3 and len(button.assignedAnims) == 3,
      "the game gets the calm crackle and breath to loop, and the strike for when the buff comes")
dressed = state.dressed
check(dressed is not None and dressed.ready, "and takes them")
files = [e[1].tex for e in dressed.tinted.values()]
check(files.count(MEDIA + "bolts_glow") == 4 and files.count(MEDIA + "bolts_core") == 4,
      f"two columns of lightning, calm and strike: {files}")
check(dressed.calm.alpha == 0.3 and dressed.strike.alpha == 0.85, "the strike strong, the calm faint")
timer = button.durationText
rules = timer and timer.options and timer.options.textFormatter.rules
check(timer is not None and G.Same(timer.text, dressed.timer) and rules[2].format == "%d" and rules[2].rounding == 2,
      "the seconds it has left: the game writes them, whole and rounded up")
tpoint = list(dressed.timer.points[1].values())
check(tpoint[0] == "TOP" and tpoint[2:] == ["CENTER", 0, -146] and dressed.timer.font[2] == 22
      and dressed.timer.font[3] == "OUTLINE" and dressed.timer.shown, f"centred under the lightning: {tpoint}")
gaps = [e[1].points[1][4] * e[2] for e in dressed.placed.values()]
check(set(gaps) == {150} and {e[2] for e in dressed.placed.values()} == {-1, 1}, f"150 out from the middle on each side: {set(gaps)}")
colors = [tuple(round(c, 2) for c in e[1].color.values()) for e in dressed.tinted.values()]
check(colors[1] == (0.62, 0.32, 1.0) and colors[2][2] == 1.0 and colors[2][0] > 0.8, f"purple, the cores nearly white: {colors[:3]}")
holder, place = state.holder, state.place
check(place.point[1] == "CENTER" and G.Same(place.point[2], G.UIParent) and place.point[5] == 30
      and G.Same(holder.point[2], place) and holder.scale == 1, "in the middle of the screen, above you")
check(not state.spot.shown, "the sample is hidden")

auras(Missile_Barrage=(10, 15, 999001))
new = ns.MissilesState().container
check(not G.Same(new, box) and 999001 in watched(new) and not box.enabled and not holder.shown,
      f"a Missile Barrage with another number: a new container watches it too, the old one is off: {watched(new)}")
check(db.missiles.learned[999001], "and it's remembered")
auras(Missile_Barrage=(0, 0, 401736))
newer = ns.MissilesState().container
check(401736 not in watched(newer) and db.missiles.ignored[401736], f"one that never ends is a passive: left out {watched(newer)}")
built = len(boxes())
auras(Missile_Barrage=(0, 0, 401736))
check(len(boxes()) == built, "nothing new to build when nothing changed")
S.combat = True
auras(Missile_Barrage=(10, 15, 999002))
check(len(boxes()) == built, "in combat it waits")
S.combat = False
G.Fire("PLAYER_REGEN_ENABLED")
check(len(boxes()) == built + 1 and 999002 in watched(ns.MissilesState().container), "and builds it when the fight is over")
S.secret = True
auras(Missile_Barrage=(10, 15, 999003))
check(not db.missiles.learned[999003], "with your buffs hidden it learns nothing")
S.secret = False
auras()

out = slash("rayos" if es else "lightning")
state = ns.MissilesState()
spot, sample = state.spot, state.sample
check(spot.shown and all(g.playing for g in sample.shown.values()) and sample.assigned[1].playing,
      "trying it shows the sample, playing")
check(len(out) == 1 and "400589, 467409, 999001, 999002" in out[0], f"and says what it watches: {out}")
spot.scripts.OnUpdate(spot, 0.1)
first = sample.timer.text
S.now = S.now + 3
spot.scripts.OnUpdate(spot, 0.1)
check(first == "15" and sample.timer.text == "12", f"the sample counts down as the buff would: {first}, {sample.timer.text}")
S.now = S.now + 5
G.RunTimers()
check(not spot.shown and not sample.shown[1].playing, "a few seconds later it's gone")

db.positions.missiles = lua.table("CENTER", "CENTER", 100, 40)
ns.ToggleOptions("procs")
pcontrols = {c.setting: c for c in page["procs"].controls.values()}
size = pcontrols[L.OPT_MISSILES_SIZE]
size.scripts.OnValueChanged(size, 200)
holder = state.holder
pos = db.positions.missiles
check(db.missiles.size == 200 and holder.scale == 2 and spot.scale == 2 and place.width == 1000, "size: twice as big")
check(pos[3] == 100 and pos[4] == 40 and place.point[4] == 100 and place.point[5] == 40, "in the same place")
check(spot.shown, "changing it shows the sample a moment")
size.scripts.OnValueChanged(size, 100)
x, y = pcontrols[L.OPT_MISSILES_X], pcontrols[L.OPT_MISSILES_Y]
x.scripts.OnValueChanged(x, -120)
y.scripts.OnValueChanged(y, -60)
check(tuple(db.positions.missiles.values()) == ("CENTER", "CENTER", -120, -60) and place.point[4] == -120 and place.point[5] == -60,
      f"left, right, up and down from the options: {tuple(db.positions.missiles.values())}")
gap = pcontrols[L.OPT_MISSILES_GAP]
gap.scripts.OnValueChanged(gap, 220)
check({e[1].points[1][4] * e[2] for e in dressed.placed.values()} == {220} and place.width == 640,
      "and the space between the sides")
calm = pcontrols[L.OPT_MISSILES_CALM]
calm.scripts.OnValueChanged(calm, 15)
strike = pcontrols[L.OPT_MISSILES_ALPHA]
strike.scripts.OnValueChanged(strike, 100)
check(dressed.calm.alpha == 0.15 and dressed.strike.alpha == 1 and sample.calm.alpha == 0.15,
      "the strike's strength and the calm's, each its own")
S.combat = True
gap.scripts.OnValueChanged(gap, 260)
check({e[1].points[1][4] * e[2] for e in dressed.placed.values()} == {220}
      and {e[1].points[1][4] * e[2] for e in sample.placed.values()} == {260},
      "in a fight the game's lightning can't be touched, the sample can")
S.combat = False
G.Fire("PLAYER_REGEN_ENABLED")
check({e[1].points[1][4] * e[2] for e in dressed.placed.values()} == {260}, "the fight over, it's fitted")
db.positions.missiles = lua.table("BOTTOMLEFT", "BOTTOMLEFT", 700, 420)
place.GetCenter = lua.eval("function() return 700, 420 end")
G.UIParent.GetCenter = lua.eval("function() return 600, 400 end")
place.mover.hooks.OnDragStop()
check(tuple(db.positions.missiles.values()) == ("CENTER", "CENTER", 100, 20), "dragged: kept as an offset from the middle")
switch = pcontrols[L.OPT_MISSILES.replace("%s", "Missile Barrage")]
switch.checked = False
switch.scripts.OnClick(switch)
check(not db.missiles.enabled and not holder.shown, "switched off: the game shows nothing")
switch.checked = True
switch.scripts.OnClick(switch)
check(db.missiles.enabled and holder.shown, "and on again")
color = pcontrols[L.OPT_MISSILES_COLOR]
color.scripts.OnClick(color)
G.COLOR_INFO.swatchFunc()
check(tuple(state.dressed.tinted[2][1].color.values()) == (0, 0, 1), "its colour is yours to pick")
G.COLOR_INFO.cancelFunc()
check(pcontrols[L.OPT_MISSILES_ALPHA] is not None and pcontrols[L.OPT_MISSILES_TEST] is not None,
      "and its strength, and a button to try it")
timer_on = pcontrols[L.OPT_MISSILES_TIMER]
timer_on.checked = False
timer_on.scripts.OnClick(timer_on)
check(not dressed.timer.shown and not sample.timer.shown, "the seconds can go")
timer_on.checked = True
timer_on.scripts.OnClick(timer_on)
tsize = pcontrols[L.OPT_MISSILES_TIMER_SIZE]
tsize.scripts.OnValueChanged(tsize, 30)
check(dressed.timer.shown and dressed.timer.font[2] == 30, "and come back, at the size you want")
tsize.scripts.OnValueChanged(tsize, 22)
win.Hide(win)
S.now = S.now + 10
G.RunTimers()
ns.SetUnlocked(True)
check(spot.shown, "moving the displays shows the sample to drag")
ns.SetUnlocked(False)
check(not spot.shown, "locked: hidden again")

# ---------------------------------------------------------------- Blink ready: a pulse in the middle
pst = ns.PulseState()
pulse_place, part, poller = pst.place, pst.art, pst.poller
check(pst.spell is None and not pulse_place.shown, "no Blink learned: nothing to watch")
know(1953)
check(ns.PulseState().spell == 1953, "Blink learned: watched")


def cooldown(**kw):
    G.COOLDOWNS[1953] = lua.table(**kw)


def poll(seconds=0.2):
    poller.scripts.OnUpdate(poller, seconds)


def pulse_frame(t):
    S.now = S.now + t
    pulse_place.scripts.OnUpdate(pulse_place, t)


cooldown(isActive=False, duration=0, startTime=0, isOnGCD=False)
G.Fire("SPELL_UPDATE_COOLDOWN")
check(not poller.shown and not pulse_place.shown, "ready from the start: no pulse, nothing polled")
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 1953)
cooldown(isActive=True, duration=15, startTime=S.now, isOnGCD=False)
G.Fire("SPELL_UPDATE_COOLDOWN")
st = ns.PulseState()
check(poller.shown and st.since is not None and st.own, "Blink cast: its cooldown is watched")
S.now = S.now + 5
poll()
check(not pulse_place.shown, "still cooling down: nothing")
S.now = S.now + 10
cooldown(isActive=False, duration=0, startTime=0, isOnGCD=False)
poll()
check(pulse_place.shown and part.icon.tex == 1953 and part.box.alpha == 0, "ready again: Blink's icon comes up")
pulse_frame(0.06)
check(0.4 < part.box.alpha < 0.5 and part.box.width < 80, f"popping in: {part.box.alpha}, {part.box.width}")
pulse_frame(0.2)
check(abs(part.box.alpha - 0.9) < 1e-9 and part.box.width == 80, f"held at its size and strength: {part.box.alpha}, {part.box.width}")
pulse_frame(0.4)
check(part.box.alpha < 0.9 and part.box.width > 80, f"then fades as it grows: {part.box.alpha}, {part.box.width}")
pulse_frame(0.5)
check(not pulse_place.shown and not ns.PulseState().since, "gone in under a second")
poll()
check(not poller.shown, "nothing left to poll")

# The global cooldown of another spell is not Blink coming back
cooldown(isActive=True, duration=1.5, startTime=S.now, isOnGCD=True)
G.Fire("SPELL_UPDATE_COOLDOWN")
S.now = S.now + 1.5
cooldown(isActive=False, duration=0, startTime=0, isOnGCD=False)
poll()
check(not pulse_place.shown, "a global cooldown ending: no pulse")

# In combat the times are hidden, but not whether it's cooling down
S.combat = True
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", G.SECRET)
cooldown(isActive=True, duration=G.SECRET, startTime=G.SECRET, isOnGCD=G.SECRET, secretZero=True)
G.Fire("SPELL_UPDATE_COOLDOWN")
st = ns.PulseState()
check(st.since is not None and not st.own, "in combat, a hidden cast: seen cooling down, not knowing whose")
for _ in range(10):
    S.now = S.now + 1.5
    poll()
cooldown(isActive=False, duration=G.SECRET, startTime=G.SECRET, isOnGCD=G.SECRET, secretZero=True)
poll()
check(pulse_place.shown, "back after 15 s: longer than any global cooldown, so it was Blink's own")
pulse_frame(2)
cooldown(isActive=True, duration=G.SECRET, startTime=G.SECRET, isOnGCD=G.SECRET, secretZero=True)
G.Fire("SPELL_UPDATE_COOLDOWN")
S.now = S.now + 1.4
cooldown(isActive=False, duration=G.SECRET, startTime=G.SECRET, isOnGCD=G.SECRET, secretZero=True)
poll()
check(not pulse_place.shown, "a hidden global cooldown: no pulse")
# The game won't say for a while: when it does, it's old news
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 1953)
cooldown(isActive=True, duration=G.SECRET)
G.Fire("SPELL_UPDATE_COOLDOWN")
cooldown(isActive=G.SECRET, duration=G.SECRET)
for _ in range(20):
    S.now = S.now + 1
    poll()
cooldown(isActive=False, duration=0)
poll()
check(not pulse_place.shown and not ns.PulseState().since, "ready after a long stretch it wouldn't say: no late pulse")
S.combat = False

# A login with Blink cooling down
cooldown(isActive=True, duration=15, startTime=S.now - 3, isOnGCD=False)
G.Fire("SPELL_UPDATE_COOLDOWN")
check(ns.PulseState().own, "its own cooldown read from its length")
db.pulse.enabled = False
S.now = S.now + 12
cooldown(isActive=False, duration=0)
poll()
check(not pulse_place.shown, "turned off: no pulse")
db.pulse.enabled = True

S.dead = True
G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", 1953)
cooldown(isActive=True, duration=15, startTime=S.now)
G.Fire("SPELL_UPDATE_COOLDOWN")
S.now = S.now + 15
cooldown(isActive=False, duration=0)
poll()
check(not pulse_place.shown, "dead: no pulse")
S.dead = False

out = slash("traslacion" if es else "blink")
check(pulse_place.shown and part.box.alpha == 0, "/magegod blink shows it")
pulse_frame(2)
check(not pulse_place.shown, "and it goes")

pcontrols = {c.setting: c for c in page["procs"].controls.values()}
blink_on = pcontrols[L.OPT_PULSE.replace("%s", "Blink")]
check(blink_on is not None, "the Procs tab has a switch for it")
psize = pcontrols[L.OPT_PULSE_SIZE]
psize.scripts.OnValueChanged(psize, 120)
check(db.pulse.size == 120 and pulse_place.shown and pulse_place.width == 120, "a bigger size, shown as it changes")
pulse_frame(0.2)
check(part.box.width == 120, f"the icon at that size: {part.box.width}")
pulse_frame(2)
psize.scripts.OnValueChanged(psize, 80)
pulse_frame(2)
try_it = [c for c in page["procs"].controls.values() if c.setting == L.OPT_MISSILES_TEST]
check(len(try_it) == 2, "and its own button to try it")
try_it[1].scripts.OnClick(try_it[1])
check(pulse_place.shown, "which shows it")
pulse_frame(2)
ns.SetUnlocked(True)
check(pulse_place.shown and part.box.alpha == 0.9, "moving the displays shows it to drag")
ns.SetUnlocked(False)
check(not pulse_place.shown, "locked: hidden")
blink_on.checked = False
blink_on.scripts.OnClick(blink_on)
check(not db.pulse.enabled, "it can be turned off")
blink_on.checked = True
blink_on.scripts.OnClick(blink_on)

# ---------------------------------------------------------------- Not a mage
S["class"] = "WARRIOR"
auras()
ns.RefreshAll()
S.mana = 500
ns.UpdateMana()
check(icons() == [] and not food.shown and range_at(18) is None and not mana.shown, "a warrior sees none of it")
S.mana = 1000
S["class"] = "MAGE"

out = slash("help")
check(len(out) == len(list(L.HELP.values())), "help lists the commands")
out = slash("boton" if es else "button")
check(db.minimapButton.hide and not G.NAMED["MageGodMinimapButton"].shown, "the minimap button can be hidden")
slash("button")

print()
print("FAILURES:" if fails else f"All good ({LOCALE}).", fails if fails else "")
sys.exit(1 if fails else 0)
