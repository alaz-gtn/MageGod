local _, ns = ...
local L = ns.L

-- The mage's other procs, one for each school, drawn around you (Missile Barrage has its own
-- lightning, in Missiles.lua):
-- - Clearcasting (Arcane Concentration, Arcane): your next damage spell costs no mana, 15 sec. A
--   circle of arcane light on the ground at your feet: it comes down onto you, then turns slowly
-- - Heating Up (Fire, with Pyroblast): each charge takes 25% off your next Pyroblast's cast, 20 sec.
--   Embers rising on both sides of you
-- - Fingers of Frost (Frost): your next 2 spells treat the target as Frozen, 15 sec. A snowflake
--   turning by each of your hands
-- Each one is only watched with its talent: a build without it never sees it, not even its sample.
-- Forever keeps your buffs from addons in combat, so the game shows them itself, as the lightning
-- does: an aura container watches each proc's buff, the drawing goes inside its button, and the
-- game plays the animations it's given: the burst once as the buff comes, the calm ones over and
-- over while it's on. Nothing in there can be touched in combat; the addon only builds it, and fits
-- it to your settings out of combat
local MEDIA = "Interface\\AddOns\\MageGod\\media\\"
local HEIGHT = 360
local SIDE_WIDTH = 110 -- room for a column of embers and its glow
local RING_Y = -150 -- Clearcasting's circle, on the ground at your feet
local EMBER_TIMER_Y = -200 -- Heating Up's seconds, under the circle
local FLAKE_Y = -30 -- the snowflakes, by your hands
local FLAKE_K = 0.55 -- and how far out, as a part of the space between the sides
local FROST_TIMER_Y = 120 -- Fingers of Frost's seconds, over your head
local RISE = { 1.5, 1.7 } -- one round of each column's embers while it lasts: apart, so they don't move as one
local FLARE = 0.5 -- one round of the embers as it comes: three, the last one fading out
local TURN = 2.4 -- the circle's dashes going an eighth of the way round
local SPIN = 0.3 -- and as it comes, fast: five rounds, the first coming in and the last fading out
local LAND = 0.25 -- the circle coming down onto you
local TWIRL = { 3.2, 3.6 } -- each snowflake going a sixth of the way round
local FLURRY = 0.28 -- and as it comes, fast: four rounds, the first flying in and the last fading out
local BREATH = 1.2 -- each half of a glow's breath
local TEST_SECONDS = 5
local DEFAULT_POINT = { "CENTER", "CENTER", 0, -20 } -- a little under the middle, around your character

-- spells: the buff, by Forever's numbers; talents: what gives it; seconds: how long the buff lasts,
-- for the sample's countdown
local EFFECTS = {
	{ key = "clearcasting", spells = { 12536 }, talents = { 11213 }, seconds = 15 }, -- Arcane Concentration
	{ key = "heating", spells = { 400625 }, talents = { 400624 }, seconds = 20 }, -- Heating Up
	{ key = "fingers", spells = { 400669, 400670 }, talents = { 400647 }, seconds = 15 }, -- Fingers of Frost
}
local byKey = {}
for _, e in ipairs(EFFECTS) do
	byKey[e.key] = e
	e.default = {}
	for _, id in ipairs(e.spells) do e.default[id] = true end
end
ns.PROC_EFFECTS = EFFECTS

local db
local place, spot -- where it all goes (the box you drag), and the samples you see while moving it or trying it
local pending -- something to do once the fight is over
local formatter -- how the game writes the seconds left: a plain number, rounded up
local arts = {} -- every drawing, to fit them to your settings

local function SpellName(id)
	local name = C_Spell and C_Spell.GetSpellName and C_Spell.GetSpellName(id)
	if name and not ns.IsSecret(name) then return name end
end

-- "Clearcasting", "Heating Up", "Fingers of Frost": the buff's name as the game writes it
function ns.ProcName(key)
	return SpellName(byKey[key].spells[1]) or key
end

-- The talent that gives it: by its number, or by its name among your talents if Forever gave it
-- another one
local function HasTalent(e)
	if ns.Knows(e.talents) then return true end
	local name = SpellName(e.talents[1])
	if not (name and GetNumTalentTabs and GetNumTalents and GetTalentInfo) then return false end
	for tab = 1, GetNumTalentTabs() or 0 do
		for i = 1, GetNumTalents(tab) or 0 do
			local talent, _, _, _, rank = GetTalentInfo(tab, i)
			if talent == name and type(rank) == "number" and not ns.IsSecret(rank) and rank > 0 then return true end
		end
	end
	return false
end
ns.HasProcTalent = function(key) return HasTalent(byKey[key]) end

local function Width()
	return 2 * db.gap + SIDE_WIDTH
end

-- A colour taken toward white: the core of a light is nearly white whatever its colour
local function Mix(c, toWhite)
	return c.r + (1 - c.r) * toWhite, c.g + (1 - c.g) * toWhite, c.b + (1 - c.b) * toWhite
end

-- Your colour, the space between the sides and the strength of each layer
local function Fit(art)
	local color = db[art.key].color
	for _, entry in ipairs(art.tinted) do
		pcall(entry[1].SetVertexColor, entry[1], Mix(color, entry[2]))
	end
	for _, entry in ipairs(art.placed) do
		local texture, side, y, k = entry[1], entry[2], entry[3], entry[4]
		pcall(texture.ClearAllPoints, texture)
		pcall(texture.SetPoint, texture, "CENTER", art.parent, "CENTER", side * db.gap * k, y)
	end
	pcall(art.calm.SetAlpha, art.calm, db.calm / 100)
	pcall(art.strike.SetAlpha, art.strike, db.alpha / 100)
	-- The seconds left: the range's font, outlined, in a lighter shade of the colour; the circle's a
	-- little smaller, inside it
	local size = art.key == "clearcasting" and max(floor(db.timerSize * 0.8), 10) or db.timerSize
	pcall(ns.UseFont, art.timer, ns.FONTS and ns.FONTS[ns.db.range.font], size, "OUTLINE")
	pcall(art.timer.SetTextColor, art.timer, Mix(color, 0.55))
	pcall(art.timer.SetShown, art.timer, db.timer and not art.noTimer)
end

-- 15, 14 ... 1: whole seconds rounded up, as a countdown goes. Without it the game writes "15 s"
local function Formatter()
	if formatter == nil then
		formatter = false
		local rounding = Enum and Enum.NumericRuleFormatRounding
		if rounding and C_StringUtil and C_StringUtil.CreateNumericRuleFormatter then
			local ok, made = pcall(C_StringUtil.CreateNumericRuleFormatter)
			if ok and made and pcall(made.SetBreakpoints, made, {
				{ threshold = 0, format = "" },
				{ threshold = 0.000001, format = "%d", step = 1, rounding = rounding.Up },
			}) then
				formatter = made
			end
		end
	end
	return formatter or nil
end

-- Drawing pieces. The textures rest invisible and only a playing animation shows them, so if the
-- game doesn't play them nothing shows, not a still picture. side: -1 left, 1 right, 0 the middle;
-- k: how far out, as a part of the space between the sides
local function Tex(art, layer, file, drawLayer, sublevel, side, y, w, h, toWhite, k)
	local t = layer:CreateTexture(nil, drawLayer, nil, sublevel)
	t:SetTexture(MEDIA .. file)
	t:SetBlendMode("ADD")
	t:SetSize(w, h)
	t:SetAlpha(0)
	art.tinted[#art.tinted + 1] = { t, toWhite }
	art.placed[#art.placed + 1] = { t, side, y, k or 1 }
	return t
end

-- Animations go to two lists: shown (they loop while the buff is on) and assigned (once, as it comes)
local function Group(art, list, loop)
	local group = art.parent:CreateAnimationGroup()
	if loop then group:SetLooping("REPEAT") end
	list[#list + 1] = group
	return group
end

local function Fade(group, target, from, to, order, seconds)
	local a = group:CreateAnimation("Alpha")
	a:SetTarget(target)
	a:SetFromAlpha(from)
	a:SetToAlpha(to)
	a:SetOrder(order)
	a:SetDuration(seconds)
end

local function Grow(group, target, from, to, order, seconds)
	local a = group:CreateAnimation("Scale")
	a:SetTarget(target)
	a:SetOrigin("CENTER", 0, 0)
	a:SetOrder(order)
	a:SetDuration(seconds)
	if a.SetScaleFrom then
		a:SetScaleFrom(from, from)
		a:SetScaleTo(to, to)
	else
		a:SetScale(to / from, to / from)
	end
end

-- The sixteen pictures of a sheet in turn
local function Flip(group, target, order, seconds)
	local a = group:CreateAnimation("FlipBook")
	a:SetTarget(target)
	a:SetOrder(order)
	a:SetDuration(seconds)
	a:SetFlipBookRows(4)
	a:SetFlipBookColumns(4)
	a:SetFlipBookFrames(16)
	a:SetFlipBookFrameWidth(0)
	a:SetFlipBookFrameHeight(0)
end

-- Clearcasting: a circle of arcane light on the ground at your feet
local function Circle(art)
	local function Ring(layer)
		return Tex(art, layer, "proc_spot", "BACKGROUND", 0, 0, RING_Y, 280, 110, 0),
			Tex(art, layer, "ring_base", "ARTWORK", 0, 0, RING_Y, 256, 128, 0.3),
			Tex(art, layer, "ring_glow", "ARTWORK", 1, 0, RING_Y, 256, 128, 0),
			Tex(art, layer, "ring_core", "ARTWORK", 2, 0, RING_Y, 256, 128, 0.6)
	end
	-- While it lasts: the dashes going slowly round, the inner circle still, its glow breathing
	local glow, base, dashGlow, dashCore = Ring(art.calm)
	local turn = Group(art, art.shown, true)
	for _, dash in ipairs({ dashGlow, dashCore }) do
		Flip(turn, dash, 1, TURN)
		Fade(turn, dash, 1, 1, 1, TURN)
	end
	Fade(turn, base, 1, 1, 1, TURN)
	local breath = Group(art, art.shown, true)
	Fade(breath, glow, 0.3, 0.75, 1, BREATH)
	Fade(breath, glow, 0.75, 0.3, 2, BREATH)
	-- As it comes: the circle comes down onto you from big, its dashes spinning fast, a flash as it
	-- lands, and then it fades into the calm
	local landGlow, landBase, spinGlow, spinCore = Ring(art.strike)
	local flash = Tex(art, art.strike, "proc_spot", "OVERLAY", 0, 0, RING_Y, 320, 130, 0.35)
	local land = Group(art, art.assigned)
	Grow(land, landBase, 2.2, 1, 1, LAND)
	Fade(land, landBase, 0, 1, 1, LAND)
	Fade(land, landBase, 1, 1, 2, 0.7)
	Fade(land, landBase, 1, 0, 3, 0.5)
	local spin = Group(art, art.assigned)
	for order = 1, 5 do
		for _, dash in ipairs({ spinGlow, spinCore }) do
			Flip(spin, dash, order, SPIN)
			Fade(spin, dash, order == 1 and 0 or 1, order < 5 and 1 or 0, order, SPIN)
			if order == 1 then Grow(spin, dash, 2.2, 1, 1, SPIN) end
		end
	end
	local glows = Group(art, art.assigned)
	Fade(glows, landGlow, 0, 0.9, 1, LAND)
	Fade(glows, landGlow, 0.9, 0.9, 2, 0.7)
	Fade(glows, landGlow, 0.9, 0, 3, 0.5)
	local flashes = Group(art, art.assigned)
	Fade(flashes, flash, 0, 0, 1, LAND) -- waits for the circle to land
	Fade(flashes, flash, 0, 1, 2, 0.07)
	Grow(flashes, flash, 0.5, 1, 2, 0.07)
	Fade(flashes, flash, 1, 0, 3, 0.45)
	Grow(flashes, flash, 1, 1.6, 3, 0.45)
	-- The seconds it has left, in the middle of the circle
	art.timer = art.parent:CreateFontString(nil, "OVERLAY")
	art.timer:SetPoint("CENTER", art.parent, "CENTER", 0, RING_Y)
end

-- Heating Up: a column of embers rising on each side of you
local function Embers(art)
	local function Column(layer, side)
		return Tex(art, layer, "proc_aura", "BACKGROUND", 0, side, 0, 80, 280, 0),
			Tex(art, layer, "ember_glow", "ARTWORK", 0, side, 0, 66, 264, 0),
			Tex(art, layer, "ember_core", "ARTWORK", 1, side, 0, 66, 264, 0.6)
	end
	-- While it lasts: the embers floating up and their glow breathing slowly
	local breath = Group(art, art.shown, true)
	for i, side in ipairs({ -1, 1 }) do
		local glow, emberGlow, emberCore = Column(art.calm, side)
		local rise = Group(art, art.shown, true)
		for _, ember in ipairs({ emberGlow, emberCore }) do
			Flip(rise, ember, 1, RISE[i])
			Fade(rise, ember, 1, 1, 1, RISE[i]) -- what shows it
		end
		Fade(breath, glow, 0.3, 0.7, 1, BREATH)
		Fade(breath, glow, 0.7, 0.3, 2, BREATH)
	end
	-- As it comes: a flash, the embers at full and faster for over a second, and then they fade into
	-- the calm
	local flares, glows, flashes = Group(art, art.assigned), Group(art, art.assigned), Group(art, art.assigned)
	for _, side in ipairs({ -1, 1 }) do
		local glow, emberGlow, emberCore = Column(art.strike, side)
		local flash = Tex(art, art.strike, "proc_aura", "OVERLAY", 0, side, 0, 110, 340, 0.35)
		for order = 1, 3 do
			for _, ember in ipairs({ emberGlow, emberCore }) do
				Flip(flares, ember, order, FLARE)
				Fade(flares, ember, 1, order < 3 and 1 or 0, order, FLARE)
			end
		end
		Fade(glows, glow, 0, 0.9, 1, 0.1)
		Fade(glows, glow, 0.9, 0.9, 2, 2 * FLARE - 0.1)
		Fade(glows, glow, 0.9, 0, 3, FLARE)
		Fade(flashes, flash, 0, 1, 1, 0.07)
		Grow(flashes, flash, 0.5, 1, 1, 0.07)
		Fade(flashes, flash, 1, 0, 2, 0.45)
		Grow(flashes, flash, 1, 1.5, 2, 0.45)
	end
	-- The seconds it has left, under Clearcasting's circle
	art.timer = art.parent:CreateFontString(nil, "OVERLAY")
	art.timer:SetPoint("TOP", art.parent, "CENTER", 0, EMBER_TIMER_Y)
end

-- Fingers of Frost: a snowflake turning by each of your hands
local function Frost(art)
	local function Flakes(layer)
		local list = {}
		for _, side in ipairs({ -1, 1 }) do
			list[#list + 1] = { side = side,
				Tex(art, layer, "proc_spot", "BACKGROUND", 0, side, FLAKE_Y, 120, 120, 0, FLAKE_K),
				Tex(art, layer, "frost_glow", "ARTWORK", 0, side, FLAKE_Y, 96, 96, 0, FLAKE_K),
				Tex(art, layer, "frost_core", "ARTWORK", 1, side, FLAKE_Y, 96, 96, 0.65, FLAKE_K) }
		end
		return list
	end
	-- While it lasts: each snowflake turning slowly, its glow breathing
	local breath = Group(art, art.shown, true)
	for i, flake in ipairs(Flakes(art.calm)) do
		local turn = Group(art, art.shown, true)
		for _, part in ipairs({ flake[2], flake[3] }) do
			Flip(turn, part, 1, TWIRL[i])
			Fade(turn, part, 1, 1, 1, TWIRL[i])
		end
		Fade(breath, flake[1], 0.3, 0.75, 1, BREATH)
		Fade(breath, flake[1], 0.75, 0.3, 2, BREATH)
	end
	-- As it comes: the snowflakes fly in from big, spinning fast, a flash as they settle, and then
	-- they fade into the calm
	local spin, glows, flashes = Group(art, art.assigned), Group(art, art.assigned), Group(art, art.assigned)
	for _, flake in ipairs(Flakes(art.strike)) do
		local flash = Tex(art, art.strike, "proc_spot", "OVERLAY", 0, flake.side, FLAKE_Y, 160, 160, 0.35, FLAKE_K)
		for order = 1, 4 do
			for _, part in ipairs({ flake[2], flake[3] }) do
				Flip(spin, part, order, FLURRY)
				Fade(spin, part, order == 1 and 0 or 1, order < 4 and 1 or 0, order, FLURRY)
				if order == 1 then Grow(spin, part, 2.4, 1, 1, FLURRY) end
			end
		end
		Fade(glows, flake[1], 0, 0.9, 1, FLURRY)
		Fade(glows, flake[1], 0.9, 0.9, 2, 2 * FLURRY)
		Fade(glows, flake[1], 0.9, 0, 3, FLURRY)
		Fade(flashes, flash, 0, 0, 1, FLURRY) -- waits for the snowflakes to settle
		Fade(flashes, flash, 0, 1, 2, 0.07)
		Grow(flashes, flash, 0.5, 1, 2, 0.07)
		Fade(flashes, flash, 1, 0, 3, 0.45)
		Grow(flashes, flash, 1, 1.5, 3, 0.45)
	end
	-- The seconds it has left, over your head
	art.timer = art.parent:CreateFontString(nil, "OVERLAY")
	art.timer:SetPoint("BOTTOM", art.parent, "CENTER", 0, FROST_TIMER_Y)
end

local DRAW = { clearcasting = Circle, heating = Embers, fingers = Frost }

-- A proc's drawing inside parent, centred on it, in two layers: the strike and the calm
local function Draw(parent, key)
	local art = { parent = parent, key = key, shown = {}, assigned = {}, tinted = {}, placed = {} }
	for _, layer in ipairs({ "calm", "strike" }) do
		local frame = CreateFrame("Frame", nil, parent)
		frame:SetAllPoints(parent)
		art[layer] = frame
	end
	DRAW[key](art)
	arts[#arts + 1] = art
	if db then Fit(art) end
	return art
end

-- The container's button: the drawing goes in, and its animations to the game
local function Dress(button, box, e)
	button:SetAllPoints(box)
	button:EnableMouse(false)
	local art = Draw(button, e.key)
	art.live = true
	art.ready = pcall(function()
		for _, group in ipairs(art.shown) do button:AddAuraShownAnimation(group) end
		for _, group in ipairs(art.assigned) do button:AddAuraAssignedAnimation(group) end
	end)
	-- The time left is secret in combat: the game fills the text in itself
	local options = Formatter() and { textFormatter = Formatter() }
	if not (pcall(button.SetDurationText, button, art.timer, options)
		or options and pcall(button.SetDurationText, button, art.timer)) then
		art.noTimer = true
		art.timer:Hide()
	end
	e.dressed = art
end

local function Passive(id)
	if not (C_Spell and C_Spell.IsSpellPassive) then return false end
	local passive = C_Spell.IsSpellPassive(id)
	if ns.IsSecret(passive) then return false end
	return passive == true
end

-- The spells a proc watches: Forever's, and any other the addon saw by that name, less the ones it
-- saw always on (a passive, not the proc). None without its talent
local function WatchList(e)
	local spells, ids = {}, {}
	if not HasTalent(e) then return spells, "" end
	local function Add(id)
		if spells[id] or db.ignored[id] or Passive(id) then return end
		spells[id] = true
		ids[#ids + 1] = id
	end
	for _, id in ipairs(e.spells) do Add(id) end
	for id, key in pairs(db.learned) do
		if key == e.key then Add(id) end
	end
	table.sort(ids)
	return spells, table.concat(ids, ", ")
end

-- The samples: while you move the displays (the procs you have the talents for) and for a few
-- seconds when you try one
local function ShowSample(e, show)
	if show == e.sampleShown then return end
	e.sampleShown = show
	if show then e.sampleStart = GetTime() end
	e.sampleFrame:SetShown(show)
	for _, list in ipairs({ e.sample.shown, e.sample.assigned }) do
		for _, group in ipairs(list) do
			if show then group:Play() else group:Stop() end
		end
	end
end

function ns.UpdateProcsSample()
	if not spot then return end
	local any = false
	for _, e in ipairs(EFFECTS) do
		local show = (ns.unlocked and db[e.key].enabled and ns.IsMage() and HasTalent(e)) or GetTime() < (e.testUntil or 0)
		ShowSample(e, show and true or false)
		any = any or show
	end
	spot:SetShown(any and true or false)
end

-- Shows a proc's sample a moment (or all three), as you change how it looks
function ns.PeekProcs(key)
	for _, e in ipairs(EFFECTS) do
		if not key or key == e.key then e.testUntil = max(e.testUntil or 0, GetTime() + TEST_SECONDS) end
	end
	ns.UpdateProcsSample()
	C_Timer.After(TEST_SECONDS + 0.1, ns.UpdateProcsSample)
end

-- And its burst again, as if the buff had just come
function ns.TestProcs(key)
	for _, e in ipairs(EFFECTS) do
		if not key or key == e.key then
			if e.sampleShown then
				e.sampleStart = GetTime()
				for _, group in ipairs(e.sample.assigned) do
					group:Stop()
					group:Play()
				end
			end
			e.testUntil = GetTime() + TEST_SECONDS
		end
	end
	ns.UpdateProcsSample()
	C_Timer.After(TEST_SECONDS + 0.1, ns.UpdateProcsSample)
end

function ns.StyleProcs()
	if not place then return end
	local scale, width = db.size / 100, Width()
	local fight = InCombatLockdown()
	spot:SetScale(scale)
	spot:SetSize(width, HEIGHT)
	for _, art in ipairs(arts) do
		if art.live and fight then pending = true else Fit(art) end
	end
	-- What the game shows, and the box it hangs from, can't be touched in a fight
	if fight then
		pending = true
	else
		place:SetSize(width * scale, HEIGHT * scale)
		ns.PlaceFrame(place)
		if place.mover then place.mover:SetSize(width * scale + 16, HEIGHT * scale + 16) end
		for _, e in ipairs(EFFECTS) do
			if e.holder then
				e.holder:SetScale(scale)
				e.holder:SetSize(width, HEIGHT)
				e.holder:SetShown(db[e.key].enabled and true or false)
			end
		end
	end
	ns.UpdateProcsSample()
end

function ns.SetProcsSize(size)
	db.size = size
	ns.StyleProcs()
end

-- Where it is, from the middle of the screen. A place saved by dragging may hang from another
-- corner: then it's measured
local function Measure()
	local x, y = place:GetCenter()
	local cx, cy = UIParent:GetCenter()
	if not (x and cx) or ns.IsSecret(x) or ns.IsSecret(y) then return end
	return floor(x - cx + 0.5), floor(y - cy + 0.5)
end

function ns.ProcsOffset()
	local p = ns.db.positions.procs
	if p and p[1] == "CENTER" and p[2] == "CENTER" then return p[3], p[4] end
	if p and place then
		local x, y = Measure()
		if x then return x, y end
	end
	return DEFAULT_POINT[3], DEFAULT_POINT[4]
end

function ns.MoveProcs(x, y)
	ns.db.positions.procs = { "CENTER", "CENTER", x, y }
	ns.StyleProcs()
end

-- Built out of combat. A list that changes (a talent learnt or unlearnt, another number seen)
-- builds a new one; containers can't be thrown away, so the old one is switched off
local function Build(e)
	if InCombatLockdown() then
		pending = true
		return
	end
	if e.broken or not (ns.IsMage() and CustomAuraContainerAuraProcessingPolicy and C_UnitAuras) then return end
	local spells, list = WatchList(e)
	if list == (e.watching or "") then return end
	if e.container then
		pcall(e.container.SetEnabled, e.container, false)
		e.holder:Hide()
		e.holder, e.container, e.watching, e.dressed = nil, nil, nil, nil
	end
	if list == "" then return end
	local box = CreateFrame("Frame", nil, UIParent)
	box:SetSize(Width(), HEIGHT)
	box:SetFrameStrata("BACKGROUND")
	box:SetPoint("CENTER", place, "CENTER")
	local ok, aurasBox = pcall(CreateFrame, "AuraContainer", nil, box, "CustomAuraContainerTemplate")
	if not ok or not aurasBox then
		e.broken = true
		return
	end
	aurasBox:SetAllPoints(box)
	aurasBox:SetEnabled(false)
	aurasBox:SetAuraProcessingPolicy(CustomAuraContainerAuraProcessingPolicy.None)
	if not pcall(aurasBox.AddAuraSlot, aurasBox, "MageGodProc" .. e.key, "HELPFUL", {
		candidateFilters = { includeSpellIDs = spells },
		initializeFrame = function(button) Dress(button, box, e) end,
	}) then
		e.broken = true
		return
	end
	aurasBox:SetUnit("player")
	aurasBox:SetEnabled(true)
	e.holder, e.container, e.watching = box, aurasBox, list
	ns.StyleProcs()
end

local function BuildAll()
	for _, e in ipairs(EFFECTS) do Build(e) end
end

-- Out of combat the addon can read your buffs: one of these procs with another number joins its
-- list, and one that never ends (a passive) leaves it
local function Learn()
	if C_Secrets and C_Secrets.ShouldAurasBeSecret and C_Secrets.ShouldAurasBeSecret() then return end
	if not (C_UnitAuras and C_UnitAuras.GetAuraDataByIndex) then return end
	local byName = {}
	for _, e in ipairs(EFFECTS) do
		local name = SpellName(e.spells[1])
		if name then byName[name] = e end
	end
	local changed = {}
	for i = 1, 40 do
		local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
		if not aura or ns.IsSecret(aura) then break end
		local name, id, duration = aura.name, aura.spellId, aura.duration
		local e = not (ns.IsSecret(name) or ns.IsSecret(id) or ns.IsSecret(duration)) and byName[name]
		if e and type(id) == "number" then
			if type(duration) == "number" and duration > 0 then
				if db.ignored[id] then
					db.ignored[id] = nil
					changed[e] = true
				end
				if not e.default[id] and db.learned[id] ~= e.key then
					db.learned[id] = e.key
					changed[e] = true
				end
			elseif not db.ignored[id] then
				db.ignored[id] = true
				changed[e] = true
			end
		end
	end
	for e in pairs(changed) do Build(e) end
end

-- /magegod procs: shows them and says what each watches
local function Report()
	ns.TestProcs()
	if not ns.IsMage() then return end
	for _, e in ipairs(EFFECTS) do
		local name = ns.ProcName(e.key)
		if not HasTalent(e) then
			ns.Print(format(L.PROCS_NO_TALENT, name, SpellName(e.talents[1]) or "?"))
		elseif not e.container then
			ns.Print(format(L.PROCS_NOT_READY, name))
		elseif e.dressed and not e.dressed.ready then
			ns.Print(format(L.PROCS_REFUSED, name))
		else
			ns.Print(format(L.PROCS_WATCHING, name, e.watching))
		end
	end
end
ns.commands.procs = Report

-- For the tests
function ns.ProcsState(key)
	local e = byKey[key]
	return { holder = e.holder, container = e.container, dressed = e.dressed, sample = e.sample,
		sampleFrame = e.sampleFrame, sampleShown = e.sampleShown, watching = e.watching, place = place, spot = spot }
end

local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(self, event)
	if event == "PLAYER_LOGIN" then
		self:UnregisterEvent("PLAYER_LOGIN") -- built once
		db = ns.db.procs
		place = CreateFrame("Frame", "MageGodProcs", UIParent)
		place:SetSize(Width(), HEIGHT)
		spot = CreateFrame("Frame", nil, place)
		spot:SetPoint("CENTER")
		spot:SetFrameStrata("BACKGROUND")
		spot:Hide()
		for _, e in ipairs(EFFECTS) do
			e.sampleFrame = CreateFrame("Frame", nil, spot)
			e.sampleFrame:SetAllPoints(spot)
			e.sampleFrame:Hide()
			e.sample = Draw(e.sampleFrame, e.key)
		end
		-- Their countdowns: as the real ones would go, from the moment each sample shows
		spot:SetScript("OnUpdate", function()
			local now = GetTime()
			for _, e in ipairs(EFFECTS) do
				if e.sampleShown then
					e.sample.timer:SetText(format("%d", max(ceil(e.seconds - (now - e.sampleStart)), 1)))
				end
			end
		end)
		ns.Movable(place, "procs", DEFAULT_POINT, L.PROCS_NAME)
		-- Dragged: kept as an offset from the middle, as the options set it
		place.mover:HookScript("OnDragStop", function()
			local x, y = Measure()
			if x then ns.MoveProcs(x, y) end
			if ns.RefreshOptionsPage then ns.RefreshOptionsPage("procs") end
		end)
		table.insert(ns.refreshers, ns.StyleProcs)
		self:RegisterUnitEvent("UNIT_AURA", "player")
		self:RegisterEvent("PLAYER_REGEN_ENABLED")
		self:RegisterEvent("SPELLS_CHANGED")
		-- Talents learnt or unlearnt. An event the game doesn't have would stop the rest of the file
		pcall(self.RegisterEvent, self, "CHARACTER_POINTS_CHANGED")
		pcall(self.RegisterEvent, self, "TRAIT_CONFIG_UPDATED")
		Learn()
		BuildAll()
		ns.StyleProcs()
	elseif event == "UNIT_AURA" then
		Learn()
	elseif event == "PLAYER_REGEN_ENABLED" then
		Learn()
		if pending then
			pending = false
			BuildAll()
			ns.StyleProcs()
		end
	else
		-- A talent changed: each proc follows it (out of combat; in a fight, once it's over)
		BuildAll()
		ns.UpdateProcsSample()
	end
end)
