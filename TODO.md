# SplitRingGears TODO

## 3DPrinting

pressure advance test for old-style PA
PA calibration test
pressure model calibration tests

## Configuration Options

* bearings
* join types
* input/output sizes? 10/15/20/30?
* efficient gears?

# Design Changes

* standardize on 20mm input/output?
* Figure out input/output with bearings.
* Add a metal axle through the middle?
  * Could anchor between case and ring2, provide input fixed to sun1, and pass through carrier and sun2.
  * Could allow 2x5x2.5 bearings for all of them?
    * Sun2 is too small for bearings?
  * Could stabilize/center them all, but is floating better?
* Add optional bearings
  * none: - as is.
    * +0.1mm clearance for diameters and surfaces at contact points and +0.3mm space for non-contact gaps.
    * Use +0.2mm 1mm wide chamfered rims to close 0.3mm space gap to 0.1mm clearance at bearing points.
  * sleve:
    * config options: outer diameter.
    * Inner diameter is axle diameter +0.1mm.
    * Length is through-all. With +0.1mm exta extrusion?
    * Can be made out of PTFE tube.
  * colar:
    * Config options: outer diameter, length, colar diameter, colar thickness.
    * Inner diameter is axle diameter +0.1mm.
    * Can be made out of rivets.
  * ring:
    * Config Options: inner x outer x height.
    * Inner-diameter should equal axle diameter.
    * Axle hole should be axle-diameter+0.3mm.
    * Inserted into gears or around input/output.
    * Insertion hole should include +0.2mm (layer height) clearance for 2/3 of inner ring width.
    * Can be purchased.
  * Design integrated bearings?
* Add optional planet bearings
  * none/sleve/colar/ring.
* Add optional input bearings.
  * none/ring/ptfe ring?
  * on metal axle?
* Add optional output bearings.
  * none/ring/ptfe ring?
  * output is so slow it doesn't need bearings?
  
* Drive gear module from preferred case size?
* Output tables for parts?
* table? driven component selection?

## Gear Profiles

* high efficiency gears.
* Calculate contact ratios.
  * transverse (addendum and size driven).
  * axial (helix angle and width driven).
* Figure out addendum vs size for target transverse contact ratios.
* Figure out helix angle for target axial contact ratio

## Featurescript utilities

* heat set pins. 
  * 0.1mm smallert than pin size avg.
  * insert end +0.1mm, other end -0.3mm
  * initial shaft +0.1mm, chamfer 0.2mm off over length
* heat set inserts?
  * standard heatset dimensions data?
  * Add custom option?
  * include tapers?
* standard metric bolt/nut dimension data?
  * standard cap/low/flat heads
  * non-standard wafer heads?
  * export from spreadsheet?
* detents on embedded nuts.
* detents on force-fit holes?
  * end dome vs shaft length?
  * select hole and depth(s)/plane(s)?
* bearings?
* shafts?
* sacrificial bridging.

research:

* options/workarounds for one config per part studio.
* configuring enum inputs from variables.
* calling other featurescript from featurescript.
* exposing sub-configuration inputs as external inputs.
* driving parts list tables.
