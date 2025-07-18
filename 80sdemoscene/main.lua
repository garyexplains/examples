-- Checkerboard settings
local tileSize = 64
local cols, rows
local offsetX, offsetY = 0, 0

-- Movement animation
local time = 0
local bounceAmplitude = 25
local bounceSpeed = 2

-- Sphere
local sphere = {}
local radius = 150
local segments = 12
local rings = 12
local originalPoints = {}
local position = { x = 400, y = 300 }
local velocity = { x = 120, y = 90 }

-- Rotation angles
local angleX = 0
local angleY = 0
local rotationSpeedX = 0.6
local rotationSpeedY = 1.0

function love.load()
    love.window.setTitle("80s Demoscene 1")
    love.window.setMode(800, 600, { vsync = true })

    local width, height = love.graphics.getDimensions()
    cols = math.ceil(width / tileSize) + 2
    rows = math.ceil(height / tileSize) + 2

    -- Generate base sphere points (lat/lon)
    for i = 0, rings do
        local theta = math.pi * i / rings
        local sinTheta = math.sin(theta)
        local cosTheta = math.cos(theta)
        for j = 0, segments do
            local phi = 2 * math.pi * j / segments
            local sinPhi = math.sin(phi)
            local cosPhi = math.cos(phi)

            local x = radius * cosPhi * sinTheta
            local y = radius * sinPhi * sinTheta
            local z = radius * cosTheta

            table.insert(originalPoints, { x = x, y = y, z = z })
        end
    end

    -- Music
    music = love.audio.newSource( 'chiptune1.mp3', 'static' )
    music:setLooping( true ) --so it doesnt stop
    music:play()
end

-- Rotate a 3D point around X and Y axes
local function rotatePoint(p, angleX, angleY)
    -- Rotate around X axis
    local cosX = math.cos(angleX)
    local sinX = math.sin(angleX)
    local y1 = p.y * cosX - p.z * sinX
    local z1 = p.y * sinX + p.z * cosX

    -- Rotate around Y axis
    local cosY = math.cos(angleY)
    local sinY = math.sin(angleY)
    local x2 = p.x * cosY + z1 * sinY
    local z2 = -p.x * sinY + z1 * cosY

    return { x = x2, y = y1, z = z2 }
end

-- Simple perspective projection
local function project3D(x, y, z)
    local scale = 300 / (z + 400)
    return x * scale + position.x, y * scale + position.y
end

local colorIndex = 0
local totalColors = 64

function getNextColor()
    colorIndex = (colorIndex + 1) % totalColors

    local phase = (colorIndex / totalColors) * 2 * math.pi

    -- Sine wave color cycling
    local r = 0.5 + 0.5 * math.sin(phase)
    local g = 0.5 + 0.5 * math.sin(phase + 2 * math.pi / 3)
    local b = 0.5 + 0.5 * math.sin(phase + 4 * math.pi / 3)

    return r, g, b
end

function love.update(dt)
    time = time + dt

    -- Use sine and cosine to bounce offset
    offsetX = math.sin(time * bounceSpeed) * bounceAmplitude
    offsetY = math.cos(time * bounceSpeed * 1.2) * bounceAmplitude

    -- Sphere movement

    -- Update rotation angles
    angleX = angleX + rotationSpeedX * dt
    angleY = angleY + rotationSpeedY * dt

    -- Bounce off screen edges
    position.x = position.x + velocity.x * dt
    position.y = position.y + velocity.y * dt

    local width, height = love.graphics.getDimensions()
    if position.x - radius < 0 or position.x + radius > width then
        velocity.x = -velocity.x
    end
    if position.y - radius < 0 or position.y + radius > height then
        velocity.y = -velocity.y
    end
end

function love.draw()
    for row = 1, rows do
        for col = 1, cols do
            local isDark = (row + col) % 2 == 0
            if isDark then
                love.graphics.setColor(0.1, 0.1, 0.5) -- dark tile
            else
                love.graphics.setColor(0.5, 0.5, 0.9) -- light tile
            end

            local x = (col - 2) * tileSize + offsetX
            local y = (row - 2) * tileSize + offsetY
            love.graphics.rectangle("fill", x, y, tileSize, tileSize)
        end
    end

    -- Draw sphere
    love.graphics.setColor(getNextColor())
    local cols = segments + 1

    -- Apply rotation and draw wireframe
    for i = 1, #originalPoints do
        local p = rotatePoint(originalPoints[i], angleX, angleY)
        local x1, y1 = project3D(p.x, p.y, p.z)

        -- Connect to neighbor along longitude
        if (i % cols) ~= 0 then
            local q = rotatePoint(originalPoints[i + 1], angleX, angleY)
            local x2, y2 = project3D(q.x, q.y, q.z)
            love.graphics.line(x1, y1, x2, y2)
        end

        -- Connect to neighbor along latitude
        if i + cols <= #originalPoints then
            local r = rotatePoint(originalPoints[i + cols], angleX, angleY)
            local x3, y3 = project3D(r.x, r.y, r.z)
            love.graphics.line(x1, y1, x3, y3)
        end
    end
end
