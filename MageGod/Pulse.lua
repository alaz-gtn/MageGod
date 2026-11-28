local _, ns = ...
local L = ns.L

-- When Blink is back, or another big cooldown of yours (Evocation, Ice Block, Cold Snap, Presence
-- of Mind, Arcane Power, Combustion): its icon big in the middle of the screen, fading fast. In
-- combat Forever hides how long a cooldown has left, but not whether it is running: the pulse comes
-- when the spell goes from cooling down to ready. Two back at once pulse one after the other.
-- Only the ones you know, each with its own switch
local BLINK = { 1953 }
local TRACKED = {
	{ key = "blink", ids = BLINK },
	{ key = "evocation", ids = { 12051 } },
	{ key = "iceBlock", ids = { 11958 } },
	{ key = "coldSnap", ids = { 12472 } },
	{ key = "presence", ids = { 12043 } },
	{ key = "arcanePower", ids = { 12042 } },
	{ key = "combustion", ids = { 11129 } },
}
ns.PULSE_SPELLS = TRACKED
local DEFAULT_POINT = { "CENTER", "CENTER", 0, 80 }
local GCD_MAX = 2.5 -- no global cooldown lasts this long: a longer wait was Blink's own
local POLL = 0.1
-- The pulse: it pops in, holds, and fades while it grows
local POP, HOLD, FADE = 0.12, 0.3, 0.55
local SHINE = 0.5
local STAR = "Interface\\Cooldown\\star4"

local db
local place, art
-- Each tracked spell's state: spell (the one you know), since (first seen cooling down), own (known
-- to be its own cooldown, not the global one), real (seen cooling down with the global one over), castAt (when you last cast it), blind (since when
-- the game won't say whether it is cooling down)
local states = {}
for _, t in ipairs(TRACKED) do states[t.key] = { own = false } end
local playing -- when the pulse started
local queue = {} -- spells waiting for their pulse

local function Resolve(ids)
	for _, id in ipairs(ids) do
		local known = IsPlayerSpell and IsPlayerSpell(id)
		if known and not ns.IsSecret(known) then return id end
	end
	-- Forever may give it another number: the spellbook answers for its name
	local name = ns.SpellName(ids[1])
	local info = name and C_Spell and C_Spell.GetSpellInfo and C_Spell.GetSpellInfo(name)
	if type(info) == "table" and not ns.IsSecret(info) then
		local id = info.spellID
		if id and not ns.IsSecret(id) then return id end
	end
end

-- Is it cooling down? nil when the game won't say
local function Cooling(spell)
	local info = C_Spell.GetSpellCooldown(spell)
	if type(info) ~= "table" or ns.IsSecret(info) then return nil end
	local active = info.isActive
	if active == nil or ns.IsSecret(active) then
		local duration = info.duration
		if duration == nil or ns.IsSecret(duration) then return nil end
		active = duration > 0
	end
	return active and true or false, info
end

-- Is the global cooldown running? nil when the game won't say. While it runs, any spell shows as
-- cooling down: that alone says nothing about its own cooldown
local GCD_SPELL = 61304
local function GlobalRunning()
	local info = C_Spell.GetSpellCooldown(GCD_SPELL)
	if type(info) ~= "table" or ns.IsSecret(info) then return nil end
	local active = info.isActive
	if active == nil or ns.IsSecret(active) then
		local duration = info.duration
		if duration == nil or ns.IsSecret(duration) then return nil end
		active = duration > 0
	end
	return active and true or false
end

-- Silenced, stunned, or your school locked out: the game shows every spell cooling down until it
-- ends, and that says nothing about their own cooldowns. nil when the game won't say
local function Locked(spell)
	if C_Spell.GetSpellLossOfControlCooldown then
		local _, duration = C_Spell.GetSpellLossOfControlCooldown(spell)
		if type(duration) == "number" and not ns.IsSecret(duration) and duration > 0 then return true end
	end
	if C_LossOfControl and C_LossOfControl.GetActiveLossOfControlDataCount then
		local count = C_LossOfControl.GetActiveLossOfControlDataCount()
		if type(count) == "number" and not ns.IsSecret(count) then return count > 0 end
	end
end

-- Is that its own cooldown and not the global one? nil when the game won't say
local function Own(info, spell)
	local duration = info.duration
	if duration and not ns.IsSecret(duration) then return duration > 1.6 end
	local gcd = info.isOnGCD
	if gcd ~= nil and not ns.IsSecret(gcd) then return not gcd end
	if C_Spell.GetSpellCooldownDuration then
		local timer = C_Spell.GetSpellCooldownDuration(spell, true)
		local zero = timer and timer.IsZero and timer:IsZero()
		-- While the global one runs this may count it too: it can't tell then
		if zero ~= nil and not ns.IsSecret(zero) then
			if not zero and GlobalRunning() ~= false then return nil end
			return not zero
		end
	end
end

local function Draw(parent)
	local a = {}
	a.shine = parent:CreateTexture(nil, "BACKGROUND")
	a.shine:SetPoint("CENTER")
	a.shine:SetTexture(STAR)
	a.shine:SetBlendMode("ADD")
	a.shine:SetAlpha(0)
	a.box = CreateFrame("Frame", nil, parent)
	a.box:SetPoint("CENTER")
	a.edge = a.box:CreateTexture(nil, "BACKGROUND")
	a.edge:SetColorTexture(0, 0, 0, 1)
	a.icon = a.box:CreateTexture(nil, "ARTWORK")
	a.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	a.edge:SetAllPoints(a.box)
	return a
end

-- How it looks t seconds in: its alpha, its size, and the shine's
local function Frame(t)
	local alpha, scale
	if t < POP then
		alpha, scale = t / POP, 0.6 + 0.4 * t / POP
	elseif t < POP + HOLD then
		alpha, scale = 1, 1
	else
		local f = min((t - POP - HOLD) / FADE, 1)
		alpha, scale = 1 - f, 1 + 0.3 * f
	end
	local shine = t < SHINE and (1 - t / SHINE) * 0.9 or 0
	return alpha, scale, shine, 0.8 + 1.2 * min(t / SHINE, 1)
end

local function Paint(alpha, scale, shine, shineScale)
	local size = db.size
	art.box:SetAlpha(alpha * db.alpha / 100)
	art.box:SetSize(size * scale, size * scale)
	local px = ns.OnePixel(place)
	art.icon:ClearAllPoints()
	art.icon:SetPoint("TOPLEFT", art.box, "TOPLEFT", px, -px)
	art.icon:SetPoint("BOTTOMRIGHT", art.box, "BOTTOMRIGHT", -px, px)
	art.shine:SetAlpha(shine * db.alpha / 100)
	art.shine:SetSize(size * 1.6 * shineScale, size * 1.6 * shineScale)
end

-- While unlocked it stays up to be dragged
local function Rest()
	if playing then return end
	place:SetSize(db.size, db.size)
	if ns.unlocked and db.enabled and ns.IsMage() then
		art.icon:SetTexture(ns.SpellIcon(states.blink.spell or BLINK[1]))
		place:Show()
		Paint(1, 1, 0, 1)
	else
		place:Hide()
	end
end

local function Start(spell)
	art.icon:SetTexture(ns.SpellIcon(spell))
	art.shine:SetVertexColor(db.color.r, db.color.g, db.color.b)
	playing = GetTime()
	place:SetSize(db.size, db.size)
	place:Show()
	Paint(Frame(0))
end

local function Animate()
	local t = GetTime() - playing
	if t >= POP + HOLD + FADE then
		playing = nil
		-- The next one back, if two came at once
		local nextSpell = table.remove(queue, 1)
		if nextSpell then
			Start(nextSpell)
			return
		end
		Rest()
		return
	end
	Paint(Frame(t))
end

-- A spell's pulse: now, or after the one playing
local function Pulse(spell)
	if playing then
		queue[#queue + 1] = spell
		return
	end
	Start(spell)
end

function ns.PulseBlink()
	Start(states.blink.spell or BLINK[1])
end

function ns.StylePulse()
	if not place then return end
	art.shine:SetVertexColor(db.color.r, db.color.g, db.color.b)
	Rest()
end

-- Checks whether one spell is back
local function CheckOne(t)
	local s = states[t.key]
	if not s.spell then return end
	local now = GetTime()
	local cooling, info = Cooling(s.spell)
	if cooling == nil then
		s.blind = s.blind or now
		return
	end
	-- After a stretch where the game wouldn't say, what it says now may be old news
	local stale = s.blind and now - s.blind > 1
	s.blind = nil
	-- Half a second more: the game may say the silence is over a moment before the spells
	if cooling and not s.real and Locked(s.spell) then s.lockedAt = now end
	if cooling and not s.real and s.lockedAt and now - s.lockedAt < 0.5 then
		-- What it shows now may be the silence's: its wait starts again when that is over
		s.own, s.since = false, now
	elseif cooling then
		local own = not s.own and Own(info, s.spell)
		if own then s.own, s.real = true, true end
		-- Only the global cooldown, as the game says: its time doesn't count. Spells cast one after
		-- another chain them for longer than any one, and that isn't the spell's own coming back.
		-- In combat it may not say whose it is: while the global one runs, the wait doesn't start
		local global = not s.own and own == nil and GlobalRunning()
		if s.own then
			s.since = s.since or now
			s.real = true
		elseif own == false or global and not s.real then
			s.since = now -- the global one, or maybe: its wait starts afresh
		else
			s.since = s.since or now
			if global == false then s.real = true end -- the global one is over and it still cools down
		end
	elseif s.since then
		if not stale and (s.own or now - s.since > GCD_MAX) and db.enabled and db.spells[t.key] ~= false
			and ns.IsMage() and not UnitIsDeadOrGhost("player") then
			Pulse(s.spell)
		end
		s.since, s.own, s.real, s.lockedAt = nil, false, nil, nil
	elseif s.own and s.castAt and now - s.castAt > 1 then
		s.own, s.real = false, nil -- the cast never showed a cooldown
	end
end

local function Check()
	for _, t in ipairs(TRACKED) do CheckOne(t) end
end

local function Waiting()
	for _, s in pairs(states) do
		if s.since or s.own then return true end
	end
	return false
end

local function ResolveAll()
	for _, t in ipairs(TRACKED) do states[t.key].spell = Resolve(t.ids) end
end

-- Watched often only while it is cooling down, or just cast
local poller = CreateFrame("Frame")
poller:Hide()
local waited = 0
poller:SetScript("OnUpdate", function(self, elapsed)
	waited = waited + elapsed
	if waited < POLL then return end
	waited = 0
	Check()
	if not Waiting() then self:Hide() end
end)

local function Watch()
	Check()
	if Waiting() then poller:Show() end
end

-- /magegod blink: shows it
local function Test()
	if not ns.IsMage() then return end
	ns.PulseBlink()
end
ns.commands.blink = Test
ns.commands.traslacion = Test
ns.commands["traslación"] = Test

-- For the tests
function ns.PulseState()
	local b = states.blink
	return { place = place, art = art, spell = b.spell, since = b.since, own = b.own, poller = poller, states = states,
		queue = queue }
end

local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(self, event, unit, _, spellID)
	if event == "PLAYER_LOGIN" then
		self:UnregisterEvent("PLAYER_LOGIN") -- built once
		db = ns.db.pulse
		place = CreateFrame("Frame", "MageGodPulse", UIParent)
		place:SetFrameStrata("HIGH")
		place:SetSize(db.size, db.size)
		place:Hide()
		art = Draw(place)
		place:SetScript("OnUpdate", function()
			if playing then Animate() end
		end)
		ns.Movable(place, "pulse", DEFAULT_POINT, L.PULSE_NAME)
		table.insert(ns.refreshers, ns.StylePulse)
		ResolveAll()
		self:RegisterEvent("SPELL_UPDATE_COOLDOWN")
		self:RegisterEvent("SPELLS_CHANGED")
		self:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "player")
		ns.StylePulse()
		Watch()
	elseif event == "SPELLS_CHANGED" then
		ResolveAll()
		Watch()
	elseif event == "UNIT_SPELLCAST_SUCCEEDED" then
		if unit ~= "player" or not spellID or ns.IsSecret(spellID) then return end
		local name = ns.SpellName(spellID)
		for _, t in ipairs(TRACKED) do
			local s = states[t.key]
			-- The same spell under another number counts too
			if s.spell and (spellID == s.spell or name and not ns.IsSecret(name) and name == ns.SpellName(s.spell)) then
				s.own, s.castAt = true, GetTime()
			end
		end
		Watch()
	elseif event == "SPELL_UPDATE_COOLDOWN" then
		Watch()
	end
end)
