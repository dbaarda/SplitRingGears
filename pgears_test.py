#!/usr/bin/python3

import unittest
import pgears

# ulim is a (min,max) range that implies no limits.
ulim=(-1000,1000)

class TestPGearsUtils(unittest.TestCase):

  def test_TpRange(self):
    self.assertEqual(pgears.TpRange(Ts=9), (8,43))
    self.assertEqual(pgears.TpRange(Ts=10), (8,49))
    self.assertEqual(pgears.TpRange(Tr=95), (8,43))
    self.assertEqual(pgears.TpRange(Tr=99), (8,44))
    self.assertEqual(pgears.TpRange(Tr=100), (8,45))
    self.assertEqual(pgears.TpRange(Tr=101), (8,45))
    self.assertEqual(pgears.TpRange(Tr=102), (8,46))
    self.assertEqual(pgears.TpRange(Tr=108), (8,49))
    # Tp cannot fit between Ts and Tr without planets touching.
    self.assertEqual(pgears.TpRange(Tr=100, Ts=8), (46,36))
    # Invalid Tr and Ts combination; violates (Ts+Tr)%2=0
    self.assertEqual(pgears.TpRange(Tr=100, Ts=9), (46,43))
    # Valid Tr and Ts with Tp fits with planets just not touching.
    self.assertEqual(pgears.TpRange(Tr=100,Ts=10), (45,45))
    # Invalid Tr and Ts combination; violates (Ts+Tr)%2=0
    self.assertEqual(pgears.TpRange(Tr=100, Ts=11), (45,44))
    # Valid Tr and Ts with Tp fits with planets far from touching.
    self.assertEqual(pgears.TpRange(Tr=100,Ts=12), (44,44))
    self.assertEqual(pgears.TpRange(Tr=100,Ts=(8,12)), (44,45))
    self.assertEqual(pgears.TpRange(Tr=(95,108),Ts=(8,12)), (42,49))
    self.assertEqual(pgears.TpRange(Tr=100,Tp=12), (12,12))

  def test_TpRange_np(self):
    # Try different numbers of planets
    self.assertEqual(pgears.TpRange(Ts=8,np=2), (8,96))
    self.assertEqual(pgears.TpRange(Ts=8,np=3), (8,36))
    self.assertEqual(pgears.TpRange(Ts=8,np=4), (8,12))
    self.assertEqual(pgears.TpRange(Tr=100,np=2), (8,46))
    self.assertEqual(pgears.TpRange(Tr=100,np=3), (8,45))
    self.assertEqual(pgears.TpRange(Tr=100,np=4), (8,40))

  def test_TRanges(self):
    self.assertEqual(pgears.TRanges(), ((24, 200), (8,91), (8, 184)))
    self.assertEqual(pgears.TRanges(Tr=(8,100)), ((24,100),(8,45),(8,84)))
    self.assertEqual(pgears.TRanges(Tr=(95,108), Ts=(8,12)), ((95,108),(42,49),(9,12)))
    self.assertEqual(pgears.TRanges(32), ((32,32),(8,12),(8,16)))
    self.assertEqual(pgears.TRanges((8,64)),((24, 64), (8, 28), (8, 48)))
    self.assertEqual(pgears.TRanges(100), ((100, 100), (8, 45), (10, 84)))

  def test_TRanges_smin(self):
    self.assertEqual(pgears.TRanges(smin=2), ((20, 200), (8, 91), (4, 184)))

  def test_TxRange(self):
    rmin=24
    for d in range(rmin,200):
      rr = pgears.TrRange(tmax=d)
      rp = pgears.TpRange(tmax=d)
      rs = pgears.TsRange(tmax=d)
      self.assertEqual(pgears.TRanges(tmax=d), (rr,rp,rs))
      self.assertEqual(pgears.TRanges(rr, rp, rs,tmax=d), (rr,rp,rs))


if __name__ == '__main__':
  unittest.main()
