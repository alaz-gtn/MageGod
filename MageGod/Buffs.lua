local _, ns = ...
local L = ns.L

-- Every rank of each buff: the name covers them all, the ids say which you know
local SPELLS = {
	frost = { 168, 7300, 7301 }, -- Frost Armor
	ice = { 7302, 7320, 10219, 10220 }, -- Ice Armor
	mage = { 6117, 22782, 22783 }, -- Mage Armor
	molten = { 428741, 428743, 429307, 456403, 30482 }, -- Molten Armor, should Forever give it to you
	intellect = { 1459, 1460, 1461, 10156, 10157 }, -- Arcane Intellect
	brilliance = { 23028 }, -- Arcane Brilliance
	dampen = { 604, 8450, 8451, 10173, 10174 }, -- Dampen Magic
	amplify = { 1008, 8455, 10169, 10170 }, -- Amplify Magic
}
ns.BUFF_SPELLS = SPELLS
-- Which reminder each buff answers for
local SLOT = {
	frost = "armor", ice = "armor", mage = "armor", molten = "armor",
	intellect = "intellect", brilliance = "intellect",
	dampen = "magic", amplify = "magic",
}
local SLOTS = { "armor", "intellect", "magic", "food" }
-- How long each lasts until the game says otherwise (Forever doubled Arcane Intellect to an hour)
local DURATION = {
	frost = 1800, ice = 1800, mage = 1800, molten = 1800,
	intellect = 3600, brilliance = 3600, dampen = 600, amplify = 600,
}
-- The mana gems, the best last: the spell that conjures each one and the gem it makes
ns.GEMS = {
	{ spell = 759, item = 5514 }, -- Mana Agate
	{ spell = 3552, item = 5513 }, -- Mana Jade
	{ spell = 10053, item = 8007 }, -- Mana Citrine
	{ spell = 10054, item = 8008 }, -- Mana Ruby
}
-- Every Well Fed has this name; in Forever cooked food also gives +5% XP from kills
local WELL_FED = 19705
local SIZE, GAP = 36, 8

local db
local byName = {} -- buff name -> key
local gemNames = {}
local wellFedName
-- Well Fed in lower case: what the game calls it, and the English and your language's words in
-- case Forever names the buff otherwise
local fedWords = { "well fed" }
local known = {} -- by key, and gemKnown by gem: what you've learned
local gemKnown = {}
-- By slot: GetTime() when it runs out (math.huge for no end), false when it isn't on you,
-- nil while the addon hasn't seen your buffs yet
local ends = {}
local wearing = {} -- by slot: the key of the buff that's on you
local lasts = {} -- by key: how long it lasts, as the game said last time
local inCombat = false
local row, food
local icons = {}
local UpdateExtras

local function Learn()
	wipe(byName)
	wipe(gemNames)
	for key, ids in pairs(SPELLS) do
		local name = ns.SpellName(ids[1])
		if name then byName[name] = key end
		known[key] = ns.Knows(ids)
	end
	for i, gem in ipairs(ns.GEMS) do
		local name = ns.SpellName(gem.spell)
		if name then gemNames[name] = true end
		gemKnown[i] = ns.Knows({ gem.spell })
	end
	wellFedName = ns.SpellName(WELL_FED)
	fedWords = { "well fed", strlower(L.WELL_FED) }
	if wellFedName then fedWords[#fedWords + 1] = strlower(wellFedName) end
end

local function IsFedName(name)
	if type(name) ~= "string" then return false end
	local low = strlower(name)
	for _, word in ipairs(fedWords) do
		if low == word then return true end
	end
	return false
end

local function AurasHidden()
	return C_Secrets and C_Secrets.ShouldAurasBeSecret and C_Secrets.ShouldAurasBeSecret()
end

-- Reads your buffs; false when the game hides them (in combat, in Forever). Then what you
-- cast keeps the count
local function Scan()
	if AurasHidden() or not (C_UnitAuras and C_UnitAuras.GetAuraDataByIndex) then return false end
	local found = {}
	for i = 1, 40 do
		local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
		if not aura then break end
		if ns.IsSecret(aura) or ns.IsSecret(aura.name) or ns.IsSecret(aura.expirationTime) then return false end
		local key = byName[aura.name]
		local slot = key and SLOT[key] or (IsFedName(aura.name) and "food")
		if slot and not found[slot] then
			local duration = aura.duration
			if key and type(duration) == "number" and not ns.IsSecret(duration) and duration > 0 then
				lasts[key] = duration
			end
			local expires = aura.expirationTime
			found[slot] = { key = key, ends = type(expires) == "number" and expires > 0 and expires or math.huge }
		end
	end
	for _, slot in ipairs(SLOTS) do
		ends[slot] = found[slot] and found[slot].ends or false
		wearing[slot] = found[slot] and found[slot].key
	end
	return true
end

-- The armor to remind you of: the one you chose, or the last one you cast
local function WantedArmor()
	local pick = db.armorChoice == "auto" and ns.db.lastArmor or db.armorChoice
	if pick == "mage" and known.mage then return "mage" end
	if pick == "molten" and known.molten then return "molten" end
	-- Ice Armor takes over from Frost Armor once you learn it
	if known.ice then return "ice" end
	if known.frost then return "frost" end
	if known.mage then return "mage" end
end

local FROST_LINE = { frost = true, ice = true }
local function ArmorFits(want, on)
	if not on then return false end
	if db.armorChoice == "auto" then return true end
	if FROST_LINE[want] then return FROST_LINE[on] or false end
	return on == want
end

local function GemCount(item)
	local count = C_Item and C_Item.GetItemCount and C_Item.GetItemCount(item) or GetItemCount and GetItemCount(item)
	if ns.IsSecret(count) then return 1 end
	return count or 0
end

local function Dead()
	local dead = UnitIsDeadOrGhost("player")
	if ns.IsSecret(dead) then return false end
	return dead or (UnitOnTaxi and UnitOnTaxi("player"))
end

-- What to remind you of now: { icon, left (0 when it's missing), gem }
local function Reminders()
	local list = {}
	if not ns.IsMage() or Dead() then return list end
	local now, warn = GetTime(), db.warnMinutes * 60
	local function Add(slot, key, fits, cast)
		local e = ends[slot]
		if e == nil or not key then return end -- your buffs not seen yet
		local left = 0
		if e and fits then
			left = e - now
			if left > warn then return end
			left = max(left, 0)
		end
		list[#list + 1] = { icon = ns.SpellIcon(SPELLS[key][1]), left = left, name = ns.SpellName(SPELLS[key][1]),
			spell = ns.SpellName(SPELLS[cast or key][1]), slot = slot }
	end
	if db.enabled and (db.combat or not inCombat) then
		if db.armor then
			local want = WantedArmor()
			local on = wearing.armor
			local fits = ArmorFits(want, on)
			Add("armor", fits and on or want, fits)
		end
		if db.intellect and known.intellect then
			-- A click casts Arcane Intellect on you, whichever of the two is running out
			Add("intellect", wearing.intellect or "intellect", true, "intellect")
		end
		if db.magic ~= "none" and known[db.magic] then
			Add("magic", db.magic, wearing.magic == db.magic)
		end
	end
	-- A gem is conjured out of combat
	local gems = ns.db.gems
	local gather = not inCombat and ns.GatherReminder()
	if gems.enabled and not inCombat then
		for i = #ns.GEMS, 1, -1 do
			local gem = ns.GEMS[i]
			if gemKnown[i] then
				if GemCount(gem.item) == 0 then
					list[#list + 1] = { icon = ns.SpellIcon(gem.spell), left = 0, gem = true, spell = ns.SpellName(gem.spell) }
				end
				if not gems.all then break end
			end
		end
	end
	-- In a group, someone without your Arcane Intellect: how many, and a click casts it on the first
	if not inCombat then
		for _, g in ipairs(ns.GroupBuffReminders()) do
			list[#list + 1] = { icon = g.icon, left = 0, spell = g.unit and g.spell or nil, unit = g.unit,
				label = tostring(g.count), name = g.text, tip = g.click }
		end
	end
	-- Herbalism or Mining without its tracking on, out in the world: a click puts it on
	if gather then
		list[#list + 1] = { icon = gather.icon, left = 0, spell = gather.spell, track = gather.key }
	end
	return list
end

local function Clock(seconds)
	seconds = floor(seconds)
	if seconds >= 3600 then
		return format("%d:%02d:%02d", floor(seconds / 3600), floor(seconds % 3600 / 60), seconds % 60)
	end
	return format("%d:%02d", floor(seconds / 60), seconds % 60)
end

local function Icon(i)
	local b = icons[i]
	if b then return b end
	b = CreateFrame("Frame", nil, row)
	b:SetSize(SIZE, SIZE)
	b:SetPoint("LEFT", (i - 1) * (SIZE + GAP), 0)
	local border = b:CreateTexture(nil, "BORDER")
	border:SetPoint("TOPLEFT", -2, 2)
	border:SetPoint("BOTTOMRIGHT", 2, -2)
	border:SetColorTexture(0.25, 0.78, 0.92, 0.9)
	b.icon = b:CreateTexture(nil, "ARTWORK")
	b.icon:SetAllPoints()
	b.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	b.text = b:CreateFontString(nil, "OVERLAY", "GameFontNormal")
	b.text:SetPoint("TOP", b, "BOTTOM", 0, -3)
	b.text:SetTextColor(0.6, 0.9, 1)
	ns.FancyFont(b.text, 14, "THICKOUTLINE")
	b.pulse = b:CreateAnimationGroup()
	b.pulse:SetLooping("BOUNCE")
	local fade = b.pulse:CreateAnimation("Alpha")
	fade:SetFromAlpha(1)
	fade:SetToAlpha(0.45)
	fade:SetDuration(0.7)
	icons[i] = b
	return b
end

-- Clicking a reminder casts it. The game only lets addons set up such buttons out of combat,
-- so they sit apart from the icons, over them, and go away as a fight starts
local casters = {}
local castHolder = CreateFrame("Frame", "MageGodCast", UIParent)
castHolder:SetSize(SIZE, SIZE)
castHolder:Hide()

local function Caster_OnEnter(self)
	GameTooltip:SetOwner(self, "ANCHOR_TOP")
	GameTooltip:AddLine(self.spellName or "?", 1, 1, 1)
	GameTooltip:AddLine(self.armorMenu and L.CLICK_PICK_ARMOR or self.tip or L.CLICK_CAST, 0.4, 0.8, 1)
	GameTooltip:Show()
end

-- The armors you know, one of each line: Ice Armor once you have it, else Frost Armor; Mage Armor;
-- Molten Armor if Forever gives it to you
local function KnownArmors()
	local list = {}
	if known.ice then list[#list + 1] = "ice" elseif known.frost then list[#list + 1] = "frost" end
	if known.mage then list[#list + 1] = "mage" end
	if known.molten then list[#list + 1] = "molten" end
	return list
end
ns.KnownArmors = KnownArmors

local function Caster(i)
	local b = casters[i]
	if b then return b end
	b = CreateFrame("Button", "MageGodCast" .. i, castHolder, "SecureActionButtonTemplate")
	b:SetSize(SIZE, SIZE)
	b:SetPoint("LEFT", (i - 1) * (SIZE + GAP), 0)
	b:RegisterForClicks("AnyUp", "AnyDown")
	b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
	b:SetAttribute("type", "spell")
	b:SetAttribute("unit", "player") -- Arcane Intellect on you, not on whoever you have targeted
	b:SetScript("OnEnter", Caster_OnEnter)
	-- The armor reminder, when you know more than one: a click opens them to pick from
	b:HookScript("OnClick", function(self, _, down)
		if self.armorMenu and not down then ns.ToggleArmorMenu(self) end
	end)
	b:SetScript("OnLeave", GameTooltip_Hide)
	casters[i] = b
	return b
end

local function UpdateCasters(list)
	if InCombatLockdown() then return end
	local left, bottom = row:GetLeft(), row:GetBottom()
	if inCombat or ns.unlocked or not db.click or not row:IsShown()
		or ns.IsSecret(left) or ns.IsSecret(bottom) or not left or not bottom then
		castHolder:Hide()
		return
	end
	castHolder:ClearAllPoints()
	castHolder:SetPoint("BOTTOMLEFT", UIParent, "BOTTOMLEFT", left, bottom)
	castHolder:SetSize(row:GetWidth(), SIZE)
	local shown = 0
	for i, r in ipairs(list) do
		if r.spell then
			local b = Caster(i)
			-- Armor: with a choice, the click opens the list instead of casting
			local pick = r.slot == "armor" and #KnownArmors() > 1
			local kind = not pick and "spell" or nil
			if b:GetAttribute("type") ~= kind then b:SetAttribute("type", kind) end
			if b:GetAttribute("spell") ~= r.spell then b:SetAttribute("spell", r.spell) end
			-- On you, or on the group member it's for
			local unit = r.unit or "player"
			if b:GetAttribute("unit") ~= unit then b:SetAttribute("unit", unit) end
			b.spellName = r.name or r.spell
			b.tip = r.tip
			b.armorMenu = pick
			b:Show()
			shown = shown + 1
		elseif casters[i] then
			casters[i]:Hide()
		end
	end
	for i = #list + 1, #casters do casters[i]:Hide() end
	castHolder:SetShown(shown > 0)
end

-- Forever's mage scrolls (Comprehension) that last an hour: weapon imbues, each for one kind of
-- weapon, and familiars, which add Intellect. The rest (Cryoblast, Minor Evocation...) are used
-- when you need them, not kept up
local IMBUES = {
	[274947] = "staff", [277485] = "staff", [277486] = "staff", [277487] = "staff", [277494] = "staff",
	[277495] = "staff", [277496] = "staff", [277497] = "staff", [277500] = "staff", [277501] = "staff",
	[277502] = "staff",
	[275067] = "dagger", [277488] = "dagger", [277498] = "dagger",
	[277489] = "sword",
}
local FAMILIARS = { 275069, 277483, 277493 } -- Rat, Frog and Cat, each with more Intellect
ns.IMBUES, ns.FAMILIARS = IMBUES, FAMILIARS
local SCROLL_TIME = 3600
-- Weapon subclasses: staff, dagger, and one and two-handed swords
local WEAPON_KIND = { [10] = "staff", [15] = "dagger", [7] = "sword", [8] = "sword" }
local MAIN_HAND = INVSLOT_MAINHAND or 16
local scrollCounts = {} -- by item: how many you carry

local function ItemCount(item)
	local count = C_Item and C_Item.GetItemCount and C_Item.GetItemCount(item) or GetItemCount and GetItemCount(item)
	if ns.IsSecret(count) then return nil end
	return count or 0
end

local function ItemIcon(item)
	return C_Item and C_Item.GetItemIconByID and C_Item.GetItemIconByID(item) or GetItemIcon and GetItemIcon(item)
end
ns.ItemIcon = ItemIcon

-- A scroll that left your bags was used, unless a vendor, the bank, the mail or a trade took it
local function Elsewhere()
	for _, name in ipairs({ "MerchantFrame", "BankFrame", "MailFrame", "TradeFrame", "GuildBankFrame" }) do
		local f = _G[name]
		if f and f:IsShown() then return true end
	end
	return false
end

local function CountScrolls(noticeUse)
	local function Count(item, kind)
		local count = ItemCount(item)
		if count == nil then return end
		local before = scrollCounts[item]
		if noticeUse and before and count < before and not Elsewhere() then
			ns.db.scrollUsed[kind] = time()
			if kind == "imbue" then ns.db.lastImbue = item else ns.db.lastFamiliar = item end
		end
		scrollCounts[item] = count
	end
	for item in pairs(IMBUES) do Count(item, "imbue") end
	for _, item in ipairs(FAMILIARS) do Count(item, "familiar") end
end

local function UsedLately(kind)
	local t = ns.db.scrollUsed[kind]
	return t ~= nil and time() - t < SCROLL_TIME
end

local function MainHandKind()
	local id = GetInventoryItemID("player", MAIN_HAND)
	if not id then return end
	local getInfo = C_Item and C_Item.GetItemInfoInstant or GetItemInfoInstant
	local classID, subclassID = select(6, getInfo(id))
	if classID == 2 then return WEAPON_KIND[subclassID] end
end

-- Your weapon has a temporary enchant on it (when the game hides it, nothing is said)
local function Imbued()
	if not GetWeaponEnchantInfo then return true end
	local has = GetWeaponEnchantInfo()
	if ns.IsSecret(has) then return true end
	return has and true or false
end

-- The imbue for the weapon in your hand: the one you used last if you still carry it, else the best
local function PickImbue(kind)
	local last = ns.db.lastImbue
	if last and IMBUES[last] == kind and (scrollCounts[last] or 0) > 0 then return last end
	local best
	for item, k in pairs(IMBUES) do
		if k == kind and (scrollCounts[item] or 0) > 0 and (not best or item > best) then best = item end
	end
	return best
end

local function PickFamiliar()
	local last = ns.db.lastFamiliar
	if last and (scrollCounts[last] or 0) > 0 then return last end
	for i = #FAMILIARS, 1, -1 do
		if (scrollCounts[FAMILIARS[i]] or 0) > 0 then return FAMILIARS[i] end
	end
end

-- A familiar is out: used in the last hour, or its buff on you when the game shows your buffs
local function FamiliarOut()
	if UsedLately("familiar") then return true end
	if AurasHidden() or not (C_Item and C_Item.GetItemSpell and C_UnitAuras and C_UnitAuras.GetAuraDataByIndex) then return false end
	local names = {}
	for _, item in ipairs(FAMILIARS) do
		local name = C_Item.GetItemSpell(item)
		if name and not ns.IsSecret(name) then names[name] = true end
	end
	for i = 1, 40 do
		local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
		if not aura or ns.IsSecret(aura) or ns.IsSecret(aura.name) then break end
		if names[aura.name] then return true end
	end
	return false
end

-- Scrolls you haven't deciphered yet ("Scroll: KWYJIBO"...): Comprehend Scroll turns each into
-- one of the scrolls above or another. The Season of Discovery ones keep their numbers in
-- Forever, the last four are Forever's own. Each wants some Comprehension: 1, 15, 50 or 175
local ENCIPHERED = {
	[211780] = 1, [211785] = 1, [211786] = 1, [211787] = 1,
	[211784] = 15, [211853] = 15, [211854] = 15, [211855] = 15,
	[213543] = 50, [213544] = 50, [213545] = 50, [213546] = 50, [213547] = 50,
	[281015] = 175, [281016] = 175, [281017] = 175, [281018] = 175,
}
ns.ENCIPHERED = ENCIPHERED
local COMPREHEND = 1296017
local BUNDLE = 277651 -- what Study gives once an hour: a few deciphered scrolls inside

-- Your Comprehension, or nil when the skill list doesn't say
local function Comprehension()
	if not (GetNumSkillLines and GetSkillLineInfo) then return end
	for i = 1, GetNumSkillLines() or 0 do
		local name, header, _, rank = GetSkillLineInfo(i)
		if not header and name == L.COMPREHENSION and type(rank) == "number" and not ns.IsSecret(rank) then
			return rank
		end
	end
end

-- An undeciphered scroll is in the list, or (another number Forever may give it) has that kind of
-- name: "Scroll: " and words in capitals
local function Enciphered(itemID, name)
	if ENCIPHERED[itemID] then return ENCIPHERED[itemID] end
	if type(name) == "string" and not ns.IsSecret(name) and name:match("^Scroll: [%u%p ]+$") then return 1 end
end

-- How many undeciphered scrolls you carry, and where the one to decipher first is: the easiest
-- your Comprehension can read
local function FindEnciphered()
	if not (C_Container and C_Container.GetContainerNumSlots and C_Container.GetContainerItemInfo) then return 0 end
	local skill = Comprehension()
	local count, best = 0, nil
	for bag = 0, NUM_BAG_SLOTS or 4 do
		for slot = 1, C_Container.GetContainerNumSlots(bag) or 0 do
			local info = C_Container.GetContainerItemInfo(bag, slot)
			local id = type(info) == "table" and info.itemID
			if id and not ns.IsSecret(id) then
				local name = info.itemName or (C_Item and C_Item.GetItemNameByID and C_Item.GetItemNameByID(id))
				local needs = Enciphered(id, name)
				if needs and (not skill or needs <= skill) then
					count = count + (info.stackCount or 1)
					if not best or needs < best.needs then best = { bag = bag, slot = slot, item = id, needs = needs } end
				end
			end
		end
	end
	return count, best
end

local function FoodMissing()
	if not ns.db.food.enabled or not ns.IsMage() or inCombat or Dead() then return false end
	local maxLevel = GetMaxPlayerLevel and GetMaxPlayerLevel() or 60
	if UnitLevel("player") >= maxLevel then return false end
	return ends.food == false
end

-- Beside the chat, small, out of combat: the food buff, and the scrolls you carry but haven't used.
-- A click uses the scroll, so the rows are the game's protected buttons: they only change out of combat
local ROW, BIG_ROW, ROW_GAP = 22, 30, 2
local extras = {}
-- The mage's look: a stack of dark bars, all as long as the longest, each with a blue stripe on
-- its left, the icon in a thin blue frame and the text in light ice blue
local MAGE_BLUE = { 0.25, 0.78, 0.92 }
local TEXT_BLUE = { 0.72, 0.9, 1 }
local HEADER_BLUE = { 0.45, 0.85, 1 }
-- A thin font for these: the game's narrow Arial
local ThinFont = ns.ThinFont

local function Extras(expiring)
	local list = {}
	local o = ns.db.scrolls
	-- On top, bigger: the buffs running out, with their time; a click casts them again
	for _, r in ipairs(expiring) do
		list[#list + 1] = { icon = r.icon, text = format("%s  %s", r.name or r.spell or "?", Clock(r.left)),
			spell = r.spell, big = true }
	end
	if ns.unlocked then
		-- Samples to drag around
		if ns.db.food.enabled then list[#list + 1] = { icon = ns.SpellIcon(WELL_FED), text = L.FOOD_MISSING, grey = true, food = true } end
		if o.imbue then list[#list + 1] = { icon = ItemIcon(277485), text = L.IMBUE_MISSING } end
		if o.familiar then list[#list + 1] = { icon = ItemIcon(FAMILIARS[1]), text = L.FAMILIAR_MISSING } end
		if o.decipher then list[#list + 1] = { icon = ItemIcon(211780), text = L.DECIPHER } end
		return list
	end
	if FoodMissing() then list[#list + 1] = { icon = ns.SpellIcon(WELL_FED), text = L.FOOD_MISSING, grey = true, food = true } end
	if not ns.IsMage() or inCombat or Dead() then return list end
	if o.imbue and not UsedLately("imbue") and not Imbued() then
		local kind = MainHandKind()
		local item = kind and PickImbue(kind)
		if item then
			-- If the scroll asks which weapon, the second line answers: the one in your hand
			list[#list + 1] = { icon = ItemIcon(item), text = L.IMBUE_MISSING, item = item,
				macro = format("/use item:%d\n/use %d", item, MAIN_HAND) }
		end
	end
	if o.familiar then
		local item = PickFamiliar()
		if item and not FamiliarOut() then
			list[#list + 1] = { icon = ItemIcon(item), text = L.FAMILIAR_MISSING, item = item, use = "item:" .. item }
		end
	end
	if o.decipher then
		-- Cast Comprehend Scroll on the scroll, as a Disenchant macro does on an item
		local count, scroll = FindEnciphered()
		if scroll and ns.Knows({ COMPREHEND }) then
			local spell = ns.SpellName(COMPREHEND) or "Comprehend Scroll"
			list[#list + 1] = { icon = ItemIcon(scroll.item), item = scroll.item, click = L.CLICK_DECIPHER,
				text = count > 1 and format("%s (%d)", L.DECIPHER, count) or L.DECIPHER,
				macro = format("/cast %s\n/use %d %d", spell, scroll.bag, scroll.slot) }
		end
		if (ItemCount(BUNDLE) or 0) > 0 then
			list[#list + 1] = { icon = ItemIcon(BUNDLE), text = L.OPEN_BUNDLE, item = BUNDLE, use = "item:" .. BUNDLE }
		end
	end
	-- Gear wearing out, bags filling up (Repair.lua)
	for _, r in ipairs(ns.RepairReminders()) do
		list[#list + 1] = { icon = r.icon, text = r.text }
	end
	-- Reagents running low (Reagents.lua): how many are left; the tooltip says what spends them
	for _, r in ipairs(ns.ReagentReminders()) do
		list[#list + 1] = { icon = ItemIcon(r.item), text = r.text, item = r.item, click = r.uses }
	end
	return list
end

local function Extra_OnEnter(self)
	if self.item then
		GameTooltip:SetOwner(self, "ANCHOR_TOP")
		if GameTooltip.SetItemByID then GameTooltip:SetItemByID(self.item) end
		GameTooltip:AddLine(self.clickText or L.CLICK_USE, 0.4, 0.8, 1)
		GameTooltip:Show()
	elseif self.spellName then
		GameTooltip:SetOwner(self, "ANCHOR_TOP")
		GameTooltip:AddLine(self.spellName, 1, 1, 1)
		GameTooltip:AddLine(L.CLICK_CAST, 0.4, 0.8, 1)
		GameTooltip:Show()
	elseif self.isFood then
		GameTooltip:SetOwner(self, "ANCHOR_TOP")
		GameTooltip:AddLine(L.CLICK_FOOD, 0.4, 0.8, 1)
		GameTooltip:Show()
	end
end

-- The XP food in your bags: food whose tooltip promises Well Fed (in Forever, cooked food, which
-- also gives +5% XP from kills). Each item is looked at once its tooltip has loaded
local xpFood = {} -- by item: true / false
local foodStock = {} -- { id, count }, in the order of your bags

local function IsXPFood(id, bag, slot)
	if xpFood[id] ~= nil then return xpFood[id] end
	local getInfo = C_Item and C_Item.GetItemInfoInstant or GetItemInfoInstant
	local classID, subclassID = select(6, getInfo(id))
	-- Food & Drink only
	if classID ~= 0 or subclassID ~= 5 then
		xpFood[id] = false
		return false
	end
	if not (C_TooltipInfo and C_TooltipInfo.GetBagItem) then return false end
	local data = C_TooltipInfo.GetBagItem(bag, slot)
	if type(data) ~= "table" or type(data.lines) ~= "table" then return false end
	local use = strlower(ITEM_SPELL_TRIGGER_ONUSE or "Use:")
	local loaded = false
	for _, line in ipairs(data.lines) do
		local text = line.leftText
		if type(text) == "string" and not ns.IsSecret(text) then
			local low = strlower(text)
			for _, word in ipairs(fedWords) do
				if low:find(word, 1, true) then
					xpFood[id] = true
					return true
				end
			end
			-- What eating it does, written out: the game has its text
			if low:sub(1, #use) == use and #low > #use + 8 then loaded = true end
		end
	end
	-- Read before the game had loaded what it does: looked at again next time, not written off
	if loaded then xpFood[id] = false end
	return false
end

local function ScanFood()
	wipe(foodStock)
	if not (C_Container and C_Container.GetContainerNumSlots and C_Container.GetContainerItemInfo) then return end
	local byID = {}
	for bag = 0, NUM_BAG_SLOTS or 4 do
		for slot = 1, C_Container.GetContainerNumSlots(bag) or 0 do
			local info = C_Container.GetContainerItemInfo(bag, slot)
			local id = type(info) == "table" and info.itemID
			if id and not ns.IsSecret(id) and IsXPFood(id, bag, slot) then
				local entry = byID[id]
				if not entry then
					entry = { id = id, count = 0 }
					byID[id] = entry
					foodStock[#foodStock + 1] = entry
				end
				local count = info.stackCount
				entry.count = entry.count + (type(count) == "number" and not ns.IsSecret(count) and count or 1)
			end
		end
	end
end

-- Clicking the food row opens the list beside it; a click on one of them eats it. Out of combat,
-- like the row itself
local menu = CreateFrame("Frame", "MageGodFoodMenu", UIParent)
menu:SetSize(120, 22)
menu:Hide()
local menuRows = {}
local menuAnchor

local function MenuRow_OnEnter(self)
	if not self.itemID then return end
	GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
	if GameTooltip.SetItemByID then GameTooltip:SetItemByID(self.itemID) end
	GameTooltip:AddLine(L.CLICK_EAT, 0.4, 0.8, 1)
	GameTooltip:Show()
end

local function MenuRow(i)
	local b = menuRows[i]
	if b then return b end
	b = CreateFrame("Button", "MageGodFoodMenu" .. i, menu, "SecureActionButtonTemplate")
	b:RegisterForClicks("AnyUp", "AnyDown")
	b.back = b:CreateTexture(nil, "BACKGROUND")
	b.back:SetAllPoints()
	b.back:SetColorTexture(0.02, 0.04, 0.09, 0.85)
	b.stripe = b:CreateTexture(nil, "BORDER")
	b.stripe:SetPoint("TOPLEFT")
	b.stripe:SetPoint("BOTTOMLEFT")
	b.stripe:SetWidth(2)
	b.stripe:SetColorTexture(MAGE_BLUE[1], MAGE_BLUE[2], MAGE_BLUE[3], 1)
	b.icon = b:CreateTexture(nil, "ARTWORK")
	b.icon:SetPoint("LEFT", 6, 0)
	b.icon:SetSize(ROW - 6, ROW - 6)
	b.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	b.edge = b:CreateTexture(nil, "BORDER")
	b.edge:SetPoint("TOPLEFT", b.icon, -1, 1)
	b.edge:SetPoint("BOTTOMRIGHT", b.icon, 1, -1)
	b.edge:SetColorTexture(MAGE_BLUE[1], MAGE_BLUE[2], MAGE_BLUE[3], 0.9)
	b.text = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
	b.text:SetPoint("LEFT", b.icon, "RIGHT", 7, 0)
	b.text:SetShadowOffset(1, -1)
	b.text:SetShadowColor(0, 0, 0, 1)
	b.text:SetTextColor(TEXT_BLUE[1], TEXT_BLUE[2], TEXT_BLUE[3])
	b:SetHighlightTexture("Interface\\Buttons\\UI-Listbox-Highlight2", "ADD")
	b:SetScript("OnEnter", MenuRow_OnEnter)
	b:SetScript("OnLeave", GameTooltip_Hide)
	-- Once you've picked one the list goes (the game has eaten it by then)
	b:HookScript("OnClick", function(self, _, down)
		if not down and self.itemID and not InCombatLockdown() then menu:Hide() end
	end)
	menuRows[i] = b
	return b
end

local function FillMenu()
	local list = {}
	for _, f in ipairs(foodStock) do
		local name = C_Item and C_Item.GetItemNameByID and C_Item.GetItemNameByID(f.id)
		list[#list + 1] = { id = f.id, text = format("%s  x%d", name or "?", f.count), icon = ItemIcon(f.id) }
	end
	if #list == 0 then list[1] = { text = L.NO_XP_FOOD, icon = ns.SpellIcon(WELL_FED) } end
	local width = 120
	for i, r in ipairs(list) do
		local b = MenuRow(i)
		b:ClearAllPoints()
		b:SetPoint("TOPLEFT", 0, -(i - 1) * (ROW + ROW_GAP))
		b:SetHeight(ROW)
		ThinFont(b.text, 13)
		b.text:SetText(r.text)
		b.icon:SetTexture(r.icon)
		b.icon:SetDesaturated(r.id == nil)
		b.itemID = r.id
		local use = r.id and ("item:" .. r.id) or nil
		if b:GetAttribute("type") ~= (use and "item" or nil) then b:SetAttribute("type", use and "item" or nil) end
		if b:GetAttribute("item") ~= use then b:SetAttribute("item", use) end
		width = max(width, b.text:GetStringWidth() + ROW + 24)
		b:Show()
	end
	for i = 1, #list do menuRows[i]:SetWidth(width) end
	for i = #list + 1, #menuRows do menuRows[i]:Hide() end
	menu:SetSize(width, #list * (ROW + ROW_GAP) - ROW_GAP)
end

local function ToggleFoodMenu(row)
	if InCombatLockdown() then return end
	if menu:IsShown() then
		menu:Hide()
		return
	end
	ScanFood()
	FillMenu()
	menuAnchor = row
	menu:ClearAllPoints()
	menu:SetPoint("TOPLEFT", row, "TOPRIGHT", 4, 0)
	menu:Show()
end
ns.ToggleFoodMenu = ToggleFoodMenu

-- The armors to pick from, as bars beside the armor reminder; a click on one puts it on
local armorMenu = CreateFrame("Frame", "MageGodArmorMenu", UIParent)
armorMenu:SetFrameStrata("DIALOG")
armorMenu:Hide()
local armorRows = {}

local function ArmorRow(i)
	local b = armorRows[i]
	if b then return b end
	b = CreateFrame("Button", "MageGodArmorMenu" .. i, armorMenu, "SecureActionButtonTemplate")
	b:RegisterForClicks("AnyUp", "AnyDown")
	b:SetAttribute("type", "spell")
	b:SetAttribute("unit", "player")
	b.back = b:CreateTexture(nil, "BACKGROUND")
	b.back:SetAllPoints()
	b.back:SetColorTexture(0.02, 0.04, 0.09, 0.85)
	b.stripe = b:CreateTexture(nil, "BORDER")
	b.stripe:SetPoint("TOPLEFT")
	b.stripe:SetPoint("BOTTOMLEFT")
	b.stripe:SetWidth(2)
	b.stripe:SetColorTexture(MAGE_BLUE[1], MAGE_BLUE[2], MAGE_BLUE[3], 1)
	b.icon = b:CreateTexture(nil, "ARTWORK")
	b.icon:SetPoint("LEFT", 6, 0)
	b.icon:SetSize(ROW - 6, ROW - 6)
	b.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	b.edge = b:CreateTexture(nil, "BORDER")
	b.edge:SetPoint("TOPLEFT", b.icon, -1, 1)
	b.edge:SetPoint("BOTTOMRIGHT", b.icon, 1, -1)
	b.edge:SetColorTexture(MAGE_BLUE[1], MAGE_BLUE[2], MAGE_BLUE[3], 0.9)
	b.text = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
	b.text:SetPoint("LEFT", b.icon, "RIGHT", 7, 0)
	b.text:SetShadowOffset(1, -1)
	b.text:SetShadowColor(0, 0, 0, 1)
	b.text:SetTextColor(TEXT_BLUE[1], TEXT_BLUE[2], TEXT_BLUE[3])
	b:SetHighlightTexture("Interface\\Buttons\\UI-Listbox-Highlight2", "ADD")
	-- Once you've picked one the list goes
	b:HookScript("OnClick", function(_, _, down)
		if not down and not InCombatLockdown() then armorMenu:Hide() end
	end)
	armorRows[i] = b
	return b
end

function ns.ToggleArmorMenu(anchor)
	if InCombatLockdown() then return end
	if armorMenu:IsShown() then
		armorMenu:Hide()
		return
	end
	local list = KnownArmors()
	local width = 120
	for i, key in ipairs(list) do
		local b = ArmorRow(i)
		local name = ns.SpellName(SPELLS[key][1]) or key
		b:ClearAllPoints()
		b:SetPoint("TOPLEFT", 0, -(i - 1) * (ROW + ROW_GAP))
		b:SetHeight(ROW)
		ThinFont(b.text, 13)
		b.text:SetText(name)
		b.icon:SetTexture(ns.SpellIcon(SPELLS[key][1]))
		if b:GetAttribute("spell") ~= name then b:SetAttribute("spell", name) end
		width = max(width, b.text:GetStringWidth() + ROW + 24)
		b:Show()
	end
	for i = 1, #list do armorRows[i]:SetWidth(width) end
	for i = #list + 1, #armorRows do armorRows[i]:Hide() end
	armorMenu:SetSize(width, max(#list * (ROW + ROW_GAP) - ROW_GAP, 1))
	-- Where the reminder is now, on the screen, so the row can still move in a fight
	armorMenu:ClearAllPoints()
	local right, top = anchor:GetRight(), anchor:GetTop()
	if right and top and not ns.IsSecret(right) then
		armorMenu:SetPoint("TOPLEFT", UIParent, "BOTTOMLEFT", right + 4, top)
	else
		armorMenu:SetPoint("TOPLEFT", anchor, "TOPRIGHT", 4, 0)
	end
	armorMenu:Show()
end
ns.ArmorMenu = function() return armorMenu, armorRows end

local function Extra(i)
	local b = extras[i]
	if b then return b end
	b = CreateFrame("Button", "MageGodExtra" .. i, food, "SecureActionButtonTemplate")
	b:RegisterForClicks("AnyUp", "AnyDown")
	b.back = b:CreateTexture(nil, "BACKGROUND")
	b.back:SetAllPoints()
	b.back:SetColorTexture(0.02, 0.04, 0.09, 0.8)
	b.stripe = b:CreateTexture(nil, "BORDER")
	b.stripe:SetPoint("TOPLEFT")
	b.stripe:SetPoint("BOTTOMLEFT")
	b.stripe:SetWidth(2)
	b.stripe:SetColorTexture(MAGE_BLUE[1], MAGE_BLUE[2], MAGE_BLUE[3], 1)
	b.icon = b:CreateTexture(nil, "ARTWORK")
	b.icon:SetPoint("LEFT", 6, 0)
	b.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
	b.edge = b:CreateTexture(nil, "BORDER")
	b.edge:SetPoint("TOPLEFT", b.icon, -1, 1)
	b.edge:SetPoint("BOTTOMRIGHT", b.icon, 1, -1)
	b.edge:SetColorTexture(MAGE_BLUE[1], MAGE_BLUE[2], MAGE_BLUE[3], 0.9)
	b.text = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
	b.text:SetPoint("LEFT", b.icon, "RIGHT", 7, 0)
	b.text:SetShadowOffset(1, -1)
	b.text:SetShadowColor(0, 0, 0, 1)
	b:SetScript("OnEnter", Extra_OnEnter)
	-- The food row opens the list of your XP food
	b:HookScript("OnClick", function(self, _, down)
		if not down and self.isFood then ToggleFoodMenu(self) end
	end)
	b:SetScript("OnLeave", GameTooltip_Hide)
	extras[i] = b
	return b
end

local function SetAction(b, r)
	local kind = r.macro and "macro" or r.use and "item" or r.spell and "spell" or nil
	if b:GetAttribute("type") ~= kind then b:SetAttribute("type", kind) end
	-- A row that did something else before keeps nothing of it
	if b:GetAttribute("macrotext") ~= r.macro then b:SetAttribute("macrotext", r.macro) end
	if b:GetAttribute("item") ~= r.use then b:SetAttribute("item", r.use) end
	local spell = kind == "spell" and r.spell or nil
	if b:GetAttribute("spell") ~= spell then b:SetAttribute("spell", spell) end
	-- On you, not on whoever you have targeted
	local unit = spell and "player" or nil
	if b:GetAttribute("unit") ~= unit then b:SetAttribute("unit", unit) end
end

function UpdateExtras(expiring)
	if InCombatLockdown() then return end
	local list = Extras(expiring)
	local width, y = 120, 0
	local foodRow = false
	for i, r in ipairs(list) do
		local b = Extra(i)
		local height = r.big and BIG_ROW or ROW
		b:ClearAllPoints()
		b:SetPoint("TOPLEFT", 0, -y)
		b:SetHeight(height)
		y = y + height + ROW_GAP
		local side = height - 6
		b.icon:SetSize(side, side)
		b.icon:SetTexture(r.icon)
		b.icon:SetDesaturated(r.grey or false)
		ThinFont(b.text, r.big and 16 or 13)
		local colour = r.big and HEADER_BLUE or TEXT_BLUE
		b.text:SetTextColor(colour[1], colour[2], colour[3])
		b.text:SetText(r.text)
		b.item, b.spellName = r.item, not r.item and r.spell or nil
		b.clickText = r.click
		b.isFood = r.food
		-- The open list follows its row, and goes with it
		if r.food and menu:IsShown() then
			if menuAnchor ~= b then
				menuAnchor = b
				menu:ClearAllPoints()
				menu:SetPoint("TOPLEFT", b, "TOPRIGHT", 4, 0)
			end
			foodRow = true
		end
		SetAction(b, r)
		width = max(width, b.text:GetStringWidth() + side + 24)
		b:Show()
	end
	-- All as long as the longest, so they stack as one block
	for i = 1, #list do extras[i]:SetWidth(width) end
	for i = #list + 1, #extras do extras[i]:Hide() end
	if not foodRow then menu:Hide() end
	food:SetSize(width, max(y - ROW_GAP, ROW))
	food:SetShown(#list > 0)
end

function ns.UpdateBuffs()
	local list, expiring = {}, {}
	if ns.unlocked then
		-- Samples to drag around
		list = {
			{ icon = ns.SpellIcon(SPELLS.frost[1]), left = 0 },
			{ icon = ns.SpellIcon(ns.GEMS[1].spell), left = 0, gem = true },
		}
		expiring[1] = { icon = ns.SpellIcon(SPELLS.intellect[1]), left = 95, name = ns.SpellName(SPELLS.intellect[1]) }
	else
		-- Up here what's missing; out of combat what's running out goes beside the chat, bigger
		for _, r in ipairs(Reminders()) do
			if r.left > 0 and not inCombat then expiring[#expiring + 1] = r else list[#list + 1] = r end
		end
	end
	for i, r in ipairs(list) do
		local b = Icon(i)
		b.icon:SetTexture(r.icon)
		-- Grey while it's missing, in colour with its time left while it runs out
		b.icon:SetDesaturated(r.left == 0)
		b.text:SetText(r.label or (r.left > 0 and Clock(r.left) or ""))
		b:Show()
		if not b.pulse:IsPlaying() then b.pulse:Play() end
	end
	for i = #list + 1, #icons do
		icons[i].pulse:Stop()
		icons[i]:Hide()
	end
	row:SetWidth(max(#list, 1) * (SIZE + GAP) - GAP)
	row:SetShown(#list > 0)
	UpdateCasters(list)
	UpdateExtras(expiring)
	ns.UpdateBarrier()
end

-- /magegod bufos: what the addon sees
local function Describe(slot, label)
	local e = ends[slot]
	if e == nil then return L.BUFF_UNKNOWN end
	if e == false then return L.BUFF_NONE end
	local key = wearing[slot]
	local name = key and ns.SpellName(SPELLS[key][1]) or label or "?"
	if e == math.huge then return format(L.BUFF_ON, name) end
	return format(L.BUFF_LEFT, name, Clock(max(e - GetTime(), 0)))
end

local function BuffsReport()
	Learn()
	local seen = Scan()
	local gem = L.GEM_NONE
	for i = #ns.GEMS, 1, -1 do
		if gemKnown[i] then
			gem = format(L.GEM_HAVE, ns.SpellName(ns.GEMS[i].spell) or "?", GemCount(ns.GEMS[i].item))
			break
		end
	end
	local fed = Describe("food", wellFedName)
	local maxLevel = GetMaxPlayerLevel and GetMaxPlayerLevel() or 60
	if ends.food == false then fed = UnitLevel("player") >= maxLevel and L.FOOD_MAX_LEVEL or L.FOOD_OFF end
	ns.Print(format(L.BUFFS_REPORT, Describe("armor"),
		known.intellect and Describe("intellect") or L.BUFF_NOT_KNOWN, gem, fed))
	-- The food it took for not giving XP gets a fresh look
	for id, yes in pairs(xpFood) do
		if not yes then xpFood[id] = nil end
	end
	ScanFood()
	local stock = {}
	for _, f in ipairs(foodStock) do
		local name = C_Item and C_Item.GetItemNameByID and C_Item.GetItemNameByID(f.id)
		stock[#stock + 1] = format("%s x%d", name or ("item " .. f.id), f.count)
	end
	ns.Print(format(L.FOOD_STOCK, #stock > 0 and table.concat(stock, ", ") or L.BUFF_NONE))
	if not seen then
		ns.Print(L.BUFFS_HIDDEN)
		return
	end
	local names = {}
	for i = 1, 40 do
		local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
		if not aura then break end
		names[#names + 1] = aura.name
	end
	ns.Print(format(L.BUFFS_SEEN, #names > 0 and table.concat(names, ", ") or L.BUFF_NONE))
end
ns.commands.buffs = BuffsReport
ns.commands.bufos = BuffsReport

-- For the tests
function ns.BuffState(slot)
	return ends[slot], wearing[slot]
end

local BarrierCast

local function Cast(spellID)
	local name = ns.SpellName(spellID)
	local key = name and byName[name]
	if BarrierCast(spellID, name) then return end
	if not key then
		-- A gem conjured: the bags say so a moment later
		if name and gemNames[name] then C_Timer.After(0.5, ns.UpdateBuffs) end
		return
	end
	local slot = SLOT[key]
	if slot == "armor" then ns.db.lastArmor = key end
	-- Out of combat your buffs say whether it went on you (Arcane Intellect can go on anyone)
	if Scan() then
		ns.UpdateBuffs()
		return
	end
	-- In combat they're hidden: what you cast is taken as being on you
	ends[slot] = GetTime() + (lasts[key] or DURATION[key])
	wearing[slot] = key
	ns.UpdateBuffs()
end

-- What's left of the shield on you, each in its own colour: Ice Barrier, Mana Shield, Fire Ward,
-- Frost Ward, a protection potion, or a priest's Power Word: Shield. Forever hides how much a
-- shield absorbs, but lets the addon hand it to a bar and its text, which the game fills in
-- itself. The bar starts full at what the shield absorbs as it goes on, and goes when it ends.
-- The game only gives the total of every shield on you: with two at once the bar shows both, in
-- the colour of the last one
local SHIELDS = {
	{ key = "barrier", ids = { 11426, 13031, 13032, 13033 }, seconds = 60 }, -- Ice Barrier
	{ key = "manaShield", ids = { 1463, 8494, 8495, 10191, 10192, 10193 }, seconds = 60 },
	{ key = "fireWard", ids = { 543, 8457, 8458, 10223, 10225 }, seconds = 30 },
	{ key = "frostWard", ids = { 6143, 8461, 8462, 10177, 28609 }, seconds = 30 },
	-- Cast on you by a priest: the bar only sees it when the game lets it read your shields
	{ key = "powerWord", ids = { 17, 592, 600, 3747, 6065, 6066, 10898, 10899, 10900, 10901 }, seconds = 30 },
	-- The protection potions, two minutes each: by their numbers only, as other buffs share their
	-- names (a priest's Shadow Protection)
	{ key = "fire", ids = { 7233, 17543 }, seconds = 120, potion = true },
	{ key = "frost", ids = { 7239, 17544 }, seconds = 120, potion = true },
	{ key = "nature", ids = { 7254, 17546 }, seconds = 120, potion = true },
	{ key = "shadow", ids = { 7242, 17548 }, seconds = 120, potion = true },
	{ key = "arcane", ids = { 17549 }, seconds = 120, potion = true },
	{ key = "holy", ids = { 7245, 17545 }, seconds = 120, potion = true },
}
ns.SHIELDS = SHIELDS
local BARRIER_TIME = 60 -- a shield the addon can't tell: a minute until the game says otherwise
local shieldById, shieldByName = {}, {}
for _, shield in ipairs(SHIELDS) do
	for _, id in ipairs(shield.ids) do shieldById[id] = shield end
end
local barrier
local barrierEnds = 0 -- GetTime() when the shield runs out
local barrierFull -- what it absorbed at the start: may be hidden
local current -- the shield the bar shows: its colour

local function Absorbs()
	return UnitGetTotalAbsorbs and UnitGetTotalAbsorbs("player")
end

local function LearnBarriers()
	wipe(shieldByName)
	for _, shield in ipairs(SHIELDS) do
		local name = not shield.potion and ns.SpellName(shield.ids[1])
		if name then shieldByName[name] = shield end
	end
end

-- Its colour: Ice Barrier's is the bar's own, the others each their own (the potions their school's)
local function ShieldColor(shield)
	local o = ns.db.barrier
	return shield and shield.key ~= "barrier" and o.colors[shield.key] or o.color
end

local function Paint()
	local c = ShieldColor(current)
	barrier.status:SetStatusBarColor(c.r, c.g, c.b)
end

-- How long the shield has left, from your buffs when the game shows them
local function BarrierLeft(name)
	if AurasHidden() or not (C_UnitAuras and C_UnitAuras.GetAuraDataByIndex) then return end
	for i = 1, 40 do
		local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
		if not aura or ns.IsSecret(aura) or ns.IsSecret(aura.name) then return end
		if aura.name == name then
			local expires = aura.expirationTime
			if type(expires) == "number" and not ns.IsSecret(expires) and expires > 0 then return expires - GetTime() end
			return
		end
	end
end

local function BarrierStart(id, name, shield)
	local amount = Absorbs()
	if not ns.IsSecret(amount) and amount == nil then return end
	current = shield
	barrierFull = amount
	barrierEnds = GetTime() + (BarrierLeft(name) or shield.seconds)
	barrier.icon:SetTexture(ns.SpellIcon(id))
	barrier.status:SetMinMaxValues(0, amount)
	Paint()
	ns.UpdateBarrier()
end

-- A shield cast or a potion drunk: the bar starts a moment later, once the game has put it on you
function BarrierCast(spellID, name)
	local shield = shieldById[spellID] or name and shieldByName[name]
	if not shield or shield.potion and not ns.db.barrier.potions then return false end
	C_Timer.After(0.2, function() BarrierStart(spellID, name, shield) end)
	return true
end

-- A shield the addon didn't see go on (a priest's): which one, when the game shows your buffs.
-- false: only a potion you chose to leave out
local function Identify()
	if AurasHidden() or not (C_UnitAuras and C_UnitAuras.GetAuraDataByIndex) then return end
	for i = 1, 40 do
		local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
		if not aura or ns.IsSecret(aura) or ns.IsSecret(aura.name) or ns.IsSecret(aura.spellId) then return end
		local shield = shieldById[aura.spellId] or shieldByName[aura.name]
		if shield and shield.potion and not ns.db.barrier.potions then return false end
		if shield then
			current = shield
			barrier.icon:SetTexture(ns.SpellIcon(aura.spellId or shield.ids[1]))
			local expires = aura.expirationTime
			if type(expires) == "number" and not ns.IsSecret(expires) and expires > 0 then
				barrierEnds = expires
			end
			Paint()
			return shield
		end
	end
end

function ns.StyleBarrier()
	local o = ns.db.barrier
	barrier:SetSize(o.width, o.height)
	local px = ns.OnePixel(barrier)
	barrier.edge:ClearAllPoints()
	barrier.edge:SetPoint("TOPLEFT", -px, px)
	barrier.edge:SetPoint("BOTTOMRIGHT", px, -px)
	-- The shield's icon on its own square tag against the bar's left end, as MP5 sits by the mana
	-- bar: their black edges one line between them
	barrier.tag:SetSize(o.height, o.height)
	barrier.tag:ClearAllPoints()
	barrier.tag:SetPoint("RIGHT", barrier, "LEFT", -px, 0)
	barrier.tagEdge:ClearAllPoints()
	barrier.tagEdge:SetPoint("TOPLEFT", -px, px)
	barrier.tagEdge:SetPoint("BOTTOMRIGHT", px, -px)
	barrier.tag:SetShown(o.icon)
	Paint()
	local size = max(floor(o.height * 0.9), 10)
	ThinFont(barrier.text, size)
	ThinFont(barrier.time, size)
end

function ns.UpdateBarrier()
	local o = ns.db.barrier
	if ns.unlocked then
		-- A sample to drag and size
		barrier.status:SetMinMaxValues(0, 811)
		barrier.status:SetValue(600)
		barrier.text:SetText(o.text and "600" or "")
		barrier.time:SetText(o.time and "42" or "")
		barrier:SetShown(o.enabled)
		return
	end
	local now = GetTime()
	local amount = Absorbs()
	-- A hidden value can't even be compared with nil: ask first
	local hidden = ns.IsSecret(amount)
	local on = o.enabled and ns.IsMage() and (hidden or amount ~= nil) and now < barrierEnds
	-- When the game lets the addon read it: gone at nothing, and a shield it didn't see you
	-- cast (a priest's) shows too
	if not hidden and amount ~= nil then
		if amount <= 0 then
			on, barrierEnds = false, 0
		elseif o.enabled and ns.IsMage() then
			if now >= barrierEnds then
				current = nil
				if Identify() == false then
					barrier:Hide()
					return
				end
				-- The time its buff gives, else a minute
				if barrierEnds <= now then barrierEnds = now + BARRIER_TIME end
				barrierFull = amount
				barrier.status:SetMinMaxValues(0, amount)
				Paint()
			elseif not ns.IsSecret(barrierFull) and barrierFull and amount > barrierFull then
				barrierFull = amount
				barrier.status:SetMinMaxValues(0, amount)
			end
			on = true
		end
	end
	if not on then
		barrier:Hide()
		return
	end
	barrier.status:SetValue(amount)
	if o.text then barrier.text:SetFormattedText("%d", amount) else barrier.text:SetText("") end
	-- A potion's two minutes as 2:00, the rest in seconds
	local left = ceil(barrierEnds - now)
	barrier.time:SetText(o.time and (left >= 100 and Clock(left) or format("%d", left)) or "")
	barrier:Show()
end

barrier = CreateFrame("Frame", "MageGodBarrier", UIParent)
barrier:SetSize(160, 14)
barrier:Hide()
-- Flat and square, like the mana bar: a plain fill on a dark back, a black edge one screen pixel
-- thin, and thin letters with a shadow
barrier.edge = barrier:CreateTexture(nil, "BACKGROUND", nil, -1)
barrier.edge:SetColorTexture(0, 0, 0, 1)
barrier.status = CreateFrame("StatusBar", nil, barrier)
barrier.status:SetAllPoints()
barrier.status:SetStatusBarTexture("Interface\\Buttons\\WHITE8X8")
local barrierBack = barrier.status:CreateTexture(nil, "BACKGROUND")
barrierBack:SetAllPoints()
barrierBack:SetColorTexture(0.02, 0.04, 0.09, 0.8)
barrier.text = barrier.status:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
barrier.text:SetPoint("CENTER")
barrier.time = barrier.status:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
barrier.time:SetPoint("RIGHT", -3, 0)
barrier.time:SetTextColor(0.8, 0.92, 1)
for _, text in ipairs({ barrier.text, barrier.time }) do
	text:SetShadowOffset(1, -1)
	text:SetShadowColor(0, 0, 0, 1)
end
barrier.tag = CreateFrame("Frame", nil, barrier)
barrier.tagEdge = barrier.tag:CreateTexture(nil, "BACKGROUND", nil, -1)
barrier.tagEdge:SetColorTexture(0, 0, 0, 1)
barrier.icon = barrier.tag:CreateTexture(nil, "ARTWORK")
barrier.icon:SetAllPoints()
barrier.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)

row = CreateFrame("Frame", "MageGodBuffs", UIParent)
row:SetSize(SIZE, SIZE)
row:Hide()

-- The food and scroll reminders are small: reminders, not alarms
food = CreateFrame("Frame", "MageGodFood", UIParent)
food:SetSize(150, 20)
food:Hide()
-- Until you move it, beside the chat, out of the way
function food:placeDefault()
	if not ChatFrame1 then return false end
	self:ClearAllPoints()
	self:SetPoint("LEFT", ChatFrame1, "RIGHT", 25, 0)
	return true
end

-- Gathering.lua says when your tracking changes or you go in or out of an instance, and
-- Reagents.lua when your bags or spells change
function ns.GatherChanged()
	if db then ns.UpdateBuffs() end
end
ns.ReagentsChanged = ns.GatherChanged
ns.GroupBuffsChanged = ns.GatherChanged
ns.RepairChanged = ns.GatherChanged

local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(self, event, unit, _, spellID)
	if event == "PLAYER_LOGIN" then
		db = ns.db.buffs
		Learn()
		Scan()
		CountScrolls(false)
		ScanFood()
		ns.Movable(row, "buffs", { "CENTER", "CENTER", 0, 160 }, L.BUFFS_NAME)
		ns.Movable(food, "food", { "CENTER", "CENTER", 0, 125 }, L.FOOD_NAME)
		LearnBarriers()
		barrier.icon:SetTexture(ns.SpellIcon(SHIELDS[1].ids[1]))
		ns.StyleBarrier()
		ns.Movable(barrier, "barrier", { "CENTER", "CENTER", 0, -95 }, L.BARRIER_NAME)
		table.insert(ns.refreshers, function() ns.StyleBarrier() ns.UpdateBuffs() end)
		self:RegisterUnitEvent("UNIT_AURA", "player")
		self:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "player")
		self:RegisterEvent("PLAYER_REGEN_DISABLED")
		self:RegisterEvent("PLAYER_REGEN_ENABLED")
		self:RegisterEvent("SPELLS_CHANGED")
		self:RegisterEvent("BAG_UPDATE_DELAYED")
		self:RegisterEvent("PLAYER_LEVEL_UP")
		self:RegisterEvent("PLAYER_DEAD")
		self:RegisterEvent("PLAYER_UNGHOST")
		self:RegisterEvent("PLAYER_ALIVE")
		self:RegisterUnitEvent("UNIT_ABSORB_AMOUNT_CHANGED", "player")
		self:RegisterEvent("UI_SCALE_CHANGED")
		self:RegisterEvent("DISPLAY_SIZE_CHANGED")
		-- The time left ticks on its own
		local since = 0
		self:SetScript("OnUpdate", function(_, dt)
			since = since + dt
			if since < 0.25 then return end
			since = 0
			ns.UpdateBuffs()
		end)
	elseif event == "UNIT_ABSORB_AMOUNT_CHANGED" then
		ns.UpdateBarrier()
		return
	elseif event == "UI_SCALE_CHANGED" or event == "DISPLAY_SIZE_CHANGED" then
		-- A screen pixel is another size now
		ns.StyleBarrier()
		return
	elseif event == "UNIT_AURA" then
		Scan()
	elseif event == "UNIT_SPELLCAST_SUCCEEDED" then
		if unit ~= "player" or not spellID or ns.IsSecret(spellID) then return end
		Cast(spellID)
		return
	elseif event == "BAG_UPDATE_DELAYED" then
		CountScrolls(true)
		ScanFood()
		if menu:IsShown() and not InCombatLockdown() then FillMenu() end
	elseif event == "PLAYER_REGEN_DISABLED" then
		inCombat = true
		-- Before the game locks its buttons for the fight
		menu:Hide()
		armorMenu:Hide()
	elseif event == "PLAYER_REGEN_ENABLED" then
		inCombat = false
		Scan()
	elseif event == "SPELLS_CHANGED" or event == "PLAYER_LEVEL_UP" then
		Learn()
		LearnBarriers()
	end
	ns.UpdateBuffs()
end)
