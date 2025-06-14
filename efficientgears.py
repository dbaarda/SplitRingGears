#!/bin/python3
from math import *


def d2r(d):
  """Convert degrees to radians."""
  return d/180*pi

def r2d(r):
  """Convert radians to degrees."""
  return r/pi*180

def cosd(d):
  """cos() for degrees."""
  return cos(d2r(d))

def acosd(v):
  """acos() for degrees."""
  return r2d(acos(v))

def sind(d):
  """sin() for degrees."""
  return sin(d2r(d))

def asind(v):
  """asin() for degrees."""
  return r2d(asin(v))

def tand(d):
  """tan() for degrees."""
  return tan(d2r(d))

def atand(v):
  """atan() for degrees."""
  return r2d(atan(v))

def inv(a):
  """ The involute function. Note a is in radians, and this returns an angle in radians."""
  return tan(a) - a

def invd(d):
  """inv() for degrees."""
  return r2d(inv(d2r(d)))


class Gear(object):
  """ A base class for a simple gear. """
  z : int    # number of gear teeth.
  m : float  # transverse module.
  a : float  # pressure angle.
  B : float  # helix angle.
  ha : float # addendum factor.
  hf : float # dedendum factor.
  hx : float # tooth face width factor.

  def __init__(self, z:int, m:float=1.0, a:float=20.0, B:float=0.0, ha:float=1.0, hf:float=1.25, hx:float=1.0):
    self.z, self.m, self.a, self.B, self.ha, self.hf, self.hx = z, m, a, B, ha, hf, hx

  def __repr__(self):
    fargs = ', '.join((f'{n}={getattr(self,n):.2f}' for n in ('m a B ha hf hx'.split())))
    return f'{self.__class__.__name__}(z={self.z}, {fargs})'

  def __str__(self):
    rep = self.__repr__()
    props = f'sf={self.sf:.2f} sa={self.sa:.2f} La={self.La:.2f} Ea={self.Ea:.2f} Ex={self.Ex:.2f}'
    return f'{rep}: {props}'

  @property
  def b(self):
    """Get the tooth face width."""
    return self.m*self.hx

  @property
  def Dp(self):
    """Get the pitch radius from size and module."""
    return self.z*self.m

  @property
  def Db(self):
    """Get the base radius from the size, module, and pressure angle. """
    return self.Dp*cosd(self.a)

  @property
  def Da(self):
    """Get the tip radius from addendum factor ha."""
    return self.Dy(self.ha)

  @property
  def Df(self):
    """Get the root radius from dedendum factor hf."""
    return self.Dy(-self.hf)

  def Dy(self, hy):
    """Get the radius at an arbitary hight-factor hy from the pitch circle."""
    return (self.z + 2*hy) * self.m

  @property
  def Rp(self):
    """Get the pitch radius from size and module."""
    return self.Dp/2

  @property
  def Rb(self):
    """Get the base radius from the size, module, and pressure angle. """
    return self.Db/2

  @property
  def Ra(self):
    """Get the tip radius from addendum factor ha."""
    return self.Da/2

  @property
  def Rf(self):
    """Get the root radius from dedendum factor hf."""
    return self.Df/2

  def Ry(self, hy):
    """Get the radius at an arbitary hight-factor hy from the pitch circle."""
    return self.Dy(hy)/2

  @property
  def Pp(self):
    """Get the pitch at the pitch cicle."""
    return self.m*pi

  @property
  def Pb(self):
    """ Get the pitch at the base cicle."""
    return self.Pp*cosd(self.a)

  @property
  def Px(self):
    """ Get the axial pitch."""
    try:
      return self.Pp/tand(self.B)
    except:
      return inf

  @property
  def sp(self):
    """ Tooth thickness-factor at the pitch cicle."""
    return pi/2

  @property
  def sa(self):
    """ Tooth thickness-factor at the tip (addendum)."""
    return self.sy(self.ha)

  @property
  def sf(self):
    """ Tooth thickness-factor at the root (dedendum)."""
    return self.sy(-self.hf)

  def sy(self, hy):
    """Get the tooth thickness-factor at tooth height factor hy.

    Note this takes and returns the tooth height and thickness scaled by m. Use
    a negative hy value for thicknesses below the pitch circle. For the tip
    thickness use hy=ha, for the root thickness use hy=-hf.
    """
    dp, dy = self.z, self.z+2*hy  # diameters scaled by m.
    ay = self.ay(hy)
    return dy*(self.sp/dp + d2r(invd(self.a) - invd(ay)))

  @property
  def mn(self):
    """Get the normal module from transverse module and helix angle."""
    return self.m*cosd(self.B)

  def ay(self, hy):
    """Get the pressure angle at an arbitary hy height factor.

    Note this returns an angle in degrees like all the other angles.
    """
    try:
      return acosd(self.Rb/self.Ry(hy))
    except:
      return 0

  @property
  def Bb(self):
    """Get the helix angle at the base radius."""
    return atand(cosd(self.a) * tand(self.B))

  def By(self, ry):
    """Get the helix angle at a radius ry from the pitch helix angle."""
    return atand(ry/self.Rp * tand(self.B))

  @property
  def La(self):
    """ Transverse addendum contact path length.

    This is the contact line length from the mid-pitch point to where the
    addendum disengages. It does not depend on the size of the other gear, and
    the sum of engaging gear's L1 is the total transverse contact line length.
    """
    return sqrt(self.Ra**2 - self.Rb**2) - self.Rp * sind(self.a)

  def Lt(self, g2=None):
    """ Transverse contact path length.

    Note if g2 is not provided, it assumes it is the same as this one.
    """
    if g2 is None: g2=self
    assert self.a == g2.a
    return self.La + g2.La

  @property
  def Ea(self):
    """Get the transverse addendum contact ratio.

    This is the contact ratio for the contact line length from the mid-pitch
    point to where the addendum disengages. It does not depend on the size of
    the other gear and summing E1 for meshing gears gives the total transverse
    contact ratio.
    """
    return self.La/self.Pb

  def Et(self, g2=None):
    """Get the transverse contact ratio of a gear-pair.

    Note if g2 is not provided, it assumes it is the same as this one.
    """
    return self.Lt(g2)/self.Pb

  @property
  def Ex(self):
    """ Get axial contact ratio. """
    return self.b/self.Px

  def E(self, g2=None):
    """ Get total contact ratio. """
    return self.Et(g2) + self.Ex

  def Cxavg(self, g2=None):
   """Get the avg axial face contact line length."""
   return self.b*self.Et(g2)

  def Cxmin(self, g2=None, e=0.0001):
    """ Get the minimum axial face contact line length. """
    et=self.Et(g2)
    ex=self.Ex
    nt = (et-e) % 1
    nx = (ex-e) % 1
    cxavg = self.Cxavg(g2)
    if self.B == 0:
      return cxavg*(1 - nt/et)
    elif nt+nx <= 1:
      return cxavg*(1 - nt*nx/(et*ex))
    else:
      return cxavg*(1 - (1-nt)*(1-nx)/(et*ex))

  def Chavg(self, g2=None):
   """Get the avg helical face contact line length."""
   return self.Cxavg(g2)/cosd(self.Bb)

  def Chmin(self, g2=None, e=0.0001):
    """Get the minimum helical face contact line length. """
    return self.Cxmin(g2,e)/cosd(self.Bb)

def optB(ex, hx):
  """Get the required helix angle for the target axial contact ratio ex for a given gear widthfactor hx=b/m."""
  return atand(ex*pi/hx)

def optWf(ex, B=15):
  """ Get optimum width factor for the target axial contact ratio ex from helix angle B."""
  return eb*pi/tand(B)

def optha(z, et, a=20):
  """Get optimum addendum factor (ha) values for a gear for a transverse contact ratio (et) for a given pressure angle (a).

  The optimum is with both gears having the same addendum transverse contact
  ratio and the total transverse contact ratio being at the target ha (e).
  """
  ea = et/2
  rp = z/2
  rb = rp*cosd(a)
  return sqrt((ea*pi*cosd(a) + rp*sind(a))**2 + rb**2) - rp

def opta(z, et, ha=1):
  """ Get optimum pressure angle (a) for the target transverse contact ratio (et) and addendum factor (ha)."""
  # This gets a bit hard...
  # aet=et/2
  # rp = z/2
  # ra = rp + ha
  # rb = rp*cos(a)
  # le = sqrt(ra**2 - rb**2) # length of line of action from base circle to adendum disengagement point.
  # lp = rp*sind(a) = sqrt(rp^2 - rb^2)  # length of line of action from base cicle to the middle pitch-point.
  # aet = sqrt(ra^2 - rb^2) - sqrt(rp^2 - rb^2)
  # aet = ra*sin(a+b) - rp*sin(a)


  # # need to solve for rb, then a = acos(rb/rp) or solve for lp and a = asin(lp/rp)
  # aet^2 = ra^2 - rb^2 + rp^2 - rb^2 - 2*sqrt((ra^2 - rb^2)*(rp^2 - rb^2))
  #       = ra^2 + rp^2 - 2*rb^2  - 2*sqrt((ra*rp)^2 - (ra*rb)^2 - (rb*rp)^2 + rb^4))
  #       = ra^2 + rp^2 - 2*rb^2  - 2*sqrt((ra*rp)^2 - (ra*rb)^2 - (rb*rp)^2 + rb^4))


  # # aet = (le - rp*sin(a))/ pi*cosd(a)
  # # aet*pi*cos(a) = le - rp*sin(a)
  # # le = aet*pi*cos(a) + rp*sin(a)
  # rp = z/2
  # ra = rp + ha
  # aet = (sqrt(ra^2 - (rp*cos(a))^2) - rp*sin(a)) / (pi*cos(a))
  # aet*pi*cos(a) = sqrt(ra^2 - (rp*cos(a))^2) - rp*sin(a)

  # R = sqrt((aet*pi)^2 + rp^2)
  # b = atan(aet*pi/rp)
  # le = R*sin(a+b)
  # a + b = asin(le/R)
  # a = asin(le/R) - b
  # return asin(sqrt((ra**2 - rb**2)/((aet*pi)^2 + rp^2)))/atan(aet*pi/rp))

def optStats(z1, Et, Ex, m1=1, m2=None, a1=20, a2=None, B1=0, b1=4, b2=None):
  if b2 is None: b2=b1
  if m2 is None: m2=m1
  if a2 is None: a2=a1
  g1=Gear(z=z1, m=m1, a=a1, B=B1, hx=b1/m1)
  print(g1)
  z2=round(z1*m1/m2)
  ha2=optha(z2, Et, a2)
  hf2=ha2+0.25
  hx2=b2/m2
  B2=optB(Ex, hx2)
  g2=Gear(z=z2, m=m2, a=a2, B=B2, ha=ha2, hf=hf2, hx=hx2)
  print(g2)
  print('---')

def optSRP(Et, Ex, m=0.5, a=40, b=4):
  hx=b/m
  r1,p1,s1 = Gear(34,m=0.5,hx=8),Gear(13, m=0.5, hx=8),Gear(8, m=0.5, hx=8)
  r2,p2,s2 = Gear(39, m=0.5, hx=8),Gear(11, m=0.5, hx=8),Gear(7, m=0.5, hx=8)
  B=optB(Ex,hx)
  r1_ha = optha(r1, Et, a)
  p1_ha = optha(p1, Et, a)


def MeshStats(g1, g2):
  assert g1.m == g2.m
  assert g1.a == g2.a
  assert g1.B == g2.B
  assert g1.hx == g2.hx
  assert g1.ha + 0.1 < g2.hf
  assert g1.hf > g2.ha + 0.1
  Lt = g1.Lt(g2)
  Ex, Et, E = g1.Ex, g1.Et(g2), g1.E(g2)
  Cxavg, Cxmin = g1.Cxavg(g2), g1.Cxmin(g2)
  return f'{Lt=:.2f} {Et=:.2f} {Ex=:.2f} {E=:.2f} {Cxavg=:.2f} {Cxmin=:.2f}'

def adjustm(g1, g2, m):
  """Get new z1,z2,m values when changing to a target m.

  Note this preserves the ratio and diameters exactly, which means the actual
  m value might be a little different from the target m value.
  """
  d = gcd(g1.z, g2.z)
  n = round(d*m/g1.m)
  z1, z2 = g1.z*n//d, g2.z*n//d
  m = g1.Dp/z1
  return z1, z2, m


def optGears(g1, g2, Et=0.5, Ex=1.0, m=None, a=None, b=None):
  """ Optimize a gear pair."""
  c = g1.Rp + g2.Rp
  if m is None:
    z1,z2,m = g1.z, g2.z, g1.m
  else:
    z1,z2,m = adjustm(g1,g2,m)
  if a is None: a = g1.m
  if b is None: b = g1.b
  hx = b/m
  B = optB(Ex,hx)
  ha1,ha2 = optha(z1, Et, a), optha(z2,Et,a)
  hf1,hf2 = ha2+0.25, ha1+0.25
  return Gear(z1, m, a, B, ha1, hf1, hx), Gear(z2, m, a, B, ha2, hf2, hx)

b = 4.0
m1 = 0.5
m2 = m1*(34 - 13)/(29 - 11)
hx1,hx2 = b/m1,b/m2
s1 = Gear( 8, m=m1, hx=hx1)
p1 = Gear(13, m=m1, hx=hx1)
r1 = Gear(34, m=m1, hx=hx1)
s2 = Gear( 7, m=m2, hx=hx2)
p2 = Gear(11, m=m2, hx=hx2)
r2 = Gear(29, m=m2, hx=hx2)

print('Optimizing the following gears.')
print(f'{s1=!s}')
print(f'{p1=!s}')
print(f'{r1=!s}')
print(f'{s2=!s}')
print(f'{p2=!s}')
print(f'{r2=!s}')

Et,Ex,m,a,b=0.6,1.0,0.5,40,4

def OptOut(n1,n2,g1,g2):
  print(f'Optimizing {n1} + {n2} mesh:')
  g1o,g2o = optGears(g1, g2, Et, Ex, m, a, b)
  print(f'  {n1} -> {n1}o={g1o!s}')
  print(f'  {n2} -> {n2}o={g2o!s}')
  print(f'  {n1}  + {n2}  = {MeshStats(g1,g2)}')
  print(f'  {n1}o + {n2}o = {MeshStats(g1o,g2o)}')

OptOut('s1', 'p1', s1, p1)
OptOut('p1', 'r1', p1, r1)
OptOut('s2', 'p2', s2, p2)
OptOut('p2', 'r2', p2, r2)
