local _, ns = ...

-- Your debuffs on your target, beside its nameplate: Fire Vulnerability (Improved Scorch, up to 5
-- stacks) and Winter's Chill (up to 5), each with its stacks and the seconds it has left. Only the
-- ones your talents give. Forever hides the target's auras in a fight, so the game shows them
-- itself, as HunterGod's Freezing Trap timer: an aura container on "target" per debuff, and the
-- game fills in the icon, the stacks and the countdown
local DEBUFFS = {
	{ key = "scorch", ids = { 22959 }, talent = { 11095 } }, -- Fire Vulnerability, from Improved Scorch
	{ key = "chill", ids = { 12579 }, talent = { 11180 } }, -- Winter's Chill
}
ns.MAGE_DEBUFFS = DEBUFFS
local SIZE, GAP = 24, 3

local db, holder
local plate -- the nameplate it sits beside

local function Style(button, box)
	button:SetAllPoints(box)
	button:EnableMouse(false)
	local edge = button:CreateTexture(nil, "BACKGROUND")
	edge:SetPoint("TOPLEFT", -1, 1)
	edge:SetPoint("BOTTOMRIGHT", 1, -1)
	edge:SetColorTexture(0, 0, 0, 1)
	local icon = button:CreateTexture(nil, "ARTWORK")
	icon:SetAllPoints(button)
	icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	pcall(button.SetIcon, button, icon)
	-- The stacks, in a corner
	local stacks = button:CreateFontString(nil, "OVERLAY")
	stacks:SetPoint("BOTTOMRIGHT", 2, -2)
	pcall(ns.UseFont, stacks, ns.FONTS and ns.FONTS[ns.db.range.font], 12, "OUTLINE")
	pcall(button.SetApplicationCount, button, stacks)
	-- The game counts down a time the addon can't read
	local ok, cooldown = pcall(CreateFrame, "Cooldown", nil, button, "CooldownFrameTemplate")
	if ok and cooldown then
		cooldown:SetAllPoints(button)
		pcall(cooldown.SetDrawEdge, cooldown, false)
		pcall(cooldown.SetHideCountdownNumbers, cooldown, false)
		pcall(cooldown.SetUseAuraDisplayTime, cooldown, true)
		pcall(button.SetDurationCooldown, button, cooldown)
	end
	box.dressed = true
end

-- One container per debuff, side by side, built out of combat once its talent is known
local function Build()
	if not holder or InCombatLockdown() or not (CustomAuraContainerAuraProcessingPolicy and C_UnitAuras) then return end
	for i, d in ipairs(DEBUFFS) do
		local want = db.enabled and ns.IsMage() and ns.Knows(d.talent)
		if want and not d.container then
			local box = CreateFrame("Frame", nil, holder)
			box:SetSize(SIZE, SIZE)
			box:SetPoint("RIGHT", holder, "RIGHT", -(i - 1) * (SIZE + GAP), 0)
			local ok, container = pcall(CreateFrame, "AuraContainer", nil, box, "CustomAuraContainerTemplate")
			if ok and container then
				container:SetAllPoints(box)
				container:SetEnabled(false)
				container:SetAuraProcessingPolicy(CustomAuraContainerAuraProcessingPolicy.None)
				local spells = {}
				for _, id in ipairs(d.ids) do spells[id] = true end
				if pcall(container.AddAuraSlot, container, "MageGodDebuff" .. d.key, "HARMFUL", {
					candidateFilters = { includeSpellIDs = spells },
					initializeFrame = function(button) Style(button, box) end,
				}) then
					container:SetUnit("target")
					container:SetEnabled(true)
					d.container, d.box = container, box
				end
			end
		elseif d.container then
			pcall(d.container.SetEnabled, d.container, want and true or false)
		end
	end
end

-- Beside the target's nameplate, left of its health bar; hidden without one
local function Place()
	if not holder then return end
	local p = C_NamePlate and C_NamePlate.GetNamePlateForUnit and C_NamePlate.GetNamePlateForUnit("target")
	if not (db.enabled and p) or (p.IsForbidden and p:IsForbidden()) then
		holder:Hide()
		plate = nil
		return
	end
	if InCombatLockdown() and holder:IsProtected() then return end
	if p ~= plate then
		holder:SetParent(p)
		holder:ClearAllPoints()
		local bar = ns.PlateBar and ns.PlateBar(p) or p
		if pcall(holder.SetPoint, holder, "RIGHT", bar, "LEFT", -6, 0) then plate = p end
	end
	holder:Show()
	for _, d in ipairs(DEBUFFS) do
		if d.container then pcall(d.container.UpdateAllAuras, d.container) end
	end
end
ns.PlaceDebuffs = Place

function ns.DebuffsState()
	return { holder = holder, debuffs = DEBUFFS }
end

local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(self, event)
	if event == "PLAYER_LOGIN" then
		db = ns.db.debuffs
		holder = CreateFrame("Frame", "MageGodDebuffs", UIParent)
		holder:SetSize(#DEBUFFS * (SIZE + GAP), SIZE)
		holder:Hide()
		for _, e in ipairs({ "PLAYER_TARGET_CHANGED", "NAME_PLATE_UNIT_ADDED", "PLAYER_REGEN_ENABLED", "SPELLS_CHANGED" }) do
			pcall(self.RegisterEvent, self, e)
		end
		table.insert(ns.refreshers, function()
			Build()
			Place()
		end)
		Build()
		Place()
	elseif event == "SPELLS_CHANGED" or event == "PLAYER_REGEN_ENABLED" then
		Build()
		Place()
	else
		Place()
	end
end)
