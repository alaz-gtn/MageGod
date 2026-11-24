local _, ns = ...
local L = ns.L

-- The five-second rule. A spell that costs mana stops what your Spirit gives back for five
-- seconds, and each new one starts the five again; wands and free spells don't. After that your
-- mana comes back in ticks, every two seconds. The bar shows both: grey and emptying while you
-- wait, then blue, filling up to each tick
local WAIT, TICK = 5, 2
local BEAT = 0.3 -- how far off the two-second beat a tick may still come (the server's lag)
local MANA = Enum and Enum.PowerType and Enum.PowerType.Mana or 0
-- The MP5 label beside it: grey while you wait, green while your mana comes back
local LABEL_WAIT = { 0.75, 0.75, 0.75 }
local LABEL_REGEN = { 0.3, 1, 0.3 }
local ThinFont = ns.ThinFont

local bar
local waitEnds = 0 -- GetTime() when Spirit gives mana back again
local lastTick -- GetTime() of the last tick seen
local lastGain -- what it gave
local offBeat -- GetTime() of a gain off the beat: another one two seconds later moves the beat
local lastMana -- your mana, the last time the game let the addon read it
local inCombat = false
local fullCurve -- your mana as a share to 0 when it's full and 1 when not, for when it's hidden

local function Positive(v)
	if ns.IsSecret(v) then return true end
	return type(v) == "number" and v > 0
end

-- Whether a spell costs mana: the shots of a wand don't
local function CostsMana(spellID)
	if not (C_Spell and C_Spell.GetSpellPowerCost) then return false end
	local costs = C_Spell.GetSpellPowerCost(spellID)
	if ns.IsSecret(costs) then return true end
	if type(costs) ~= "table" then return false end
	for _, c in ipairs(costs) do
		if ns.IsSecret(c.type) or c.type == MANA then
			if Positive(c.cost) or Positive(c.costPerSec) then return true end
		end
	end
	return false
end

-- Your mana went up: a tick when it keeps the two-second beat. A potion, a gem or a drink comes
-- off it and doesn't move it, unless two gains in a row come two seconds apart
local function Gained(now, gain)
	if lastTick then
		if now - lastTick <= BEAT then
			-- Two gains in the same tick (your Spirit and a drink): one tick
			lastGain = (lastGain or 0) + gain
			return
		end
		local into = (now - lastTick) % TICK
		if into > BEAT and into < TICK - BEAT then
			if offBeat and abs(now - offBeat - TICK) <= BEAT then
				lastTick, lastGain, offBeat = now, gain, nil
			else
				offBeat = now
			end
			return
		end
	end
	lastTick, lastGain, offBeat = now, gain, nil
end

local function PowerChanged()
	local mana = UnitPower("player", MANA)
	if ns.IsSecret(mana) then
		lastMana = nil
		return
	end
	if lastMana and mana > lastMana then Gained(GetTime(), mana - lastMana) end
	lastMana = mana
end

local function OnePixel()
	return ns.OnePixel(bar)
end

function ns.StyleMana()
	local o = ns.db.mana
	bar:SetSize(o.width, o.height)
	local px = OnePixel()
	bar.edge:ClearAllPoints()
	bar.edge:SetPoint("TOPLEFT", -px, px)
	bar.edge:SetPoint("BOTTOMRIGHT", px, -px)
	local size = max(floor(o.height * 0.9), 10)
	ThinFont(bar.text, size)
	ThinFont(bar.label, size)
	-- The tag sits against the bar's left end, their black edges one line between them
	bar.tag:SetSize(ceil(bar.label:GetStringWidth() or 0) + 8, o.height)
	bar.tag:ClearAllPoints()
	bar.tag:SetPoint("RIGHT", bar, "LEFT", -px, 0)
	bar.tagEdge:ClearAllPoints()
	bar.tagEdge:SetPoint("TOPLEFT", -px, px)
	bar.tagEdge:SetPoint("BOTTOMRIGHT", px, -px)
end

local function Paint(waiting, value, text)
	local color = ns.db.mana.colors[waiting and "wait" or "regen"]
	bar:SetStatusBarColor(color.r, color.g, color.b)
	bar:SetValue(value)
	bar.text:SetText(ns.db.mana.text and text or "")
	local labelColor = waiting and LABEL_WAIT or LABEL_REGEN
	bar.label:SetTextColor(labelColor[1], labelColor[2], labelColor[3])
	bar.tag:SetShown(ns.db.mana.label)
end

function ns.UpdateMana()
	local o = ns.db.mana
	bar:SetAlpha(1)
	if ns.unlocked then
		-- A sample to drag and size
		Paint(true, 0.64, "3.2")
		bar:SetShown(o.enabled)
		return
	end
	if not (o.enabled and ns.IsMage()) or UnitIsDeadOrGhost("player") or (o.onlyCombat and not inCombat) then
		bar:Hide()
		return
	end
	local now = GetTime()
	local mana, most = UnitPower("player", MANA), UnitPowerMax("player", MANA)
	if ns.IsSecret(mana) or ns.IsSecret(most) then
		-- Hidden in a fight: the game still hides the bar at full mana, through its transparency
		if fullCurve and UnitPowerPercent then bar:SetAlpha(UnitPowerPercent("player", MANA, false, fullCurve)) end
	elseif not most or most <= 0 or mana >= most then
		bar:Hide()
		return
	end
	if now < waitEnds then
		local left = waitEnds - now
		Paint(true, left / WAIT, format("%.1f", left))
	else
		local value = 1
		if o.ticks and lastTick then value = ((now - lastTick) % TICK) / TICK end
		Paint(false, value, lastGain and format("+%d", lastGain) or "")
	end
	bar:Show()
end

bar = CreateFrame("StatusBar", "MageGodMana", UIParent)
bar:SetSize(160, 8)
bar:Hide()
-- Flat and square, like the food and scroll reminders: a plain fill on their dark back, a black
-- edge one screen pixel thin, and their thin letters with a shadow
bar:SetStatusBarTexture("Interface\\Buttons\\WHITE8X8")
bar:SetMinMaxValues(0, 1)
bar.edge = bar:CreateTexture(nil, "BACKGROUND", nil, -1)
bar.edge:SetColorTexture(0, 0, 0, 1)
local back = bar:CreateTexture(nil, "BACKGROUND")
back:SetAllPoints()
back:SetColorTexture(0.02, 0.04, 0.09, 0.8)
bar.text = bar:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
bar.text:SetPoint("CENTER")
-- MP5 on its own dark tag at the bar's left end, so it reads over grass, snow or anything
bar.tag = CreateFrame("Frame", nil, bar)
bar.tagEdge = bar.tag:CreateTexture(nil, "BACKGROUND", nil, -1)
bar.tagEdge:SetColorTexture(0, 0, 0, 1)
local tagBack = bar.tag:CreateTexture(nil, "BACKGROUND")
tagBack:SetAllPoints()
tagBack:SetColorTexture(0.02, 0.04, 0.09, 0.9)
bar.label = bar.tag:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
bar.label:SetPoint("CENTER")
bar.label:SetText(L.MANA_LABEL)
for _, text in ipairs({ bar.text, bar.label }) do
	text:SetShadowOffset(1, -1)
	text:SetShadowColor(0, 0, 0, 1)
end
local since = 0
bar:SetScript("OnUpdate", function(_, dt)
	since = since + dt
	if since < 0.03 then return end
	since = 0
	ns.UpdateMana()
end)

local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(self, event, unit, power, spellID)
	if event == "PLAYER_LOGIN" then
		if C_CurveUtil and C_CurveUtil.CreateCurve then
			fullCurve = C_CurveUtil.CreateCurve()
			if Enum and Enum.LuaCurveType then fullCurve:SetType(Enum.LuaCurveType.Linear) end
			fullCurve:AddPoint(0, 1)
			fullCurve:AddPoint(0.999, 1)
			fullCurve:AddPoint(1, 0)
		end
		inCombat = UnitAffectingCombat("player") and true or false
		ns.StyleMana()
		ns.Movable(bar, "mana", { "CENTER", "CENTER", 0, -110 }, L.MANA_NAME)
		table.insert(ns.refreshers, function() ns.StyleMana() ns.UpdateMana() end)
		self:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "player")
		self:RegisterUnitEvent("UNIT_POWER_UPDATE", "player")
		self:RegisterUnitEvent("UNIT_POWER_FREQUENT", "player")
		self:RegisterUnitEvent("UNIT_MAXPOWER", "player")
		self:RegisterEvent("PLAYER_REGEN_DISABLED")
		self:RegisterEvent("PLAYER_REGEN_ENABLED")
		self:RegisterEvent("PLAYER_DEAD")
		self:RegisterEvent("PLAYER_ALIVE")
		self:RegisterEvent("PLAYER_UNGHOST")
		self:RegisterEvent("UI_SCALE_CHANGED")
		self:RegisterEvent("DISPLAY_SIZE_CHANGED")
		PowerChanged()
	elseif event == "UNIT_SPELLCAST_SUCCEEDED" then
		if unit ~= "player" or not spellID or ns.IsSecret(spellID) then return end
		if CostsMana(spellID) then waitEnds = GetTime() + WAIT end
	elseif event == "UNIT_POWER_UPDATE" or event == "UNIT_POWER_FREQUENT" then
		if not ns.IsSecret(power) and power ~= "MANA" then return end
		PowerChanged()
	elseif event == "PLAYER_REGEN_DISABLED" then
		inCombat = true
	elseif event == "PLAYER_REGEN_ENABLED" then
		inCombat = false
		PowerChanged()
	elseif event == "UI_SCALE_CHANGED" or event == "DISPLAY_SIZE_CHANGED" then
		-- A screen pixel is another size now
		ns.StyleMana()
	end
	ns.UpdateMana()
end)
