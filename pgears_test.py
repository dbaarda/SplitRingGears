#!/usr/bin/python3

import unittest
import pgears

# ulim is a (min,max) range that implies no limits.
ulim=(-1000,1000)

# Set gear teeth limits.
pgears.setLimits(tmin=8, tmax=200)

class TestPGearsUtils(unittest.TestCase):

  def test_TpRange_lims(self):
    self.assertEqual(pgears.TpRange(rs=9), (8,43))
    self.assertEqual(pgears.TpRange(rs=10), (8,49))
    self.assertEqual(pgears.TpRange(rr=95), (8,43))
    self.assertEqual(pgears.TpRange(rr=99), (8,44))
    self.assertEqual(pgears.TpRange(rr=100), (8,45))
    self.assertEqual(pgears.TpRange(rr=101), (8,45))
    self.assertEqual(pgears.TpRange(rr=102), (8,46))
    self.assertEqual(pgears.TpRange(rr=108), (8,49))
    # Tp cannot fit between Ts and Tr without planets touching.
    self.assertEqual(pgears.TpRange(rr=100, rs=8), (46,36))
    # Invalid Tr and Ts combination; violates (Ts+Tr)%2=0
    self.assertEqual(pgears.TpRange(rr=100, rs=9), (46,43))
    # Valid Tr and Ts with Tp fits with planets just not touching.
    self.assertEqual(pgears.TpRange(rr=100,rs=10), (45,45))
    # Invalid Tr and Ts combination; violates (Ts+Tr)%2=0
    self.assertEqual(pgears.TpRange(rr=100, rs=11), (45,44))
    # Valid Tr and Ts with Tp fits with planets far from touching.
    self.assertEqual(pgears.TpRange(rr=100,rs=12), (44,44))
    self.assertEqual(pgears.TpRange(rr=100,rs=(8,12)), (44,45))
    self.assertEqual(pgears.TpRange(rr=(95,108),rs=(8,12)), (42,49))
    self.assertEqual(pgears.TpRange(rr=100,rp=12), (12,12))

  def test_TpRange_n(self):
    # Try different numbers of planets
    self.assertEqual(pgears.TpRange(rs=8,n=2), (8,96))
    self.assertEqual(pgears.TpRange(rs=8,n=3), (8,36))
    self.assertEqual(pgears.TpRange(rs=8,n=4), (8,12))
    self.assertEqual(pgears.TpRange(rr=100,n=2), (8,46))
    self.assertEqual(pgears.TpRange(rr=100,n=3), (8,45))
    self.assertEqual(pgears.TpRange(rr=100,n=4), (8,40))

  def test_TpRange(self):
    self.assertEqual(pgears.TpRange(), (8, 91))
    self.assertEqual(pgears.TpRange(rr=(8,100)), (8,45),(8,84))
    self.assertEqual(pgears.TpRange(rr=(95,108), rs=(8,12)), (42,49))
    self.assertEqual(pgears.TpRange(32), (8,12))
    self.assertEqual(pgears.TpRange((8,64)), (8, 28))
    self.assertEqual(pgears.TpRange(100), (8, 45))

  def test_TsRange(self):
    self.assertEqual(pgears.TsRange(), (8, 184))
    self.assertEqual(pgears.TsRange(rr=(8,100)), (8,84))
    self.assertEqual(pgears.TsRange(rr=(95,108), rs=(8,12)), (9,12))
    self.assertEqual(pgears.TsRange(32), (8,16))
    self.assertEqual(pgears.TsRange((8,64)), (8, 48))
    self.assertEqual(pgears.TsRange(100), (10, 84))

  def test_TxRange(self):
    self.assertEqual(pgears.TrRange(), (24, 200))
    self.assertEqual(pgears.TrRange(rr=(8,100)), (24,100))
    self.assertEqual(pgears.TrRange(rr=(95,108), rs=(8,12)), (95,108))
    self.assertEqual(pgears.TrRange(32), (32,32))
    self.assertEqual(pgears.TrRange((8,64)), (24, 64))
    self.assertEqual(pgears.TrRange(100), (100, 100))

  def test_TxRange_smin(self):
    self.assertEqual(pgears.TpRange(smin=2), (8, 91))
    self.assertEqual(pgears.TsRange(smin=2), (4, 184))
    self.assertEqual(pgears.TrRange(smin=2), (20, 200))


if __name__ == '__main__':
  unittest.main()
