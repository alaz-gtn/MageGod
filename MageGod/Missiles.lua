local _, ns = ...
local L = ns.L

-- Purple lightning on both sides of you while Missile Barrage is up: your next Arcane Missiles
-- are free and fire faster. A big strike as it comes, then calm lightning, faint, while it lasts.
-- Forever keeps your buffs from addons in combat, so the game shows it itself, as ForeverAuras
-- does: an aura container watches your buffs for that one alone, the lightning is drawn inside its
-- button, and the game plays the animations it's given: the strike once as the buff comes, the
-- calm ones over and over while it's on. Nothing in there can be touched in combat; the addon only
-- builds it, and fits it to your settings out of combat
local BARRAGE = { 400589, 401736, 467409 } -- Missile Barrage in Forever's spells; 400588 is the passive that procs it
local NAME_SPELL = 400589
local MEDIA = "Interface\\AddOns\\MageGod\\media\\"
local HEIGHT = 360
local SIDE_WIDTH = 200 -- room for a column and its glow
local STRIKE = 0.62 -- one round of the strike's crackle: it plays three, the last one fading out
local CALM_SPEEDS = { 1.1, 1.3 } -- one round of each column's calm crackle: slower, and apart
local BREATH = 1.2 -- each half of the calm glow's breath
local TEST_SECONDS = 5
local BUFF_SECONDS = 15 -- how long Missile Barrage lasts: the sample counts it down
local TIMER_Y = -146 -- the seconds left, just under the lightning
local DEFAULT_POINT = { "CENTER", "CENTER", 0, -20 } -- a little under the middle, around your character
ns.BARRAGE_SPELL = NAME_SPELL

local DEFAULT = {}
for _, id in ipairs(BARRAGE) do DEFAULT[id] = true end

local db
local holder, container -- what the game shows
local watching -- the spells it watches, as text: another list means building it again
local broken -- the game refused the container: it isn't tried again until you log in
local pending -- something to do once the fight is over
local dressed -- the lightning in the container's button
local arts = {} -- every drawing, to fit them to your settings
local place -- where it all goes, the box you drag; it keeps its scale, so its offsets are plain
local spot, sample -- the sample you see while moving the displays or trying it
local testUntil = 0
local sampleStart = 0 -- GetTime() when the sample's buff "came", for its countdown
local formatter -- how the game writes the seconds left: a plain number, rounded up

local function Width()
	return 2 * db.gap + SIDE_WIDTH
end

-- A colour taken toward white: the core of a bolt is nearly white whatever its colour
local function Mix(c, toWhite)
	return c.r + (1 - c.r) * toWhite, c.g + (1 - c.g) * toWhite, c.b + (1 - c.b) * toWhite
end

-- Your colour, the space between the sides and the strength of each layer
local function Fit(art)
	for _, entry in ipairs(art.tinted) do
		pcall(entry[1].SetVertexColor, entry[1], Mix(db.color, entry[2]))
	end
	for _, entry in ipairs(art.placed) do
		local texture, side = entry[1], entry[2]
		pcall(texture.ClearAllPoints, texture)
		pcall(texture.SetPoint, texture, "CENTER", art.parent, "CENTER", side * db.gap, 0)
	end
	pcall(art.calm.SetAlpha, art.calm, db.calm / 100)
	pcall(art.strike.SetAlpha, art.strike, db.alpha / 100)
	-- The seconds left: the addon's round font, outlined, in a lighter shade of your colour
	pcall(ns.FancyFont, art.timer, db.timerSize, "OUTLINE")
	pcall(art.timer.SetTextColor, art.timer, Mix(db.color, 0.55))
	pcall(art.timer.SetShown, art.timer, db.timer)
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

-- The lightning, inside parent and centred on it, in two layers: the strike and the calm. Their
-- animations go to two lists: shown (they loop while the buff is on) and assigned (once, as it
-- comes). The textures rest invisible and only a playing animation shows them, so if the game
-- doesn't play them nothing shows, not a still picture
local function Draw(parent)
	local art = { parent = parent, shown = {}, assigned = {}, tinted = {}, placed = {} }
	for _, key in ipairs({ "calm", "strike" }) do
		local layer = CreateFrame("Frame", nil, parent)
		layer:SetAllPoints(parent)
		art[key] = layer
	end
	local function Tex(layer, file, drawLayer, sublevel, side, w, h, toWhite)
		local t = layer:CreateTexture(nil, drawLayer, nil, sublevel)
		t:SetTexture(MEDIA .. file)
		t:SetBlendMode("ADD")
		t:SetSize(w, h)
		t:SetAlpha(0)
		art.tinted[#art.tinted + 1] = { t, toWhite }
		art.placed[#art.placed + 1] = { t, side }
		return t
	end
	local function Group(list, loop)
		local group = parent:CreateAnimationGroup()
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
	-- The eight pictures of the sheet in turn
	local function Flip(group, target, order, seconds)
		local a = group:CreateAnimation("FlipBook")
		a:SetTarget(target)
		a:SetOrder(order)
		a:SetDuration(seconds)
		a:SetFlipBookRows(2)
		a:SetFlipBookColumns(4)
		a:SetFlipBookFrames(8)
		a:SetFlipBookFrameWidth(0)
		a:SetFlipBookFrameHeight(0)
	end

	-- The calm, while the buff lasts: a slower crackle and a glow breathing slowly
	local breath = Group(art.shown, true)
	for i, side in ipairs({ -1, 1 }) do
		local glow = Tex(art.calm, "aura", "BACKGROUND", 0, side, 170, 320, 0)
		local boltGlow = Tex(art.calm, "bolts_glow", "ARTWORK", 0, side, 120, 280, 0)
		local boltCore = Tex(art.calm, "bolts_core", "ARTWORK", 1, side, 120, 280, 0.65)
		local crackle = Group(art.shown, true)
		for _, bolt in ipairs({ boltGlow, boltCore }) do
			Flip(crackle, bolt, 1, CALM_SPEEDS[i])
			Fade(crackle, bolt, 1, 1, 1, CALM_SPEEDS[i]) -- what shows it
		end
		Fade(breath, glow, 0.35, 0.8, 1, BREATH)
		Fade(breath, glow, 0.8, 0.35, 2, BREATH)
	end

	-- The strike, once as the buff comes: a flash, the lightning at full for over a second, and then
	-- it fades into the calm
	local bolts = Group(art.assigned)
	local glows = Group(art.assigned)
	local flashes = Group(art.assigned)
	for _, side in ipairs({ -1, 1 }) do
		local glow = Tex(art.strike, "aura", "BACKGROUND", 0, side, 170, 320, 0)
		local boltGlow = Tex(art.strike, "bolts_glow", "ARTWORK", 0, side, 120, 280, 0)
		local boltCore = Tex(art.strike, "bolts_core", "ARTWORK", 1, side, 120, 280, 0.65)
		local flash = Tex(art.strike, "aura", "OVERLAY", 0, side, 200, 360, 0.35)
		for order = 1, 3 do
			for _, bolt in ipairs({ boltGlow, boltCore }) do
				Flip(bolts, bolt, order, STRIKE)
				Fade(bolts, bolt, 1, order < 3 and 1 or 0, order, STRIKE)
			end
		end
		Fade(glows, glow, 0, 0.9, 1, 0.1)
		Fade(glows, glow, 0.9, 0.9, 2, 2 * STRIKE - 0.1)
		Fade(glows, glow, 0.9, 0, 3, STRIKE)
		Fade(flashes, flash, 0, 1, 1, 0.07)
		Grow(flashes, flash, 0.5, 1, 1, 0.07)
		Fade(flashes, flash, 1, 0, 2, 0.45)
		Grow(flashes, flash, 1, 1.5, 2, 0.45)
	end

	-- The seconds the buff has left, centred under it: the game writes them in the real one
	art.timer = parent:CreateFontString(nil, "OVERLAY")
	art.timer:SetPoint("TOP", parent, "CENTER", 0, TIMER_Y)
	arts[#arts + 1] = art
	if db then Fit(art) end
	return art
end

-- The container's button: the lightning goes in, and its animations to the game
local function Dress(button, box)
	button:SetAllPoints(box)
	button:EnableMouse(false)
	local art = Draw(button)
	art.live = true
	art.ready = pcall(function()
		for _, group in ipairs(art.shown) do button:AddAuraShownAnimation(group) end
		for _, group in ipairs(art.assigned) do button:AddAuraAssignedAnimation(group) end
	end)
	-- The time left is secret in combat: the game fills the text in itself
	local options = Formatter() and { textFormatter = Formatter() }
	if not (pcall(button.SetDurationText, button, art.timer, options)
		or options and pcall(button.SetDurationText, button, art.timer)) then
		art.timer:Hide()
	end
	dressed = art
end

local function Passive(id)
	if not (C_Spell and C_Spell.IsSpellPassive) then return false end
	local passive = C_Spell.IsSpellPassive(id)
	if ns.IsSecret(passive) then return false end
	return passive == true
end

-- The spells to watch: Forever's Missile Barrage buffs and any other the addon saw by that name,
-- less the ones it saw always on (a passive, not the proc)
local function WatchList()
	local spells, ids = {}, {}
	local function Add(id)
		if spells[id] or db.ignored[id] or Passive(id) then return end
		spells[id] = true
		ids[#ids + 1] = id
	end
	for _, id in ipairs(BARRAGE) do Add(id) end
	for id in pairs(db.learned) do Add(id) end
	table.sort(ids)
	return spells, table.concat(ids, ", ")
end

-- The sample: while you move the displays (if it's on) and for a few seconds when you try it
function ns.UpdateMissilesSample()
	local show = (ns.unlocked and db.enabled and ns.IsMage()) or GetTime() < testUntil
	if show == spot:IsShown() then return end
	if show then sampleStart = GetTime() end
	spot:SetShown(show)
	for _, list in ipairs({ sample.shown, sample.assigned }) do
		for _, group in ipairs(list) do
			if show then group:Play() else group:Stop() end
		end
	end
end

-- Shows the sample for a while, as you change how it looks
function ns.PeekMissiles()
	testUntil = max(testUntil, GetTime() + TEST_SECONDS)
	ns.UpdateMissilesSample()
	C_Timer.After(TEST_SECONDS + 0.1, ns.UpdateMissilesSample)
end

-- And the strike again, as if the buff had just come
function ns.TestMissiles()
	if spot:IsShown() then
		sampleStart = GetTime()
		for _, group in ipairs(sample.assigned) do
			group:Stop()
			group:Play()
		end
	end
	testUntil = GetTime() + TEST_SECONDS
	ns.UpdateMissilesSample()
	C_Timer.After(TEST_SECONDS + 0.1, ns.UpdateMissilesSample)
end

function ns.StyleMissiles()
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
		if holder then
			holder:SetScale(scale)
			holder:SetSize(width, HEIGHT)
			holder:SetShown(db.enabled)
		end
	end
	ns.UpdateMissilesSample()
end

function ns.SetMissilesSize(size)
	db.size = size
	ns.StyleMissiles()
end

-- Where it is, from the middle of the screen. A place saved by dragging may hang from another
-- corner: then it's measured
local function Measure()
	local x, y = place:GetCenter()
	local cx, cy = UIParent:GetCenter()
	if not (x and cx) or ns.IsSecret(x) or ns.IsSecret(y) then return end
	return floor(x - cx + 0.5), floor(y - cy + 0.5)
end

function ns.MissilesOffset()
	local p = ns.db.positions.missiles
	if p and p[1] == "CENTER" and p[2] == "CENTER" then return p[3], p[4] end
	if p then
		local x, y = Measure()
		if x then return x, y end
	end
	return DEFAULT_POINT[3], DEFAULT_POINT[4]
end

function ns.MoveMissiles(x, y)
	ns.db.positions.missiles = { "CENTER", "CENTER", x, y }
	ns.StyleMissiles()
end

-- Built out of combat. A list that changes builds a new one; containers can't be thrown away, so
-- the old one is switched off
local function Build()
	if InCombatLockdown() then
		pending = true
		return
	end
	if broken or not (ns.IsMage() and CustomAuraContainerAuraProcessingPolicy and C_UnitAuras) then return end
	local spells, list = WatchList()
	if list == watching then return end
	if container then
		pcall(container.SetEnabled, container, false)
		holder:Hide()
		holder, container, watching, dressed = nil, nil, nil, nil
	end
	if list == "" then return end
	local box = CreateFrame("Frame", nil, UIParent)
	box:SetSize(Width(), HEIGHT)
	box:SetFrameStrata("BACKGROUND")
	box:SetPoint("CENTER", place, "CENTER")
	local ok, aurasBox = pcall(CreateFrame, "AuraContainer", nil, box, "CustomAuraContainerTemplate")
	if not ok or not aurasBox then
		broken = true
		return
	end
	aurasBox:SetAllPoints(box)
	aurasBox:SetEnabled(false)
	aurasBox:SetAuraProcessingPolicy(CustomAuraContainerAuraProcessingPolicy.None)
	if not pcall(aurasBox.AddAuraSlot, aurasBox, "MageGodBarrage", "HELPFUL", {
		candidateFilters = { includeSpellIDs = spells },
		initializeFrame = function(button) Dress(button, box) end,
	}) then
		broken = true
		return
	end
	aurasBox:SetUnit("player")
	aurasBox:SetEnabled(true)
	holder, container, watching = box, aurasBox, list
	ns.StyleMissiles()
end

-- Out of combat the addon can read your buffs: a Missile Barrage with another number joins the
-- list, and one that never ends (a passive) leaves it
local function Learn()
	if C_Secrets and C_Secrets.ShouldAurasBeSecret and C_Secrets.ShouldAurasBeSecret() then return end
	if not (C_UnitAuras and C_UnitAuras.GetAuraDataByIndex) then return end
	local name = ns.SpellName(NAME_SPELL)
	if not name or ns.IsSecret(name) then return end
	local changed = false
	for i = 1, 40 do
		local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
		if not aura or ns.IsSecret(aura) then break end
		local id, duration = aura.spellId, aura.duration
		if not (ns.IsSecret(aura.name) or ns.IsSecret(id) or ns.IsSecret(duration))
			and aura.name == name and type(id) == "number" then
			if type(duration) == "number" and duration > 0 then
				if db.ignored[id] then
					db.ignored[id] = nil
					changed = true
				end
				if not DEFAULT[id] and not db.learned[id] then
					db.learned[id] = true
					changed = true
				end
			elseif not db.ignored[id] then
				db.ignored[id] = true
				changed = true
			end
		end
	end
	if changed then Build() end
end

-- /magegod lightning: shows it and says what it watches
local function Report()
	ns.TestMissiles()
	if not ns.IsMage() then return end
	local name = ns.SpellName(NAME_SPELL) or "Missile Barrage"
	if not container then
		ns.Print(L.MISSILES_NOT_READY)
	elseif dressed and not dressed.ready then
		ns.Print(L.MISSILES_REFUSED)
	else
		ns.Print(format(L.MISSILES_WATCHING, name, watching))
	end
end
ns.commands.lightning = Report
ns.commands.rayos = Report

-- For the tests
function ns.MissilesState()
	return { holder = holder, container = container, place = place, spot = spot, sample = sample, dressed = dressed }
end

local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(self, event)
	if event == "PLAYER_LOGIN" then
		self:UnregisterEvent("PLAYER_LOGIN") -- built once
		db = ns.db.missiles
		place = CreateFrame("Frame", "MageGodMissiles", UIParent)
		place:SetSize(Width(), HEIGHT)
		spot = CreateFrame("Frame", nil, place)
		spot:SetPoint("CENTER")
		spot:SetFrameStrata("BACKGROUND")
		spot:Hide()
		sample = Draw(spot)
		-- Its countdown: as the real one would go, from the moment the sample shows
		spot:SetScript("OnUpdate", function()
			sample.timer:SetText(format("%d", max(ceil(BUFF_SECONDS - (GetTime() - sampleStart)), 1)))
		end)
		ns.Movable(place, "missiles", DEFAULT_POINT, L.MISSILES_NAME)
		-- Dragged: kept as an offset from the middle, as the options set it
		place.mover:HookScript("OnDragStop", function()
			local x, y = Measure()
			if x then ns.MoveMissiles(x, y) end
			if ns.RefreshOptionsPage then ns.RefreshOptionsPage("procs") end
		end)
		table.insert(ns.refreshers, ns.StyleMissiles)
		self:RegisterUnitEvent("UNIT_AURA", "player")
		self:RegisterEvent("PLAYER_REGEN_ENABLED")
		Learn()
		Build()
		ns.StyleMissiles()
	elseif event == "UNIT_AURA" then
		Learn()
	elseif event == "PLAYER_REGEN_ENABLED" then
		Learn()
		if pending then
			pending = false
			Build()
			ns.StyleMissiles()
		end
	end
end)
