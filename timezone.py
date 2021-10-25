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

day   = "tz.png"          # images for day
bgmap = pygame.image.load(day)

tpi = 2 * pi
degs = 180 / pi
rads = pi / 180

RES = 1200, 615
inter = 60     # update interval in seconds

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

# northern and southern map limits
lmin, lmax = -59.5, 85.3

def ns(x):
    return "%.1f" % x

def miller():
    q = lmin
    t = {}
    while q <= lmax + 1:
        p = q * pi / 180
        t[ns(q)] = 1.25 * asinh(tan(.8 * p))
        q += .1
    return t
mil = miller()
top, bot = mil[ns(lmax)], mil[ns(lmin)]
#print(mil)
#1/0

def lattab():
    t = {}
    for y in range(RES[1]):
        mm = top + y / RES[1] * (bot - top)
        d = 1e9
        #print(mm)
        for k in mil.keys():
            if abs(mil[k] - mm) < d:
                d = abs(mil[k] - mm)
                lat = float(k)
        t[y] = lat
    return t

ltab = lattab()

def xy2ll(x, y, res):
    lat = ltab[y]
    lon = x / res[0] * 360. - 170. + 2.5
    return lat, lon

#print(xy2ll(96, 143, RES))   # Dawson +64.0
#print(xy2ll(1062, 508, RES))   # Sydney -34.0
#1/0

def plot(x, y, alt, width):
    ix = 4*int(y * width + x)
    if alt >= 0:
        odat[ix:ix+4] = [0,0,0,max(0, int(128 - 300 * alt))]
    else:
        odat[ix:ix+4] = [0,0,0,128]

def calc_image(res = RES):
    global odat

    odat = 4 * res[0] * res[1] * []

    y, m, d, h = init()
    ra, dec = calc_ra_dec(y, m, d, h)
    hx = res[0] / 2
    hy = res[1] / 2

    for y in range(int(res[1])):
        for x in range(res[0]):
            lat, lon = xy2ll(x, y, res)
            alt = calc_alt(ra, dec, lat, lon, h)
            plot(x, y, alt, res[0])    

    output = bytes(odat)
    result = pygame.image.fromstring(output, res, "RGBA")
    return result

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
                    s.map = pygame.transform.smoothscale(bgmap, (s.res))
                s.screen.blit(s.map, (0, 0))
                s.screen.blit(s.out2, (0, 0))
                pygame.display.flip()
            return
        s.last = time.time()
        s.out = calc_image()
        s.out2 = pygame.transform.smoothscale(s.out, (s.res))
        s.map = pygame.transform.smoothscale(bgmap, (s.res))
        s.screen.blit(s.map, (0, 0))
        s.screen.blit(s.out2, (0, 0))
        pygame.display.flip()

c = Earth()
c.run()

