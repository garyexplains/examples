# Rotating 3D Wireframe Cube using MicroPython on Badger2040
# Derived from Martin Fitzpatrick's example here https://www.mfitzp.com/creating-a-3d-rotating-cube-with-micropython-and-oled-display/

import math
import time
import random
import picodisplay as display

width = display.get_width()
height = display.get_height()

display_buffer = bytearray(width * height * 2)  # 2-bytes per pixel (RGB565)
display.init(display_buffer)

display.set_backlight(1.0)

def ROUND(a):
  return int(a + 0.5)

def drawDDA(x1,y1,x2,y2):
    x,y = x1,y1
    if abs(x2-x1) > abs(y2-y1):
        length = abs(x2-x1) 
    else:
        length = abs(y2-y1)
    
    if length == 0:
        length = 1
        
    dx = (x2-x1)/float(length)
    dy = (y2-y1)/float(length)

    display.pixel(ROUND(x), ROUND(y))

    for i in range(length):
        x += dx
        y += dy
        display.pixel(ROUND(x), ROUND(y))
    
class Point3D:
    def __init__(self, x = 0, y = 0, z = 0):
        self.x, self.y, self.z = x, y, z
 
    def rotateX(self, angle):
        """ Rotates this point around the X axis the given number of degrees. """
        rad = angle * math.pi / 180
        cosa = math.cos(rad)
        sina = math.sin(rad)
        y = self.y * cosa - self.z * sina
        z = self.y * sina + self.z * cosa
        return Point3D(self.x, y, z)
 
    def rotateY(self, angle):
        """ Rotates this point around the Y axis the given number of degrees. """
        rad = angle * math.pi / 180
        cosa = math.cos(rad)
        sina = math.sin(rad)
        z = self.z * cosa - self.x * sina
        x = self.z * sina + self.x * cosa
        return Point3D(x, self.y, z)
 
    def rotateZ(self, angle):
        """ Rotates this point around the Z axis the given number of degrees. """
        rad = angle * math.pi / 180
        cosa = math.cos(rad)
        sina = math.sin(rad)
        x = self.x * cosa - self.y * sina
        y = self.x * sina + self.y * cosa
        return Point3D(x, y, self.z)
 
    def project(self, win_width, win_height, fov, viewer_distance):
        """ Transforms this 3D point to 2D using a perspective projection. """
        factor = fov / (viewer_distance + self.z)
        x = self.x * factor + win_width / 2
        y = -self.y * factor + win_height / 2
        return Point3D(x, y, self.z)

class Simulation:
    def __init__(
            self, 
            width=240, 
            height=135, 
            fov=64, 
            distance=3, 
            rotateX=5, 
            rotateY=5, 
            rotateZ=5
            ):
 
        self.vertices = [
            Point3D(-1,1,-1),
            Point3D(1,1,-1),
            Point3D(1,-1,-1),
            Point3D(-1,-1,-1),
            Point3D(-1,1,1),
            Point3D(1,1,1),
            Point3D(1,-1,1),
            Point3D(-1,-1,1)
        ]
        
        # Define the edges, the numbers are indices to the vertices above.
        self.edges  = [
            # Back
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
            # Front
            (5, 4),
            (4, 7),
            (7, 6),
            (6, 5),
            # Front-to-back
            (0, 4),
            (1, 5),
            (2, 6),
            (3, 7),
        ]
 
        # Dimensions
        self.projection = [width, height, fov, distance]
        
        # Rotational speeds
        self.rotateX = rotateX
        self.rotateY = rotateY
        self.rotateZ = rotateZ
 
    def run(self):
        # Starting angle (unrotated in any dimension)
        angleX, angleY, angleZ = 0, 0, 0
        distance_delta = 0.1
        
        while 1:
            # It will hold transformed vertices.
            t = []
            
 
            for v in self.vertices:
                # Rotate the point around X axis, then around Y axis, and finally around Z axis.
                r = v.rotateX(angleX).rotateY(angleY).rotateZ(angleZ)

                # Transform the point from 3D to 2D
                p = r.project(*self.projection)
                
                # Put the point in the list of transformed vertices
                t.append(p)
            
            display.set_pen(40, 40, 40)
            display.clear()

            display.set_pen(255, 255, 255)
    
            for e in self.edges:
                drawDDA(*to_int(t[e[0]].x, t[e[0]].y, t[e[1]].x, t[e[1]].y))
            
            display.update()
            
            # Continue the rotation
            angleX += self.rotateX
            angleY += self.rotateY
            angleZ += self.rotateZ
            
            self.projection[3] += distance_delta
            if self.projection[3] > 12.0:
                distance_delta = -0.1

            if self.projection[3] < 2.0:
                distance_delta = 0.1

def to_int(*args):
    return [int(v) for v in args]

 
s = Simulation()
s.run()