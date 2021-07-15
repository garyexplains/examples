import random

WIDTH = 800
HEIGHT = 640

alien = Actor('alien')
alien.pos = WIDTH / 2, HEIGHT - alien.height / 2
boxes = []
box_interval = 2.2

def draw():
    screen.clear()
    alien.draw()
    for x in boxes:
        x.draw()

def add_box():
    global boxes
    global box_interval
    global alien
    box = Actor('box_empty')
    box.pos = random.randrange(int(WIDTH/alien.width)) * alien.width, 0
    boxes.append(box)
    if box_interval > 0.7:
        box_interval = box_interval - 0.3
    clock.schedule_unique(add_box, box_interval)

def update():
    global boxes
    ox = alien.x

    if keyboard.left:
        alien.x = alien.x - 2
    if keyboard.right:
        alien.x = alien.x + 2

    if alien.x > WIDTH or alien.x < 0:
        alien.x = ox        

    c=alien.collidelist(boxes)
    if  c >= 0:
        alien.image = 'alien_hurt'
        boxes = []
        clock.unschedule(add_box)
        clock.schedule_unique(reset_game, 1.0)
    
    boxes_to_remove = []
    for i in range(len(boxes)):
        boxes[i].y = boxes[i].y + 2
        if boxes[i].y > HEIGHT:
            boxes_to_remove.append(i)
            
    for i in range(len(boxes_to_remove)):
        boxes.pop(boxes_to_remove[i])

def reset_game():
    global boxes
    box_interval = 2.2
    boxes = []
    alien.image = 'alien'
    add_box()

add_box()