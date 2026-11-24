local _, ns = ...
local L = ns.L

-- When Blink is back: its icon big in the middle of the screen, fading fast. In combat Forever
-- hides how long a cooldown has left, but not whether it is running: the pulse comes when Blink
-- goes from cooling down to ready.
local BLINK = { 1953 }
local DEFAULT_POINT = { "CENTER", "CENTER", 0, 80 }
local GCD_MAX = 2.5 -- no global cooldown lasts this long: a longer wait was Blink's own
local POLL = 0.1
-- The pulse: it pops in, holds, and fades while it grows
local POP, HOLD, FADE = 0.12, 0.3, 0.55
local SHINE = 0.5
local STAR = "Interface\\Cooldown\\star4"

local db
local place, art
local spell -- the Blink you know
local since -- when it was first seen cooling down
local own = false -- known to be Blink's own cooldown, not the global one
local castAt -- when you last cast it
local blind -- since when the game won't say whether it is cooling down
local playing -- when the pulse started

local function Resolve()
	for _, id in ipairs(BLINK) do
		local known = IsPlayerSpell and IsPlayerSpell(id)
		if known and not ns.IsSecret(known) then return id end
	end
	-- Forever may give it another number: the spellbook answers for its name
	local name = ns.SpellName(BLINK[1])
	local info = name and C_Spell and C_Spell.GetSpellInfo and C_Spell.GetSpellInfo(name)
	if type(info) == "table" and not ns.IsSecret(info) then
		local id = info.spellID
		if id and not ns.IsSecret(id) then return id end
	end
end

-- Is it cooling down? nil when the game won't say
local function Cooling()
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

-- Is that its own cooldown and not the global one? nil when the game won't say
local function Own(info)
	local duration = info.duration
	if duration and not ns.IsSecret(duration) then return duration > 1.6 end
	local gcd = info.isOnGCD
	if gcd ~= nil and not ns.IsSecret(gcd) then return not gcd end
	if C_Spell.GetSpellCooldownDuration then
		local timer = C_Spell.GetSpellCooldownDuration(spell, true)
		local zero = timer and timer.IsZero and timer:IsZero()
		if zero ~= nil and not ns.IsSecret(zero) then return not zero end
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
		art.icon:SetTexture(ns.SpellIcon(spell or BLINK[1]))
		place:Show()
		Paint(1, 1, 0, 1)
	else
		place:Hide()
	end
end

local function Animate()
	local t = GetTime() - playing
	if t >= POP + HOLD + FADE then
		playing = nil
		Rest()
		return
	end
	Paint(Frame(t))
end

function ns.PulseBlink()
	art.icon:SetTexture(ns.SpellIcon(spell or BLINK[1]))
	art.shine:SetVertexColor(db.color.r, db.color.g, db.color.b)
	playing = GetTime()
	place:SetSize(db.size, db.size)
	place:Show()
	Paint(Frame(0))
end

function ns.StylePulse()
	if not place then return end
	art.shine:SetVertexColor(db.color.r, db.color.g, db.color.b)
	Rest()
end

-- Checks whether Blink is back
local function Check()
	if not spell then return end
	local now = GetTime()
	local cooling, info = Cooling()
	if cooling == nil then
		blind = blind or now
		return
	end
	-- After a stretch where the game wouldn't say, what it says now may be old news
	local stale = blind and now - blind > 1
	blind = nil
	if cooling then
		if not since then since = now end
		if not own and Own(info) then own = true end
	elseif since then
		if not stale and (own or now - since > GCD_MAX) and db.enabled and ns.IsMage()
			and not UnitIsDeadOrGhost("player") then
			ns.PulseBlink()
		end
		since, own = nil, false
	elseif own and castAt and now - castAt > 1 then
		own = false -- the cast never showed a cooldown
	end
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
	if not since and not own then self:Hide() end
end)

local function Watch()
	Check()
	if since or own then poller:Show() end
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
	return { place = place, art = art, spell = spell, since = since, own = own, poller = poller }
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
		spell = Resolve()
		self:RegisterEvent("SPELL_UPDATE_COOLDOWN")
		self:RegisterEvent("SPELLS_CHANGED")
		self:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "player")
		ns.StylePulse()
		Watch()
	elseif event == "SPELLS_CHANGED" then
		spell = Resolve()
		Watch()
	elseif event == "UNIT_SPELLCAST_SUCCEEDED" then
		if unit ~= "player" or not spellID or ns.IsSecret(spellID) or not spell then return end
		if spellID ~= spell then
			-- The same spell under another number
			local name = ns.SpellName(spellID)
			if not name or ns.IsSecret(name) or name ~= ns.SpellName(spell) then return end
		end
		own, castAt = true, GetTime()
		Watch()
	elseif event == "SPELL_UPDATE_COOLDOWN" then
		Watch()
	end
end)
