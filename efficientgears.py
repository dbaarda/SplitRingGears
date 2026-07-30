#!/bin/python3
from math import *

def solve(f, x0=-1.0e9, x1=1.0e9, e=1.0e-9):
 """ Solve f(x)=0 for x where x0<=x<=x1 within +-e. """
 y0, y1 = f(x0), f(x1)
 # y0 and y1 must have different sign.
 assert y0*y1 <= 0
 while (x1 - x0) > e:
   xm = (x0 + x1) / 2.0
   ym = f(xm)
   if y0*ym > 0:
     x0,y0 = xm,ym
   else:
     x1,y1 = xm,ym
 return x0


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
  hx : float # thickness factor.

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
    """Get the tooth face width (gear thickness)."""
    return self.m*self.hx

  @property
  def Dp(self):
    """Get the pitch diameter from size and module."""
    return self.z*self.m

  @property
  def Db(self):
    """Get the base diameter from the size, module, and pressure angle. """
    return self.Dp*cosd(self.a)

  @property
  def Da(self):
    """Get the tip diameter from addendum factor ha."""
    return self.Dy(self.ha)

  @property
  def Df(self):
    """Get the root diameter from dedendum factor hf."""
    return self.Dy(-self.hf)

  def Dy(self, hy):
    """Get the diameter at an arbitary hight-factor hy from the pitch circle."""
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
    """ Get the axial pitch from the helix angle."""
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
      # Ry(hy) is less than Rb.
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
    the summing La for both gears is the total transverse contact line length.
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
    the other gear and summing Ea for meshing gears gives the total transverse
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
      return cxavg*(1 - nt/et) # == floor(et-e)*b
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

def opthx(ex, B=15):
  """ Get optimum width factor for the target axial contact ratio ex from helix angle B."""
  return ex*pi/tand(B)

def optha(z, et, a=20):
  """Get optimum addendum factor (ha) values for a gear for a transverse contact ratio (et) for a given pressure angle (a).

  The optimum is with both gears having the same addendum transverse contact
  ratio and the total transverse contact ratio being at the target ha (e).
  """
  # For m=1 to simplify things.
  Ea = et/2
  Rp = z/2
  Pp = pi
  return sqrt((Ea*Pp*cosd(a))**2 + Rp*(Ea*Pp*sind(2*a) + Rp)) - Rp

def opta(z, et, ha=1):
  """ Get optimum pressure angle (a) for the target transverse contact ratio (et) and addendum factor (ha)."""
  # This gets a bit hard...
  #
  # From the optha() eqn above we have;
  #
  # ha = sqrt((Ea*Pp*cosd(a))**2 + Rp*(Ea*Pp*sind(2*a) + Rp)) - Rp
  # ha = sqrt((Ea*Pp*cosd(a))**2 + Rp*(Ea*Pp*2*sind(a)*cosd(a) + Rp)) - Rp
  # (ha - Rp)^2 = (Ea*Pp*cosd(a))**2 + Rp*(Ea*Pp*2*sind(a)*cosd(a) + Rp)
  # (ha - Rp)^2 = (Ea*Pp*cosd(a))**2 + 2*Rp*Ea*Pp*sind(a)*cosd(a) + Rp^2
  # ha^2 - 2*ha*Rp = (Ea*Pp*cosd(a))**2 + 2*Rp*Ea*Pp*sind(a)*cosd(a)
  # ha*(ha - 2*Rp) = (Ea*Pp*cosd(a))**2 + 2*Rp*Ea*Pp*sind(a)*cosd(a)
  # ha*(ha - 2*Rp)/(Ea*Pp) = (Ea*Pp*cosd(a)^2 + 2*Rp*sind(a)*cosd(a)
  # ha*(ha - 2*Rp)/(Ea*Pp) = cosd(a)*(Ea*Pp*cosd(a) + 2*Rp*sind(a))
  # ha*(ha - Dp)/(Ea*Pp) = cosd(a)*(Ea*Pp*cosd(a) + Dp*sind(a))
  #
  # This eqn make all the symbolic solvers struggle, so just solve #
  # numerically, but note that for most z,et, only a narrow range of ha values
  # have a solution.
  return solve(lambda a: optha(z,et,a) - ha, 0.0, 45.0)


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
  return f'{Lt=:.2f}={g1.La:.2f}+{g2.La:.2f} {Et=:.2f}={g1.Ea:.2f}+{g2.Ea:.2f} {Ex=:.2f} {E=:.2f} {Cxavg=:.2f} {Cxmin=:.2f}'

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


def optGears(g1, g2, Et=0.5, Ex=1.0, m=None, a=None, b=None, hx=None):
  """ Optimize a gear pair."""
  c = g1.Rp + g2.Rp
  if m is None:
    z1,z2,m = g1.z, g2.z, g1.m
  else:
    z1,z2,m = adjustm(g1,g2,m)
  if a is None: a = g1.a
  if b is None: b = g1.b
  if hx is None: hx = b/m
  B = optB(Ex,hx)
  ha1,ha2 = optha(z1, Et, a), optha(z2,Et,a)
  hf1,hf2 = ha2+0.25, ha1+0.25
  return Gear(z1, m, a, B, ha1, hf1, hx), Gear(z2, m, a, B, ha2, hf2, hx)


def optPGears(r, p, s, Et=1.0, Ex=1.0, m=None, a=None, b=None, hx=None):
  """ Optimize a planetary Ring/Planet/Sun trio. """
  assert (r.a == p.a == s.a)
  assert (r.z == s.z + 2*p.z)
  if m is None: m = r.m
  if a is None: a = s.a
  if b is None: b = s.b
  if hx is None: hx = b/m
  B = optB(Ex,hx)
  r_ha, p_ha, s_ha = optha(r.z, Et, a), optha(p.z, Et, a), optha(s.z, Et, a)
  r_hf, p_hf, s_hf = p_ha+0.25, s_ha+0.25, p_ha+0.25
  return Gear(r.z, m, a, B, r_ha, r_hf, hx), Gear(p.z, m, a, B, p_ha, p_hf, hx), Gear(s.z, m, a, B, s_ha, s_hf, hx)

def OptPGearsOut(n,r,p,s, Et=1.0, Ex=1.0, m=None, a=None, b=None, hx=None):
  print(f'Optimizing SRP r{n} p{n} s{n} mesh with {Et=} {Ex=}:')
  ro,po,so = optPGears(r, p, s, Et, Ex, m, a, b, hx)
  print(f'  r{n} -> r{n}o={ro!s}')
  print(f'  p{n} -> p{n}o={po!s}')
  print(f'  s{n} -> s{n}o={so!s}')
  print(f'  s{n}  + p{n}  = {MeshStats(s,p)}')
  print(f'  s{n}o + p{n}o = {MeshStats(so,po)}')
  print(f'  p{n}  + r{n}  = {MeshStats(p,r)}')
  print(f'  p{n}o + r{n}o = {MeshStats(po,ro)}')
  return ro,po,so

def OptOut(n1,n2,g1,g2):
  print(f'Optimizing {n1} + {n2} mesh:')
  g1o,g2o = optGears(g1, g2, Et, Ex, m, a, b)
  print(f'  {n1} -> {n1}o={g1o!s}')
  print(f'  {n2} -> {n2}o={g2o!s}')
  print(f'  {n1}  + {n2}  = {MeshStats(g1,g2)}')
  print(f'  {n1}o + {n2}o = {MeshStats(g1o,g2o)}')

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
print(f'{r1=!s}')
print(f'{p1=!s}')
print(f'{s1=!s}')
ro6,_,_ = OptPGearsOut('1',r1,p1,s1, a=40, Et=0.6)
ro8,_,_ = OptPGearsOut('1',r1,p1,s1, a=40, Et=0.8)
ro1,_,_ = OptPGearsOut('1',r1,p1,s1, a=40, Et=1.0)

print('Optimizing the following gears.')
print(f'{r2=!s}')
print(f'{p2=!s}')
print(f'{s2=!s}')
OptPGearsOut('2',r2,p2,s2, a=40, Et=0.6)
OptPGearsOut('2',r2,p2,s2, a=40, Et=0.8)
OptPGearsOut('2',r2,p2,s2, a=40, Et=1.0)
