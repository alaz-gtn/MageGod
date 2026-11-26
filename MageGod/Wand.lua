local _, ns = ...
local L = ns.L

-- Your wand's swing timer: one bar, like HunterGod's for Auto Shot, with the wand's icon on a tag at
-- its left. Forever tells addons when each ranged shot goes and how long the next one takes
-- (PLAYER_SWING), so no combat log is needed. The bar starts dim, lights up as the next shot comes
-- and flashes when it goes; grey when your target is out of reach. If the game says nothing of
-- the wand's shots, Shoot starting and stopping (the auto-repeat events) keep it going at your
-- wand's speed instead
local RANGED = 2 -- Enum.PlayerSwingType
local SLOT = 18
local LINGER = 2 -- seconds the bar stays once the last shot is done
local FLASH = 0.18
local DEFAULT_POINT = { "CENTER", "CENTER", 0, -120 }
local SAMPLE_SPEED = 1.6
local TEST_SECONDS = 6

local db, bar
local swing -- { start, duration, guessed }
local inRange -- nil when the game can't tell
local shooting = false -- Shoot on (auto-repeat)
local heard = false -- the game has told the addon of a wand shot: no need to guess
local sampleUntil = 0

local function Sampling()
	return ns.unlocked or GetTime() < sampleUntil
end

local function HasWand()
	return GetInventoryItemID and GetInventoryItemID("player", SLOT) ~= nil
end

local function Speed()
	local speed = UnitRangedDamage and UnitRangedDamage("player")
	if type(speed) ~= "number" or ns.IsSecret(speed) or speed <= 0 then return SAMPLE_SPEED end
	return speed
end

function ns.StyleWand()
	if not bar then return end
	local px = ns.OnePixel(bar)
	local w, h = db.width, db.height
	local tagWidth = db.icon and h + 3 or 0
	bar:SetSize(tagWidth + w, h)
	bar.tag:ClearAllPoints()
	bar.tag:SetPoint("TOPLEFT")
	bar.tag:SetSize(h, h)
	bar.tag:SetShown(db.icon)
	bar.tagEdge:SetShown(db.icon)
	bar.tagEdge:ClearAllPoints()
	bar.tagEdge:SetPoint("TOPLEFT", bar.tag, -px, px)
	bar.tagEdge:SetPoint("BOTTOMRIGHT", bar.tag, px, -px)
	bar.tag:SetTexture(GetInventoryItemTexture and GetInventoryItemTexture("player", SLOT)
		or "Interface\\Icons\\INV_Wand_07")
	bar.back:ClearAllPoints()
	bar.back:SetPoint("TOPRIGHT")
	bar.back:SetSize(w, h)
	bar.edge:ClearAllPoints()
	bar.edge:SetPoint("TOPLEFT", bar.back, -px, px)
	bar.edge:SetPoint("BOTTOMRIGHT", bar.back, px, -px)
	bar.shine:SetHeight(px)
	ns.ThinFont(bar.time, max(floor(h * 0.85), 9))
	bar.time:SetShadowOffset(1, -1)
	bar.time:SetShadowColor(0, 0, 0, 1)
	bar.time:SetTextColor(1, 1, 1)
	bar.time:SetShown(db.time)
	ns.UpdateWand()
end

-- The bar at this moment: how far the shot has come, lit up as it nears
local function Paint(now)
	local w = db.width
	local p, left = 1, 0
	if swing and swing.duration > 0 then
		p = min(max((now - swing.start) / swing.duration, 0), 1)
		left = max(swing.start + swing.duration - now, 0)
	end
	local c = db.color
	local r, g, b = c.r, c.g, c.b
	local away = inRange == false and not Sampling()
	if away then r, g, b = 0.5, 0.5, 0.48 end
	local k = 0.45 + 0.55 * p * p
	bar.fill:SetColorTexture(r * k, g * k, b * k, 1)
	bar.fill:SetWidth(max(w * p, 0.01))
	bar.fill:SetShown(p > 0)
	bar.shine:SetShown(p > 0)
	bar:SetAlpha(away and 0.55 or 1)
	local since = swing and now - swing.start or FLASH
	bar.flash:SetAlpha(since < FLASH and 0.55 * (1 - since / FLASH) or 0)
	bar.time:SetText(left > 0 and format("%.1f", left) or "")
end

local wasSampling = false

function ns.UpdateWand()
	if not bar then return end
	local now = GetTime()
	local sampling = Sampling()
	if wasSampling and not sampling then swing = nil end
	wasSampling = sampling
	local on = db.enabled and ns.IsMage()
	if on and sampling then
		if not swing or now >= swing.start + swing.duration then swing = { start = now, duration = Speed() } end
	elseif on then
		-- Shooting without word from the game: the next shot at your wand's speed
		if shooting and not heard and (not swing or now >= swing.start + swing.duration) then
			swing = { start = swing and swing.start + swing.duration or now, duration = Speed(), guessed = true }
			if swing.start + swing.duration < now then swing.start = now end
		end
		on = swing ~= nil and (shooting or now < swing.start + swing.duration + LINGER)
	end
	if on then
		Paint(now)
		bar:Show()
	else
		bar:Hide()
	end
end

-- A shot just went: the next one comes in this long
local function Shot(duration, swingType)
	if ns.IsSecret(duration) or ns.IsSecret(swingType) or swingType ~= RANGED then return end
	if type(duration) ~= "number" or duration <= 0 or duration ~= duration or duration == math.huge then return end
	heard = true
	swing = { start = GetTime(), duration = duration }
	ns.UpdateWand()
end
ns.WandShot = Shot -- for the tests

-- /magegod wand: the bar shooting for a few seconds
function ns.TestWand()
	sampleUntil = GetTime() + TEST_SECONDS
	swing = nil
	ns.UpdateWand()
	C_Timer.After(TEST_SECONDS + 0.1, function()
		swing = nil
		ns.UpdateWand()
	end)
end
ns.commands.wand = ns.TestWand
ns.commands.varita = ns.TestWand

-- For the tests
function ns.WandState()
	return { bar = bar, swing = swing, shooting = shooting, inRange = inRange }
end

local events = CreateFrame("Frame")
local function Listen(event)
	pcall(events.RegisterEvent, events, event) -- an event the game doesn't have would stop the file
end

events:RegisterEvent("PLAYER_LOGIN")
events:SetScript("OnEvent", function(self, event, ...)
	if event == "PLAYER_LOGIN" then
		self:UnregisterEvent("PLAYER_LOGIN")
		db = ns.db.wand
		bar = CreateFrame("Frame", "MageGodWand", UIParent)
		bar:SetFrameStrata("MEDIUM")
		-- Flat and square, like the mana bar: a dark back, a black edge one screen pixel thin
		bar.tagEdge = bar:CreateTexture(nil, "BACKGROUND", nil, -1)
		bar.tagEdge:SetColorTexture(0, 0, 0, 1)
		bar.tag = bar:CreateTexture(nil, "ARTWORK")
		bar.tag:SetTexCoord(0.08, 0.92, 0.08, 0.92)
		bar.edge = bar:CreateTexture(nil, "BACKGROUND", nil, -1)
		bar.edge:SetColorTexture(0, 0, 0, 1)
		bar.back = bar:CreateTexture(nil, "BACKGROUND")
		bar.back:SetColorTexture(0.02, 0.04, 0.09, 0.85)
		bar.fill = bar:CreateTexture(nil, "BORDER")
		bar.fill:SetPoint("TOPLEFT", bar.back)
		bar.fill:SetPoint("BOTTOMLEFT", bar.back)
		-- A thread of light along the top of what's filled
		bar.shine = bar:CreateTexture(nil, "ARTWORK")
		bar.shine:SetColorTexture(1, 1, 1, 0.14)
		bar.shine:SetPoint("TOPLEFT", bar.fill)
		bar.shine:SetPoint("TOPRIGHT", bar.fill)
		bar.flash = bar:CreateTexture(nil, "OVERLAY")
		bar.flash:SetColorTexture(1, 1, 1, 1)
		bar.flash:SetAllPoints(bar.back)
		bar.flash:SetAlpha(0)
		bar.time = bar:CreateFontString(nil, "OVERLAY")
		bar.time:SetPoint("RIGHT", bar.back, "RIGHT", -4, 0)
		bar:SetScript("OnUpdate", function()
			if Sampling() or swing or shooting then ns.UpdateWand() end
		end)
		bar:Hide()
		ns.Movable(bar, "wand", DEFAULT_POINT, L.WAND_NAME)
		table.insert(ns.refreshers, ns.StyleWand)
		Listen("PLAYER_SWING")
		Listen("PLAYER_SWING_RANGE_UPDATE")
		Listen("START_AUTOREPEAT_SPELL")
		Listen("STOP_AUTOREPEAT_SPELL")
		Listen("PLAYER_EQUIPMENT_CHANGED")
		Listen("UI_SCALE_CHANGED")
		Listen("DISPLAY_SIZE_CHANGED")
		if C_SwingTimer and C_SwingTimer.EnableRangeCheck then pcall(C_SwingTimer.EnableRangeCheck, RANGED, true) end
		ns.StyleWand()
	elseif event == "PLAYER_SWING" then
		Shot(...)
	elseif event == "PLAYER_SWING_RANGE_UPDATE" then
		local swingType, within, checks = ...
		if ns.IsSecret(swingType) or ns.IsSecret(within) or ns.IsSecret(checks) or swingType ~= RANGED then return end
		if checks then inRange = within and true or false else inRange = nil end
		ns.UpdateWand()
	elseif event == "START_AUTOREPEAT_SPELL" then
		-- Each time you start shooting: guessed until the game reports a shot
		shooting, heard = HasWand(), false
		ns.UpdateWand()
	elseif event == "STOP_AUTOREPEAT_SPELL" then
		shooting = false
		ns.UpdateWand()
	elseif event == "PLAYER_EQUIPMENT_CHANGED" then
		if not HasWand() then swing, shooting = nil, false end
		ns.StyleWand()
	else
		ns.StyleWand()
	end
end)
