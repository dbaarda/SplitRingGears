# SplitRingGears

Tools and tests for Split Ring Planetary Gear systems.

To use high-speed motors for slow/precise tasks like 3DPrinter extruders you
need efficient and small gearboxes. Split Ring Planetary Gears look promising
for small/light gearboxes with very high ratios and low backlash.

## Gears

https://en.m.wikipedia.org/wiki/Involute_gear

Involute gears have 3 primary attributes that define the gear;

1. teeth (T or z)- the number of teeth around the full circumferance.

2. module (m or M)- the tooth width measured in mm of pitch diameter per tooth.

3. pressure angle (a)- tooth profile shape defined by the angle between the
circumfrence tangent and the meshed driving force. A high pressure angle gives
a stronger tooth that is wider at the base. A low pressure angle gives better
power transmission and less force on the bearings. Common values in order of
popularity are 20deg, 14.5deg, 25deg.

Gears need to have the same module and pressure angle to mesh correctly. Note
however it is also fairly common to use "adjusted profiles" with various
modifications to the tooth profile for things like reducing tooth-tip loads,
reduce undercutting during machineing, avoid burrs, add backlash, etc.

These three parameters give you

1. pitch diameter: `D=m*T` the effective diameter of the gear (the
   diameter where tooth-width equals tooth gap, assuming no additional gap for
   backlash. The center distance between two meshed gears is half the sum of
   their pitch diameters.

   https://evolventdesign.com/pages/blank-calc?srsltid=AfmBOoqIeC1GeN0xRCCzShE4golEJItWD8LYPrN6MvdKhPSl6ZD1NvbX#google_vignette
   https://en.wikipedia.org/wiki/Involute

2. inner diameter: `Dint=m*(T+2.5)` for an external spur gear, or `Dint= m*(T+2)`
   for an internal ring gear. Note the teeth stick out "addendum" `1*m` from the
   pitch line, and have `1.25*m` tooth-width "dedendum" for extra clearance.

3. outer diameter: `Dext=m*(T+2)` for an external gear, or `Dext=m*(T+2.5)`
   for an internal gear.

If meshing gears have a coprime number of teeth, then every tooth of both
gears will mesh with every tooth of the other gear. This can reduce wear, and
is called a "hunting tooth" design.


## Planetary Gearbox

https://en.wikipedia.org/wiki/Epicyclic_gearing

Requires the sum of sun and ring gear teeth to be an integer multiple of the number of
planet gears:

```python
#  Np = number of evenly spaced planet gears.
#  Ts,Tp,Tr = sun planet and ring gear teeth.
#  Ds,Dp,Dr = diameter of sun,planet, and ring gear.
(Ts + Tr) % Np = 0
```

We also require that the sun gear is in the centre, and the planets can fit
around it, so the ring diameter is equal to the sun diameter plus two planet
diameters;

```
  Tr = Ts + 2*Tp
```

Note that since Tp is integer, this means `Tr - Ts` must be even, which is the
same as also requiring Ts+Tr be even, or that Ts and Tr are either both odd or
both even. So we can express this constraint in various ways;

```
  (Ts + Tr) % Np = 0     # (1) the original constraint for gear meshing.
  (Ts + Tr) % 2 = 0      # (2) the both even or odd constraint.
  2*(Ts + Tp) % Np = 0   # writing (1) with Ts and Tp implying (2)
  (Ts + Tr) % (Np * 2^(Np%2)) # combining (1) and (2) for mod Np*2 if necessary.
```

These can be used in three different ways to use these for different gear
ratios;

* carrier locked, ratio of sun to ring is -Ts/Tr
* ring locked, ratio of of sun to carrier is Ts/(Ts+Tr)
* sun locked, ratio of carrier to ring is (Ts+Tr)/Tr

Example (used by Orbiter2.0 extruder):

```python
sun gear input, carrier output.
Np = 3
m = 0.5
Ts = 10
Tr = Np*20 - Ts = 62
Tp = (Tr-Ts)/2 = 26
Dr = 31mm
Ws:Wc = Ts:Ts+Tr = 1:7.2
```

Starting with an assembly position with planets numbered 0..Np-1
anti-clockwise with planet0 meshing with phase=0 to the ring on the on the
right hand side, each planet will mesh with the ring with an increasing
phase-offset measured in fractions of a tooth-pitch between [0,1) of;

```python
Pp = Tr/Np%1
   = (Tr%Np)/Np
   = (-Ts%Np)/Np   # since (Ts+Tr)%Np=0
```

Note that if Ts%Np=1, then each planet will be engaging the sun 1/Np of a
"tooth phase" offset from each other. In general, if Tr and Np is coprime,
then every planet will engage with the ring and sun gear with a different
phase, and thus engage/disengage at different times. This should ensure
smoother tooth loading for less noise and wear, and might combine for less
backlash. However it does mean the loads are not perfectly symetrical, which
might induce extra oscilations and cause more bearing wear.

Alternatively if Np is a factor of Tr, then all planets engage the ring (and
sun) with the same phase angle, making the loads perfectly symetrical, which
should reduce the bearing loads.

A compromise would be to have only opposite side planets mesh with the same
phase. For even Np, this would mean having `gcd(Tr,Np)=2`. In the general case
it works out as `min(Tr*(Np//2)%Np,-Tr*(Np//2)%Np)<=1 and gcd(Tr,Np)<=2`

These result in various hard and optional constraints for the gear sizes. Hard
constraints are;

* **rsm** (ring and sun mesh): `(Tr+Ts) % Np = 0`. The ring and sun both mesh
  correctly with with the planets. This is not required if the sun (or ring)
  gear is removed. It ensures that the ring and sun gear teeth align correctly
  to mesh with the planets at each planet position.

* **pgs** (planetry gear size): `Tr = Ts + 2*Tp`. The gears all touch and are
  centered around the sun. If you don't have a sun gear this still applies
  with Ts being the middle gap size. This can possibly be ignored for strange
  eccentric gear arrangements.

* **rps** (ring and planet size): `(Tr-Tp)*sin(pi/Np) > Tp+2` or
  `(Ts+Tp)*sin(pi/Np) > Tp+2`. The planets fit within the ring and around the
  sun without touching each other.  Note when Np=2 this implies a minimum Ts
  of 2, which is the gap needed to ensure the planets don't touch even without
  a sun gear. This can be bypassed by offsetting the planets so they are on
  different planes.

Additional optional constraints are;

* **rpc** (Tr and Tp are coprime): `iscoprime(Tr,Tp)`. Every tooth of the ring
  meshes with every tooth of the planet during rotation. This spreads and
  smooths out the gear wear, improving gear endurance.

* **psc** (Tp and Ts are coprime): `iscoprime(Tp,Ts)`. Every tooth of the
  planet meshes with every tooth of the sun during rotation. This spreads and
  smooths out the gear wear, improving gear endurance.

* **rnc** (Tr and Np are coprime): `iscoprime(Tr,Np)`. Every planet engages
  the ring (and sun) with a different phase. Note since **rsm** means
  `(Tr+Ts)%Np=0`, this means Ts and Np are also coprime. This means the teeth
  of each planet engage and disengage at different times, which might smooth
  the tooth loading, reducing wear and noise. This is the opposite of **rnf**.

* **rnf** (Tr has Np as a factor): `Tr % Np = 0`. Every planet engages the
  ring (and sun) with the same phase. Note since **rsm** means `(Tr+Ts)%Np=0`,
  this also means Np is a factor of Ts. This ensures the forces on the sun and
  ring gears are perfectly symetrical, which might reduce load and wear on the
  bearings. This is the opposite of **rnc**.

* **rnb** (ring has planets balanced): `min(Tr*(Np//2)%Np,-Tr*(Np//2)%Np)<=1
  and gcd(Tr,Np)<=2`. Only opposite planets engage the ring (and sun) with the
  same phase. This is a compromise between **rnc** and **rnf** that might give
  you the best of both worlds with reduced wear of teeth and bearings, less
  backlash, less noise, and less load oscilations. Note for Np=2 this is the
  same as **rnf**, for Np=3 it's the same as **rnc**, and for larger Np
  it's a looser constraint than **rnf** but tighter than **rnc**.

Note that **pgs** `Tr=Ts+2*Tp` means that if **rpc** `Tr` and `Tp` are
coprime, then **psc** `Tp` and `Ts` are also coprime, and `gcd(Tr,Ts)<=2`. So
`Tr` and `Ts` are either also coprime, or are both even and `Tr/2` and `Ts/2`
are coprime.

Also **rsm** `(Tr+Ts)%Np=0` means that `Tr+Ts` must have `Np` as a factor, and
`Tr` and `Ts` either both have, or both don't have, `Np` as a factor. When
**rpc** `Tr` and `Tp` are coprime we know that `gcd(Tr,Ts)<=2`, which means
`gcd(Tr+Ts,Tr,Ts)<=2`, which means `gcd(Np,Tr,Ts)<=2`. This means when `Tr`
and `Tp` are coprime, `Tr`, `Ts` and `Np` are either all coprime, or they are
all even and `Tr/2`, `Ts/2` and `Np/2` are all coprime. So `Np` can only be a
factor of `Tr` when `Tr` and `Tp` are coprime if `Np=2`.

This means the following;

1. **rpc** is equivalent to **psc**, because of **pgs**.

2. **rpc** is contradictory with **rnf** unless `Np=2`, because of **rsm** and
   **pgs**

3. **rpc** implies **rnc** when `Tr` and `Np` are not both even, because of
   **rsm** and **pgs**.

So **rpc** always gives us **psc**, and also **rnc** when `Np` or `Tr` is odd.
If we want **rnf** we can't also have **rpc** unless we have `Np=2`.


## Compound split-ring planetary gearbox

This has a second stage of planet gears on the same carrier and driven by the
same shaft of the first layer planet gears that engage with a second stage
ring with slightly different gearing. The first ring is fixed and the output
is the second ring. The small difference in gearing means a small rotation of
the secondary ring for every rotation of the carrier.  This gives us the
following attributes;

```python
Np              # number of planets.
Tr,Tp,Ts,m      # primary stage planetary gear attributes.
Tr2,Tp2,Ts2,m2  # secondary stage planetary gear attributes.
Dr,Dp,Ds        # primary stage pitch diameters.
Dr2,Dp2,Ds2     # secondary stage pitch diameters.
Pp = Tr%Np/Np   # primary stage ring-mesh phase difference between planets.
Pp2 = Tr2%Np/Np # secondary stage ring-mesh phase difference between planets.
```

We can think of the second stage in terms of change in size measured in teeth
added compared to the first stage;

```python
Tr2 = Tr + dr
Tp2 = Tp + dp
```

The second stage planets have the same axies as the first stage planets, and
they don't need to engage with a sun gear if they have a carrier to hold them
apart. Alternatively an idler sun gear can be used to hold them apart removing
the need for a carrier. This gives us a constraint that constrains the module
of the secondary ring stage;

```python
Dr - Dp = Dr2 - Dp2
m*(Tr - Tp) = m2*(Tr2 - Tp2)
m2 = m*(Tr - Tp)/(Tr2 - Tp2)
   = m*(Tr - Tp)/((Tr - Tp) + (dr-dp))
```

Note that even when teeth are added to the second stage gears, we normally add
more to the ring than the planet, which gives a reduction in the module, which
results in them having a slightly smaller diameter. This can be handy to give
extra clearance for a bearing around the second stage ring. If we add less
teeth to the ring than the planet they would instead be larger.

It may be possible to select secondry ring and planet gear sizes that result
in m2 being a standard module, but it is hard to do this while also selecting
a particular ratio. If we try to keep the same gear module, we must satisfy
the constraint dr = dp. So to keep the same module we must add as many
additional teeth to the planet as we do to the ring. This does not correspond
with the sizing for max gearing, and results in the ratio from the second
stage being around the same as another planetary stage.

```python
(Tr-Tp)+(dr-dp) = (Tr-Tp)*m/m2
dr-dp = (Tr-Tp)*(m/m2 - 1)
```

To get integer dr-dp value requires m/m2 be converted to an integer fraction,
and then (Tr-Tp) must be an integer multiple of that fraction's denominator.
For example m=0.5, m2=0.45, m/m2=10/9, Tr-Tp=36=4*9, (dr-dp)=4.

For the relative speeds of the gears we get;

```python
# ws = sun rotation rate
# wp = planet rotation rate
# wr = ring rotation rate
# wr2 = secondary ring rotation rate.
Ts*ws + Tp*wp - (Ts+Tp)*wc = 0           # (1) sun->planet
Tr*wr - Tp*wp - (Tr-Tp)*wc = 0           # (2) planet->ring
Tr2*wr2 - Tp2*wp - (Tr2 - Tp2)*wc = 0    # (3) planet2->ring2
Ts*ws + Tr*wr = (Ts + Tr)*wc             # (4) = (1) + (2)
```

These give us the following relationships between the different gear speeds;

```python
ws = (Ts+Tr)/Ts*wc - Tr/Ts*wr            # (5) from (4)
wr =(Ts+Tr)/Tr*wc - Ts/Tr*ws             # (6) from (4)
wc = Ts/(Ts+Tr)*ws + Tr/(Ts+Tr)*wr       # (7) from (4)
wp = -(Tr-Tp)/Tp*wc + Tr/Tp*wr           # (8) from (2)
wr2 = (Tr2 - (Tp2/Tp)*Tr)/Tr2*wc + (Tp2/Tp)*(Tr/Tr2)*wr # (9) as derived below.
```

The derevation of (9) is shown below;

```python
wr2 = (Tr2 - Tp2)/Tr2*wc + Tp2/Tr2*wp     # (10) from (3)
    = (Tr2 - Tp2)/Tr2*wc + Tp2/Tr2*(-(Tr-Tp)/Tp*wc + Tr/Tp*wr)   #  subst (8)
    = (Tr2 - Tp2)/Tr2*wc - Tp2/Tr2*((Tr-Tp)/Tp*wc - Tr/Tp*wr
    = (Tr2 - Tp2)/Tr2*wc - Tp2/Tr2*(Tr-Tp)/Tp*wc + Tp2/Tr2*Tr/Tp*wr
    = (Tr2 - Tp2)/Tr2*wc - (Tp2/Tp)*(Tr-Tp)/Tr2*wc + (Tp2/Tp)*(Tr/Tr2)*wr
    = (Tr2 - Tp2 - (Tp2/Tp)*(Tr-Tp))/Tr2*wc + (Tp2/Tp)*(Tr/Tr2)*wr
    = (Tr2 - Tp2 - (Tp2/Tp)*Tr + (Tp2/Tp)*Tp)/Tr2*wc + (Tp2/Tp)*(Tr/Tr2)*wr
    = (Tr2 - Tp2 - (Tp2/Tp)*Tr + Tp2)/Tr2*wc + (Tp2/Tp)*(Tr/Tr2)*wr
    = (Tr2 - (Tp2/Tp)*Tr)/Tr2*wc + (Tp2/Tp)*(Tr/Tr2)*wr
```

If we set wr=0 and substitute in wc we get the equation for wr2 from ws as;

```python
wr2 = (Tr2 - (Tp2/Tp)*Tr)/Tr2*wc              # from (9) with wr=0
    = (Tr2 - (Tp2/Tp)*Tr)/Tr2 * Ts/(Ts+Tr)*ws # (11) subst (7) with wr=0
```

This gives us a ws/wr2 ratio of;

```python
ws/wr2 = Tr2/(Tr2 - (Tp2/Tp)*Tr) * (Ts+Tr)/Ts
       = Tr2*Tp/(Tr2*Tp - Tp2*Tr) * (Ts+Tr)/Ts
```

Note that this is the ratio for the split-ring stage times the normal first
stage planetary gear ratio, which can be written as separate ratios for each
stage as;

```python
R1 = ws/wc = (Ts+Tr)/Ts
R2 = wc/wr2 = Tr2*Tp/(Tr2*Tp - Tp2*Tr)
            = Tr2*Tp/((Tr+dr)*Tp - (Tp+dp)*Tr)
            = Tr2*Tp/(Tr*Tp + dr*Tp - Tp*Tr -dp*Tr)
            = Tr2*Tp/(dr*Tp - dp*Tr)
N = (Tr2*Tp - Tp2*Tr) = (dr*Tp - dp*Tr) # put N = denominator of R2.
R2 = Tr2*Tp/N
```

Note the R2 ratio is similar to the ratio for harmonic drives with Tp2 = Tp
because they don't have planets and Tr2 = Tr-2, giving a ratio of -Tr/2. The
splitring approach can achieve significantly higher ratios because it is not
constrained to changing the ring gear by a even number so can do Tr/1 or
double the ratio, and by also changing the planet gear the ratio can be
greater than Tr/1. It also has the planetary first-stage to further multiply
the ratio by up to 10x. So it can achieve ratios more than 20x of harmonic
drives. The backlash is more than a harmonic drive, but the second stage is
not a full planetary stage and shares the same carrier, so it's a tiny bit
worse than a single-stage planetary, but better than a two stage planetary
while achiving ratios greater than even the highest three stage planetarys.

To maximize the ratio we need to maximize the second stage ratio R2, which is
achieved by making `N=(Tr2*Tp - Tp2*Tr)` as small as possible, but not zero.
Note if it actually is zero, the ratio becomes infinite and the secondary ring
gear will not rotate at all. For the max but not infinite gearing ratio we
would like the denominator for R2 to be 1 (the smallest non-zero result for
integer gear sizes). For a given Tr and Tp we can get the closest dp for
dr, or dr for dp, values to give the desired N value like this;

```python
dr*Tp - dp*Tr = N              # required for target N.
dr = round((Tr*dp + N)/Tp)     # gives closest dr from dp for target N.
dp = round((Tr*dr - N)/Tr)     # or dp from dr.
(Tp*dr - N) % Tr = 0    # requirement so that dp is integer for exact N.
(Tr*dp + N) % Tp = 0    # same requirement rearanged for dr is integer.
Tp*dr%Tr = N            # requirements re-arranged to find N from dr.
Tr*dp%Tp = N            # same thing rearranged to find N from dp.
```

Note `(Tr*dp + N)%Tp` looks like an
[LCG](https://en.wikipedia.org/wiki/Linear_congruential_generator) with a=Tr,
c=N, and m=Tp. This will produced psedo-random values from different dp
values, making it rather hard to find a dp value that gives the desired N value.
For `Tr*dp%Tp` the result will always be a multiple of the largest common
factor of Tp and Tr which is the minimum non-zero N value, and N=1 is only
possible when Tp and Tr are co-prime. If Tp and Tr are coprime we also know
that the mapping from dp to all possible 0<=N<Tp is complete for 0<=dp<Tp, so
this covers all N values 0<=N<Tp, and similarly 0<=dr<Tr will cover all N
values 0<=N<Tr. This constrains m/2 <= m2 <= m. Alternatively
`-Tp//2<dp<=Tp//2` and `-Tr//2<dr<=Tr//2` will also cover all 0<=N<Tp and
constrains m*2/3 <= m2 <= m*2.

Note it is also possible to have a negative N, which means the rotation
direction is reversed. The eqns are the same as above with N replaced by N%Tr
or N%Pr, using the same dr/pr ranges just chosen to produce the negative N
value.

Given that the ratio R2 of the second stage is effectively a random number
generator function of the dr and dp changes, and the requirement to satisfy
various other constraints on the relationships between gear sizes, this makes
choosing gear sizes to target a particular ratio while also satisfying
required and desired constraints very hard. Fortunately the typical gear sizes
are around 8 to 200 teeth, which makes an exhuastive search feasible.

Note that backlash is mostly in the planetary first stage and dominated by the
size of the sun gear (Assuming the sun gear is smaller than the planets). The
larger the sun gear, the less the backlash, but also means the less the gear
ratio in the first stage. However, the vast majority of the overall ratio
comes from the second stage, and the second stage ratio is less affected by
increasing the sun gear, so it might be worth having a larger sun gear to
reduce backlash if super-high ratios are not required.

The secondary planet gears are directly driven by the primary planet gears, so
we have a requirement that they have and maintain the right phase to engage
correctly with the secondary ring as they are driven around by the primary
planet gears. We use starting assembly position with the secondary ring also
meshing with the secondary planet0 with phase=0 on the right hand side. This
means the phase-difference between the primary and secondary planet0 is 0
where they mesh with the rings. If dr%Np!=0 then the primary-secondary phase
difference at their mesh points for the other planets will be different.
Additionally, if dp!=0 then the primary-secondary phase difference will be
different around the planets.

For the joined primary-secondary planets to be interchangable requires that
there is at least one angle where the phase=0 for both primary and secondary
for all planets so they match planet0. Since the phase offsets increase the
same for each planet, it is enough to prove that planet1 has a point were both
phase angles are 0. If this constraint is met, we can also calculate the
initial assembly rotation angle required for each identical planet-pair. The
constraint for planet-pairs to be interchangeable can be calculated as;

```python
(Tr/Np+k1)/Tp = (Tr2/Np + k2)/Tp2       # where k1 and k2 are integers.
(Tr/Np+k1)*Tp2 = (Tr2/Np + k2)*Tp
Tr*Tp2/Np - Tr2*Tp/Np = k2*Tp - k1*Tp2
Tr*Tp2 - Tr2*Tp = (k2*Tp - k1*Tp2)*Np
Tr*Tp2 - Tr2*Tp = k3*gcd(Tp,Tp2)*Np     # where k3 is a different integer.
Tr*Tp2 - Tr2*Tp = 0 (mod pf*Np)         # where pf=gcd(Tp,Tp2)
Tr*Tp2 = Tr2*Tp  (mod pf*Np)
# so we require
pf = gcd(Tp,Tp2)
(Tr*Tp2/pf)%Np == (Tr2*Tp/pf)%Np
```

The implications of this are;

1. In all cases, `Tp/pf%Np==Tp2/pf%Np==0` is not possible since if both had Np
   as a factor, it would be included in pf. So no values of Tp and Tp2 exist
   that would allow Tr and Tr2 to be anything.

2. For `Tr%Np==Tr2%Np==0`, AKA `pp=pp2=0`, it always works, since Tp and Tp2
   by definition have pf as a factor, so Tp and Tp2 can be anything. Planets
   all align the same and mesh with the rings with phase=0.

3. For `Tr%Np==Tr2%Np!=0` AKA `pp==pp2!=0`, requires `Tp/pf%Np = Tp2/pf%Np` to
   work. Note Tp=Tp2 is a special case of this. The planets all align and mesh
   with the rings with different phases, requiring different rotations.

4. For `Tr%Np!=Tr2%Np` AKA `pp!=pp2`, requires the full `(Tr*Tp2/pf)%Np ==
   (Tr2*Tp/pf)%Np` constraint with no simplifications.

Given the constraint that the planets are interchangable is met, the rotation
fraction of a full rotation for the initial assembly can be calculated;


```python
# fraction of a full rotation difference for each planet.
Pr = (Pp + k1)/Tp = (Pp2 + k2)/Tp2  # where k1,k2 are integers.

Pr = (Tr%Np+ k1*Np)/(Tp*Np) = (Tr2%Np + k2*Np)/(Tp2*Np)
Pr*(Tp*Np) = (Tr%Np+ k1*Np)
Pr*(Tp2*Np)= (Tr2%Np + k2*Np)
Pr*Tp2= Tr2%Np/Np + k2

Pr*Tp = Tr/Np     (mod 1)
Pr*Tp2 = Tr2/Np   (mod 1)
Pr = Tr/(Tp*Np)    (mod 1) ???
Pr = Tr2/(Tp2*Np)  (mod 1) ???

(Err... not finished here...)

```

### Split-Ring Variants

There are a few options on how these can be arranged;

1. Split-Ring with no sun gears, only split rings, and split planets in a
   carrier. This has primary ring as fixed, the carrier as the input , and
   secondary ring as the output. This doesn't give you the extra 4-10x ratio
   from a first-stage planetary gears, but removes the **rsm** constraint from
   the primary and secondary gears giving a wider range of spit-ring stage
   ratios. Note you could still add idler sun gears to provided outward
   pressure with this arrangement, but that adds the **rsm** constraints and
   you still need a carrier for the input which can provide that outward
   pressure for you. Without the first planetary stage this should give less
   backlash.

2. Planetary Split-Ring, with first stage sun gear, split planets in a
   carrier, and split rings. This has the primary ring as fixed, the first
   stage sun as input, and the secondary ring as output. This gives the extra
   4-10x ratio from the planetary first stage which might also improve
   efficiency by having less torque on a fast-moving first stage. This has the
   **rsm** constraint on the planetary first stage but not on the secondary
   stage, and relies on the carrier to provide outward pressure and hold the
   planets correctly aligned. Note you could also add a secondary idler gear
   to provide more outward pressure, but it's probably not necessary, and adds
   the **rsm** constraint to the second stage limiting options.

3. Idler Split-Ring, with a first stage sun gear, split planets, split rings,
   and a secondary idler sun gear. This is like Planetary Split-Ring with the
   same inputs and outputs, but because the idler provides outward pressure
   there is no need for a planet carrier, significantly simplifying it. This
   has the **rsm** constraint on both the primary and secondary stages. Note
   the torque difference between the primary and secondary rings translates to
   a twisting torque on the split-planets, which probably translates into them
   pressing and rubbing against the top and bottom of the casing that
   holds the planets in place. This friction cannot be reduced with any sort of
   bearing arrangement, only with smooth and lubricated surfaces. So the
   simplification of eliminating the carrier and bearings for the gears might
   be at the cost of efficiency.
