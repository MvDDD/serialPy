from arduino import *
from time import sleep
from random import random as rnd



import math

import math

def inverse_kinematics(coords, L1, L2):
    x, y = coords
    # Calculate the distance from the origin to the point (x, y)
    r = math.sqrt(x**2 + y**2)

    # Check if the point is reachable
    if r > L1 + L2:
        print("The target is unreachable.")
        return None, None
    
    # Calculate theta_2 using the law of cosines
    cos_theta_2 = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
    
    # Ensure the cosine value is in the valid range [-1, 1] for acos
    cos_theta_2 = max(-1, min(1, cos_theta_2))
    
    theta_2 = math.acos(cos_theta_2)
    
    # Calculate theta_1 using the geometry of the arm
    k1 = L1 + L2 * math.cos(theta_2)
    k2 = L2 * math.sin(theta_2)
    
    theta_1 = math.atan2(y, x) - math.atan2(k2, k1)
    
    # Convert angles to degrees
    theta_1_deg = math.degrees(theta_1)
    theta_2_deg = math.degrees(theta_2)
    
    # Normalize theta_1 to be within 0 to 180 degrees
    theta_1_deg = (theta_1_deg + 360) % 360  # Ensure it's within 0-360 range
    if theta_1_deg > 180:
        theta_1_deg = 360 - theta_1_deg  # Convert to the 0-180 range

    # Normalize theta_2 to be within 0 to 180 degrees
    theta_2_deg = (theta_2_deg + 360) % 360  # Ensure it's within 0-360 range
    if theta_2_deg > 180:
        theta_2_deg = 360 - theta_2_deg  # Convert to the 0-180 range

    return theta_1_deg, theta_2_deg


def normalize_coords(coords):
	# Extract the x and y values from the coordinates list
	x_vals = [coord[0] for coord in coords]
	y_vals = [coord[1] for coord in coords]
	
	# Find the min and max values for both x and y
	x_min, x_max = min(x_vals), max(x_vals)
	y_min, y_max = min(y_vals), max(y_vals)
	
	# Normalize each coordinate
	normalized_coords = [
		[(x - x_min) / (x_max - x_min), (y - y_min) / (y_max - y_min)]
		for x, y in coords
	]
	
	return normalized_coords

connect()



j0 = Servo(3)
j1 = Servo(4)
p = Servo(5)

with open("dino.ttpd", "r") as file:
	data = file.read()
	data = [[int(q) for q in d.split(" ")] for d in data.split("\n")]

R = []
for d in data:
	R.append([d[0],d[1]])
	R.append([d[2],d[3]])

R = normalize_coords(R)


def lerp2d(c1, c2, t):
    return (
    	c1[0] + (c2[0] - c1[0]) * t,
    	c1[1] + (c2[1] - c1[1]) * t
    )
scale = 10
offx = 10
offy = 10
lastcoord = [0,0]
for i, coord in enumerate(R):
	p1 = 1
	if ((lastcoord[0]-coord[0])**2 + (lastcoord[1]-coord[1])**2) > 0.01 and i % 2 == 1:
		p1 = 0
	if p1:
		p.write(0)
	else:
		p.write(180)

	scaledCoords = [
		[
			lastcoord[0]*scale + offx,
			lastcoord[1]*scale + offy
		],[
			coord[0]*scale + offx,
			coord[1]*scale + offy
		]
	]
	for i in range(101):
		i /= 100
		targetcoords = lerp2d(scaledCoords[0], scaledCoords[1], i)
		angles = inverse_kinematics(targetcoords,10 , 10)
		j0.write(int(angles[0]))
		j1.write(int(angles[1]))
		sleep(0.01)
	lastcoord = coord