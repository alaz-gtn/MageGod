local _, ns = ...
local L = ns.L

-- Counterspell ready while your target casts: its icon, with a thin black edge and a soft glow,
-- above the middle of the screen (drag it where you like). Only when you know it, it isn't cooling
-- down and the target is in its reach. Forever may hide what the target casts in a fight: then
-- it's enough to know that it is casting
local COUNTERSPELL = { 2139 }
local DEFAULT_POINT = { "CENTER", "CENTER", 0, 200 }
local SIZE = 44

local db, frame
local spell -- the Counterspell you know

local function Resolve()
	for _, id in ipairs(COUNTERSPELL) do
		local known = IsPlayerSpell and IsPlayerSpell(id)
		if known and not ns.IsSecret(known) then return id end
	end
	local name = ns.SpellName(COUNTERSPELL[1])
	local info = name and C_Spell and C_Spell.GetSpellInfo and C_Spell.GetSpellInfo(name)
	if type(info) == "table" and not ns.IsSecret(info) and info.spellID and not ns.IsSecret(info.spellID) then
		return info.spellID
	end
end

-- Is the target casting something you can interrupt? A hidden spell still counts as a cast
local function Casting()
	if not UnitExists("target") then return false end
	local hostile = UnitCanAttack("player", "target")
	if ns.IsSecret(hostile) or not hostile then return false end
	for _, get in ipairs({ UnitCastingInfo, UnitChannelInfo }) do
		if get then
			-- notInterruptible and the cast bar's number (never hidden) sit in different places for the two
			local name, _, _, _, _, _, a, b, _, d, e = get("target")
			local notInterruptible, castBar
			if get == UnitCastingInfo then notInterruptible, castBar = b, d else notInterruptible, castBar = a, e end
			if ns.IsSecret(name) or name ~= nil or (not ns.IsSecret(castBar) and castBar ~= nil) then
				if not ns.IsSecret(notInterruptible) and notInterruptible == true then return false end
				return true
			end
		end
	end
	return false
end

local function Ready()
	local info = C_Spell.GetSpellCooldown(spell)
	if type(info) ~= "table" or ns.IsSecret(info) then return true end
	local active = info.isActive
	if active == nil or ns.IsSecret(active) then return true end
	return not active
end

local function InReach()
	if not (C_Spell and C_Spell.IsSpellInRange) then return true end
	local within = C_Spell.IsSpellInRange(ns.SpellName(spell) or spell, "target")
	if ns.IsSecret(within) then return true end
	return within ~= false
end

function ns.UpdateKick()
	if not frame then return end
	local show
	if ns.unlocked then
		show = db.enabled and ns.IsMage()
	else
		show = db.enabled and ns.IsMage() and spell ~= nil and Casting() and Ready() and InReach()
	end
	if show then
		frame.icon:SetTexture(ns.SpellIcon(spell or COUNTERSPELL[1]))
		if not frame:IsShown() then frame.glow:Play() end
		frame:Show()
	else
		frame.glow:Stop()
		frame:Hide()
	end
end

-- For the tests
function ns.KickFrame() return frame end

local events = CreateFrame("Frame")
local function Listen(event, unit)
	if unit then pcall(events.RegisterUnitEvent, events, event, unit) else pcall(events.RegisterEvent, events, event) end
end

events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(self, event)
	if event == "PLAYER_LOGIN" then
		self:UnregisterEvent("PLAYER_LOGIN")
		db = ns.db.kick
		frame = CreateFrame("Frame", "MageGodKick", UIParent)
		frame:SetSize(SIZE, SIZE)
		frame:SetFrameStrata("HIGH")
		frame.edge = frame:CreateTexture(nil, "BACKGROUND")
		frame.edge:SetAllPoints()
		frame.edge:SetColorTexture(0, 0, 0, 1)
		frame.icon = frame:CreateTexture(nil, "ARTWORK")
		frame.icon:SetPoint("TOPLEFT", 1, -1)
		frame.icon:SetPoint("BOTTOMRIGHT", -1, 1)
		frame.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
		-- A soft glow that breathes while you can cut the cast
		frame.glow = frame:CreateAnimationGroup()
		frame.glow:SetLooping("BOUNCE")
		local fade = frame.glow:CreateAnimation("Alpha")
		fade:SetFromAlpha(1)
		fade:SetToAlpha(0.6)
		fade:SetDuration(0.35)
		frame:Hide()
		ns.Movable(frame, "kick", DEFAULT_POINT, L.KICK_NAME)
		table.insert(ns.refreshers, ns.UpdateKick)
		spell = Resolve()
		for _, e in ipairs({ "UNIT_SPELLCAST_START", "UNIT_SPELLCAST_STOP", "UNIT_SPELLCAST_CHANNEL_START",
			"UNIT_SPELLCAST_CHANNEL_STOP", "UNIT_SPELLCAST_INTERRUPTED", "UNIT_SPELLCAST_FAILED" }) do
			Listen(e, "target")
		end
		Listen("PLAYER_TARGET_CHANGED")
		Listen("SPELL_UPDATE_COOLDOWN")
		Listen("SPELLS_CHANGED")
		ns.UpdateKick()
	elseif event == "SPELLS_CHANGED" then
		spell = Resolve()
		ns.UpdateKick()
	else
		ns.UpdateKick()
	end
end)
