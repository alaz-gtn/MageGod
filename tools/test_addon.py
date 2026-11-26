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
format = string.format; strlower = string.lower; strupper = string.upper; max = math.max; min = math.min; abs = math.abs; floor = math.floor; ceil = math.ceil
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
  [1953] = "Blink", [1296017] = "Comprehend Scroll",
  [2383] = "Find Herbs", [2580] = "Find Minerals",
  [11213] = "Arcane Concentration", [12536] = "Clearcasting",
  [543] = "Fire Ward", [10225] = "Fire Ward", [6143] = "Frost Ward", [28609] = "Frost Ward",
  [3561] = "Teleport: Stormwind", [3562] = "Teleport: Ironforge", [10059] = "Portal: Stormwind",
  [1225503] = "Reagent Economy", [130] = "Slow Fall",
  [10193] = "Mana Shield", [17] = "Power Word: Shield", [10901] = "Power Word: Shield",
  [7233] = "Fire Protection", [17543] = "Fire Protection", [17548] = "Shadow Protection",
  [400624] = "Heating Up", [400625] = "Heating Up",
  [400647] = "Fingers of Frost", [400669] = "Fingers of Frost", [400670] = "Fingers of Frost",
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
GetInventoryItemID = function(_, slot) if slot == 16 then return G.mainHand end if slot == 18 then return G.wand end end
GetInventoryItemDurability = function(slot) if slot == 5 and G.durability then return G.durability, 100 end end
CanMerchantRepair = function() return G.repairs end
GetInventoryItemTexture = function(_, slot) if slot == 18 and G.wand then return 135463 end end
UnitRangedDamage = function() return G.wandSpeed or 1.5 end
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
  GetContainerNumFreeSlots = function(bag) if bag == 0 then return G.freeSlots or 10, 0 end return 0, 0 end,
  GetContainerNumSlots = function(bag) return G.bags[bag] and #G.bags[bag] or 0 end,
  GetContainerItemInfo = function(bag, slot) local it = G.bags[bag] and G.bags[bag][slot] if it then return { itemID = it[1], stackCount = it[2], itemName = it[3] } end end,
}
-- Your skills: { name, rank }
SKILLS = {}
GetNumSkillLines = function() return #SKILLS end
GetSkillLineInfo = function(i) local s = SKILLS[i] return s[1], false, false, s[2] end
C_TooltipInfo = { GetBagItem = function(bag, slot)
  local it = G.bags[bag] and G.bags[bag][slot]
  if not it then return end
  TIP_LOOKS = (TIP_LOOKS or 0) + 1
  -- Before the game has loaded what the item does, only its name
  if G.tipsLoading then return { lines = { { leftText = FOODS[it[1]] } } } end
  return { lines = { { leftText = FOODS[it[1]] }, { leftText = FOOD_TIPS[it[1]] } } }
end }

UnitClass = function(unit) local c = unit ~= "player" and G.unitClasses and G.unitClasses[unit] return "Class", c or G.class end
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
UnitCastingInfo = function(u) if u == "target" and G.casting then return G.casting, "", 1, 0, 0, false, nil, G.uninterruptible end end
UnitChannelInfo = function() end
UnitIsDead = function() return false end
UnitIsDeadOrGhost = function() return G.dead end
UnitOnTaxi = function() return G.taxi end
IsInInstance = function() return G.instance, G.instance and "party" or "none" end
-- What the merchant you talk to sells
G.merchant = {}
GetMerchantNumItems = function() return #G.merchant end
GetMerchantItemID = function(i) return G.merchant[i] end
-- The minimap's tracking list: { name, spellID, active, type }
G.tracking = {}
C_Minimap = {
  GetNumTrackingTypes = function() return #G.tracking end,
  GetTrackingInfo = function(i) return G.tracking[i] end,
}
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
  elseif k == "SetText" then
    -- As in the game: a text with no font can't be written
    if rawget(self, "isFont") and not rawget(self, "font") then error("FontString:SetText(): Font not set", 2) end
    self.text = ...
  elseif k == "GetStringWidth" then return #tostring(self.text or "") * 6
  elseif k == "SetFormattedText" then
    if rawget(self, "isFont") and not rawget(self, "font") then error("FontString:SetFormattedText(): Font not set", 2) end
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
-- Secure frames, and what an addon tried to do to them in a fight
SECURE, BLOCKED = {}, {}
function Protected(frame)
  for _, s in ipairs(SECURE) do
    local p = s
    while p do
      if rawequal(p, frame) then return true end
      p = rawget(p, "parent")
    end
  end
  return false
end

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
  -- A text made from a template has its font; one made bare has none until it's given one
  function f:CreateFontString(_, _, template) local t = Texture() t.isFont = true if template then t.font = { template } end return t end
  function f:SetAlpha(a) self.alpha = Unwrap(a) self.hiddenAlpha = issecretvalue(a) end
  -- The game reads the secret itself: the frame gets one alpha or the other
  function f:SetAlphaFromBoolean(b, yes, no) if Unwrap(b) then self.alpha = yes else self.alpha = no end end
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
  function f:GetRight() return 336 end
  function f:GetTop() return 536 end
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
  -- As in the game: in a fight a secure button, and any frame holding one, can't be shown, hidden,
  -- moved or changed by an addon (the game blocks it). Recorded in BLOCKED, the tests fail on it
  if type(template) == "string" and template:find("Secure") then SECURE[#SECURE + 1] = f end
  for _, method in ipairs({ "Show", "Hide", "SetShown", "SetAttribute", "SetPoint", "ClearAllPoints", "SetParent", "SetSize" }) do
    local orig = rawget(f, method)
    if orig then
      f[method] = function(self, ...)
        if InCombatLockdown() and not ENTERING_COMBAT and Protected(self) then
          local info = debug.getinfo(2, "Sl")
          if info and info.source:sub(1, 1) == "@" then
            BLOCKED[#BLOCKED + 1] = info.source:sub(2) .. ":" .. tostring(info.currentline) .. " " .. method .. " on " .. tostring(name or "a secure frame")
          end
        end
        return orig(self, ...)
      end
    end
  end
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
-- Talent reset: the trainer's options, the game's price dialog, the gold and the server's clock
GOSSIP_OPTIONS = {}
C_GossipInfo = { GetOptions = function() return GOSSIP_OPTIONS end, SelectOption = function() end }
GossipFrame = CreateFrame("Frame")
POPUPS = {}
StaticPopup_FindVisible = function(which) return POPUPS[which] end
GetMoney = function() return G.money or 0 end
GetServerTime = function() return G.server or 0 end
date = os.date
ConfirmTalentWipe = function() end
hooksecurefunc = function(a, b, c)
  local t, key, fn = _G, a, b
  if type(a) == "table" then t, key, fn = a, b, c end
  local orig = t[key]
  t[key] = function(...) local r = { orig(...) } fn(...) return unpack(r) end
end

-- The reminder icons showing, in order
function ShownIcons(parent)
  local t = {}
  for _, f in ipairs(FRAMES) do if f.parent == parent and f.shown and f.icon then t[#t + 1] = f end end
  return t
end
function Same(a, b) return rawequal(a, b) end
function Fire(event, ...) for _, f in ipairs(FRAMES) do if f.events[event] and f.scripts.OnEvent then f.scripts.OnEvent(f, event, ...) end end end
''')

lua.execute('''
-- PLAYER_REGEN_DISABLED is the last moment the game lets an addon change its secure buttons
ENTERING_COMBAT = false
local fire = Fire
Fire = function(event, ...)
  ENTERING_COMBAT = event == "PLAYER_REGEN_DISABLED"
  fire(event, ...)
  ENTERING_COMBAT = false
end
-- Globals an addon file leaves behind: only its own name's, SLASH_ and BINDING_ are fine
LEAKS = {}
setmetatable(_G, { __newindex = function(t, k, v)
  local info = debug.getinfo(2, "Sl")
  if info and info.source:sub(1, 1) == "@" and type(k) == "string" and not k:find("^MageGod")
    and not k:find("^SLASH_") and not k:find("^BINDING_") then
    LEAKS[#LEAKS + 1] = info.source:sub(2) .. ":" .. tostring(info.currentline) .. " " .. k
  end
  rawset(t, k, v)
end })
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
check(casters() == [(None, "Mage Armor", "player")], f"Ice and Mage Armor known: the armor one doesn't cast, it opens a choice: {casters()}")
acaster = [b for b in G.ShownIcons(cast).values()][0]
amenu, arows = ns.ArmorMenu()
acaster.hooks.OnClick(acaster, "LeftButton", False)
check(amenu.shown and [(r.attrs.type, r.attrs.spell, r.attrs.unit) for r in arows.values() if r.shown]
      == [("spell", "Ice Armor", "player"), ("spell", "Mage Armor", "player")],
      "a click: your armors as bars, each puts that one on you")
arows[2].hooks.OnClick(arows[2], "LeftButton", False)
check(not amenu.shown, "picking one closes the list")
know(6117, on=False)
check(casters() == [("spell", "Ice Armor", "player")], f"only one armor known: the click casts it straight away: {casters()}")
know(6117)
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


def shield(spell, amount, *aura):
    S.absorb = amount
    if aura:
        auras(**{aura[0]: aura[1]})
    G.Fire("UNIT_SPELLCAST_SUCCEEDED", "player", "cast", spell)
    G.RunTimers()
    return [round(v, 2) for v in status.barColor.values()]


def tone(key):
    c = db.barrier.colors[key]
    return [round(c.r, 2), round(c.g, 2), round(c.b, 2)]


got = shield(10225, 913, "Fire_Ward", (30, 30, 10225))
check(bar.shown and got == tone("fireWard") and bar.time.text == "30" and bar.icon.tex == 10225,
      f"Fire Ward: the bar in its own orange, its 30 seconds and icon: {got}, {bar.time.text}")
got = shield(28609, 913, "Frost_Ward", (30, 30, 28609))
check(got == tone("frostWard") and bar.icon.tex == 28609, f"Frost Ward: its own pale frost: {got}")
got = shield(10193, 900, "Mana_Shield", (60, 60, 10193))
check(got == tone("manaShield") and bar.time.text == "60", f"Mana Shield: arcane: {got}")
got = shield(11426, 800, "Ice_Barrier", (60, 60, 11426))
check(got == [0.52, 0.78, 0.92], f"Ice Barrier: the bar's own frost: {got}")
got = shield(17543, 2600, "Fire_Protection", (120, 120, 17543))
check(got == tone("fire") and bar.time.text == "2:00" and list(status.minmax.values()) == [0, 2600],
      f"a Greater Fire Protection Potion: in fire's colour, its two minutes as 2:00: {got}, {bar.time.text}")
got = shield(17548, 2600, "Shadow_Protection", (120, 120, 17548))
check(got == tone("shadow"), f"each potion in its school's colour: {got}")
S.absorb = 0
ns.UpdateBarrier()
db.barrier.potions = False
shield(7233, 1300, "Fire_Protection", (120, 120, 7233))
S.absorb = G.Hidden(1300)
ns.UpdateBarrier()
check(not bar.shown, "the potions can be left out")
db.barrier.potions = True
S.absorb = 0
ns.UpdateBarrier()
auras(Power_Word__Shield=(30, 30, 10901))
S.absorb = 600
G.Fire("UNIT_ABSORB_AMOUNT_CHANGED", "player")
check(bar.shown and [round(v, 2) for v in status.barColor.values()] == tone("powerWord") and bar.icon.tex == 10901,
      f"a priest's Power Word: Shield, seen out of combat: its own colour and icon: {list(status.barColor.values())}")
S.absorb = 0
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(1900, 3600), Well_Fed=(800, 900), Ice_Barrier=(60, 60))
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

# Scrolls not yet deciphered: a click casts Comprehend Scroll on one
saved_bags = S.bags
S.bags = lua.table_from({0: lua.table_from([lua.table(211787, 1), lua.table(281015, 1)]),
                         1: lua.table_from([lua.table(700, 3), lua.table(999123, 1, "Scroll: NEW WORDS"),
                                            lua.table(999124, 1, "Scroll of Wit")])})
G.Fire("BAG_UPDATE_DELAYED")
check(extras() == [], "Comprehend Scroll not learned yet: nothing")
know(1296017)
decipher = "/cast Comprehend Scroll\n/use 0 1"
check(extras() == [(f"{L.DECIPHER} (3)", "macro", decipher)],
      f"three to decipher (one by its name alone, not the deciphered Scroll of Wit), the easiest first: {extras()}")
drow = list(G.ShownIcons(food).values())[0]
check(drow.icon.tex == 2117870 and drow.item == 211787 and drow.clickText == L.CLICK_DECIPHER,
      "with the scroll's icon, and its tooltip says what a click does")
G.SKILLS = lua.table(lua.table(L.COMPREHENSION, 12))
ns.UpdateBuffs()
check(extras() == [(f"{L.DECIPHER} (2)", "macro", decipher)], f"Comprehension 12: the one that wants 175 left out: {extras()}")
S.bags = lua.table_from({0: lua.table_from([lua.table(700, 3), lua.table(281015, 1)])})
G.Fire("BAG_UPDATE_DELAYED")
check(extras() == [], "only one you can't read yet: nothing")
G.SKILLS = lua.table()
G.Fire("BAG_UPDATE_DELAYED")
check(extras() == [(L.DECIPHER, "macro", "/cast Comprehend Scroll\n/use 0 2")], f"skill unknown: tried anyway, where it is: {extras()}")
S["items"][277651] = 1
G.Fire("BAG_UPDATE_DELAYED")
check(extras()[1] == (L.OPEN_BUNDLE, "item", "item:277651"), f"a Bundle of Scrolls: a click opens it: {extras()}")
db.scrolls.decipher = False
ns.UpdateBuffs()
check(extras() == [], "can be turned off")
db.scrolls.decipher = True
S["items"][277651] = 0
S.bags = saved_bags
G.Fire("BAG_UPDATE_DELAYED")

# ---------------------------------------------------------------- Moving the displays
ns.SetUnlocked(True)
check(len(icons()) == 2 and food.shown and rng.shown and thr.shown and bar.shown and mana.shown,
      "unlocked: samples of everything to drag")
check(mana.text.text == "3.2" and bar_color() == (0.45, 0.5, 0.62), "the mana bar's sample is a wait")
check(not cast.shown, "the cast buttons stay out of the way")
check([r[0] for r in extras()] == ["Arcane Intellect  1:35", L.FOOD_MISSING, L.IMBUE_MISSING, L.FAMILIAR_MISSING, L.DECIPHER],
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
check(controls[L.OPT_BARRIER_ICON] is not None and controls[L.OPT_SHIELD_COLOR % "Ice Barrier"] is not None
      and controls[L.OPT_SHIELD_COLOR % "Fire Ward"] is not None and controls[L.OPT_BARRIER_POTIONS] is not None,
      "and its icon, a colour for each shield and the potions")
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
check(place.point[1] == "CENTER" and G.Same(place.point[2], G.UIParent) and place.point[5] == -20
      and G.Same(holder.point[2], place) and holder.scale == 0.6, "around you: a bit under the middle, at 60%")
for saved, fresh, want in ((dict(size=100), False, 60), (dict(size=80), False, 80), (dict(size=100, v=2), False, 100)):
    old = lua.table(missiles=lua.table(size=saved["size"]), version=saved.get("v"))
    ns.MigrateSettings(old, fresh)
    check(old.missiles.size == want and old.version == 2, f"settings from 1.0.0, size {saved}: {old.missiles.size}")
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

# ---------------------------------------------------------------- Clearcasting, Heating Up and Fingers of Frost
KEYS = ("clearcasting", "heating", "fingers")


def pst(key):
    return ns.ProcsState(key)


def files_of(art):
    return [e[1].tex for e in art.tinted.values()]


def xs_of(art):
    return sorted({round(e[1].points[1][4]) for e in art.placed.values()})


before = len(boxes())
check(all(pst(k).container is None for k in KEYS), "no talent for any of them: nothing watched")
know(11213)  # Arcane Concentration
cc = pst("clearcasting")
check(cc.container is not None and len(boxes()) == before + 1 and watched(cc.container) == [12536],
      "Arcane Concentration learnt: a container watching Clearcasting's buff")
check(cc.container.slot.filter == "HELPFUL" and cc.container.unit == "player" and cc.container.enabled, "your buffs")
check(pst("heating").container is None and pst("fingers").container is None, "the others still wait for their talents")
art = cc.dressed
button = cc.container.button
check(art.ready and len(button.shownAnims) == 2 and len(button.assignedAnims) == 4,
      "Clearcasting: the circle turning and breathing while it lasts; it lands, spins, glows and flashes as it comes")
files = files_of(art)
check(files.count(MEDIA + "ring_glow") == 2 and files.count(MEDIA + "ring_core") == 2 and files.count(MEDIA + "ring_base") == 2,
      f"a circle on the ground, calm and burst: {files}")
check(art.calm.alpha == 0.2 and art.strike.alpha == 0.6, "small and see-through by default: 60% as it procs, 20% while it lasts")
tpoint = list(art.timer.points[1].values())
check(tpoint[0] == "CENTER" and tpoint[2:] == ["CENTER", 0, -150] and art.timer.font[2] == 16,
      f"its seconds inside the circle, a little smaller: {tpoint}, {art.timer.font[2]}")
cs = [round(e[1].color[1], 2) for e in art.tinted.values()][:1]
check(cs == [0.72], f"arcane lilac: {cs}")
check(cc.holder.scale == 0.4, "at 40%")

know(400624)  # Heating Up
hu = pst("heating")
art = hu.dressed
check(hu.container is not None and watched(hu.container) == [400625], "Heating Up learnt: its buff watched, not the talent")
check(len(hu.container.button.shownAnims) == 3 and len(hu.container.button.assignedAnims) == 3,
      "embers: each column rising and their glow breathing; a flare as it comes")
files = files_of(art)
check(files.count(MEDIA + "ember_glow") == 4 and files.count(MEDIA + "ember_core") == 4, f"two columns of embers: {files}")
check(xs_of(art) == [-120, 120], f"one on each side of you: {xs_of(art)}")

know(400647)  # Fingers of Frost
ff = pst("fingers")
art = ff.dressed
check(ff.container is not None and watched(ff.container) == [400669, 400670], "Fingers of Frost: both its buffs")
files = files_of(art)
check(files.count(MEDIA + "frost_glow") == 4 and files.count(MEDIA + "frost_core") == 4, f"a snowflake by each hand: {files}")
check(xs_of(art) == [-66, 66], f"closer in than the embers: {xs_of(art)}")
check(len(ff.container.button.shownAnims) == 3 and len(ff.container.button.assignedAnims) == 3, "turning, and flying in as it comes")

# Another number for the same buff, seen out of combat, joins the list
auras(Clearcasting=(10, 15, 999101))
check(watched(pst("clearcasting").container) == [12536, 999101] and db.procs.learned[999101] == "clearcasting",
      "a Clearcasting with another number joins it")
auras()

# A talent unlearnt: its proc stops being watched
old = pst("fingers").container
know(400647, on=False)
check(pst("fingers").container is None and not old.enabled, "Fingers of Frost unlearnt: switched off")
S.combat = True
know(400647)
check(pst("fingers").container is None, "learnt again in a fight: it waits")
S.combat = False
G.Fire("PLAYER_REGEN_ENABLED")
check(pst("fingers").container is not None, "and is built once the fight is over")

# The samples: while moving the displays, only the ones you have the talent for
know(400624, on=False)
ns.SetUnlocked(True)
check(pst("clearcasting").sampleShown and pst("fingers").sampleShown and not pst("heating").sampleShown,
      "moving the displays: the samples of the procs your talents give, not Heating Up's")
check(pst("clearcasting").spot.shown and G.NAMED["MageGodProcs"].mover.shown, "with a box to drag")
ns.SetUnlocked(False)
check(not pst("clearcasting").sampleShown and not pst("clearcasting").spot.shown, "locked: gone")
out = slash("procs")
check(len(out) == 3 and "12536, 999101" in out[0] and L.PROCS_NO_TALENT % ("Heating Up", "Heating Up") == out[1].split("|r ", 1)[-1]
      and "400669, 400670" in out[2], f"/magegod procs: what each watches, and the one without its talent: {out}")
check(all(pst(k).sampleShown for k in KEYS), "and shows all three a moment, even without the talent")
heat = pst("heating")
heat.spot.scripts.OnUpdate(heat.spot, 0.1)
check(heat.sample.timer.text == "20", f"Heating Up's sample counts down from 20: {heat.sample.timer.text}")
S.now = S.now + 6
G.RunTimers()
check(not any(pst(k).sampleShown for k in KEYS), "a few seconds later they're gone")

# The options
ns.ShowOptionsPage("procs")
pcontrols = {c.setting: c for c in page["procs"].controls.values()}
name = "Clearcasting"
check(L.OPT_PROC_CLEARCASTING % ("Clearcasting", "Arcane Concentration") in pcontrols
      and L.OPT_PROC_HEATING % ("Heating Up", "Heating Up") in pcontrols
      and L.OPT_PROC_FINGERS % ("Fingers of Frost", "Fingers of Frost") in pcontrols,
      "a switch for each, saying its talent")
psize = pcontrols[L.OPT_PROCS_SIZE]
psize.scripts.OnValueChanged(psize, 100)
check(db.procs.size == 100 and pst("clearcasting").holder.scale == 1 and pst("clearcasting").spot.scale == 1, "their size")
pgap = pcontrols[L.OPT_PROCS_GAP]
pgap.scripts.OnValueChanged(pgap, 200)
check(xs_of(pst("fingers").dressed) == [-110, 110], f"the space between the sides moves the snowflakes too: {xs_of(pst('fingers').dressed)}")
px = pcontrols[L.OPT_PROCS_X]
px.scripts.OnValueChanged(px, 50)
check(list(db.positions.procs.values()) == ["CENTER", "CENTER", 50, -20], f"left or right: {list(db.positions.procs.values())}")
check(db.missiles.size != 100 or db.positions.missiles is None or db.positions.missiles[3] != 50,
      "the lightning keeps its own size and place")
pcalm = pcontrols[L.OPT_PROCS_CALM]
pcalm.scripts.OnValueChanged(pcalm, 40)
check(pst("clearcasting").dressed.calm.alpha == 0.4, "their calm strength")
on = pcontrols[L.OPT_PROC_CLEARCASTING % ("Clearcasting", "Arcane Concentration")]
on.checked = False
on.scripts.OnClick(on)
check(not db.procs.clearcasting.enabled and not pst("clearcasting").holder.shown, "Clearcasting can be turned off")
on.checked = True
on.scripts.OnClick(on)
check(pst("clearcasting").holder.shown, "and on again")
win.Hide(win)
db.procs.size, db.procs.gap, db.procs.calm = 40, 120, 20
db.positions.procs = None
ns.StyleProcs()
know(11213, 400647, on=False)

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

# ---------------------------------------------------------------- Reagents running low
RT = ns.REAGENT_TEXT
check(db.reagents.enabled, "the reagent reminder is on by default")


def reagent_rows():
    return [r for r in extras() if "17031" in r[0] or "17032" in r[0] or "17056" in r[0]]


G.Fire("BAG_UPDATE_DELAYED")
check(reagent_rows() == [], "no teleports known: no runes to remind")
know(3561, 3562)
check(reagent_rows() == [(RT.NONE % "gem 17031", None, None)], f"Teleport known, no runes: says so: {reagent_rows()}")
S["items"][17031] = 2
G.Fire("BAG_UPDATE_DELAYED")
check(reagent_rows() == [(RT.LOW % ("gem 17031", 2), None, None)], f"two left: how many: {reagent_rows()}")
rrow = [b for b in G.ShownIcons(food).values() if b.text.text == RT.LOW % ("gem 17031", 2)][0]
check(rrow.item == 17031 and rrow.clickText == RT.FOR % "Teleport: Stormwind, Teleport: Ironforge",
      f"its tooltip says what spends them: {rrow.clickText}")
S["items"][17031] = 5
G.Fire("BAG_UPDATE_DELAYED")
check(reagent_rows() == [], "five: enough")
S["items"][17031] = 1
know(10059)
check(len(reagent_rows()) == 2, "Portal known too: its runes as well")
S.known[1225503] = True
G.Fire("SPELLS_CHANGED")
check(reagent_rows() == [], "with Reagent Economy no reminder for what vendors sell")
S.known[1225503] = None
G.Fire("SPELLS_CHANGED")
printed.clear()
S.merchant = lua.table(159, 17031, 17032)
G.Fire("MERCHANT_SHOW")
check(len(printed) == 2 and RT.VENDOR % ("gem 17031", 1) in printed[0] and RT.VENDOR % ("gem 17032", 0) in printed[1],
      f"a merchant that sells them says so in the chat: {list(printed)}")
S.merchant = lua.table()
db.reagents.enabled = False
ns.RefreshReagents()
check(reagent_rows() == [], "it can be turned off")
db.reagents.enabled = True
check("%s" in L.OPT_REAGENTS and L.SEC_REAGENTS, "its option has its words")
know(3561, 3562, 10059, on=False)
S["items"][17031] = 0
G.Fire("BAG_UPDATE_DELAYED")
check(reagent_rows() == [], "no teleports: gone")

# ---------------------------------------------------------------- The wand's swing timer
wbar = G.NAMED["MageGodWand"]
check(db.wand.enabled and not wbar.shown, "the wand bar is on, hidden until you shoot")
S.wand = 5240
S.wandSpeed = 1.5
ns.StyleWand()
G.Fire("PLAYER_SWING", 1.5, 0)
check(not wbar.shown, "a melee swing doesn't count")
G.Fire("PLAYER_SWING", 1.5, 2)
check(wbar.shown and wbar.time.text == "1.5" and wbar.tag.tex == 135463, f"a wand shot: the bar, its seconds and your wand's icon: {wbar.time.text}")
S.now = S.now + 0.75
ns.UpdateWand()
check(wbar.time.text == "0.8", f"halfway: 0.8 s left ({wbar.time.text})")
S.now = S.now + 0.75 + 2.1
ns.UpdateWand()
check(not wbar.shown, "two seconds after the last shot it goes")
G.Fire("PLAYER_SWING", G.SECRET, 2)
check(not wbar.shown, "a hidden duration is left alone")
# The game says nothing of the wand's shots: Shoot keeps it going at the wand's speed
st = ns.WandState
G.Fire("START_AUTOREPEAT_SPELL")
check(wbar.shown and wbar.time.text == "1.5", f"Shoot on, no word from the game: the bar at your wand's speed: {wbar.time.text}")
S.now = S.now + 1.6
ns.UpdateWand()
check(wbar.shown and float(wbar.time.text) > 1.3, f"and the next shot after it: {wbar.time.text}")
G.Fire("STOP_AUTOREPEAT_SPELL")
S.now = S.now + 4
ns.UpdateWand()
check(not wbar.shown, "Shoot off: it goes")
G.Fire("PLAYER_SWING_RANGE_UPDATE", 2, False, True)
G.Fire("PLAYER_SWING", 1.5, 2)
check(wbar.shown and abs(wbar.alpha - 0.55) < 1e-6, "your target out of reach: grey and faded")
G.Fire("PLAYER_SWING_RANGE_UPDATE", 2, True, True)
db.wand.enabled = False
ns.UpdateWand()
check(not wbar.shown, "it can be turned off")
db.wand.enabled = True
S.now = S.now + 5
ns.UpdateWand()
out = slash("varita" if es else "wand")
check(wbar.shown, "/magegod wand shows it shooting")
S.now = S.now + 7
G.RunTimers()
check(not wbar.shown, "and it goes after a while")
S.wand = None

# ---------------------------------------------------------------- Group buffs, gear and bags
GT, RPT = ns.GROUP_BUFF_TEXT, ns.REPAIR_TEXT
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(3600, 3600), Well_Fed=(800, 900))
base = icons()
S.group = True
G.Fire("GROUP_ROSTER_UPDATE")
check(icons() == base, "in a group where everyone has Arcane Intellect: nothing")
auras(Mage_Armor=(1800, 1800), Well_Fed=(800, 900))
G.Fire("UNIT_AURA", "party1")
gb = list(ns.GroupBuffReminders().values())
check(len(gb) == 1 and gb[0].count == 4 and gb[0].unit == "party1" and gb[0].text == GT.MISSING % ("Arcane Intellect", 4),
      f"four party members without it: how many, and the first to cast it on: {[(r.count, r.unit) for r in gb]}")
check((1459, True, "4") in icons(), f"its icon in the row with the count: {icons()}")
check(("spell", "Arcane Intellect", "party1") in casters(), f"a click casts it on that member: {casters()}")
S.unitClasses = lua.table(party1="WARRIOR", party2="ROGUE")
G.Fire("UNIT_AURA", "party1")
gb = list(ns.GroupBuffReminders().values())
check(len(gb) == 1 and gb[0].count == 2 and gb[0].unit == "party3",
      f"warriors and rogues have no mana: not counted for it: {[(r.count, r.unit) for r in gb]}")
S.unitClasses = None
G.Fire("UNIT_AURA", "party1")
auras(Mage_Armor=(1800, 1800), Arcane_Brilliance=(3600, 3600), Well_Fed=(800, 900))
G.Fire("UNIT_AURA", "party1")
check(ns.GroupBuffReminders() == [] or len(list(ns.GroupBuffReminders())) == 0, "Arcane Brilliance counts too")
S.group = False
G.Fire("GROUP_ROSTER_UPDATE")
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(3600, 3600), Well_Fed=(800, 900))
check(len(list(ns.GroupBuffReminders())) == 0, "alone: nothing")

def repair_rows():
    return [r[0] for r in extras() if "%" in r[0] or r[0].startswith(RPT.BAGS.split(":")[0]) or r[0] == RPT.BAGS_FULL]

S.durability = 18
G.Fire("UPDATE_INVENTORY_DURABILITY")
check(RPT.WORN % 18 in repair_rows(), f"gear at 18%: a reminder: {repair_rows()}")
S.durability = 60
G.Fire("UPDATE_INVENTORY_DURABILITY")
check(repair_rows() == [], "at 60%: nothing")
S.freeSlots = 1
G.Fire("BAG_UPDATE_DELAYED")
check(RPT.BAGS % 1 in repair_rows(), f"one free slot left: a reminder: {repair_rows()}")
S.freeSlots = 0
G.Fire("BAG_UPDATE_DELAYED")
check(RPT.BAGS_FULL in repair_rows(), "bags full: says so")
S.freeSlots = 10
G.Fire("BAG_UPDATE_DELAYED")
printed.clear()
S.repairs = True
G.Fire("MERCHANT_SHOW")
check(len(printed) == 1 and RPT.VENDOR % 60 in printed[0], f"a vendor who repairs says how worn your gear is: {list(printed)}")
S.repairs = False
S.durability = None
db.repair.enabled = False
ns.RefreshRepair()
check(repair_rows() == [], "it can be turned off")
db.repair.enabled = True

# ---------------------------------------------------------------- Herbalism or Mining: their tracking
check(db.gather.enabled, "the gathering tracking reminder is on by default")
auras(Mage_Armor=(1800, 1800), Arcane_Intellect=(3600, 3600), Well_Fed=(800, 900))
base = icons()
G.Fire("MINIMAP_UPDATE_TRACKING")
check(icons() == base and ns.GatherReminder() is None, "no gathering profession: no tracking reminder")


def tracking(*rows):
    S.tracking = lua.table(*[lua.table(name=n, spellID=i, active=a, type="spell") for n, i, a in rows])
    G.Fire("MINIMAP_UPDATE_TRACKING")


tracking(("Find Herbs", 2383, False))
know(2383)
check(icons() == base + [(2383, True, "")], f"a herbalist without Find Herbs on: its icon in the row, grey: {icons()}")
check(("spell", "Find Herbs", "player") in casters(), f"a click turns it on: {casters()}")
tracking(("Find Herbs", 2383, True))
check(icons() == base and db.gather.last == "herbs", "Find Herbs on: gone, and it remembers it was herbs")
know(2580)
tracking(("Find Herbs", 2383, False), ("Find Minerals", 2580, True))
check(icons() == base and db.gather.last == "minerals", "herbalist and miner: Find Minerals on counts too")
tracking(("Find Herbs", 2383, False), ("Find Minerals", 2580, False))
check(icons() == base + [(2580, True, "")], f"both off: the one you had on last, Find Minerals: {icons()}")
check(("spell", "Find Minerals", "player") in casters(), "and its click")
db.gather.last = None
ns.UpdateBuffs()
check(icons() == base + [(2383, True, "")], "nothing remembered: the first you know, Find Herbs")
S.instance = True
G.Fire("PLAYER_ENTERING_WORLD")
check(icons() == base, "in a dungeon, raid or battleground: no reminder")
S.instance = False
S.taxi = True
ns.UpdateBuffs()
check((2383, True, "") not in icons(), "nor on a flight")
S.taxi = False
S.combat = True
G.Fire("PLAYER_REGEN_DISABLED")
check((2383, True, "") not in icons(), "nor in a fight")
S.combat = False
G.Fire("PLAYER_REGEN_ENABLED")
check(icons() == base + [(2383, True, "")], "back after it")
S.tracking[1].active = G.SECRET
G.Fire("MINIMAP_UPDATE_TRACKING")
check(icons() == base, "the game hides the tracking list: no guessing")
tracking(("Find Herbs", 2383, False))
know(2383, 2580, on=False)
check(icons() == base + [(2383, True, "")], "known through the tracking list when the spellbook doesn't say")
minimap = G.C_Minimap
G.C_Minimap = None
ns.UpdateBuffs()
check(icons() == base, "no tracking list in the game: nothing")
G.C_Minimap = minimap
db.gather.enabled = False
ns.UpdateBuffs()
check(icons() == base, "it can be turned off")
db.gather.enabled = True
check("%s" in L.OPT_GATHER and L.SEC_GATHER, "its option has its words")
tracking()
check(icons() == base, "no gathering profession left: gone")

# ---------------------------------------------------------------- Other big cooldowns back
pst = ns.PulseState()
ppl = pst.place
S.now = S.now + 10
pst.place.scripts.OnUpdate(pst.place, 0.1)
know(12051)  # Evocation
G.COOLDOWNS[12051] = lua.table(isActive=True, duration=480)
G.Fire("SPELL_UPDATE_COOLDOWN")
check(ns.PulseState().states.evocation.since is not None, "Evocation cooling down: watched")
G.COOLDOWNS[12051] = lua.table(isActive=False, duration=0)
G.Fire("SPELL_UPDATE_COOLDOWN")
check(ppl.shown and pst.art.icon.tex == 12051, f"Evocation back: its icon pulses in the middle ({pst.art.icon.tex})")
know(12472)  # Cold Snap, back while Evocation's pulse plays
G.COOLDOWNS[12472] = lua.table(isActive=True, duration=600)
G.Fire("SPELL_UPDATE_COOLDOWN")
G.COOLDOWNS[12472] = lua.table(isActive=False, duration=0)
G.Fire("SPELL_UPDATE_COOLDOWN")
check(pst.art.icon.tex == 12051 and len(list(ns.PulseState().queue.values())) == 1, "two at once: the second waits its turn")
S.now = S.now + 1.2
pst.place.scripts.OnUpdate(pst.place, 0.1)
check(pst.art.icon.tex == 12472, "and pulses right after")
S.now = S.now + 1.2
pst.place.scripts.OnUpdate(pst.place, 0.1)
db.pulse.spells.evocation = False
G.COOLDOWNS[12051] = lua.table(isActive=True, duration=480)
G.Fire("SPELL_UPDATE_COOLDOWN")
G.COOLDOWNS[12051] = lua.table(isActive=False, duration=0)
G.Fire("SPELL_UPDATE_COOLDOWN")
check(not ppl.shown, "each one can be turned off")
db.pulse.spells.evocation = True
know(12051, 12472, on=False)

# ---------------------------------------------------------------- Counterspell ready
kick = ns.KickFrame()
S.target = lua.table(hostile=True)
S.dist = 20
know(2139)
G.Fire("PLAYER_TARGET_CHANGED")
check(not kick.shown, "Counterspell known, the target not casting: nothing")
S.casting = "Fireball"
G.Fire("UNIT_SPELLCAST_START", "target")
check(kick.shown and kick.icon.tex == 2139, "the target casts and Counterspell is ready: its icon")
S.casting = G.SECRET
G.Fire("UNIT_SPELLCAST_START", "target")
check(kick.shown, "a cast the game hides still counts")
S.casting = "Fireball"
G.COOLDOWNS[2139] = lua.table(isActive=True, duration=24)
G.Fire("SPELL_UPDATE_COOLDOWN")
check(not kick.shown, "Counterspell cooling down: nothing")
G.COOLDOWNS[2139] = None
S.uninterruptible = True
G.Fire("UNIT_SPELLCAST_START", "target")
check(not kick.shown, "a cast that can't be cut: nothing")
S.uninterruptible = None
S.uninterruptible = G.Hidden(True)
G.Fire("UNIT_SPELLCAST_START", "target")
check(kick.shown and kick.inner.alpha == 0, f"in a fight the game hides that it can't be cut: the game hides the icon: {kick.inner.alpha}")
S.uninterruptible = G.Hidden(False)
G.Fire("UNIT_SPELLCAST_NOT_INTERRUPTIBLE", "target")
check(kick.shown and kick.inner.alpha == 1, "hidden, and it can be cut: the icon shows")
S.uninterruptible = True
G.Fire("UNIT_SPELLCAST_NOT_INTERRUPTIBLE", "target")
check(not kick.shown, "the cast becomes uncuttable halfway: gone")
S.uninterruptible = None
G.Fire("UNIT_SPELLCAST_INTERRUPTIBLE", "target")
check(kick.shown and kick.inner.alpha == 1, "and cuttable again: back")
check(kick.width == 30, f"small by default: {kick.width}")
S.casting = None
G.Fire("UNIT_SPELLCAST_STOP", "target")
check(not kick.shown, "the cast over: gone")
db.kick.enabled = False
S.casting = "Fireball"
ns.UpdateKick()
check(not kick.shown, "it can be turned off")
db.kick.enabled = True
S.casting = None
ns.UpdateKick()
know(2139, on=False)
S.target = None

# ---------------------------------------------------------------- Your debuffs on the target
dst = ns.DebuffsState()
deb = {d.key: d for d in dst.debuffs.values()}
check(deb["scorch"].container is None and deb["chill"].container is None, "no talents: nothing watched on the target")
know(11095)  # Improved Scorch
c = deb["scorch"].container
check(c is not None and c.slot.filter == "HARMFUL" and c.unit == "target" and c.enabled
      and sorted(c.slot.options.candidateFilters.includeSpellIDs.keys()) == [22959],
      "Improved Scorch learnt: Fire Vulnerability watched on your target")
check(deb["scorch"].box.dressed, "its icon dressed by the game, with stacks and countdown")
check(deb["chill"].container is None, "Winter's Chill waits for its talent")
S.plate = G.CreateFrame("Frame")
G.Fire("PLAYER_TARGET_CHANGED")
check(dst.holder.shown, "beside the target's nameplate")
S.plate = None
G.Fire("PLAYER_TARGET_CHANGED")
check(not dst.holder.shown, "no nameplate: hidden")
db.debuffs.enabled = False
ns.RefreshAll()
check(not c.enabled, "it can be turned off")
db.debuffs.enabled = True
ns.RefreshAll()
know(11095, on=False)

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

# ---------------------------------------------------------------- Talent reset price at the trainer
S["class"] = "MAGE"
rs = ns.RespecState()
rnote, recs = rs.note, rs.records
DAY = 86400
T0 = 1795600000
S.server, S.money = T0, 500000
popup = G.CreateFrame("Frame")
TRAINER = lua.eval('{ { gossipOptionID = 101, name = "I am here for training." }, { gossipOptionID = 102, name = "I wish to unlearn my class or legacy talents." } }')
G.GOSSIP_OPTIONS = TRAINER
G.Fire("GOSSIP_SHOW")
check(rnote.shown and G.Same(rnote.anchor, G.GossipFrame) and rnote.point[1] == "TOPLEFT", "your class trainer: a note under its window")
check((L.RESPEC_UNKNOWN % "MageGod") in rnote.body.text and rnote.title.text == L.RESPEC_TITLE, "no reset written down yet: it says so")
G.Fire("GOSSIP_CLOSED")
check(not rnote.shown, "it goes with the window")
G.GOSSIP_OPTIONS = lua.eval('{ { gossipOptionID = 201, name = "I wish to untrain my pet." }, { gossipOptionID = 202, name = "I am here for training." } }')
G.Fire("GOSSIP_SHOW")
check(not rnote.shown, "any other trainer: nothing")
# Asking for the reset: the trainer's price, and the note under the game's dialog
G.GOSSIP_OPTIONS = TRAINER
G.C_GossipInfo.SelectOption(102)
G.POPUPS.CONFIRM_TALENT_WIPE = popup
G.Fire("CONFIRM_TALENT_WIPE", 10000, 0)
G.RunTimers()
check(rnote.shown and G.Same(rnote.anchor, popup) and rnote.point[1] == "TOP", "the price dialog: the note under it")
check((L.RESPEC_ASKED % ("1 g", L.RESPEC_MINUTES % 1)) in rnote.body.text, f"what the trainer asked: {rnote.body.text}")
check(db.respec.options[102], "the option that led there is learnt")
# Not enough gold: the game says no, and nothing is written down
G.ConfirmTalentWipe()
S.now = S.now + 11
G.RunTimers()
G.Fire("PLAYER_MONEY")
check(not recs["0"].reset and not ns.RespecState().pending, "accepted but no gold went: not a reset")
# Paid
G.Fire("CONFIRM_TALENT_WIPE", 10000, 0)
G.RunTimers()
G.ConfirmTalentWipe()
S.money = 490000
G.Fire("PLAYER_MONEY")
r = recs["0"]
check(r.reset == T0 and r.paid == 10000 and r.cost is None, "paid: the reset written down, with its price")
popup.shown = False
rnote.scripts.OnUpdate(rnote, 0.3)
check(not rnote.shown, "the dialog gone: the note too")
# A day on, at the trainer: a step up, and back down in six days
S.server = T0 + DAY
G.GOSSIP_OPTIONS = lua.eval('{ { gossipOptionID = 102, name = "Ich möchte meine Fähigkeiten verlernen." } }')
G.Fire("GOSSIP_SHOW")
drop = T0 + 7 * DAY
when = L.RESPEC_ON % (L.RESPEC_WEEKDAYS[G.date("*t", drop).wday], G.date("%H:%M", drop))
body = rnote.body.text
check(rnote.shown, "an option it learnt, in another language: still your trainer")
check((L.RESPEC_LAST % (L.RESPEC_HOURS % 24, "1 g")) in body and (L.RESPEC_NOW_ABOUT % "5 g") in body
      and (L.RESPEC_DROPS % ("1 g", when, L.RESPEC_DAYS % 6)) in body, f"a day on: about 5 g, down to 1 g in six days: {body}")
S.server = T0 + 7 * DAY - 3600
G.Fire("GOSSIP_SHOW")
check((L.RESPEC_TODAY % G.date("%H:%M", drop)) in rnote.body.text or (L.RESPEC_TOMORROW % G.date("%H:%M", drop)) in rnote.body.text,
      "the day it drops: today (or tomorrow, past midnight)")


def price(paid, days, seen=None, cost=None):
    rec = lua.table(reset=T0, paid=paid * 10000)
    if seen is not None:
        rec.seen, rec.cost = T0 + seen * DAY, cost * 10000
    out = tuple(ns.RespecPrice(rec, T0 + days * DAY)) + (None, None)
    return out[0] / 10000, out[1], out[2], out[3] and out[3] / 10000


check(price(10, 1) == (15, None, T0 + 7 * DAY, 10), f"paid 10 g: 15 g that week, then 10 g: {price(10, 1)}")
check(price(10, 8) == (10, None, T0 + 14 * DAY, 5), "a week on: 10 g, then 5 g")
check(price(10, 15) == (5, None, T0 + 21 * DAY, 1), "two weeks: 5 g, then 1 g")
check(price(10, 22)[:3] == (1, None, None), "three weeks: 1 g, the lowest")
check(price(50, 1) == (50, None, T0 + 7 * DAY, 45) and price(1, 1)[0] == 5, "50 g at most; after the first, 5 g")
check(price(10, 3, 2, 20)[:2] == (20, True), "the trainer asked more than worked out: its price counts")
check(price(10, 8, 2, 20)[:2] == (15, None), "and a week later, a step under it")
# The legacy tree's reset, kept apart
G.Fire("CONFIRM_TALENT_WIPE", 100000, 1)
G.RunTimers()
G.Fire("GOSSIP_SHOW")
body = rnote.body.text
check(L.RESPEC_CLASS in body and L.RESPEC_LEGACY in body and body.index(L.RESPEC_CLASS) < body.index(L.RESPEC_LEGACY),
      "class talents and the legacy tree, each with its own price")
out = slash("talentos" if es else "respec")
check(any(L.RESPEC_TITLE in line for line in out) and any(L.RESPEC_LEGACY in line for line in out), "and in the chat")
db.respec.enabled = False
G.Fire("GOSSIP_CLOSED")
G.Fire("GOSSIP_SHOW")
check(not rnote.shown, "the option off: no note")
db.respec.enabled = True
S["class"] = "HUNTER"
G.Fire("GOSSIP_SHOW")
check(not rnote.shown, "another class: not this addon's trainer")
S["class"] = "MAGE"

print()
# ---------------------------------------------------------------- Another class: nothing on screen
# Every ...God addon loads for every class: with another one, this one must draw nothing on top of
# the others (the minimap button and the options aside)
lua.execute('''
function VisibleFrames()
  local out = {}
  for name, f in pairs(NAMED) do
    local p, seen = f, true
    while p do
      if not rawget(p, "shown") then seen = false break end
      p = rawget(p, "parent")
    end
    -- A frame that only holds others draws nothing of its own: it counts only through them
    local holder = false
    for _, c in ipairs(FRAMES) do if rawequal(rawget(c, "parent"), f) then holder = true break end end
    if seen and not holder and not name:find("Spot$") and not name:find("Minimap") and not name:find("Options")
      and not name:find("Settings") then out[#out + 1] = name end
  end
  table.sort(out)
  return out
end
''')
S["class"] = "PRIEST"
S.freeSlots = 1  # bags nearly full: every ...God would warn its own class
S.combat = False
for ev in ("SPELLS_CHANGED", "BAG_UPDATE_DELAYED", "GROUP_ROSTER_UPDATE", "UPDATE_INVENTORY_DURABILITY", "PLAYER_REGEN_ENABLED"):
    G.Fire(ev)
G.Fire("UNIT_AURA", "player")
G.RunTimers() if G.RunTimers else None
for f in (ns.refreshers or lua.table()).values():
    f()
shown = list(G.VisibleFrames().values())
check(not shown, f"another class: nothing on screen: {shown}")
S.repairs = True  # a vendor who repairs, with your gear worn: its own class would hear of it
S.durability = 40
printed.clear()
G.Fire("MERCHANT_SHOW")
G.Fire("CONFIRM_TALENT_WIPE")
check(not printed, f"another class: nothing said at a vendor or a trainer: {list(printed)}")
out = slash("unlock")
check(out == [L.PREFIX + L.OTHER_CLASS] and not ns.unlocked and not list(G.VisibleFrames().values()),
      f"another class: no move mode, and it says why: {out}")

blocked = sorted(set(G.BLOCKED.values()))
check(not blocked, f"nothing secure touched in a fight (the game blocks it): {blocked}")
leaks = sorted(set(G.LEAKS.values()))
check(not leaks, f"no globals left behind: {leaks}")

print("FAILURES:" if fails else f"All good ({LOCALE}).", fails if fails else "")
sys.exit(1 if fails else 0)
