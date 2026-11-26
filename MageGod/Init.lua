local addonName, ns = ...
local L = ns.L

-- Settings: whatever is missing from the saved ones is filled in from here
local defaults = {
	buffs = {
		enabled = true,
		armor = true,
		armorChoice = "auto", -- auto (the last one you cast) | frost (Frost or Ice Armor) | mage
		intellect = true,
		magic = "none", -- none | dampen | amplify
		warnMinutes = 2, -- the reminder shows this long before a buff ends
		combat = false, -- in a fight the reminders would only get in the way
		click = true, -- clicking a reminder casts it, out of combat
	},
	lastArmor = nil, -- the armor you cast last: frost | ice | mage | molten
	gems = { enabled = true, all = false },
	-- Herbalism or Mining: Find Herbs or Find Minerals on, out in the world (last: the one you had on)
	gather = { enabled = true },
	-- Runes for teleports and portals, Arcane Powder, Light Feathers running low (not with Reagent Economy)
	reagents = { enabled = true },
	-- In a group, Arcane Intellect missing on someone: a click casts it on them
	groupBuffs = { enabled = true },
	-- Gear under this % and bags with this many free slots or fewer
	repair = { enabled = true, low = 25, bags = 2 },
	food = { enabled = true },
	-- Forever's mage scrolls that last an hour: a weapon imbue and a familiar
	scrolls = { imbue = true, familiar = true, decipher = true },
	-- At the class trainer: when the talent reset price drops. The trainer options seen to lead to the reset
	respec = { enabled = true, options = {} },
	scrollUsed = {}, -- by kind: time() when you last used one
	lastImbue = nil, -- the scroll you used last of each kind
	lastFamiliar = nil,
	-- What's left of your Ice Barrier or Mana Shield, on a bar you size to sit over the game's own
	barrier = {
		enabled = true, width = 160, height = 14, text = true, time = true,
		icon = true, -- the shield's icon on a tag at its left end, as the mana bar has MP5
		color = { r = 0.52, g = 0.78, b = 0.92 }, -- Ice Barrier's, and a shield the addon can't tell: frost
		-- Each other shield in its own colour; the protection potions in their school's
		colors = {
			manaShield = { r = 0.6, g = 0.5, b = 1 }, -- arcane
			fireWard = { r = 1, g = 0.5, b = 0.15 },
			frostWard = { r = 0.75, g = 0.95, b = 1 }, -- paler than Ice Barrier
			powerWord = { r = 1, g = 0.92, b = 0.6 }, -- a priest's Power Word: Shield
			fire = { r = 1, g = 0.42, b = 0.1 },
			frost = { r = 0.45, g = 0.75, b = 1 },
			nature = { r = 0.4, g = 0.85, b = 0.3 },
			shadow = { r = 0.62, g = 0.38, b = 0.85 },
			arcane = { r = 0.85, g = 0.55, b = 1 },
			holy = { r = 1, g = 0.85, b = 0.35 },
		},
		potions = true, -- the protection potions too: each absorbs a school's damage for 2 minutes
	},
	-- The five-second rule: how long until your Spirit gives mana back, then each tick
	mana = {
		enabled = true, width = 160, height = 8, text = true, ticks = true, label = true,
		onlyCombat = true, -- out of a fight it only gets in the way
		colors = {
			wait = { r = 0.45, g = 0.5, b = 0.62 }, -- the five seconds without regen
			regen = { r = 0.38, g = 0.56, b = 0.7 }, -- your mana coming back: a quiet blue
		},
	},
	-- Your wand's swing timer: when the next shot comes
	wand = { enabled = true, width = 160, height = 10, icon = true, time = true, color = { r = 0.25, g = 0.78, b = 0.92 } },
	-- Purple lightning on both sides of you while Missile Barrage is up
	missiles = {
		enabled = true,
		size = 60, -- %: around your character, not over half the screen
		gap = 150, -- from the middle to each side
		alpha = 85, -- the strike as it comes, %
		calm = 30, -- the lightning while it lasts, after the strike: faint, %
		timer = true, -- the seconds it has left, under it
		timerSize = 22,
		color = { r = 0.62, g = 0.32, b = 1 },
		learned = {}, -- other spells the addon saw by Missile Barrage's name
		ignored = {}, -- ones it saw always on: a passive, not the proc
	},
	-- Clearcasting, Heating Up and Fingers of Frost around you, each with its talent: small and
	-- see-through by default, as HunterGod's procs
	procs = {
		size = 40, -- %
		gap = 120, -- from the middle to each side of the embers; the snowflakes go half as far
		alpha = 60, -- the burst as it procs, %
		calm = 20, -- afterwards, while it lasts: fainter, %
		timer = true, -- the seconds each has left
		timerSize = 20,
		clearcasting = { enabled = true, color = { r = 0.72, g = 0.62, b = 1 } }, -- arcane lilac
		heating = { enabled = true, color = { r = 1, g = 0.45, b = 0.1 } }, -- embers
		fingers = { enabled = true, color = { r = 0.45, g = 0.8, b = 1 } }, -- ice
		learned = {}, -- other spells the addon saw by these buffs' names
		ignored = {}, -- ones it saw always on: a passive, not the proc
	},
	-- Blink's icon big in the middle of the screen each time it's ready again
	pulse = {
		enabled = true,
		size = 80,
		alpha = 90, -- %
		color = { r = 0.25, g = 0.78, b = 0.92 }, -- the shine behind it
		-- Which cooldowns pulse when they're back (only the ones you know)
		spells = { blink = true, evocation = true, iceBlock = true, coldSnap = true, presence = true,
			arcanePower = true, combustion = true },
	},
	-- Counterspell ready while your target casts
	kick = { enabled = true },
	-- Fire Vulnerability and Winter's Chill on your target, beside its nameplate
	debuffs = { enabled = true },
	range = {
		enabled = true,
		spell = "auto", -- auto (the last one you cast) | frostbolt | fireball | missiles
		lastSpell = nil,
		threat = true,
		threatPct = 90, -- warn from this % of the tank's threat, as the game's tooltip shows it
		onlyCombat = false,
		style = "text", -- text | icon | both
		anchor = "plate", -- plate | free
		plateSide = "top", -- top | bottom | left | right
		plateGap = 2,
		units = "yards", -- yards | meters
		display = "number", -- number | bracket
		font = "fredoka", -- fredoka | changa | game
		showState = false,
		farGlow = true, -- glowing in the last 5 yards of your reach
		textSize = 26,
		colors = {
			melee = { r = 1, g = 0.2, b = 0.2 },
			nova = { r = 1, g = 0.82, b = 0 },
			ranged = { r = 0.3, g = 1, b = 0.3 },
			far = { r = 0.45, g = 0.8, b = 1 },
			out = { r = 0.6, g = 0.6, b = 0.6 },
		},
	},
	minimapButton = { hide = false, angle = 200 },
	positions = {},
}

local function Fill(saved, default)
	for k, v in pairs(default) do
		if saved[k] == nil then
			saved[k] = type(v) == "table" and Fill({}, v) or v
		elseif type(v) == "table" and type(saved[k]) == "table" then
			Fill(saved[k], v)
		end
	end
	return saved
end

-- Every ...God addon loads on every character: with another class this one keeps quiet (a vendor
-- would hear each of them say the same), unless you typed one of its commands
function ns.Print(msg)
	if not (ns.inCommand or ns.IsMage()) then return end
	print(L.PREFIX .. msg)
end

-- Forever hides some values from addons during combat
-- Fonts as shared font objects, one per file, size and outline, applied with SetFontObject.
-- Each text loading the font file itself (SetFont on the FontString) left some texts undrawn in
-- Forever: FarmGod's tabs, 23 Nov 2026, had their text, shown, at full alpha and with a width,
-- and nothing on screen. The game's font goes in first, so a font that can't load still shows
local fontObjects, fontCount = {}, 0
function ns.UseFont(fontString, file, size, flags)
	local gameFont = GameFontNormal:GetFont()
	file, flags = file or gameFont, flags or ""
	local key = file .. "|" .. size .. "|" .. flags
	local font = fontObjects[key]
	if not font then
		fontCount = fontCount + 1
		font = CreateFont("MageGodFont" .. fontCount)
		font:SetFont(gameFont, size, flags)
		font:SetFont(file, size, flags)
		fontObjects[key] = font
	end
	-- The font object brings its own colour and shadow: the text keeps the ones it had
	local r, g, b, a = fontString:GetTextColor()
	local sx, sy = fontString:GetShadowOffset()
	local sr, sg, sb, sa = fontString:GetShadowColor()
	fontString:SetFontObject(font)
	if r then fontString:SetTextColor(r, g, b, a) end
	if sx then fontString:SetShadowOffset(sx, sy) end
	if sr then fontString:SetShadowColor(sr, sg, sb, sa) end
end

function ns.IsSecret(value)
	return issecretvalue and issecretvalue(value) or false
end

function ns.IsMage()
	return select(2, UnitClass("player")) == "MAGE"
end

function ns.SpellName(id)
	if C_Spell and C_Spell.GetSpellName then return C_Spell.GetSpellName(id) end
	return (GetSpellInfo(id))
end

function ns.SpellIcon(id)
	if C_Spell and C_Spell.GetSpellTexture then return C_Spell.GetSpellTexture(id) end
	return GetSpellTexture(id)
end

-- Do you know any of these ranks? Forever may give a spell other ids: then the spellbook
-- answers for its name
function ns.Knows(ids)
	for _, id in ipairs(ids) do
		local known
		if IsPlayerSpell then known = IsPlayerSpell(id) elseif IsSpellKnown then known = IsSpellKnown(id) end
		if known and not ns.IsSecret(known) then return true end
	end
	local name = ns.SpellName(ids[1])
	if name and C_Spell and C_Spell.GetSpellInfo then
		local info = C_Spell.GetSpellInfo(name)
		return type(info) == "table" and not ns.IsSecret(info)
	end
	return false
end

-- The addon's round font over the game's one, in case it can't load (a new file needs the
-- game restarted)
ns.FONTS = {
	fredoka = "Interface\\AddOns\\MageGod\\media\\FredokaOne-Regular.ttf",
	changa = "Interface\\AddOns\\MageGod\\media\\Changa-Bold.ttf",
}
function ns.FancyFont(fontString, size, flags)
	ns.UseFont(fontString, ns.FONTS[ns.db.range.font], size, flags)
end

-- The thin letters of the reminders and the bars: the game's narrow Arial, over its usual font in
-- case it isn't there
local THIN_FONT = "Fonts\\ARIALN.TTF"
function ns.ThinFont(fontString, size)
	fontString:SetFont(GameFontNormal:GetFont(), size, "")
	fontString:SetFont(THIN_FONT, size, "")
end

-- One pixel of the screen in a frame's own units: an edge one UI unit wide comes out blurry, or
-- not at all, depending on your UI scale
function ns.OnePixel(frame)
	if not (PixelUtil and PixelUtil.GetPixelToUIUnitFactor) then return 1 end
	local scale = frame:GetEffectiveScale()
	if ns.IsSecret(scale) or not scale or scale <= 0 then return 1 end
	return PixelUtil.GetPixelToUIUnitFactor() / scale
end

-- Each module adds the function that redraws it; the options call them all
ns.refreshers = {}
function ns.RefreshAll()
	for _, refresh in ipairs(ns.refreshers) do
		refresh()
	end
end

-- Displays the player can drag around while they are unlocked
ns.movers = {}
ns.unlocked = false

function ns.PlaceFrame(frame)
	local p = ns.db.positions[frame.moverKey]
	-- Some displays sit next to something of the game's until you move them
	if not p and frame.placeDefault and frame:placeDefault() then return end
	p = p or frame.defaultPoint
	frame:ClearAllPoints()
	frame:SetPoint(p[1], UIParent, p[2], p[3], p[4])
end

-- While unlocked each display gets a box on top of it, big enough to grab
local function SizeHandle(frame)
	local w, h = frame:GetWidth() or 0, frame:GetHeight() or 0
	if ns.IsSecret(w) or ns.IsSecret(h) then w, h = 0, 0 end
	frame.mover:SetSize(max(w + 16, 140), max(h + 16, 44))
end

function ns.Movable(frame, key, defaultPoint, label)
	frame.moverKey = key
	frame.defaultPoint = defaultPoint
	frame:SetMovable(true)
	frame:SetClampedToScreen(true)
	local handle = CreateFrame("Frame", nil, frame)
	handle:SetPoint("CENTER")
	handle:SetFrameLevel(frame:GetFrameLevel() + 20)
	handle:EnableMouse(true)
	handle:RegisterForDrag("LeftButton")
	handle:SetScript("OnDragStart", function()
		if not InCombatLockdown() then frame:StartMoving() end
	end)
	handle:SetScript("OnDragStop", function()
		frame:StopMovingOrSizing()
		local point, _, relPoint, x, y = frame:GetPoint()
		if x and not ns.IsSecret(x) then
			ns.db.positions[key] = { point, relPoint, x, y }
		end
	end)
	local box = handle:CreateTexture(nil, "BACKGROUND")
	box:SetAllPoints()
	box:SetColorTexture(0.25, 0.78, 0.92, 0.35)
	local name = handle:CreateFontString(nil, "OVERLAY", "GameFontNormal")
	name:SetPoint("CENTER")
	name:SetText(label)
	handle:Hide()
	frame.mover = handle
	ns.movers[key] = frame
	ns.PlaceFrame(frame)
end

function ns.SetUnlocked(on)
	if on and not ns.IsMage() then
		ns.Print(L.OTHER_CLASS)
		return
	end
	if InCombatLockdown() then
		ns.Print(L.NOT_IN_COMBAT)
		return
	end
	ns.unlocked = on
	if not on then
		for _, frame in pairs(ns.movers) do ns.PlaceFrame(frame) end
	end
	ns.RefreshAll() -- while unlocked the displays show a sample, so the boxes fit them
	for _, frame in pairs(ns.movers) do
		SizeHandle(frame)
		frame.mover:SetShown(on)
	end
	ns.Print(on and L.UNLOCKED or L.LOCKED)
end

-- Slash command words: each module adds its own
ns.commands = {}

local function Help()
	for _, line in ipairs(L.HELP) do
		print(line)
	end
end

ns.commands.unlock = function() ns.SetUnlocked(true) end
ns.commands.desbloquear = ns.commands.unlock
ns.commands.lock = function() ns.SetUnlocked(false) end
ns.commands.bloquear = ns.commands.lock
ns.commands.help = Help
ns.commands.ayuda = Help

SLASH_MAGEGOD1 = "/magegod"
SLASH_MAGEGOD2 = "/mago"
SlashCmdList.MAGEGOD = function(msg)
	local word = strlower(strtrim(msg or ""))
	if word == "" then
		if ns.ToggleOptions then ns.ToggleOptions() end
		return
	end
	local command = ns.commands[word]
	if command then
		ns.inCommand = true
		local ok, err = pcall(command, word)
		ns.inCommand = false
		if not ok then error(err, 0) end
	else
		Help()
	end
end

-- Settings saved by an older version, brought up to date
function ns.MigrateSettings(saved, fresh)
	-- 1.0.0 saved its lightning at 100% for everyone: smaller now, unless you had made it another size
	if not fresh and (saved.version or 1) < 2 and saved.missiles.size == 100 then
		saved.missiles.size = defaults.missiles.size
	end
	saved.version = 2
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", function(self, event, name)
	if name ~= addonName then return end
	local fresh = MageGodDB == nil
	MageGodDB = Fill(MageGodDB or {}, defaults)
	ns.db = MageGodDB
	ns.MigrateSettings(MageGodDB, fresh)
	self:UnregisterEvent("ADDON_LOADED")
end)
