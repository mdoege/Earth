#!/usr/bin/env python

"""
Draw the day/night distribution in rectangular projection.
Based on renderplanet.py from RSS-Planet (2007-07-17)

Based on Sun position Python code
by Grzegorz Rakoczy
which in turn is based on the web page
 http://www.stjarnhimlen.se/comp/tutorial.html
by Paul Schlyter
"""

from math import *
import os, sys, time
import pygame

day   = "earth4k_3_terrain.png"      # image for day
bgmap_d = pygame.image.load(day)
night = "BlackMarble_2016_3km_gray_geo.png"     # image for night
bgmap_n = pygame.image.load(night)

tpi = 2 * pi
degs = 180 / pi
rads = pi / 180

RES = 1200, 600
inter = 60     # update interval in seconds
NIGHT_ALPHA = 130  # alpha value of night shadow
FALLOFF = 150      # shadow blending factor

def init():
    t = time.gmtime(time.time())
    y = t[0]
    m = t[1]
    d = t[2]
    h = t[3]
    mins = t[4]

    h = h + mins/60.
    return y, m, d, h

#   Get the days to J2000
#   h is UT in decimal hours
#   FNday only works between 1901 to 2099 - see Meeus chapter 7
def FNday (y, m, d, h):
    days = 367 * y - 7 * (y + (m + 9) // 12) // 4 + 275 * m // 9 + d - 730530 + h / 24.
    return float(days)

def rev(x):
    rv = x - int(x / 360) * 360
    if rv < 0: rv += 360
    return rv    

def calc_ra_dec(y, m, d, h):
    global L

    d = FNday(y, m, d, h)    

    w = 282.9404 + 4.70935E-5 * d
    a = 1.000000
    e = 0.016709 - 1.151E-9 * d 
    M = 356.0470 + 0.9856002585 * d
    M = rev(M)

    oblecl = 23.4393 - 3.563E-7 * d
    L = rev(w + M)

    E = M + degs * e * sin(M*rads) * (1 + e * cos(M*rads))

    x = cos(E*rads) - e
    y = sin(E*rads) * sqrt(1 - e*e)
    r = sqrt(x*x + y*y)
    v = atan2( y, x ) *degs
    lon = rev(v + w)

    xequat = r * cos(lon*rads) 
    yequat = r * sin(lon*rads) * cos(oblecl*rads)
    zequat = r * sin(lon*rads) * sin(oblecl*rads) 

    RA = atan2(yequat, xequat) * degs / 15
    Decl = asin(zequat / r) * degs

    return RA, Decl

def calc_alt(RA, Decl, lat, long, h):
    GMST0 = (L*rads + 180*rads) / 15 * degs
    SIDTIME = GMST0 + h + long/15
    HA = rev((SIDTIME - RA))*15

    x = cos(HA*rads) * cos(Decl*rads)
    y = sin(HA*rads) * cos(Decl*rads)
    z = sin(Decl*rads)

    xhor = x * sin(lat*rads) - z * cos(lat*rads)
    yhor = y
    zhor = x * cos(lat*rads) + z * sin(lat*rads)

    #azimuth = atan2(yhor, xhor)*degs + 180
    altitude = atan2(zhor, sqrt(xhor*xhor+yhor*yhor)) * degs

    return altitude

def xy2ll(x, y, res):
    lat = 90. - float(y) / res[1] * 180.
    lon = float(x) / res[0] * 360. - 180.
    return lat, lon

def plot(img1, img2, x, y, alt, width):
    ix = 4*int(y * width + x)
    if alt >= 0:
        img1[ix:ix+4] = [0, 0, 47, max(0, int(NIGHT_ALPHA - FALLOFF * alt))]
        img2[ix:ix+4] = [0, 0, 0, 255]
    else:
        img1[ix:ix+4] = [0, 0, 47, NIGHT_ALPHA]
        img2[ix:ix+4] = [0, 0, 0, 0]

def calc_image(res = RES):
    odat   = 4 * res[0] * res[1] * []
    odat_n = 4 * res[0] * res[1] * []

    y, m, d, h = init()
    ra, dec = calc_ra_dec(y, m, d, h)
    hx = res[0] / 2
    hy = res[1] / 2

    for y in range(int(res[1])):
        for x in range(res[0]):
            lat, lon = xy2ll(x, y, res)
            alt = calc_alt(ra, dec, lat, lon, h)
            plot(odat, odat_n, x, y, alt, res[0])    

    output1 = bytes(odat)
    result1 = pygame.image.fromstring(output1, res, "RGBA")
    output2 = bytes(odat_n)
    result2 = pygame.image.fromstring(output2, res, "RGBA")
    return result1, result2

class Earth:
    def __init__(s):
        pygame.init()
        s.res = RES
        s.screen = pygame.display.set_mode(s.res, pygame.RESIZABLE)
        pygame.display.set_caption('Earth')
        s.clock = pygame.time.Clock()
        s.last = 0
        s.out = None
        s.out2 = None

    def events(s):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: s.running = False
            if event.type == pygame.VIDEORESIZE:
                s.res = event.w, event.h
                s.screen = pygame.display.set_mode(s.res, pygame.RESIZABLE)
                s.out2 = None

    def run(s):
        s.running = True
        while s.running:
            s.clock.tick(1)
            s.events()
            s.update()
        pygame.quit()

    def update(s):
        if time.time() - s.last < inter:
            if s.out:
                if s.out2 == None:
                    s.out2 = pygame.transform.smoothscale(s.out, (s.res))
                    s.map = pygame.transform.smoothscale(bgmap_d, (s.res))
                s.screen.blit(s.map, (0, 0))
                s.screen.blit(s.out2, (0, 0))
                lights = pygame.transform.smoothscale(s.lights, (s.res))
                night = pygame.transform.smoothscale(bgmap_n, (s.res))
                night.blit(lights, (0,0))
                s.screen.blit(night, (0,0), special_flags = pygame.BLEND_RGB_ADD)
                pygame.display.flip()
            return
        s.last = time.time()
        s.out, s.lights = calc_image()
        s.out2 = pygame.transform.smoothscale(s.out, (s.res))
        s.map = pygame.transform.smoothscale(bgmap_d, (s.res))
        s.screen.blit(s.map, (0, 0))
        s.screen.blit(s.out2, (0, 0))
        lights = pygame.transform.smoothscale(s.lights, (s.res))
        night = pygame.transform.smoothscale(bgmap_n, (s.res))
        night.blit(lights, (0,0))
        s.screen.blit(night, (0,0), special_flags = pygame.BLEND_RGB_ADD)
        pygame.display.flip()

c = Earth()
c.run()

