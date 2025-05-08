#!/usr/bin/python3

import unittest
from constraints import *

class TestConstraints(unittest.TestCase):

  def assertSame(self,v1,v2):
    self.assertEqual(v1,v2)
    self.assertEqual(type(v1), type(v2))
    if isinstance(v1, Iterable):
      if isinstance(v1, Iterator): v1,v2 = list(copy(v1)),list(copy(v2))
      for e1,e2 in zip(v1,v2):
        self.assertSame(e1,e2)

  def test_Range(self):
    # No min/max args
    self.assertSame(Range(None), (-inf,inf))
    self.assertSame(Range(5), (5,5))
    self.assertSame(Range((4,6)), (4,6))
    # vmin<values
    self.assertSame(Range(None,3), (3,inf))
    self.assertSame(Range(5,3), (5,5))
    self.assertSame(Range((4,6),3), (4,6))
    # min within values
    self.assertSame(Range(None,5), (5,inf))
    self.assertSame(Range(5,5), (5,5))
    self.assertSame(Range((4,6),5), (5,6))
    # vmin>values
    self.assertSame(Range(None,7), (7,inf))
    self.assertSame(Range(5,7), (7,5))
    self.assertSame(Range((4,6),7), (7,6))
    # vmax>values
    self.assertSame(Range(None,vmax=7), (-inf,7))
    self.assertSame(Range(5,vmax=7), (5,5))
    self.assertSame(Range((4,6),vmax=7), (4,6))
    # vmax within values
    self.assertSame(Range(None,vmax=5), (-inf,5))
    self.assertSame(Range(5,vmax=5), (5,5))
    self.assertSame(Range((4,6),vmax=5), (4,5))
    # vmax<values
    self.assertSame(Range(None,vmax=3), (-inf,3))
    self.assertSame(Range(5,vmax=3), (5,3))
    self.assertSame(Range((4,6),vmax=3), (4,3))
    # vmin<values, vmax>values
    self.assertSame(Range(None,3,7), (3,7))
    self.assertSame(Range(5,3,7), (5,5))
    self.assertSame(Range((4,6),3,7), (4,6))
    # vmin<values, vmax within values
    self.assertSame(Range(None,3,5), (3,5))
    self.assertSame(Range(5,3,5), (5,5))
    self.assertSame(Range((4,6),3,5), (4,5))
    # vmin within values, vmax>values
    self.assertSame(Range(None,5,7), (5,7))
    self.assertSame(Range(5,5,7), (5,5))
    self.assertSame(Range((4,6),5,7), (5,6))
    # vmin within values, vmax within values
    self.assertSame(Range(None,5,5), (5,5))
    self.assertSame(Range(5,5,5), (5,5))
    self.assertSame(Range((4,6),5,5), (5,5))
    # vmin and vmax > values
    self.assertSame(Range(None,7,7), (7,7))
    self.assertSame(Range(5,7,7), (7,5))
    self.assertSame(Range((4,6),7,7), (7,6))
    # vmin and vmax < values
    self.assertSame(Range(None,3,3), (3,3))
    self.assertSame(Range(5,3,3), (5,3))
    self.assertSame(Range((4,6),3,3), (4,3))
    # vmin>vmax
    self.assertSame(Range(None,7,3), (7,3))
    self.assertSame(Range(5,7,3), (7,3))
    self.assertSame(Range((4,6),7,3), (7,3))
    # string args, no vmin or vmax
    self.assertSame(Range('5'), (5,5))
    self.assertSame(Range('4..6'), (4,6))
    self.assertSame(Range('4..'), (4,inf))
    self.assertSame(Range('..6'), (-inf,6))
    self.assertSame(Range('..'), (-inf,inf))
    self.assertRaises(ValueError, Range, '1a')
    self.assertRaises(ValueError, Range, '1..2a')
    # string args, with int vmin or vmax
    self.assertSame(Range('5',3,7), (5,5))
    self.assertSame(Range('4..6',3,7), (4,6))
    self.assertSame(Range('4..',3,7), (4,7))
    self.assertSame(Range('..6',3,7), (3,6))
    self.assertSame(Range('..',3,7), (3,7))
    self.assertRaises(ValueError, Range, '1a', 3, 7)
    self.assertRaises(ValueError, Range, '4..6', 5, 7)
    self.assertRaises(ValueError, Range, '4..6', 3, 5)
    self.assertRaises(ValueError, Range, '5.0', 3, 7)
    self.assertRaises(ValueError, Range, '4.0..6', 3)
    self.assertRaises(ValueError, Range, '4.0..6', vmax=7)
    # string args, with float vmin or vmax
    self.assertSame(Range('5',3.0,7.0), (5.0,5.0))
    self.assertSame(Range('4..6',3.0,7.0), (4.0,6.0))
    self.assertSame(Range('4.0..',3.0,7.0), (4.0,7.0))
    self.assertSame(Range('..6.0',3.0,7.0), (3.0,6.0))
    self.assertSame(Range('..',3.0,7.0), (3.0,7.0))
    self.assertRaises(ValueError, Range, '1a', 3.0, 7.0)

  def test_Range_vtol(self):
    # No min/max args
    self.assertSame(Range(None,vtol=0.1), (-inf,inf))
    self.assertSame(Range(5,vtol=0.1), (4.9,5.1))
    self.assertSame(Range((4,6),vtol=0.1), (3.9,6.1))
    # vmin<values
    self.assertSame(Range(None,3,vtol=0.1), (3,inf))
    self.assertSame(Range(5,3,vtol=0.1), (4.9,5.1))
    self.assertSame(Range((4,6),3,vtol=0.1), (3.9,6.1))
    # min within values
    self.assertSame(Range(None,5,vtol=0.1), (5,inf))
    self.assertSame(Range(5,5,vtol=0.1), (5,5.1))
    self.assertSame(Range((4,6),5,vtol=0.1), (5,6.1))
    # vmin>values
    self.assertSame(Range(None,7,vtol=0.1), (7,inf))
    self.assertSame(Range(5,7,vtol=0.1), (7,5.1))
    self.assertSame(Range((4,6),7,vtol=0.1), (7,6.1))
    # vmax>values
    self.assertSame(Range(None,vmax=7,vtol=0.1), (-inf,7))
    self.assertSame(Range(5,vmax=7,vtol=0.1), (4.9,5.1))
    self.assertSame(Range((4,6),vmax=7,vtol=0.1), (3.9,6.1))
    # vmax within values
    self.assertSame(Range(None,vmax=5,vtol=0.1), (-inf,5))
    self.assertSame(Range(5,vmax=5,vtol=0.1), (4.9,5))
    self.assertSame(Range((4,6),vmax=5,vtol=0.1), (3.9,5))
    # vmax<values
    self.assertSame(Range(None,vmax=3,vtol=0.1), (-inf,3))
    self.assertSame(Range(5,vmax=3,vtol=0.1), (4.9,3))
    self.assertSame(Range((4,6),vmax=3,vtol=0.1), (3.9,3))

  def test_IRange(self):
    self.assertSame(IRange(None), (Imin,Imax))
    self.assertSame(IRange(17), (17,17))
    self.assertSame(IRange((12,15)), (12,15))
    self.assertSame(IRange(7,8), (8,7))
    self.assertSame(IRange(201,imax=200), (201,200))
    self.assertSame(IRange((2,7),8), (8,7))
    self.assertSame(IRange((201,220),8,200), (201,200))
    self.assertSame(IRange(None, 2, 15), (2,15))
    self.assertSame(IRange((7,23),2,15), (7,15))
    self.assertSame(IRange((0,23),2,15), (2,15))
    self.assertSame(IRange(16,2,15), (16,15))
    self.assertSame(IRange((16,26),2,15), (16,15))

  def test_iterConstraint(self):
    self.assertEqual(list(iterConstraint([1,(14,16),27,(28,32),90,1000],vmin=8,vmax=200,vtol=0)),
        [(14,16),(27,27),(28,32),(90,90)])
    self.assertEqual(list(iterConstraint([1,(14,16),27,(28,32),90,1000],vmin=15,vmax=30,vtol=0)),
        [(15,16),(27,27),(28,30)])
    self.assertEqual(list(iterConstraint([1,(14,16),27,(28,32),90,1000],vmin=31,vmax=30,vtol=0)),
        [])

  def test_iterIConstraint(self):
    self.assertEqual(list(iterIConstraint([1,(14,16),27,(28,32),90,1000])),
        [1,14,15,16,27,28,29,30,31,32,90,1000])
    self.assertEqual(list(iterIConstraint([1,(14,16),27,(28,32),90,1000], imin=15, imax=30)),
        [15,16,27,28,29,30])
    self.assertEqual(list(iterIConstraint([1,(14,16),27,(28,32),90,1000], imin=31, imax=30)), [])

  def test_ConstraintRange(self):
    self.assertEqual(ConstraintRange([1,(14,16),27,(28,32),90,1000],vtol=0), (1,1000))
    self.assertEqual(ConstraintRange([1,(14,16),27,(28,32),90,1000],vmin=15,vmax=30,vtol=0), (15,30))
    self.assertEqual(ConstraintRange([1,(14,16),27,(28,32),90,1000],vmin=20,vmax=40,vtol=0), (27,32))
    self.assertEqual(ConstraintRange([1,(14,16),27,(28,32),90,1000],vmin=31,vmax=30,vtol=0), (31,30))
    self.assertEqual(ConstraintRange([1,(14,16),27,(28,32),90,1000],vmin=33,vmax=50,vtol=0), (50,33))

if __name__ == '__main__':
  unittest.main()
