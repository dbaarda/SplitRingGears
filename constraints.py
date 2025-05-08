#!/usr/bin/pypy3
"""
This defines fuctions for defining and using values, ranges, and constraints.

A value is any type of number. A range is an inclusive (min,max) tuple of
values. A constraint is an iterable of ranges, or a set of values.

In general a value can be used as a range, and a range can be used as a
constraint. None for a value means no value, for a range or constraint means
an unlimited (vmin,vmax) range. An empty range is one where vmin>vmax.

This uses the following naming conventions. A 'v' is any value, and 'i' is an
integer value. An 'r' prefix indicates a range, and a c prefix indicates a
constraint, so 'ri' is an integer range, and 'cv' is a value constraint.
"""
import re
from math import inf
from collections.abc import Iterable,Iterator
from numbers import Number
from copy import deepcopy
import argparse

Imin,Imax = -2**31,2**31
Vmin,Vmax = -inf,inf
Vtol=0.0005

num_re=r'[-+]?(?:\d+(?:\.\d+)?|inf)'
range_re = rf'({num_re})?(?:(\.\.)({num_re})?)?'


def Range(rv, vmin=Vmin, vmax=Vmax, vtol=0):
  """Create a (min,max) tuple from a value or tuple.

  This will create a (min,max) range from None, a number, or a (min,max)
  tuple, clamping it to within (rmin,rmax) and adding +-vtol extra tolerance.
  Note if v is outside (vmin,vmax) this gives a result with vmin>vmax.
  """
  if isinstance(rv, str):
    rv = parseRange(rv, vmin, vmax)
  if rv is None:
    return vmin, vmax
  elif isinstance(rv, Number):
    v0, v1 = rv, rv
  elif isinstance(rv, tuple):
    v0, v1 = rv
  else:
    raise ValueError(f'Invalid range argument: {rv!r}')
  return max(vmin,v0-vtol), min(v1+vtol,vmax)


def IRange(ri, imin=Imin, imax=Imax):
  """ Create an integer (min,max) tuple from a value."""
  return Range(ri, imin, imax, 0)


def isRange(rv, t=Number):
  """Is rv a valid Range of type t?"""
  return rv is None or isinstance(rv, t) or (
      isinstance(rv, tuple) and len(rv)==2 and
      all(isinstance(v, t) for v in rv))


def isIRange(ri):
  """Is ri a valid IRange?"""
  return isRange(ri,int)


def inRange(v, rv, vtol=0):
  """Is value v within Range rv?"""
  assert isRange(rv)
  return ((isInstance(rv, tuple) and rv[0]-vtol <= v <= rv[1]+vtol) or
      rv-vtol <= v == rv+vtol or rv is None)


def parseRange(sr, vmin=Vmin, vmax=Vmax):
  """Parse a string into a Range.

  This will parse 'v' into a value v, 'v0..v1' into a tuple (v0,v1), 'v0..'
  into a tuple (v0,vmax), '..v1' into a tuple (vmin,v1), and just '..' into a
  tuple (vmin,vmax). Note this does not convert numbers into range tuples,
  clamp within limits, or add tolerances. Use Range() or IRange() for that. It
  will raise ValueError if the format is wrong or the range is outside
  vmin,vmax.
  """
  # Use the type of vmin or vmax or use eval() to parse any Number types.
  t = type(vmin) if vmin!=Vmin else type(vmax) if vmax!=Vmax else eval
  if not (gr := re.match(rf'^\s*{range_re}\s*$', sr)) or all(g is None for g in gr.groups()):
    raise ValueError(f'invalid range {sr!r}, format must be "<value>" or "[<min>]..[<max>]".')
  sv0, dsh, sv1 = gr.groups()
  v0 = t(sv0) if sv0 else vmin
  v1 = t(sv1) if sv1 else vmax
  if v0 < vmin or vmax < v1:
    raise ValueError(f'invalid range {sr!r}, values must be between {vmin} and {vmax}.')
  return (v0,v1) if dsh else v0


def formatRange(rv, vmin=Vmin, vmax=Vmax):
  """Format a Range as a string.

  This will render rv as 'v0' if rv is a value v0 or (v0,v1) where v0=v1,
  as '..' if v0<=vmin and v1>=vmax, as '..v1' if v0<=vmin, and as 'v0..' if
  v1>=vmax.
  """
  if rv is None:
    return '..'
  if isinstance(rv, Number):
    return f'{rv}'
  elif isinstance(rv, tuple) and len(rv) == 2:
    v0,v1 = rv
    if v0 == v1:
      return f'{v0}'
    if v0<=vmin: v0=''
    if v1>=vmax: v1=''
    return f'{v0}..{v1}'
  else:
    raise ValueError('not a valid range {rv!r}.')


def RangeValue(r):
  """Convert an r (min,max) range to a value."""
  # Use the middle of the range rounded to the least number of
  # digits required to fit within the range.
  if r is None or isinstance(r, Number):
    return r
  vmin,vmax = r
  m = (vmin+vmax)/2
  return next(v for v in (round(m, n) for n in range(-3,6)) if vmin<=v<=vmax)


def isConstraint(cv, t=Number):
  """Is cv a valid Constraint?."""
  if cv is None or isinstance(cv, (Number,tuple)):
    return isRange(cv, t)
  elif isinstance(cv, set):
    return all(isinstance(v, t) for v in cv)
  if isinstance(cv, Iterable):
    if isinstance(cv, Iterator): cv = copy(cv)
    return all(isRange(v,t) for v in cv)
  return False


def parseConstraint(sc, vmin=Vmin, vmax=Vmax):
  """Parse a string into a Constraint."""
  try:
    if ',' in sc:
      return [parseRange(sr,vmin,vmax) for sr in sc.split(',')]
    return parseRange(sc,vmin,vmax)
  except ValueError as e:
    raise ValueError('invalid format for Constraint {sc!r}.') from e


def formatConstraint(cv, vmin=Vmin, vmax=Vmax):
  """Format a Constraint as a string."""
  if cv is None or isinstance(cv, (Number, tuple)):
    return formatRange(cv, vmin, vmax)
  elif isinstance(cv, Iterable):
    if isinstance(cv, Iterator): cv = copy(cv)
    return ','.join(formatRange(rv,vmin,vmax) for rv in cv)
  else:
    raise ValueError('not a valid Constraint {cv!r}.')


def iterConstraint(cv, vmin=Vmin, vmax=Vmax, vtol=0):
  """Iterate through Ranges in a Constraint.

  Ranges are filtered and clamped within (vmin,vmax) with +-vtol tolerance
  added.

  Note this copies iterators so they are not consumed, allowing you to iterate
  through the same cv multiple times.
  """
  if cv is None or isinstance(cv, (Number, tuple)):
    rv = Range(cv, vmin, vmax, vtol)
    # Skip "empty" ranges with vmin>vmax.
    if rv[0] <= rv[1]:
      yield rv
  elif isinstance(cv, Iterable):
    if isinstance(cv, Iterator): cv = copy(cv)
    for i in cv:
      for v in iterConstraint(i,vmin,vmax,vtol):
        yield v
  else:
    raise RuntimeError(f'Invalid range argument: {cv!r}')


def inConstraint(cv, v, vmin=Vmin, vmax=Vmax, vtol=0):
  """ Test if value v falls within range constraint cv."""
  # Short-circuit the special case of cv being a set and vtol=0.
  if vtol==0 and isinstance(cv,set):
    return vmin <= v <= vmax and v in cv
  return vmin <= v <= vmax and any(v0 <= v <= v1 for v0,v1 in iterConstraint(cv, vmin, vmax, vtol))


def ConstraintRange(cv, vmin=Vmin, vmax=Vmax, vtol=0):
  """Get the (min,max) Range for a constraint definition."""
  mins,maxs = zip((vmax-vtol,vmin+vtol),*iterConstraint(cv,vmin,vmax,vtol))
  #print(f'ContraintRange({cv=},{vmin=},{vmax=},{vtol=}) -> min({mins}),max({maxs})')
  return max(vmin-vtol,min(mins)), min(max(maxs),vmax+vtol)


def IConstraintSet(ci, imin=Imin, imax=Imax):
  """ Create a set Constraint out of an integer constraint. """
  return set(i for i in iterIConstraint(ci,imin,imax))


def iterIConstraint(ci, imin=Imin, imax=Imax):
  """ Iterate through integer values that satisfy an integer constraint.

  The constraint ci can be None, an integer, a (min, max) inclusive
  range-tuple, a set of integers, or an iterable of constraints. The imin and
  imax values are an inclusive range-tuple limit.

  Note this copies iterators so they are not consumed, allowing you to iterate
  through the same ci value multiple times.
  """
  for r0,r1 in iterConstraint(ci, imin, imax, 0):
    for v in range(r0,r1+1):
      yield v


def inIConstraint(i, ci, imin=Imin, imax=Imax):
  """ Test if value v falls within integer range constraint ci."""
  return inConstraint(i, ci, imin, imax, 0)


def RangeType(vmin=Vmin, vmax=Vmax):
  """An argparse type used for initializing Ranges arguments."""
  def init(s):
    try:
      return parseRange(s,vmin,vmax)
    except ValueError:
      raise argparse.ArgumentTypeError(args)
  return init


def ConstraintType(vmin=Vmin, vmax=Vmax):
  """An argparse type used for initializing Constraint arguments."""
  def init(s):
    try:
      return parseConstraint(s, vmin, vmax)
    except ValueError:
      raise argparse.ArgumentTypeError(
          f'{s!r} invalid, must be a list of {type(vmin).__name__} values or min..max '
          f'ranges between {vmin} and {vmax}.')
  return init
