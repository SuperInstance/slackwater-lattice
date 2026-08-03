--[[
    slackwater-lattice Lua Port for Roblox
    =======================================
    Exact Eisenstein A₂ lattice arithmetic in Luau.

    All positions snap to the hexagonal grid. No floating-point drift.
    Every placement is an integer coordinate pair (a, b) representing
    a + bω on the Eisenstein lattice.

    Usage:
        local Lattice = require(script.Parent.Lattice)
        local point = Lattice.snapPosition(worldPos.X, worldPos.Z, 4.0)
        local neighbors = Lattice.neighbors(point)
]]

local Lattice = {}

-- Constants
local SQRT3 = math.sqrt(3)
local NEIGHBOR_DIRECTIONS = {
    {1, 0}, {-1, 0}, {0, 1},
    {0, -1}, {1, 1}, {-1, -1},
}

-- ============================================================
-- Eisenstein Integer Operations
-- ============================================================

--[[
    Create an Eisenstein integer (a, b) representing a + bω.
    Stored as a simple table {a = int, b = int}.
]]
function Lattice.eisenstein(a: number, b: number): {a: number, b: number}
    return {a = a, b = b}
end

function Lattice.add(p1: {a: number, b: number}, p2: {a: number, b: number})
    return {a = p1.a + p2.a, b = p1.b + p2.b}
end

function Lattice.sub(p1: {a: number, b: number}, p2: {a: number, b: number})
    return {a = p1.a - p2.a, b = p1.b - p2.b}
end

function Lattice.neg(p: {a: number, b: number})
    return {a = -p.a, b = -p.b}
end

function Lattice.equals(p1: {a: number, b: number}, p2: {a: number, b: number}): boolean
    return p1.a == p2.a and p1.b == p2.b
end

--[[
    Norm (squared distance from origin): N(a + bω) = a² - ab + b²
    Always a non-negative integer.
]]
function Lattice.norm(p: {a: number, b: number}): number
    return p.a * p.a - p.a * p.b + p.b * p.b
end

--[[
    Squared distance between two lattice points.
    Exact integer — no floating point.
]]
function Lattice.distance(p1: {a: number, b: number}, p2: {a: number, b: number}): number
    local diff = Lattice.sub(p1, p2)
    return Lattice.norm(diff)
end

--[[
    Hex grid distance (number of steps) between two points.
    Uses axial coordinate formula: (|da| + |db| + |da+db|) / 2
]]
function Lattice.hexDistance(p1: {a: number, b: number}, p2: {a: number, b: number}): number
    local da = p1.a - p2.a
    local db = p1.b - p2.b
    return math.floor((math.abs(da) + math.abs(db) + math.abs(da + db)) / 2)
end

--[[
    The six equidistant neighbors of a lattice point.
    Every neighbor is at unit distance. No privileged direction.
]]
function Lattice.neighbors(p: {a: number, b: number}): {{a: number, b: number}}
    local result = {}
    for _, dir in ipairs(NEIGHBOR_DIRECTIONS) do
        table.insert(result, {a = p.a + dir[1], b = p.b + dir[2]})
    end
    return result
end

-- ============================================================
-- Coordinate Conversion
-- ============================================================

--[[
    Convert lattice (a, b) to Cartesian (x, z) with given scale.
    x = (a - b/2) · scale
    z = b · (√3/2) · scale
]]
function Lattice.toCartesian(p: {a: number, b: number}, scale: number?): (number, number)
    local s = scale or 1.0
    local x = (p.a - p.b / 2.0) * s
    local z = p.b * (SQRT3 / 2.0) * s
    return x, z
end

--[[
    Convert lattice point to Roblox Vector3 (Y preserved from input).
]]
function Lattice.toVector3(p: {a: number, b: number}, y: number?, scale: number?): Vector3
    local x, z = Lattice.toCartesian(p, scale)
    return Vector3.new(x, y or 0, z)
end

--[[
    Snap a Cartesian (x, z) position to the nearest lattice point.
    The fundamental operation: continuous → discrete.
]]
function Lattice.snapCartesian(x: number, z: number, scale: number?): {a: number, b: number}
    local s = scale or 1.0
    local bRaw = 2.0 * z / (s * SQRT3)
    local aRaw = x / s + bRaw / 2.0
    return {a = math.round(aRaw), b = math.round(bRaw)}
end

--[[
    Snap a Roblox Vector3 to the lattice. Returns {a, b, y}.
    Y is preserved (vertical is continuous — terrain is irregular).
]]
function Lattice.snapPosition(x: number, z: number, scale: number?): {a: number, b: number}
    return Lattice.snapCartesian(x, z, scale)
end

--[[
    Snap a rotation to the nearest 60° increment.
    Hexagonal symmetry: {0, 60, 120, 180, 240, 300}.
]]
function Lattice.snapRotation(rotationDeg: number): number
    return math.round(rotationDeg / 60.0) * 60
end

-- ============================================================
-- Build Placement Manager
-- ============================================================

local BuildPlacement = {}
BuildPlacement.__index = BuildPlacement

--[[
    Create a new BuildPlacement manager.

    @param scale number — world units per lattice unit (default 4.0)
    @returns BuildPlacement
]]
function BuildPlacement.new(scale: number?): BuildPlacement
    return setmetatable({
        scale = scale or 4.0,
        occupied = {}, -- keyed by "a,b" string
        metadata = {},
    }, BuildPlacement)
end

function BuildPlacement._key(self, p: {a: number, b: number}): string
    return tostring(p.a) .. "," .. tostring(p.b)
end

function BuildPlacement.checkCollision(self, p: {a: number, b: number}): boolean
    return self.occupied[self:_key(p)] ~= nil
end

function BuildPlacement.reserve(self, p: {a: number, b: number}, meta: any?): {a: number, b: number}
    local key = self:_key(p)
    if self.occupied[key] ~= nil then
        error("Placement conflict at (" .. p.a .. ", " .. p.b .. "): already occupied")
    end
    self.occupied[key] = true
    if meta then
        self.metadata[key] = meta
    end
    return p
end

function BuildPlacement.release(self, p: {a: number, b: number}): boolean
    local key = self:_key(p)
    local existed = self.occupied[key] ~= nil
    self.occupied[key] = nil
    self.metadata[key] = nil
    return existed
end

function BuildPlacement.place(self, x: number, z: number, meta: any?): {a: number, b: number}
    local point = Lattice.snapCartesian(x, z, self.scale)
    return self:reserve(point, meta)
end

--[[
    Find nearest free lattice point, searching outward in rings.
]]
function BuildPlacement.nearestFree(self, p: {a: number, b: number}, maxRadius: number?): {a: number, b: number}?
    local maxR = maxRadius or 20
    if not self:checkCollision(p) then
        return p
    end
    for radius = 1, maxR do
        -- Generate ring at this radius
        for da = -radius, radius do
            for db = -radius, radius do
                if da ~= 0 or db ~= 0 then
                    local candidate = {a = p.a + da, b = p.b + db}
                    local dist = Lattice.hexDistance({a = 0, b = 0}, {a = da, b = db})
                    if dist == radius and not self:checkCollision(candidate) then
                        return candidate
                    end
                end
            end
        end
    end
    return nil
end

--[[
    Get free neighbors of a lattice point.
]]
function BuildPlacement.freeNeighbors(self, p: {a: number, b: number}): {{a: number, b: number}}
    local result = {}
    for _, n in ipairs(Lattice.neighbors(p)) do
        if not self:checkCollision(n) then
            table.insert(result, n)
        end
    end
    return result
end

Lattice.BuildPlacement = BuildPlacement

-- ============================================================
-- Simple A* Pathfinding
-- ============================================================

--[[
    Find shortest path through free lattice points.
    Uses A* with hex distance heuristic.

    @param placement BuildPlacement — the placement manager
    @param start {a, b} — start lattice point
    @param goal {a, b} — goal lattice point
    @returns array of {a, b} points, or nil if no path
]]
function Lattice.findPath(
    placement: BuildPlacement,
    start: {a: number, b: number},
    goal: {a: number, b: number}
): {{a: number, b: number}}?
    if Lattice.equals(start, goal) then
        return {start}
    end

    if placement:checkCollision(goal) then
        return nil
    end

    -- Simple BFS (optimal on unweighted hex graph)
    local queue = {start}
    local visited = {}
    visited[ tostring(start.a) .. "," .. tostring(start.b) ] = true
    local cameFrom = {}

    while #queue > 0 do
        local current = table.remove(queue, 1)

        if Lattice.equals(current, goal) then
            -- Reconstruct path
            local path = {current}
            local key = tostring(current.a) .. "," .. tostring(current.b)
            while cameFrom[key] do
                current = cameFrom[key]
                table.insert(path, current)
                key = tostring(current.a) .. "," .. tostring(current.b)
            end
            -- Reverse path
            local reversed = {}
            for i = #path, 1, -1 do
                table.insert(reversed, path[i])
            end
            return reversed
        end

        for _, neighbor in ipairs(Lattice.neighbors(current)) do
            local key = tostring(neighbor.a) .. "," .. tostring(neighbor.b)
            if not visited[key] then
                if Lattice.equals(neighbor, goal) or not placement:checkCollision(neighbor) then
                    visited[key] = true
                    cameFrom[key] = current
                    table.insert(queue, neighbor)
                end
            end
        end
    end

    return nil
end

return Lattice
