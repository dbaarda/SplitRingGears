#!/bin/pypy3
"""
Tools for calculating split-ring compound planetary gearboxes.

These use a standard first-stage planetary gearbox that drives a hybrid second
stage with planet gears driven by the same shaft as the first stage planet
gears, that drive a second "split-ring" with slightly different gearing to the
first stage. The small gearing change creates a tiny rotation change between
the first stage ring and the second ring with every full rotation of the
carrier, giving very high gearing ratios with only two planetery stages
sharing a common carrier. This is similar to how harmonic and cycloidal drives
achieve high ratios.

https://en.wikipedia.org/wiki/Epicyclic_gearing
https://khkgears.net/new/gear_knowledge/abcs_of_gears-b/basic_gear_terminology_calculation.html

Gear geometries are defined by their gear size, teeth size, and teeth
geometry. For gears to mesh properly they must have the same sized teeth and
teeth geometry. When meshed they will "touch" at their pitch-diameter.

Gear size is the gear's total number of teeth (symbol "z" "Z" or "N"), and is
often written as "T9", "T10", "T36", etc.

Teeth size is the gear's module (symbol "m"), which is the pitch-diameter per
tooth, or diameter/teeth. Technically it is measured in mm, but often written
as "m1", "m0.4", or "M1", "M0.8" etc.

Teeth geometry for normal "involute" gears is measured in pressure angle
(symbol "a"), which is the angle of the driving "force line" from the tangent
where the pitch circles touch, which is also the angle of the gear tooth
contact point from the line connecting the centerpoints. Large pressure angles
make the teeth stronger and wider at their base, but make the force transfer
less efficient and increase the load on the bearings. The most common pressure
angle is 20deg.

Backlash (symbol "j") is how much one gear can move when the other is fixed,
and can be measured as circumfrence distance at the pitch circle or angular
rotation. A rule of thumb is backlash distance is about 0.03~0.05 times the
gear module, which translates into `0.04*m/(D*pi)*360 = 0.04/z*360/pi = 4.6/z`
in degrees or `275/z` (or `206/z` to `344/z`) in arcmin.

Note angular backlash is significantly less for larger gears, but high gear
ratios require meshing small and large gears together. In practice the
backlash for each stage is dominated by the size of the smaller gear, so
backlash tends to be worse for higher ratios.

If the sizes of meshing gears is coprime, then every tooth on each gear will
mesh with every tooth on the other gear as they rotate. This helps ensure even
wear and can extend the durability. This is called a hunting tooth design;

https://en.wikipedia.org/wiki/Gear_train#Hunting_and_non-hunting_gear_sets

Most NEMA14 36mm round pancake stepper motors have T10 m0.5 a=20deg gears on a
2.5mm (or 2mm?) shaft, though there are T8 versions too. The square NEMA
steppers have 4mm, 5mm, or 8mm or shafts. DC motors have no-load speeds in the
range 1k~30k rpm. Steppers are max 1k~3k rpm.

The following table shows the characteristics of different gears per-stage.
Stacking stages multiplies ratio and efficiency, and sums backlash. Note
planetary gears have slightly better backlash than spur because the multiple
contact points of the planets combine to constrain it.

type          ratio       max-speed  efficiency    backlash    durability
----------- ------------  --------- ---------- --------------  ----------
spur            1~6       1000~6000     90~96%     20~40arcmin      high
planetary       4~10      1000~6000     90~96%     10~30arcmin      high
worm            5~50      1000~3000     30~60%     0.5~10deg        low
harmonic       30~300     2000~6000     80~90%     10~30arcsec      low
splitring      10~4000    1000~6000     86~95%?    15~45arcmin?     high

Note that splitring can give a very high ratio in a single stage, so it could
give better efficiency and less backlash than multi-staging other other types
of gearbox to achieve the same ratios. However it's efficiency is reported to
suffer because it has high torque loads on the relatively high-speed planet
gears which creates higher losses compared to other gearboxes where the high
torques are only on the slow moving gears. However it's not clear of those
losses would be worse on multi-stage gearboxes to achive the same high ratios.
The main problem is it requires custom non-standard module gears for the
secondary ring and planet gears to do it.

Note there is a max planet size for a given sun or ring to avoid planets
colliding. The more planets, the smaller they can be. This can be solved for
the triangle between the sun-center, planet center, and planet touch point.
The planet center to touch point is 1 tooth larger than the planet radius. The
angle at the center is pi/np. This gives;

  c = Ts/2 + Tp/2  # sun-center to planet-center c in terms of Ts
  a = Tp/2 + 1     # planet center to mid-point between min-distance planets.
  sin(pi/np) = a/c
           s = sin(pi/np)
             = (Tp/2 + 1)/(Ts/2 + Tp/2)
             = (Tp+2)/(Ts + Tp)
 s*(Ts + Tp) = Tp + 2
          Ts = (Tp*(1-s)+2)/s
          Tp = (Ts*s-2)/(1-s)

  c = Tr/2 - Tp/2 # c expressed in terms of Tr
  s*(Tr - Tp) = Tp + 2
          Tr = (Tp*(1+s)+2)/s
          Tp = (Tr*s-2)/(1+s)

This gives us a planet size constraint that can be expressed in terms of Tr or Ts;

   Tp < (s*Tr-2)/(1+s) or Tp < (s*Ts-2)/(1-s) where s=sin(pi/np)

Numbering the planets anti-clockwise starting with planet 0 on the right side
with phase offset 0 (planet tooth in the middle of ring gap), the phase offset
can be different for each planet. Note the phase angle difference in "fraction
of a tooth" for each planet's engagement with the ring is;

Pp(i) = (Tr*i/np) % 1  # where i is the planet number in the range [0,np), or
Pp = (Tr/np) % 1  # the increase in phase offset for each next planet.

This gives the following list of different constraints;

* pgs (planetry gear size): Tr = Ts + 2*Tp. The gears all touch and are
  centered around the sun. If you don't have a sun gear this still applies
  with Ts being the middle gap size. This can possibly be ignored for strange
  eccentric gear arrangements.

* rps (ring and planet size): Tp < (s*Tr-2)/(1+s) or Tp < (s*Ts-2)/(1-s) where
  s=sin(pi/np). The planets fit within the ring and around the sun without
  touching each other. This can be bypassed by offsetting the planets so they
  are on different planes.

* rsm (ring and sun mesh): (Tr+Ts) % np = 0. This is required for correct
  meshing of the ring and sun gears with the planets, but is not required if
  the sun gear is removed. It ensures that the ring and sun gear teeth align
  correctly to mesh with the planets at each planet position.

* rpc (ring and planet coprime): iscoprime(Tr,Tp). This is optional for more
  even wear and better durability of the planet and ring gears. For split-ring
  gears it also enables much higher gear ratios when the second ring and
  planet are both different sizes to the first.

* psc (planet and sun coprime): iscoprime(Tp,Ts). This is optional for more
  even wear and better durability of planet and sun gears.

* rnc (ring and number of planets coprime): iscoprime(Tr,np). This is optional
  and ensures that every planet meshes with the ring with different phase
  offsets. This combined with the "rsm" constraint means the sun and number of
  planets is also coprime and also mesh with different phases. This means
  every planet's teeth engage and disengage with the ring and sun at different
  times, which can smooth the tooth loads reducing wear, backlash, and noise.

* rnf (ring has number of planets as a factor): Tr % np = 0. This is the
  opposite of "rnc" and instead ensures that every planet meshes with the ring
  with the same phase.  This combined with the "rsm" constraint means the sun
  also has the number of planets as a factor. This means every planet's teeth
  engage and disengage with the ring and sun at the same time. This ensures
  the loads are more symetrical, which might reduce oscilations and bearing
  loads and wear.

* rnb (ring has planets balanced): min(Tr*(np//2)%np,-Tr*(np//2)%np) <=1. This
  very optional constraint means the planets on opposite sides of the sun mesh
  with (as close as possible) the same phase. Note this is always true if
  "rnf" is true. This can be combined with "rnc" to improve the load balance
  so it is close to what you get with "rnf". This This might give you the best
  of both worlds with reduced wear of teeth and bearings, less backlash, less
  noise, and less load oscilations.

For the secondary ring and planets, the secondary ring (and first planet) also
starts aligned with zero phase offset for planet 0 on the right hand side.
This means the phase offset between the primary and secondary ring and planet
is zero at position "zero" on the right hand side. The phase difference for
the other planets/positions can be different. This is the starting postion for
assembly.

The above constraints can also be applied to the secondary ring, planets, and
optional idler-sun gears giving pgs2, rps2, rsm2, rpc2, psc2, rnc2, rnf2, and
ppb2 constraints. Additionally we have the following constraint;

* pcd2 (planet carriers have the same diameter) : m*(Ts+Tp) = m2*(Ts2+Tp2).
  The primary and secondry planet centers have the same diameter, so the
  planets are joined on the same axle. Note this can be satisfied for any gear
  sizes with the right m2/m ratio.

* ppe2 (planet phase offsets are equal): The phase offsets between primary and
  secondary planet are the same for every planet. This means the joined
  primary and secondary planet are interchangable. Note it is not enough that
  the phase offsets between first and second planets at the ring mesh point be
  the same, since if the planets have different sizes the offset "shifts" as
  you go around the planet. Instead the requirement is that each planet has at
  least one tooth where the phase offset between primary and secondary planet
  is zero, like planet 0 has at position 0.

  # primary and secondary planet 1 rotation from mesh point equal at a tooth.
  (Tr/np+k1)/Tp = (Tr2/np + k2)/Tp2     # for k1,k2 are integers.
  Tr*Tp2/np - Tr2*Tp/np = k2*Tp - k1*Tp2
  Tr*Tp2 - Tr2*Tp = (k2*Tp - k1*Tp2)*np
  Tr*Tp2 - Tr2*Tp = k3*lcf(Tp,Tp2)*np   # for k3 is an integer.
  Tr*Tp2 - Tr2*Tp = k3*pf*np            # where pf=gcd(Tp,Tp2)
  Tr*Tp2/pf - Tr2*Tp/pf = k3*np
  Tr*Tp2/pf - Tr2*Tp/pf = 0 (mod np)
  Tr*Tp2/pf = Tr2*Tp/pf (mod np)

  # rotation angle for each planet.
  pr = (Tr2- Tr)/(Tp2 - Tp) * 1/np  # for Tp2 != Tp
     = 0                            # for Tp2 = Tp

  Note this is always true for rnf=rnf2=True, with the zero-offset point for
  each planet at the ring mesh point.

"""

from math import *
from constraints import *
from stats1 import *

# See https://khkgears.net/new/gear-module.html
# most common "I" gear module values.
m_stdI = [
    0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0,
    6.0, 8.0, 10.0]
# less common "II" gear module values.
m_stdII = [
    0.15, 0.25, 0.35, 0.45, 0.55, 0.7, 0.75, 0.9, 1.125, 1.1375, 1.75, 2.25,
    2.75, 3.5, 4.5, 5.5, 7.0, 9.0]

# Practical gear and module min and max values. Tmin=4 is not really
# practical, but is the minimum physically possible idler size with no shaft.
Tmin, Tmax = 4, 1000
Mmin, Mmax = 0.1, 10.0
Mtol = 0.0005
Mdef = 1.0


def iscoprime(i1,i2):
  return gcd(i1, i2) == 1


def clamp(v,vmin,vmax):
  """Clamp a value between vmin and vmax."""
  return min(max(vmin,v),vmax)

def fceil(v, n=0):
  """ciel a float to n decimal digits."""
  m = 10**n
  return ceil(v*m)/m

def ffloor(v, n=0):
  """floor a float to n decimal digits."""
  m = 10**n
  return floor(v*m)/m

def gearstr(name, T, m=1.0):
  """stringify a gear."""
  D = T*m
  return f'{name}({T=}, {D=:.3f}mm {m=:.3f}mm)'


def intD(T, m=1.0, ring=False):
  """Get the inside diameter of a gear from the size and module."""
  if ring:
    return round((T - 2)*m, 3)
  return round((T - 2*1.25)*m, 3)


def extD(T, m=1.0, ring=False):
  """Get the outside diameter of a gear from the size and module."""
  if ring:
    return round((T+2*1.25)*m, 3)
  return round((T+2)*m, 3)


def extT(D, m=1.0, ring=False):
  """Get the gear size from the outside diameter and module."""
  if ring:
    return floor(D/m - 2*1.25)
  return floor(D/m-2)


def intT(D, m=1.0, ring=False):
  """Get the gear size from the inside diameter and module."""
  if ring:
    return floor(D/m + 2)
  return floor(D/m + 2*1.25)


def extM(D, T, ring=False):
  """Get the module from the gear size and outside diameter."""
  if ring:
    return ffloor(D/(T + 2*1.25), 3)
  return ffloor(D/(T + 2), 3)


def intM(D, T, ring=False):
  """Get the module from the gear size and inside diameter."""
  if ring:
    return fceil(D/(T - 2), 3)
  return fceil(D/(T - 2*1.25), 3)


def maxTp(rmax=Tmax, smax=Tmax, n=3):
  """Get pmax given rmax and/or smax and n.

  The calculation for Tp from Ts or Tr with planets just not touching given
  s=sin(pi/n) is;

  (Ts+Tp)*s = Tp+2                     (Tr-Tp)*s = Tp+2
  s*Ts - 2 = (1-s)*Tp                  s*Tr - 2 = (1+s)*Tp
  Tp = (s*Ts - 2)/(1-s)                Tp = (s*Tr - 2)/(1+s)
  """
  # handle n==2 to avoid division by zero.
  if n == 2:
    return (rmax-2)//2
  s = sin(pi/n)
  return min(floor((rmax*s-2)/(1+s)), floor((smax*s-2)/(1-s)))


def minTr(pmin=Tmin, n=3):
  """Get rmin given pmin and n."""
  s = sin(pi/n)
  return ceil((pmin*(1+s)+2)/s)


def minTs(pmin=Tmin, n=3):
  """Get smin given pmin and n."""
  s = sin(pi/n)
  return ceil((pmin*(1-s)+2)/s)


def assertTValid(T, tmin=Tmin, tmax=Tmax):
  assert isinstance(T, int), f'Invalid type: T={T!r} is not an int.'
  assert tmin <= T <= tmax, f'Invalid value: {T=} violates {tmin} <= T <= {tmax}.'


class SGears(object):
  """ A base class for a simple gear pair. """
  Ts : int  # number of sun gear teeth
  Tp : int  # number of planet gear teeth

  def __init__(self, Ts, Tp, m:float=Mdef):
    self.Ts, self.Tp, self.m = Ts, Tp, m

  def __str__(self):
    prefix = f'{self.__class__.__name__}(R={self.R:.1f}, m={self.m:.3f}'
    ts=gearstr('ts', self.Ts, self.m)
    tp=gearstr('tp', self.Tp, self.m)
    return ',\n  '.join([prefix, ts, tp]) + ')'

  def __lt__(self, other):
    return self.R < other.R

  @property
  def R(self):
    return self.Tp/self.Ts


class CGears(SGears):
  """ A base class for gears with a ring gear, planet gears, and carrier.

  This has a Ts attribute, but it is for indicating the middle gap and is not
  required to be a valid gear with valid meshing.
  """
  Tr : int  # number of sun gear teeth
  Tp : int  # number of planet gear teeth
  Ts : int  # middle "sun" gap/gear teeth
  np : int  # number of planetary gears.
  m : float # gear teeth module (diameter / teeth)
  R : float = 1.0

  @classmethod
  def assertValid(cls, Tr=None, Tp=None, Ts=None, np=3, **kwargs):
    assert (Tr,Tp,Ts).count(None) < 2, f'Insufficient args: {Tr=},{Tp=},{Ts=} need to set 2.'
    if Tr is None and Tp and Ts: Tr = Ts + 2*Tp
    if Tp is None and Tr and Ts: Tp = (Tr - Ts)//2
    if Ts is None and Tr and Tp: Ts = Tr - 2*Tp
    assert isinstance(Tr, int), f'Invaid type: Tr={Tr!r} is not int.'
    assert isinstance(Tp, int), f'Invaid type: Tp={Tp!r} is not int.'
    assert isinstance(Ts, int), f'Invaid type: Ts={Ts!r} is not int.'
    assert Tmin <= Tr <= Tmax, f'Invalid size: {Tr=} violates {Tmin}<=T<={Tmax}.'
    assert Tmin <= Tp <= Tmax, f'Invalid size: {Tp=} violates {Tmin}<=T<={Tmax}.'
    assert Tr == Ts + 2*Tp, f'Invalid sizes: {Tr=},{Tp=},{Ts=} violates Tr=Ts+2*Tp.'
    assert Tp <= maxTp(rmax=Tr, n=np), f'Invalid sizes: {Tr=},{Tp=},{np=} violates Tp+2<(Tr-Tp)*sin(pi/np).'
    return Tr,Tp,Ts

  def __init__(self, Tr=None, Tp=None, Ts=None, np:int=3, m:float=Mdef, **kwargs):
    Tr, Tp, Ts = CGears.assertValid(Tr=Tr, Tp=Tp, Ts=Ts, np=np, **kwargs)
    self.Tr, self.Tp, self.Ts, self.np, self.m = Tr, Tp, Tr-2*Tp, np, m

  def __str__(self):
    prefix = f'{self.__class__.__name__}(R={self.R:.1f}, np={self.np}, m={self.m:.3f}'
    r=gearstr('r', self.Tr, self.m)
    p=gearstr('p', self.Tp, self.m) + f', Pp={self.Pp:.3f}'
    return ',\n  '.join([prefix, r, p]) + ')'

  @property
  def Dr(self):
    return self.Tr * self.m

  @property
  def Dp(self):
    return self.Tp * self.m

  @property
  def Ds(self):
    return self.Ts * self.m

  @property
  def Dc(self):
    return self.Dr - self.Dp

  @property
  def Dext(self):
    """ Get the external diameter of the ring gear."""
    return extD(self.Tr, self.m, ring=True)

  @property
  def Dint(self):
    """ Get the internal diameter of the sun gear/gap."""
    return intD(self.Ts, self.m, ring=False)

  @property
  def Pp(self):
    """ The phase offset in fractions of a tooth at contact point for each planet gear."""
    return self.Tr / self.np % 1


class PGears(CGears):
  """ This is a normal single-stage planetary gearbox.

  This is the same as CGears but also requires Ts is a valid gear with valid meshing.
  """

  @classmethod
  def assertValid(cls, Tr=None, Tp=None, Ts=None, np=3, **kwargs):
    Tr, Tp, Ts = super().assertValid(Tr=Tr, Tp=Tp, Ts=Ts, np=np, **kwargs)
    assert Tmin <= Ts <= Tmax, f'Invalid size: {Ts=} violates {Tmin}<=T<={Tmax}.'
    assert (Tr+Ts) % np == 0, f'Invalid mesh: {Tr=},{Ts=},{np=} violates (Tr+Ts)%np=0.'
    return Tr,Tp,Ts

  def __init__(self, Tr=None, Tp=None, Ts=None, np:int=3, m:float=Mdef, **kwargs):
    Tr, Tp, Ts = PGears.assertValid(Tr=Tr, Tp=Tp, Ts=Ts, np=np, **kwargs)
    super().__init__(Tr=Tr, Tp=Tp, Ts=Ts, np=np, m=m, **kwargs)

  def __str__(self):
    prefix=super().__str__()[:-1]
    s=gearstr('s', self.Ts, self.m)
    return prefix + f',\n  {s})'

  @property
  def R(self):
    return (self.Ts+self.Tr)/self.Ts


class SRGears(CGears):
  """A simple split ring gearbox.

  This has no sun gear, just primary and secondary rings and planets, with the input being the carrier.
  """
  dr : int # number of additional teeth in the secondary ring gear.
  dp : int # number of additional teeth in the secondary planet gear.

  @classmethod
  def assertValid(cls, Tr=None, Tp=None, Ts=None, Tr2=None, Tp2=None, Ts2=None, dr=None, dp=None, np=3, **kwargs):
    Tr, Tp, Ts = super().assertValid(Tr=Tr, Tp=Tp, Ts=Ts, dr=dr, dp=dp, np=np, **kwargs)
    assert ((Tr2 or dr), (Tp2 or dp), Ts2).count(None) < 2, f'Insufficient args: {Tr2=} or {dr=}, {Tp2=} or {dp=}, {Ts2=} need to set 2.'
    # Default dr to np if insufficient other args to derive it.
    #if not dr and not (Tr2 or ((Tp2 or dp) and Ts2)): dr = np
    # Default dp to 0 if insufficient other args to derive it.
    #if not dp and not (Tp2 or ((Tr2 or dr) and Ts2)): dp = 0
    if Tr2 is None and dr: Tr2 = Tr + dr
    if Tp2 is None and dp: Tp2 = Tp + dp
    Tr2, Tp2, Ts2 = CGears.assertValid(Tr=Tr2, Tp=Tp2, Ts=Ts2, dr=dr, dp=dp, np=np, **kwargs)
    if dr is None: dr = Tr2-Tr
    if dp is None: dp = Tp2-Tp
    assert Tr + dr == Tr2, f'Conflicting args: {Tr=}, {Tr2=}, {dr=} violates Tr2=Tr+dr.'
    assert Tp + dp == Tp2, f'Conflicting args: {Tp=}, {Tp2=}, {dp=} violates Tp2=Tp+dp.'
    return Tr,Tp,Ts,dr,dp

  def __init__(self, Tr=None, Tp=None, Ts=None, Tr2=None, Tp2=None, Ts2=None, dr=None, dp=None, np=3, m=Mdef, **kwargs):
    Tr, Tp, Ts, dr, dp = SRGears.assertValid(Tr=Tr, Tp=Tp, Ts=Ts, Tr2=Tr2, Tp2=Tp2, Ts2=Ts2, dr=dr, dp=dp, np=np, **kwargs)
    super().__init__(Tr=Tr, Tp=Tp, Ts=Ts, Tr2=Tr2, Tp2=Tp2, Ts2=Ts2, dr=dr, dp=dp, np=np, m=m, **kwargs)
    self.dr, self.dp = dr, dp

  def __str__(self):
    prefix = super().__str__()[:-1]
    prefix = prefix.replace('\n', f' m2={self.m2:.3f}, N={self.N},\n', count=1)
    r2=gearstr('r2', self.Tr2, self.m2)
    p2=gearstr('p2', self.Tp2, self.m2) + f', Pp2={self.Pp2:.3f}'
    return ',\n  '.join([prefix,r2,p2]) + ')'

  @property
  def Tr2(self):
    return self.Tr + self.dr

  @property
  def Tp2(self):
    return self.Tp + self.dp

  @property
  def Ts2(self):
    return self.Tr2 - 2*self.Tp2

  @property
  def m2(self):
    """module of the secondary gears. """
    return self.m * (self.Tr - self.Tp) / (self.Tr2 - self.Tp2)

  @property
  def Dr2(self):
    return self.Tr2 * self.m2

  @property
  def Dp2(self):
    return self.Tp2 * self.m2

  @property
  def Ds2(self):
    return self.Ts2 * self.m2

  @property
  def D(self):
    return max(self.Dr, self.Dr2)

  @property
  def Dext(self):
    return max(super().Dext, extD(self.Tr2, self.m2, ring=True))

  @property
  def Dint(self):
    """This is the hole in the middle between the planets for cabling etc."""
    return min(super().Dint, intD(self.Ts2, self.m2, ring=False))

  @property
  def Pp2(self):
    """ The phase offset in fractions of a tooth at contact point each secondary planet gear."""
    return self.Tr2 / self.np % 1

  @property
  def N(self):
    return self.dr*self.Tp - self.dp*self.Tr

  @property
  def R(self):
    try:
      return self.Tr2*self.Tp / self.N
    except ZeroDivisionError:
      return inf

  def dpmax(self, dr):
    """Get dp for max R for a given dr."""
    return round(dr * self.Tp/self.Tr)


class SRPGears(SRGears, PGears):
  """A split ring compound planetary gearbox with a sun. """

  @property
  def R1(self):
    """Gear ratio of the first stage (ws/wc)."""
    return super(SRGears,self).R

  @property
  def R2(self):
    """Gear ratio of the second stage (wr2/wc)."""
    return super().R

  @property
  def R(self):
    return self.R1 * self.R2


class SRIGears(SRPGears):
  """A split ring compound planetary gearbox with sun and idler secondary sun."""

  @classmethod
  def assertValid(cls, Tr=None, Tp=None, Ts=None, Tr2=None, Tp2=None, Ts2=None, dr=None, dp=None, np=3, **kwargs):
    Tr, Tp, Ts, dr, dp = super().assertValid(Tr=Tr, Tp=Tp, Ts=Ts, Tr2=Tr2, Tp2=Tp2, Ts2=Ts2, dr=dr, dp=dp, np=np, **kwargs)
    Tr2, Tp2, Ts2 = PGears.assertValid(Tr=Tr+dr, Tp=Tp+dp, np=np, **kwargs)
    return Tr,Tp,Ts,dr,dp

  def __init__(self, Tr=None, Tp=None, Ts=None, Tr2=None, Tp2=None, Ts2=None, dr=None, dp=None, np=3, m=Mdef, **kwargs):
    Tr, Tp, Ts, dr, dp = SRIGears.assertValid(Tr=Tr, Tp=Tp, Ts=Ts, Tr2=Tr2, Tp2=Tp2, Ts2=Ts2, dr=dr, dp=dp, np=np, **kwargs)
    super().__init__(Tr=Tr, Tp=Tp, Ts=Ts, Tr2=Tr2, Tp2=Tp2, Ts2=Ts2, dr=dr, dp=dp, np=np, m=m, **kwargs)

  def __str__(self):
    prefix = super().__str__()[:-1]
    s2=gearstr('s2', self.Ts2, self.m2)
    return prefix + f',\n  {s2})'


def TpRange(rr=None, rp=None, rs=None, n=3, tmin=Tmin, tmax=Tmax, smin=None):
  """Get the (pmin,pmax) range from rr, rp, and rs ranges.

  The rr, rp, and rs arguments can be None for max range, a number for a fixed
  value, or an inclusive (min,max) range-tuple.

  For pmax this gives the largest size that can fit inside rmax without
  planets touching, outside smax without planets touching, fits between rmax
  and smin, and is not larger than the input pmax.

  For pmin this gives the smallest size that fits between rmin and smax, and
  is not smaller than the input pmin.

  Note this will limit rr and rp within (tmin,tmax), and rs within
  (smin,tmax), so you can set smin=2 for SRGears that don't have a sun gear
  but requre the planets not to touch in the middle.
  """
  if smin is None: smin = tmin
  rmin,rmax = IRange(rr, smin+2*tmin, tmax)
  pmin,pmax = IRange(rp, tmin, (rmax-smin)//2)
  smin,smax = IRange(rs, smin, rmax-2*pmin)
  pmax = min(maxTp(rmax,smax,n), (rmax-smin)//2, pmax)
  # We roundup to give pmin for valid combinations of Tr>=rmin, Ts<=smax.
  pmin = max(pmin, (rmin - smax+1)//2)
  return pmin,pmax


def TsRange(rr=None, rp=None, rs=None, n=3, tmin=Tmin, tmax=Tmax, smin=None):
  """Get the (smin,smax) range from rr, rp, and rs ranges."""
  if smin is None: smin = tmin
  rmin,rmax = IRange(rr, smin+2*tmin, tmax)
  pmin,pmax = IRange(rp, tmin, (rmax-smin)//2)
  smin,smax = IRange(rs, smin, rmax-2*pmin)
  smin = max(minTs(pmin,n), rmin-2*pmax, smin)
  smax = min(rmax-2*pmin, smax)
  return smin,smax


def TrRange(rr=None, rp=None, rs=None, n=3, tmin=Tmin, tmax=Tmax, smin=None):
  """Get the (smin,smax) range from rr, rp, and rs ranges."""
  if smin is None: smin = tmin
  rmin,rmax = IRange(rr, smin+2*tmin, tmax)
  pmin,pmax = IRange(rp, tmin, (rmax-smin)//2)
  smin,smax = IRange(rs, smin, rmax-2*pmin)
  rmin = max(minTr(pmin,n), smin+2*pmin, rmin)
  rmax = min(smax+2*pmax, rmax)
  return rmin,rmax


def MRange(r, s, rm=None, Dint=None, Dext=None, mmin=Mmin, mmax=Mmax):
  """ Get the (mmin,mmax) range from r, s, rm, Dint, and Dext."""
  if Dint: mmin = max(intM(Dint, s, ring=False), mmin)
  if Dext: mmax = min(extM(Dext, r, ring=True), mmax)
  return Range(rm,mmin,mmax)


def TLimits(cm=Mdef, Dint=None, Dext=None, tmin=Tmin, tmax=Tmax, smin=2):
  mmin,mmax = ConstraintRange(cm, Mmin, Mmax)
  if Dext: tmax = min(extT(Dext, mmin), tmax)
  if Dint: smin = max(intT(Dint, mmax), smin)
  return tmin,tmax,smin


def iterRPS(cr=None, cp=None, cs=None, n=3, spr=inf,
    rsm=True, rpc=False, psc=False, rnc=False, rnf=False, rnb=False,
    tmin=Tmin, tmax=Tmax, smin=2):
  """Iterate through r,p,s values matching constraints.

  Args:
    cr: constraint for r ring gear sizes.
    cp: constraint for p planet gear sizes.
    cs: constraint for s sun gear sizes.
    n: number of planets.
    spr: max sun to planet ratio.
    rsm: ring and sun must mesh correctly.
    rpc: ring and planet must be coprime.
    psc: planet and sun must be coprime.
    rnc: ring and number of planets must be coprime.
    rnf: ring must have number of planets as a factor.
    rnb: ring and planets must be balanced (opposite sides have almost same phase).
  """
  nr = np = ny = 0
  # Change cs to a set for faster inclusion testing and adjust ranges.
  rs = TsRange(n=n, tmin=tmin, tmax=tmax, smin=smin)
  cs = IConstraintSet(cs, *rs)
  rs = min(cs), max(cs)
  rr = TrRange(rs=rs, n=n, tmin=tmin, tmax=tmax, smin=smin)
  for r in iterIConstraint(cr,*rr):
    nr += 1
    rp = (ceil(r/(2+spr)), tmax)
    rp = TpRange(rr=r, rp=rp, rs=rs, n=n, tmin=tmin, tmax=tmax, smin=smin)
    for p in iterIConstraint(cp, *rp):
      np += 1
      s = r - 2*p
      if (s not in cs or
          (rsm and (r+s) % n) or
          (rpc and not iscoprime(r,p)) or
          (psc and not iscoprime(p,s)) or
          (rnc and not iscoprime(r,n)) or
          (rnf and r % n) or
          (rnb and min(r*(n//2)%n,-r*(n//2)%n) > 1 and gcd(r,n) <= 2)):
        #print(f'{r=} {p=} {s=} {n=} fails planetary constraints.')
        continue
      #print(f'{r=} {p=} {s=} {n=} passes planetary constraints.')
      ny += 1
      yield r,p,s
  # print(f'''iterRPS({cr=}, {cp=}, {cs=}, {n=},
  #   {cm=}, {Dint=}, {Dext=},
  #   {rsm=}, {rpc=}, {psc=}, {rnc=}, {rnf=},
  #   {tmin=}, {tmax=}, {smin=}):
  # tested {nr} r sizes, {np} p sizes, and yielded {ny} r,p,s sizes.''')


def iterRPS2(r, p, s, cr2=None, cp2=None, cs2=None, n=3,
    rs2m=False, rp2c=False, ps2c=False, rn2c=False, rn2f=False, rn2b=False, pp2e=False,
    tmin=Tmin, tmax=Tmax, smin=2):
  """Iterate through r2,p2,s2,rm2 values matching constraints.

  Args:
    r: ring gear size.
    p: planet gear size.
    s: sun gear size.
    cr2: constraint for r2 ring gear sizes.
    cp2: constraint for p2 planet gear sizes.
    cs2: constraint for s2 sun gear sizes.
    n: number of planets.
    rs2m: ring2 and sun2 must mesh correctly.
    rp2c: ring2 and planet2 must be coprime.
    ps2c: planet2 and sun2 must be coprime.
    rn2c: ring2 and number of planets must be coprime.
    rn2f: ring2 must have number of planets as a factor.
    rn2b: ring2 and planets must be balanced (opposite sides have almost same phase).
    pp2e: planet and planet2 phases offsets the same for all planets.
  """
  nrps2 = ny = 0
  for r2,p2,s2 in iterRPS(cr=cr2, cp=cp2, cs=cs2, n=n,
      rsm=rs2m, rpc=rp2c, psc=rp2c, rnc=rn2c, rnf=rn2f, rnb=rn2b,
      tmin=tmin, tmax=tmax, smin=smin):
    nrps2 += 1
    if pp2e and ((r*p2-r2*p)/gcd(p,p2))%n:
      #print(f'{r=} {p=} {s=} {r2=} {p2=} {s2=} {n=} fails ring2 constraints.')
      continue
    #print(f'{r=} {p=} {s=} {r2=} {p2=} {s2=} {n=} passes ring2 constraints.')
    ny += 1
    yield r2,p2,s2
  # print(f'''iterRPS2({r=}, {p=}, {s=}, {cr2=}, {cp2=}, {cs2=}, {n=},
  #   {cm2=}, {Dint=}, {Dext=},
  #   {rs2m=}, {rp2c=}, {ps2c=}, {rn2c=}, {rn2f=}, {pp2e=},
  #   {tmin=}, {tmax=}, {smin=}):
  # tested {nrps2} r2,p2,s2 sizes, and yielded {ny} r2,p2,s2 sizes.''')


def iterM(r, p, s, cm, Dint=None, Dext=None, mmin=Mmin, mmax=Mmax, mtol=Mtol):
  mmin,mmax = MRange(r, s, Dint=None, Dext=None, mmin=mmin, mmax=mmax)
  for rm in iterConstraint(cm, mmin, mmax, mtol):
    yield RangeValue(rm)


def iter2M(r, p, s, r2, p2, s2, cm, cm2, Dint=None, Dext=None, mmin=Mmin,mmax=Mmax,mtol=Mtol):
  nm2 = ny = 0
  m2min,m2max = MRange(r2, s2, Dint=Dint, Dext=Dext, mmin=mmin, mmax=mmax)
  mmin,mmax = MRange(r, s, Dint=Dint, Dext=Dext, mmin=mmin, mmax=mmax)
  m_m2 = (r2-p2)/(r-p)
  m2min = max(mmin/m_m2, m2min)
  m2max = min(mmax/m_m2, m2max)
  for im2min,im2max in iterConstraint(cm2,m2min,m2max,mtol):
    nm2 += 1
    for rm in iterConstraint(cm, im2min*m_m2, im2max*m_m2, mtol):
      ny += 1
      #print(f'{r=} {p=} {s=} {r2=} {p2=} {s2=} {rm=} passes module constraints.')
      yield RangeValue(rm)
  # print(f'''iterM({r=}, {p=}, {s=}, {r2=}, {p2=}, {s2=},
  #   {cm=}, {cm2=}, {Dint=}, {Dext=},
  #   {mmin=}, {mmax=}, {mtol=}):
  # tested {nm2} m2 ranges, and yielded {ny} m values.''')


def iterRPSM(cr=None, cp=None, cs=None, n=3, cm=Mdef, Dint=None, Dext=None, spr=inf,
    rsm=False, rpc=False, psc=False, rnc=False, rnf=False, rnb=False,
    tmin=Tmin, tmax=Tmax, smin=None, mmin=Mmin, mmax=Mmax, mtol=Mtol):
  # Default smin=tmin, but if rsm is false assume no sun gear and default smin=2.
  if smin is None: smin = tmin if rsm else 2
  nrps = ny = 0
  tmin, tmax, smin = TLimits(cm, Dint, Dext, tmin, tmax, smin)
  for r,p,s in iterRPS(cr, cp, cs, n, spr, rsm, rpc, psc, rnc, rnf, rnb, tmin, tmax, smin):
    nrps += 1
    for m in iterM(r, p, s, cm, Dint, Dext, mmin, mmax, mtol):
        ny += 1
        yield r, p, s, m
  # print(f"""iterRPSM({cr=}, {cp=}, {cs=}, {n=},
  #   {cm=}, {Dint=}, {Dext=},
  #   {rsm=}, {rpc=}, {psc=}, {rnc=}, {rnf=},
  #   {tmin=}, {tmax=}, {smin=},
  #   {mmin=}, {mmax=}, {mtol=}):
  # tested {nrps} r,p,s sizes, and yielded {ny} results.""")


def iterRPS2M(cr=None, cp=None, cs=None, cr2=None, cp2=None, cs2=None, n=3,
    cm=Mdef, cm2=None, Dint=None, Dext=None, spr=inf,
    rsm=False, rpc=False, psc=False, rnc=False, rnf=False, rnb=False,
    rs2m=False, rp2c=False, ps2c=False, rn2c=False, rn2f=False, rn2b=False, pp2e=False,
    tmin=Tmin, tmax=Tmax, smin=None, s2min=None, mmin=Mmin, mmax=Mmax, mtol=Mtol):
  # Default smin=tmin, but if rsm is false assume no sun gear and default smin=2.
  if smin is None: smin = tmin if rsm else 2
  if s2min is None: s2min = tmin if rs2m else 2
  nrps = nrps2 = nm = ny = 0
  t2min, t2max, s2min = TLimits(cm2, Dint, Dext, tmin, tmax, s2min)
  tmin, tmax, smin = TLimits(cm, Dint, Dext, tmin, tmax, smin)
  for r,p,s in iterRPS(cr, cp, cs, n, spr, rsm, rpc, psc, rnc, rnf, rnb, tmin, tmax, smin):
    nrps += 1
    for r2,p2,s2 in iterRPS2(r, p, s, cr2, cp2, cs2, n,
        rs2m, rp2c, ps2c, rn2c, rn2f, rn2b, pp2e, t2min, t2max, s2min):
      nrps2 += 1
      # Skip combinations with N=0, AKA R=inf.
      if r2*p == p2*r:
        continue
      for m in iter2M(r, p, s, r2, p2, s2, cm, cm2, Dint, Dext, mmin, mmax, mtol):
        ny += 1
        yield r, p, s, r2, p2, s2, m
  # print(f"""iterRPS2M({cr=}, {cp=}, {cs=}, {cr2=}, {cp2=}, {cs2=}, {n=},
  #   {cm=}, {cm2=}, {Dint=}, {Dext=},
  #   {rsm=}, {rpc=}, {psc=}, {rnc=}, {rnf=}, {rnb=},
  #   {rs2m=}, {rp2c=}, {ps2c=}, {rn2c=}, {rn2f=}, {rn2b=}, {pp2e=},
  #   {tmin=}, {tmax=}, {smin=}, {s2min=},
  #   {mmin=}, {mmax=}, {mtol=}):
  # tested {nrps} r,p,s sizes, {nrps2} r2,p2,s2 sizes, and yielded {ny} results.""")


def iterSGears(cs=None, cp=None, cm=0.5, R=None, psc=False, tmin=Tmin, tmax=Tmax):
  """ Iterate through gear pairs that satisfy constraints.

  The Ts and Tp constraints are the sizes of the first and second gear as an
  int, a (min,max) range tuple, or an iterable of ints or range-tuples. The
  psc argument can be set true to require the sizes be coprime.
  """
  for s in iterIConstraint(cs,tmin,tmax):
    for p in iterIConstraint(cp,tmin,tmax):
      if not psc or iscoprime(p,s):
        g=SGears(s,p,cm)
        if not R or inConstraint(g.R, R):
          yield g


def iterPGears(cr=None, cp=None, cs=None, n=3, cm=Mdef, Dint=None, Dext=None, spr=inf,
    rpc=False, psc=False, rnc=False, rnf=False, rnb=False,
    tmin=Tmin, tmax=Tmax, smin=None, mmin=Mmin, mmax=Mmax, mtol=Mtol):
  """ Iterate through all valid planetary gear combinations within constraints.

  This yields all possible valid PGears instances within the cr, cp, cs, n,
  cm, Dext, Dint, and rpc, psc, rnc, rnf, rnb, constraints provided. The c, cp,
  cs, and cm values can be any valid constraint as used by iterValues(). Dext
  can be a max ring gear outer diameter, and Dint can be a min sun gear inner
  diameter.

  """
  rsm=True
  for r,p,s,m in iterRPSM(cr, cp, cs, n, cm, Dint, Dext, spr,
      rsm, rpc, psc, rnc, rnf, rnb, tmin, tmax, smin, mmin, mmax, mtol):
    g=PGears(Tr=r,Tp=p,Ts=s,np=n,m=m)
    assert Dint is None or g.Dint >= Dint, f'failed {g.Dint=} >= {Dint} for {g=!s}.'
    assert Dext is None or g.Dext <= Dext, f'failed {g.Dext=} <= {Dext} for {g=!s}.'
    assert inConstraint(cm, g.m, vtol=mtol)
    yield g


def iterSRGears(cr=None, cp=None, cs=None, cr2=None, cp2=None, cs2=None, n=3,
    cm=Mdef, cm2=None, Dint=None, Dext=None, spr=inf,
    rsm=False, rpc=False, psc=False, rnc=False, rnf=False, rnb=False,
    rs2m=False, rp2c=False, ps2c=False, rn2c=False, rn2f=False, rn2b=False, pp2e=False,
    tmin=Tmin, tmax=Tmax, smin=None, s2min=None, mmin=Mmin, mmax=Mmax, mtol=Mtol):
  for r,p,s,r2,p2,s2,m in iterRPS2M(cr, cp, cs, cr2, cp2, cs2, n, cm, cm2, Dint, Dext, spr,
      rsm, rpc, psc, rnc, rnf, rnb, rs2m, rp2c, ps2c, rn2c, rn2f, rn2b, pp2e,
      tmin, tmax, smin, s2min, mmin, mmax, mtol):
    g=SRGears(Tr=r,Tp=p,Ts=s,Tr2=r2,Tp2=p2,Ts2=s2,np=n,m=m)
    assert Dint is None or g.Dint >= Dint, f'failed {g.Dint=} >= {Dint} for {g=!s}.'
    assert Dext is None or g.Dext <= Dext, f'failed {g.Dext=} <= {Dext} for {g=!s}.'
    assert inConstraint(cm, g.m, vtol=mtol)
    assert inConstraint(cm2, g.m2, vtol=mtol)
    assert g.N != 0
    yield g


def iterSRPGears(cr=None, cp=None, cs=None, cr2=None, cp2=None, cs2=None, n=3,
    cm=Mdef, cm2=None, Dint=None, Dext=None, spr=inf,
    rpc=False, psc=False, rnc=False, rnf=False, rnb=False,
    rs2m=False, rp2c=False, ps2c=False, rn2c=False, rn2f=False, rn2b=False, pp2e=False,
    tmin=Tmin, tmax=Tmax, smin=None, s2min=None, mmin=Mmin, mmax=Mmax, mtol=Mtol):
  rsm=True
  for r,p,s,r2,p2,s2,m in iterRPS2M(cr, cp, cs, cr2, cp2, cs2, n, cm, cm2, Dint, Dext, spr,
      rsm, rpc, psc, rnc, rnf, rnb, rs2m, rp2c, ps2c, rn2c, rn2f, rn2b, pp2e,
      tmin, tmax, smin, s2min, mmin, mmax, mtol):
    g=SRPGears(Tr=r,Tp=p,Ts=s,Tr2=r2,Tp2=p2,Ts2=s2,np=n,m=m)
    assert Dint is None or g.Dint >= Dint, f'failed {g.Dint=} >= {Dint} for {g=!s}.'
    assert Dext is None or g.Dext <= Dext, f'failed {g.Dext=} <= {Dext} for {g=!s}.'
    assert inConstraint(cm, g.m, vtol=mtol)
    assert inConstraint(cm2, g.m2, vtol=mtol)
    assert g.N != 0
    yield g


def iterSRIGears(cr=None, cp=None, cs=None, cr2=None, cp2=None, cs2=None, n=3,
    cm=Mdef, cm2=None, Dint=None, Dext=None, spr=inf,
    rpc=False, psc=False, rnc=False, rnf=False, rnb=False,
    rp2c=False, ps2c=False, rn2c=False, rn2f=False, rn2b=False, pp2e=False,
    tmin=Tmin, tmax=Tmax, smin=None, s2min=None, mmin=Mmin, mmax=Mmax, mtol=Mtol):
  rsm=rs2m=True
  for r,p,s,r2,p2,s2,m in iterRPS2M(cr, cp, cs, cr2, cp2, cs2, n, cm, cm2, Dint, Dext, spr,
      rsm, rpc, psc, rnc, rnf, rnb, rs2m, rp2c, ps2c, rn2c, rn2f, rn2b, pp2e,
      tmin, tmax, smin, s2min, mmin, mmax, mtol):
    g=SRIGears(Tr=r,Tp=p,Ts=s,Tr2=r2,Tp2=p2,Ts2=s2,np=n,m=m)
    assert Dint is None or g.Dint >= Dint, f'failed {g.Dint=} >= {Dint} for {g=!s}.'
    assert Dext is None or g.Dext <= Dext, f'failed {g.Dext=} <= {Dext} for {g=!s}.'
    assert inConstraint(cm, g.m, vtol=mtol)
    assert inConstraint(cm2, g.m2, vtol=mtol)
    assert g.N != 0
    yield g


# def iterdp(Tp, np=3, tmin=Tmin, tmax=Tmax, smin=2):
#   """Iterate through dp ranges for a given Tp."""
#   tp2min, tp2max = TpRange(n=np,tmin=tmin,tmax=tmax,smin=smin)
#   return range(tp2min-Tp, tp2max-Tp)


# def iterdr(Tr, Tp, dp, np=3, m=0.5, m2=None, Dext=None, Dint=None, tmin=Tmin, tmax=Tmax, smin=2):
#   """Iterate through (m,dr) values for given Tr,Tp, dp values and m and m2 constraints."""
#   Tp2 = Tp + dp
#   Tr2min,Tr2max = TrRange(rp=Tp2, n=np, tmin=tmin, tmax=tmax, smin=smin)
#   Ts2min,Ts2max = TsRange(rp=Tp2, n=np, tmin=tmin, tmax=tmax, smin=smin)
#   rmmin,rmmax = rm2min,rm2max = Mmin,Mmax
#   if Dext:
#     rmmax = min(rmmax, extM(Dext, Tr, ring=True))
#     rm2max = min(rm2max, extM(Dext, Tr2min, ring=True))
#   if Dint:
#     rmmin = max(rmmin, intM(Dint, Tr - 2*Tp, ring=False))
#     rm2min = max(rm2min, intM(Dint, Ts2max, ring=False))
#   for mmin,mmax in iterConstraint(m,vmin=rmmin,vmax=rmmax,vtol=Mtol):
#     for m2min,m2max in iterConstraint(m2,vmin=rm2min,vmax=rm2max,vtol=Mtol):
#       drmin = max(ceil((Tr-Tp)*(mmin/m2max - 1)) + dp, Tr2min - Tr)
#       drmax = min(floor((Tr-Tp)*(mmax/m2min - 1)) + dp, Tr2max - Tr)
#       if Dext: drmax = min(drmax, extT(Dext, m2min, ring=True) - Tr)
#       if Dint: drmin = max(drmin, intT(Dint, m2max) + 2*Tp - Tr)
#       for dr in range(drmin, drmax+1):
#         Tr2 = Tr + dr
#         m_m2  = (Tr2 - Tp2)/(Tr - Tp)
#         tmmin,tmmax = max(mmin,m2min*m_m2), min(mmax,m2max*m_m2)
#         yield RangeValue((tmmin,tmmax)), dr


# def iterSRGears(Tr=None, Tp=None, np=3, m=0.5, m2=None, R=None, Dext=None, Dint=None,
#     rsm=False, rpc=False, psc=False, rnc=False, rnf=False,
#     rs2m=False, rp2c=False, ps2c=False, rn2c=False, rn2f=False, pp2e=False,
#     tmin=Tmin, tmax=Tmax, smin=None, s2min=None):
#   """ Iterate through all valid SRGear combinations within constraints.

#   This yields all possible valid SRGears instances within the Tr, Tp, np, m,
#   m2, R, D, and coprime constraints provided. The Tr, Tp, m, m2, and R values
#   can be any valid constraint as used by iterValues(). Dext can be a max ring
#   gear external diameter. Dint can be a min sun gear/gap inside diameter.
#   Setting rpc True will require that Tr and Tp be rpc.
#   """
#   rmmin,rmmax = ConstraintRange(m,vmin=mmin,vmax=Mmax)
#   rm2min,rm2max = ConstraintRange(m2,vmin=mmin,vmax=Mmax)
#   t2min,t2max = tmin,tmax
#   if Dext:
#     tmax = min(tmax, extT(Dext, rmmin))
#     t2max = min(t2max, extT(Dext, rm2min))
#   if Dint:
#     smin = max(smin, intT(Dint, rmmax))
#     s2min = max(s2min, intT(Dint, rm2max))
#   rr = TrRange(np=np, tmin=tmin, tmax=tmax, smin=smin)
#   #print(f'{rr=} {Tr=}')
#   for tr in iterValues(Tr,*rr):
#     # Check if tr will fit in m constraints.
#     if Dext and extD(tr, rmmin, ring=True) > Dext: continue
#     rp = TpRange(Tr=tr, np=np, tmin=tmin, tmax=tmax, smin=smin)
#     #print(f'{tr=} {rp=} {Tp=}')
#     for tp in iterValues(Tp, *rp):
#       if rpc and not iscoprime(tr,tp):
#         #print(f'{tr=} {tp=} not coprime')
#         continue
#       for dp in iterdp(tp, np, t2min, t2max, s2min):
#         #print(f'{tr=} {tp=} {dp=}')
#         for gm, dr in iterdr(tr, tp, dp, np, m, m2, Dext, Dint, t2min, t2max, s2min):
#           if rp2c and not iscoprime(tr+dr,tp+dp):
#             continue
#           #print(f'{tr=} {tp=} {dp=} {dr=}')
#           g = SRGears(tr, tp, dr, dp, np=np, m=gm)
#           if (Dext and g.Dext > Dext) or (Dint and g.Dint < Dint):
#             continue
#           # ratio will be inf if N==0, so only yield for N!=0.
#           if g.N != 0 and (not R or inConstraint(R, g.R)):
#             yield g


# def iterSRPGears(Tr=None, Tp=None, Ts=None, np=3, m=0.5, m2=None,
#     R=None, Dext=None, Dint=None, rpc=True, psc=False, rnc=False, rp2c=False,
#     tmin=Tmin, tmax=Tmax, smin=None):

#   """ Iterate through all valid gear combinations within constraints.

#   This yields all possible valid SRPGears instances within the Tr, Tp, Ts, dr,
#   dp, np, m, m2, R, D, and coprime constraints provided. The Tr, Tp, Ts, dr,
#   dp, m, m2, and R values can be any valid constraint as used by iterValues().
#   D can be a max ring gear diameter.  Setting rpc True will require that
#   Tr and Tp be coprime.
#   """
#   if smin is None: smin = tmin
#   rmmin,rmmax = ConstraintRange(m,vmin=Mmin,vmax=Mmax)
#   if Dext:
#     tmax = min(tmax, extT(Dext, rmmin))
#   if Dint:
#     smin = max(smin, intT(Dint, rmmax))
#   # Change Ts to a set for faster inclusion testing and adjust ranges.
#   rs = TsRange(n=np, tmin=tmin, tmax=tmax, smin=smin)
#   Ts = IConstraintSet(Ts, *rs)
#   rs = min(Ts), max(Ts)
#   rr = TrRange(rs=rs, n=np, tmin=tmin, tmax=tmax, smin=smin)
#   for tr in iterIConstraint(Tr,*rr):
#     rp = TpRange(rr=tr, rs=rs, n=np, tmin=tmin, tmax=tmax, smin=smin)
#     for tp in iterIConstraint(Tp, *rp):
#       ts = tr - 2*tp
#       if ((tr+ts) % np or ts not in Ts or
#           (rnc and not iscoprime(np,ts)) or
#           (psc and not iscoprime(tp,ts)) or
#           (rpc and not iscoprime(tr,tp))):
#         continue
#       for dp in iterdp(tp, np, tmin, tmax):
#         for gm, dr in iterdr(tr, tp, dp, np, m, m2, Dext, Dint, tmin, tmax):
#           if rp2c and not iscoprime(tr+dr,tp+dp):
#             continue
#           g = SRPGears(tr, tp, ts, dr, dp, np=np, m=gm)
#           if D and g.D > D:
#             continue
#           # ratio will be inf if N==0, so only yield for N!=0.
#           if g.N != 0 and (not R or inRange(R, g.R)):
#             yield g


def getGears(R, igears, topn=4, histd=2, **kwargs):
  "Select the topn gears closest to R from gear iterator."""
  args = ', '.join(f'{k}={v}' for k,v in kwargs.items())
  #print(f'Getting {igears.__name__}({args}) for R={R}:')
  n, fwdmax, revmax, top, hist = 0, None, None, [], Histogram(scale=1.0,base=10**(1/histd))
  for g in igears(**kwargs):
    n += 1
    if 0.0 < g.R:
      if not fwdmax or fwdmax.R < g.R:
        fwdmax = g
    else:
      if not revmax or g.R < revmax.R:
        revmax = g
    er = abs(g.R - R)
    hist.add(g.R)
    if len(top) < topn or er < top[-1][0]:
      top.append((er, g))
      top.sort()
      while len(top) > topn:
        del top[-1]
  top = [g for dr,g in top]
  print(f'checked {n} gear combinations.')
  print(f'{revmax=!s}')
  print(f'{fwdmax=!s}')
  print(f'Histogram of checked gear ratios:')
  print(str(hist))
  print(f'Top {topn} gears closest to {R=}:')
  for g in top:
    print(f'{g}')
  return top


def getNs(**kwargs):
  Ns = {}
  for g in iterSRGears(**kwargs):
    Ns.setdefault(g.N,[]).append(g)
    if g.N == 1:
      print(f'{g.dr=} {g.dp=} {g.N=} {g}')
  for N in (n for n in range(25) if n in Ns):
    dr=[]
    for g in Ns[N]:
      dr.append((g.dr,g.dp))
    print(f'{N=}: {dr}')


if __name__ == '__main__':
  #getNs(Tr=59,Tp=21)
  #ms=list(m for m in m_stdI if 0.5<=m<=5.0)
  #m2s=list(m for m in m_stdI if 0.4<=m<=5.0)
  #m2f=(0.4,inf)
  #getGears(10000, iterPGears, histd=0, rpc=True, psc=True,tmax=100)
  #getGears(1000, iterSRGears, Tr=(24,128), D=100, m=ms, m2=m2s)
  #getGears(400, iterSRPGears, D=30, Ts=10, m2=m2f, rpc=True)

  import argparse,re

  cmdline = argparse.ArgumentParser(
      description="Find gears for planetary and split-ring gears that satisfy constraints.",
      epilog="""\
Specify your target ratio with -R, your desired gear type with -G, and any
other constraints you require with other arguments. Gear size and module
constraints can be specified as lists of values or min..max ranges. Gear
relationship constraints are booleans. Other constraints are floats or ints.
""",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  cmdline.add_argument('-R', type=float, default=100000.0,
      help='Target ratio to find.')
  cmdline.add_argument('-N', type=int, default=4,
      help='List the top n gears closest to the target ratio.')
  cmdline.add_argument('-d', type=int, default=2,
      help='Ratio histogram buckets per order of magnitude.')
  cmdline.add_argument('-G', choices=['S', 'P', 'SR', 'SRP', 'SRI'], default="SRP",
      help='Gear type: S:simple sun/planet, P=planetary, SR=split-ring, SRP=planetary split-ring. SRI=idler split-ring.')
  cmdline.add_argument('-r', type=ConstraintType(Tmin, Tmax),
      help='Ring gear sizes or inclusive min..max ranges (eg "64", "24..32", "32,34,50..60".')
  cmdline.add_argument('-p', type=ConstraintType(Tmin, Tmax),
      help='Planet gear sizes or inclusive min..max ranges (eg "64", "24..32", "32,34,50..60".')
  cmdline.add_argument('-s', type=ConstraintType(Tmin, Tmax),
      help='Sun gear sizes or inclusive (min,max) ranges (eg "64", "24..32", "32,34,50..60".')
  cmdline.add_argument('-r2', type=ConstraintType(Tmin, Tmax),
      help='Secondary ring gear sizes or inclusive min..max ranges (eg "64", "24..32", "32,34,50..60".')
  cmdline.add_argument('-p2', type=ConstraintType(Tmin, Tmax),
      help='Secondary planet gear sizes or inclusive min..max ranges (eg "64", "24..32", "32,34,50..60".')
  cmdline.add_argument('-s2', type=ConstraintType(Tmin, Tmax),
      help='Secondary sun gear sizes or inclusive (min,max) ranges (eg "64", "24..32", "32,34,50..60".')
  cmdline.add_argument('-n', type=int, default=3,
      help='Number of planet gears.')
  cmdline.add_argument('-m', type=ConstraintType(Mmin, Mmax), default=0.5,
      help='First stage gear module values or inclusive min..max ranges (eg "0.5", "0.4..1.0", "0.4,0.5,0.6..1.0".')
  cmdline.add_argument('-m2', type=ConstraintType(Mmin, Mmax),
      help='Second stage gear module values or inclusive min..max ranges (eg "0.5", "0.4..1.0", "0.4,0.5,0.6..1.0".')
  cmdline.add_argument('-Dext', type=float,
      help='Maximum ring gear external diameter in mm (eg "64.0").')
  cmdline.add_argument('-Dint', type=float,
      help='Minimum sun gear or middle gap internal diameter in mm (eg "25.0").')
  cmdline.add_argument('-spr', type=float,
      help='Maximum sun gear to planet size ratio (eg "-spr=1.0" means sun cannot be larger than planet.')
  cmdline.add_argument('--rpc', action=argparse.BooleanOptionalAction, default=False,
      help='Do the ring and planet gears need to be coprime?')
  cmdline.add_argument('--psc', action=argparse.BooleanOptionalAction, default=False,
      help='Do the planet and sun gears need to be coprime?')
  cmdline.add_argument('--rnc', action=argparse.BooleanOptionalAction, default=False,
      help='Do the ring gear and number of planets need to be coprime?')
  cmdline.add_argument('--rnf', action=argparse.BooleanOptionalAction, default=False,
      help='Do ring gear and number of planets need to be a factor?')
  cmdline.add_argument('--rnb', action=argparse.BooleanOptionalAction, default=False,
      help='Do ring gear and planets need to be balanced?')
  cmdline.add_argument('--rp2c', action=argparse.BooleanOptionalAction, default=False,
      help='Do the secondary ring and planet gears need to be coprime?')
  cmdline.add_argument('--ps2c', action=argparse.BooleanOptionalAction, default=False,
      help='Do the secondary planet and sun gears need to be coprime?')
  cmdline.add_argument('--rn2c', action=argparse.BooleanOptionalAction, default=False,
      help='Do the secondary ring gear and number of planets need to be coprime?')
  cmdline.add_argument('--rn2f', action=argparse.BooleanOptionalAction, default=False,
      help='Do the secondary ring gear and number of planets need to be a factor?')
  cmdline.add_argument('--rn2b', action=argparse.BooleanOptionalAction, default=False,
      help='Do the secondary ring gear and planets need to be balanced?')
  cmdline.add_argument('--pp2e', action=argparse.BooleanOptionalAction, default=False,
      help='Do all the joined primary and secondary planets need the same phase offset (be interchangable)?')
  cmdline.add_argument('-tmin', type=int, default=8,
      help='Minimum gear size.')
  cmdline.add_argument('-tmax', type=int, default=128,
      help='Maxmium gear size.')
  cmdline.add_argument('-smin', type=int, default=None,
      help='Minimium sun gear size (default is tmin).')
  cmdline.add_argument('-s2min', type=int, default=None,
      help='Minimium secondary sun gear size (default is tmin).')

  args=cmdline.parse_args()
  igears = globals()[f'iter{args.G}Gears']
  gearargs = dict(
      S='p s m Dext Dint psc tmin tmax smin'.split(),
      P='r p s n m Dext Dint spr rpc psc rnc rnf rnb tmin tmax smin'.split(),
      SR='r p s r2 p2 s2 n m m2 Dext Dint rpc rnc rnf rnb rp2c rn2c rn2f rn2b pp2e tmin tmax'.split(),
      SRP='r p s r2 p2 s2 n m m2 Dext Dint spr rpc psc rnc rnf rnb rp2c rn2c rn2f rn2b pp2e tmin tmax smin s2min'.split(),
      SRI='r p s r2 p2 s2 n m m2 Dext Dint spr rpc psc rnc rnf rnb rp2c ps2c rn2c rn2f rn2b pp2e tmin tmax smin s2min'.split())
  argnames = dict(r='cr',p='cp',s='cs',r2='cr2',p2='cp2',s2='cs2',m='cm',m2='cm2')

  kwargs={argnames.get(k,k):v for (k,v) in vars(args).items() if v is not None and k in gearargs[args.G]}
  #print(kwargs)
  getGears(args.R, igears, topn=args.N, histd=args.d, **kwargs)
