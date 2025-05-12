FeatureScript 2641;
import(path : "onshape/std/common.fs", version : "2641.0");
import(path : "onshape/std/transformUV.fs", version : "2641.0");
import(path : "onshape/std/table.fs", version : "2641.0");
icon::import(path : "2c1e19686bb476b3d3a8b5ff", version : "83c1a2ddb4f05a896b4c8fe3");
image::import(path : "dbd6a7dc0e6e6e1bd68e7598", version : "6dcf4534d27ad364d37aca3f");


export enum GearInputType
{
    annotation { "Name" : "Module" }
    MODULE,
    annotation { "Name" : "Diametral pitch" }
    DIAMETRAL_PITCH,
    annotation { "Name" : "Circular pitch" }
    CIRCULAR_PITCH,
    annotation { "Name" : "Pitch diameter" }
    PITCH_DIAMETER
}

// This is used for both tooth root and tip fillets.
export enum GearFilletType
{
    annotation { "Name" : "None" }
    NONE,
    annotation { "Name" : "1/4" }
    QUARTER,
    annotation { "Name" : "1/3" }
    THIRD,
    annotation { "Name" : "Full" }
    FULL
}

//This is used for both addendum and dedendum factors.
export enum GearDendumFactor
{
    annotation { "Name" : "1.00 x Module" }
    D000,
    annotation { "Name" : "1.157 x Module" }
    D157,
    annotation { "Name" : "1.20 x Module" }
    D200,
    annotation { "Name" : "1.25 x Module" }
    D250
}

export enum GearChamferType
{
    annotation { "Name" : "Equal distance" }
    EQUAL_OFFSETS,
    annotation { "Name" : "Two distances" }
    TWO_OFFSETS,
    annotation { "Name" : "Distance and angle" }
    OFFSET_ANGLE
}

export enum HelixDirection
{
    annotation { "Name" : "Clockwise" }
    CW,
    annotation { "Name" : "Counterclockwise" }
    CCW
}

const TEETH_BOUNDS =
{
            (unitless) : [4, 25, 1000]
        } as IntegerBoundSpec;

const PRESSURE_ANGLE_BOUNDS =
{
            (degree) : [12, 20, 45]
        } as AngleBoundSpec;

const MODULE_BOUNDS =
{
            (meter) : [1e-5, 0.001, 500],
            (centimeter) : 0.1,
            (millimeter) : 1.0,
            (inch) : 0.04
        } as LengthBoundSpec;

const CENTERHOLE_BOUNDS =
{
            (meter) : [1e-5, 0.01, 500],
            (centimeter) : 1.0,
            (millimeter) : 10.0,
            (inch) : 0.375
        } as LengthBoundSpec;

const KEY_BOUNDS =
{
            (meter) : [1e-5, 0.003, 500],
            (centimeter) : 0.3,
            (millimeter) : 3.0,
            (inch) : 0.125
        } as LengthBoundSpec;

const CHAMFER_ANGLE_BOUNDS =
{
            (degree) : [0.1, 60, 179.9]
        } as AngleBoundSpec;

const CHAMFER_BOUNDS =
{
            (meter) : [1e-5, 0.0005, 500],
            (centimeter) : 0.05,
            (millimeter) : 0.5,
            (inch) : 0.02
        } as LengthBoundSpec;

const BACKLASH_BOUNDS =
{
            (meter) : [-500, 0.0, 500],
            (centimeter) : 0,
            (millimeter) : 0,
            (inch) : 0
        } as LengthBoundSpec;

const HELIX_ANGLE_BOUNDS =
{
            (degree) : [5, 15, 45]
        } as AngleBoundSpec;

annotation { "Feature Type Name" : "Spur gear",
        "Editing Logic Function" : "editGearLogic",
        "Feature Name Template" : "Spur gear (#teeth teeth)",
        "Feature Type Description" : "Creates a spur or helical gear with optional center hole and keyway",
        "Description Image" : image::BLOB_DATA,
        "Icon" : icon::BLOB_DATA }
export const SpurGear = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Sketch vertex or mate connector",
                    "Filter" : (EntityType.VERTEX && SketchObject.YES) || BodyType.MATE_CONNECTOR,
                    "MaxNumberOfPicks" : 1,
                    "Description" : "Select a sketch vertex or mate connector to locate the gear" }
        definition.center is Query;

        annotation { "Name" : "Depth" }
        isLength(definition.gearDepth, BLEND_BOUNDS);

        annotation { "Name" : "Opposite direction", "UIHint" : "OPPOSITE_DIRECTION" }
        definition.flipGear is boolean;

        annotation { "Name" : "Symmetric", "Default" : false }
        definition.symmetric is boolean;

        annotation { "Name" : "Number of teeth" }
        isInteger(definition.numTeeth, TEETH_BOUNDS);

        annotation { "Name" : "Gear size and tooth pitch calculation method",
                    "Description" : "<b>Module</b> - Pitch diameter length per tooth.<br>" ~
                    "<b>Diametral pitch</b> - Teeth per inch of pitch diameter.<br>" ~
                    "<b>Circular pitch</b> - Pitch circumference length per tooth.<br>" ~
                    "<b>Pitch diameter</b> - Fixed pitch circle diameter length." }
        definition.GearInputType is GearInputType;

        if (definition.GearInputType == GearInputType.MODULE)
        {
            annotation { "Name" : "Module" }
            isLength(definition.module, MODULE_BOUNDS);
        }
        else if (definition.GearInputType == GearInputType.DIAMETRAL_PITCH)
        {
            annotation { "Name" : "Diametral pitch (teeth/inch)" }
            isReal(definition.diametralPitch, POSITIVE_REAL_BOUNDS);
        }
        else if (definition.GearInputType == GearInputType.CIRCULAR_PITCH)
        {
            annotation { "Name" : "Circular pitch" }
            isLength(definition.circularPitch, LENGTH_BOUNDS);
        }
        else if (definition.GearInputType == GearInputType.PITCH_DIAMETER)
        {
            annotation { "Name" : "Pitch diameter" }
            isLength(definition.pitchCircleDiameter, LENGTH_BOUNDS);
        }

        annotation { "Name" : "Pressure angle" }
        isAngle(definition.pressureAngle, PRESSURE_ANGLE_BOUNDS);

        annotation { "Name" : "Root fillet", "Default" : GearFilletType.THIRD, "UIHint" : "SHOW_LABEL" }
        definition.rootFillet is GearFilletType;

        annotation { "Name" : "Tip fillet", "Default" : GearFilletType.NONE, "UIHint" : "SHOW_LABEL" }
        definition.tipFillet is GearFilletType;

        annotation { "Group Name" : "Profile offsets", "Collapsed By Default" : true }
        {
            annotation { "Name" : "Backlash",
                        "Description" : "A positive value adds clearance between all meshing faces" }
            isLength(definition.backlash, BACKLASH_BOUNDS);

            annotation { "Name" : "Dedendum", "Default" : GearDendumFactor.D250, "UIHint" : "SHOW_LABEL" }
            definition.dedendumFactor is GearDendumFactor;

            annotation { "Name" : "Addendum", "Default" : GearDendumFactor.D000, "UIHint" : "SHOW_LABEL" }
            definition.addendumFactor is GearDendumFactor;

            annotation { "Name" : "Root radius",
                        "Description" : "A positive value adds more clearance at the root" }
            isLength(definition.offsetClearance, ZERO_DEFAULT_LENGTH_BOUNDS);

            annotation { "Name" : "Tip radius",
                        "Description" : "A negative value reduces the outside diameter of the gear" }
            isLength(definition.offsetDiameter, ZERO_DEFAULT_LENGTH_BOUNDS);

            annotation { "Name" : "Clocking angle",
                        "Description" : "Adjust this value to mesh gear trains in a Part Studio" }
            isAngle(definition.offsetAngle, ANGLE_360_ZERO_DEFAULT_BOUNDS);
        }

        annotation { "Name" : "Helical",
                    "Description" : "Create helical or herringbone gear" }
        definition.helical is boolean;

        if (definition.helical)
        {
            annotation { "Group Name" : "Helical", "Collapsed By Default" : false, "Driving Parameter" : "helical" }
            {
                annotation { "Name" : "Angle" }
                isAngle(definition.helixAngle, HELIX_ANGLE_BOUNDS);

                annotation { "Name" : "Direction of helix" }
                definition.handedness is HelixDirection;

                annotation { "Name" : "Double helix" }
                definition.double is boolean;
            }
        }

        annotation { "Name" : "Chamfer", "Default" : false }
        definition.chamfer is boolean;

        if (definition.chamfer)
        {
            annotation { "Group Name" : "Chamfer", "Collapsed By Default" : false, "Driving Parameter" : "chamfer" }
            {
                annotation { "Name" : "Chamfer type", "Default" : GearChamferType.OFFSET_ANGLE }
                definition.chamferType is GearChamferType;

                if (definition.chamferType != GearChamferType.TWO_OFFSETS)
                {
                    annotation { "Name" : "Distance" }
                    isLength(definition.width, CHAMFER_BOUNDS);
                }
                else
                {
                    annotation { "Name" : "Distance 1" }
                    isLength(definition.width1, CHAMFER_BOUNDS);
                }

                if (definition.chamferType == GearChamferType.OFFSET_ANGLE ||
                    definition.chamferType == GearChamferType.TWO_OFFSETS)
                {
                    annotation { "Name" : "Opposite direction", "Default" : false, "UIHint" : "OPPOSITE_DIRECTION" }
                    definition.oppositeDirection is boolean;
                }

                if (definition.chamferType == GearChamferType.TWO_OFFSETS)
                {
                    annotation { "Name" : "Distance 2" }
                    isLength(definition.width2, CHAMFER_BOUNDS);
                }
                else if (definition.chamferType == GearChamferType.OFFSET_ANGLE)
                {
                    annotation { "Name" : "Angle" }
                    isAngle(definition.angle, CHAMFER_ANGLE_BOUNDS);
                }
            }
        }

        annotation { "Name" : "Center bore" }
        definition.centerHole is boolean;

        if (definition.centerHole)
        {
            annotation { "Group Name" : "Center Bore", "Collapsed By Default" : false, "Driving Parameter" : "centerHole" }
            {
                annotation { "Name" : "Bore diameter" }
                isLength(definition.centerHoleDia, CENTERHOLE_BOUNDS);

                annotation { "Name" : "Keyway" }
                definition.key is boolean;

                if (definition.key)
                {
                    annotation { "Name" : "Key width" }
                    isLength(definition.keyWidth, KEY_BOUNDS);

                    annotation { "Name" : "Key height" }
                    isLength(definition.keyHeight, KEY_BOUNDS);
                }
            }
        }
    }

    {
        // Note editGearLogic() is not automatically called when variables used in settings change, so we call it explicitly to ensure the settings are consistent.
        definition = editGearLogic(context, id, definition, definition, false);

        if (definition.centerHole && definition.centerHoleDia >= definition.pitchCircleDiameter - 4 * definition.module)
        {
            throw regenError("Center hole diameter must be less than root diameter", ["centerHoleDia"]);
        }

        if (definition.key && definition.keyHeight / 2 + definition.centerHoleDia >= definition.pitchCircleDiameter - 4 * definition.module)
        {
            throw regenError("Center hole diameter plus key height must be less than root diameter", ["keyHeight"]);
        }

        const remainderTransform = getRemainderPatternTransform(context, {
                    "references" : definition.center
                });

        var sketchPlane = plane(WORLD_ORIGIN, -Y_DIRECTION, X_DIRECTION);

        // else find location of selected vertex and its sketch plane or use mate connector to create a new sketch for the gear profile
        if (!isQueryEmpty(context, definition.center))
        {
            try silent
            {
                sketchPlane = plane(evMateConnector(context, {
                                "mateConnector" : definition.center
                            }));
            }
            catch
            {
                sketchPlane = evOwnerSketchPlane(context, { "entity" : definition.center });
                sketchPlane.origin = evVertexPoint(context, { "vertex" : definition.center });
            }
        }

        var addendumFactor = 1.00;
        if (definition.addendumFactor == GearDendumFactor.D157)
            addendumFactor = 1.157;
        if (definition.addendumFactor == GearDendumFactor.D200)
            addendumFactor = 1.2;
        else if (definition.addendumFactor == GearDendumFactor.D250)
            addendumFactor = 1.25;

        var dedendumFactor = 1.25;
        if (definition.dedendumFactor == GearDendumFactor.D000)
            dedendumFactor = 1.0;
        else if (definition.dedendumFactor == GearDendumFactor.D157)
            dedendumFactor = 1.157;
        else if (definition.dedendumFactor == GearDendumFactor.D200)
            dedendumFactor = 1.2;

        var gearData = { "center" : vector(0, 0) * meter };
        gearData.addendum = addendumFactor * definition.module + definition.offsetDiameter;
        gearData.dedendum = dedendumFactor * definition.module + definition.offsetClearance;
        gearData.pitchRadius = definition.pitchCircleDiameter / 2;
        gearData.outerRadius = gearData.pitchRadius + gearData.addendum;
        gearData.innerRadius = gearData.pitchRadius - gearData.dedendum;

        const blank = createBlank(context, id, definition, gearData, sketchPlane);
        const tooth = createTooth(context, id, definition, gearData, sketchPlane);

        var transforms = [];
        var instanceNames = [];

        for (var i = 1; i < definition.numTeeth; i += 1)
        {
            const instanceTransform = rotationAround(line(sketchPlane.origin, sketchPlane.normal), i * (360 / definition.numTeeth) * degree);
            transforms = append(transforms, instanceTransform);
            instanceNames = append(instanceNames, "" ~ i);
        }

        opPattern(context, id + "pattern", {
                    "entities" : tooth,
                    "transforms" : transforms,
                    "instanceNames" : instanceNames
                });

        opBoolean(context, id + "hobbed", {
                    "tools" : qUnion(tooth, qCreatedBy(id + "pattern", EntityType.BODY)),
                    "targets" : blank,
                    "operationType" : BooleanOperationType.SUBTRACTION,
                    "keepTools" : false
                });

        opDeleteBodies(context, id + "delete", {
                    "entities" : qSubtraction(qCreatedBy(id, EntityType.BODY), blank)
                });

        // create Pitch Circle Diameter sketch for aligning gear trains
        const PCDSketch = newSketchOnPlane(context, id + "PCDsketch", { "sketchPlane" : sketchPlane });

        skCircle(PCDSketch, "PCD", {
                    "center" : gearData.center,
                    "radius" : gearData.pitchRadius,
                    "construction" : true
                });

        skSolve(PCDSketch);

        transformResultIfNecessary(context, id, remainderTransform);

        setGearData(context, id, definition, gearData);
    });

function setGearData(context is Context, id is Id, definition is map, gearData is map)
{
    var gearInputType = "Module";
    var gearInputSize = definition.module;

    if (definition.GearInputType == GearInputType.DIAMETRAL_PITCH)
    {
        gearInputType = "Diametral pitch";
        gearInputSize = definition.diametralPitch;
    }
    else if (definition.GearInputType == GearInputType.CIRCULAR_PITCH)
    {
        gearInputType = "Circular pitch";
        gearInputSize = definition.circularPitch;
    }
    else if (definition.GearInputType == GearInputType.PITCH_DIAMETER)
    {
        gearInputType = "Pitch diameter";
        gearInputSize = definition.pitchCircleDiameter;
    }

    setAttribute(context, {
                "entities" : qBodyType(qCreatedBy(id, EntityType.BODY), BodyType.SOLID),
                "name" : "spurGear",
                "attribute" : {
                    "numTeeth" : definition.numTeeth,
                    "gearInputType" : gearInputType,
                    "gearInputSize" : gearInputSize,
                    "pitchCircleDiameter" : definition.pitchCircleDiameter,
                    "outerDiameter" : gearData.outerRadius * 2,
                    "innerDiameter" : gearData.innerRadius * 2,
                    "pressureAngle" : definition.pressureAngle,
                } // TODO: center hole, chamfer, helical
            });

    setFeatureComputedParameter(context, id, {
                "name" : "teeth",
                "value" : definition.numTeeth
            });

    setProperty(context, {
                "entities" : qBodyType(qCreatedBy(id, EntityType.BODY), BodyType.SOLID),
                "propertyType" : PropertyType.NAME,
                "value" : "Spur gear (" ~ definition.numTeeth ~ " teeth)"
            });
}

function createBlank(context is Context, id is Id, definition is map, gearData is map, sketchPlane is Plane) returns Query
{
    const blankSketch = newSketchOnPlane(context, id + "blankSketch", { "sketchPlane" : sketchPlane });

    skCircle(blankSketch, "addendum", {
                "center" : gearData.center,
                "radius" : gearData.outerRadius
            });

    if (definition.centerHole)
    {
        if (definition.key)
        {
            const xDirection = (definition.keyWidth / 2) * vector(1, 0);
            const yDirection = ((definition.keyHeight + definition.centerHoleDia) / 2) * vector(0, 1);

            skPolyline(blankSketch, "keyway", {
                        "points" : [
                            gearData.center + xDirection,
                            gearData.center + xDirection + yDirection,
                            gearData.center - xDirection + yDirection,
                            gearData.center - xDirection
                        ]
                    });
        }

        skCircle(blankSketch, "center", {
                    "center" : gearData.center,
                    "radius" : definition.centerHoleDia / 2
                });
    }

    skSolve(blankSketch);

    opExtrude(context, id + "blank", extrudeParams(definition, qSketchRegion(id + "blankSketch", true), sketchPlane));

    if (definition.chamfer)
    {
        definition.entities = qLargest(qCreatedBy(id + "blank", EntityType.EDGE));

        if (definition.flipGear)
            definition.oppositeDirection = !definition.oppositeDirection;

        try
        {
            opChamfer(context, id + "chamfer", definition);
        }
        catch
        {
            throw regenError("Chamfer failed, check inputs", ["width", "width1", "width2", "angle"]);
        }
    }

    return qCreatedBy(id + "blank", EntityType.BODY);
}

function createTooth(context is Context, id is Id, definition is map, gearData is map, sketchPlane is Plane) returns Query
{
    const baseRadius = gearData.pitchRadius * cos(definition.pressureAngle);
    const toothAngle = 2 * PI / definition.numTeeth * radian;
    // alpha is the angle where the involute curve crosses the pitch circle.
    const alpha = tan(definition.pressureAngle) * radian - definition.pressureAngle;
    // backlash is the extra rotation due to the extra backlash-gap (in mm) at the pitch cicle and pressure angle.
    const backlash = definition.backlash / (2 * cos(definition.pressureAngle) * definition.pitchCircleDiameter) * radian;
    // beta is the angle between the mid-tooth gap and the next tooth-edge at the pitch circle.
    const beta = toothAngle / 4 - alpha + backlash;
    // these are the raw angles to the next and previous tooth edges including offsetAngle.
    const offset1 = definition.offsetAngle + beta;
    const offset2 = definition.offsetAngle - beta;
    // This is a unit-vector pointing to the mid-tooth gap.
    const middleVect = vector(cos(definition.offsetAngle), sin(definition.offsetAngle));
    // This is a rotation transform matrix to move around a whole tooth.
    const rotateTooth = rotate(toothAngle);

    const toothSketch = newSketchOnPlane(context, id + "toothSketch", { "sketchPlane" : sketchPlane });

    // build involute splines for each tooth
    var involute1 = [];
    var involute2 = [];
    var involute3 = [];
    for (var t = 0; t <= 2; t += (1 / 50)) // (1/50) is the hard-coded involute spline tolerance
    {
        // involute definition math.
        const angle = t * radian;
        const ca1 = cos(offset1 + angle);
        const sa1 = sin(offset1 + angle);
        const ca2 = cos(offset2 - angle);
        const sa2 = sin(offset2 - angle);
        var point1;
        var point2;
        var point3;

        if (baseRadius >= gearData.innerRadius && t == 0)
        {
            // special case when base cylinder diameter is greater than dedendum
            point1 = gearData.innerRadius * vector(ca1, sa1);
            point2 = gearData.innerRadius * vector(ca2, sa2);
        }
        else
        {
            // calculate involute spline point
            point1 = baseRadius * vector((ca1 + t * sa1), (sa1 - t * ca1));
            point2 = baseRadius * vector((ca2 - t * sa2), (sa2 + t * ca2));
        }
        point3 = rotateTooth.linear * point2;

        // and add to array
        involute1 = append(involute1, point1);
        involute2 = append(involute2, point2);
        involute3 = append(involute3, point3);

        // if involute points go outside the outer diameter of the gear then stop
        if (norm(point1) >= gearData.outerRadius)
            break;
    }

    // create involute sketch splines
    skFitSpline(toothSketch, "spline1", { "points" : involute1 });
    skFitSpline(toothSketch, "spline2", { "points" : involute2 });
    skFitSpline(toothSketch, "spline3", { "points" : involute3, "construction" : true });

    // gapPoint is in the middle of the tooth-gap on the pitch circle.
    const gapPoint = gearData.pitchRadius * middleVect;
    // toothPoint is in the middle of the next tooth on the pitch circle.
    const toothPoint = rotate(toothAngle / 2).linear * gapPoint;
    // ringPoint is in the middle of the tooth-gap on the outerRadius.
    const ringPoint = gearData.outerRadius * middleVect;

    skCircle(toothSketch, "addendum", { "center" : gearData.center, "radius" : gearData.outerRadius });
    skCircle(toothSketch, "dedendum", { "center" : gearData.center, "radius" : gearData.innerRadius });
    skCircle(toothSketch, "outring", { "center" : gearData.center, "radius" : gearData.outerRadius + 1.0 * millimeter });

    // fix addendum, dedendum, and splines so they don't move when solving fillet constraints.
    skConstraint(toothSketch, "fix1", { "constraintType" : ConstraintType.FIX, "localFirst" : "addendum" });
    skConstraint(toothSketch, "fix2", { "constraintType" : ConstraintType.FIX, "localFirst" : "dedendum" });
    skConstraint(toothSketch, "fix3", { "constraintType" : ConstraintType.FIX, "localFirst" : "spline1" });
    skConstraint(toothSketch, "fix4", { "constraintType" : ConstraintType.FIX, "localFirst" : "spline2" });
    skConstraint(toothSketch, "fix5", { "constraintType" : ConstraintType.FIX, "localFirst" : "spline3" });

    if (definition.rootFillet != GearFilletType.NONE)
    {
        skCircle(toothSketch, "rfillet", { "center" : gapPoint, "radius" : 0.1 * millimeter, "construction" : true });
        skConstraint(toothSketch, "rtangent1", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "rfillet", "localSecond" : "dedendum" });
        skConstraint(toothSketch, "rtangent2", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "rfillet", "localSecond" : "spline1" });
        skConstraint(toothSketch, "rtangent3", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "rfillet", "localSecond" : "spline2" });
    }

    if (definition.tipFillet != GearFilletType.NONE)
    {
        skCircle(toothSketch, "tfillet", { "center" : toothPoint, "radius" : 0.1 * millimeter, "construction" : true });
        skConstraint(toothSketch, "ttangent1", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "tfillet", "localSecond" : "addendum" });
        skConstraint(toothSketch, "ttangent2", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "tfillet", "localSecond" : "spline1" });
        skConstraint(toothSketch, "ttangent3", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "tfillet", "localSecond" : "spline3" });
    }

    skSolve(toothSketch);

    var toothId = id + "tooth";

    // This extrudes a tooth-gap attached to an outer ring for subtracting from a gear blank.
    opExtrude(context, toothId, extrudeParams(definition, qClosestTo(qSketchRegion(id + "toothSketch"), planeToWorld(sketchPlane, ringPoint)), sketchPlane));

    if (definition.rootFillet != GearFilletType.NONE)
    {
        const rootFilletEdges = qClosestTo(qNonCapEntity(toothId, EntityType.EDGE), sketchPlane.origin);
        var rootFilletRadius = evCurveDefinition(context, { "edge" : sketchEntityQuery(id + "toothSketch", EntityType.EDGE, "rfillet") }).radius;

        if (definition.rootFillet == GearFilletType.THIRD)
            rootFilletRadius /= 1.5;
        else if (definition.rootFillet == GearFilletType.QUARTER)
            rootFilletRadius /= 2;

        opFillet(context, id + "rfillet", {
                    "entities" : rootFilletEdges,
                    "radius" : rootFilletRadius
                });
    }

    if (definition.tipFillet != GearFilletType.NONE)
    {
        const tipFilletEdges = qClosestTo(qNonCapEntity(toothId, EntityType.EDGE), planeToWorld(sketchPlane, ringPoint));
        var tipFilletRadius = evCurveDefinition(context, { "edge" : sketchEntityQuery(id + "toothSketch", EntityType.EDGE, "tfillet") }).radius;

        if (definition.tipFillet == GearFilletType.THIRD)
            tipFilletRadius /= 1.5;
        else if (definition.tipFillet == GearFilletType.QUARTER)
            tipFilletRadius /= 2;

        opFillet(context, id + "tfillet", {
                    "entities" : tipFilletEdges,
                    "radius" : tipFilletRadius
                });
    }

    if (definition.helical)
    {
        const profileFace = qCapEntity(toothId, CapType.START, EntityType.FACE);
        const helicalPitch = (PI * definition.pitchCircleDiameter) / tan(definition.helixAngle);
        var clockwise = definition.handedness == HelixDirection.CW;

        if (definition.double)
            clockwise = !clockwise;

        if (definition.flipGear && definition.double)
            clockwise = !clockwise;

        opHelix(context, id + "helix", {
                    "direction" : sketchPlane.normal * (definition.flipGear ? -1 : 1),
                    "axisStart" : sketchPlane.origin,
                    "startPoint" : sketchPlane.origin + sketchPlane.x * gearData.pitchRadius,
                    "interval" : [0, definition.gearDepth / helicalPitch / (definition.double ? 2 : 1)],
                    "clockwise" : clockwise,
                    "helicalPitch" : helicalPitch,
                    "spiralPitch" : 0 * meter
                });

        toothId = id + "toothHelix";

        opSweep(context, toothId, {
                    "profiles" : profileFace,
                    "path" : qCreatedBy(id + "helix", EntityType.EDGE)
                });

        if (definition.double)
        {
            opPattern(context, id + "mirror", {
                        "entities" : qCreatedBy(toothId, EntityType.BODY),
                        "transforms" : [mirrorAcross(evPlane(context, {
                                        "face" : qCapEntity(toothId, CapType.END, EntityType.FACE)
                                    }))],
                        "instanceNames" : ["1"] });

            opBoolean(context, id + "double", {
                        "tools" : qUnion(qCreatedBy(toothId, EntityType.BODY), qCreatedBy(id + "mirror", EntityType.BODY)),
                        "operationType" : BooleanOperationType.UNION
                    });
        }
    }

    return qCreatedBy(toothId, EntityType.BODY);
}

function extrudeParams(definition is map, entities is Query, sketchPlane is Plane) returns map
{
    var extrudeParams = {
        "entities" : entities,
        "direction" : sketchPlane.normal * (definition.flipGear ? -1 : 1),
        "endBound" : BoundingType.BLIND,
        "endDepth" : definition.gearDepth
    };

    if (definition.symmetric)
    {
        extrudeParams = mergeMaps(extrudeParams,
            {
                    "startBound" : BoundingType.BLIND,
                    "startDepth" : definition.gearDepth / 2,
                    "endDepth" : definition.gearDepth / 2
                });
    }

    return extrudeParams;
}

export function editGearLogic(context is Context, id is Id, oldDefinition is map, definition is map, isCreating is boolean) returns map
{
    // Note we only assign settings if they need to be changed so we don't overwrite correct settings using variables.
    // Update module from diametralPitch, circularPitch, or pitchCircleDiameter if they are authoratative.
    if (definition.GearInputType == GearInputType.DIAMETRAL_PITCH && definition.module != inch / definition.diametralPitch)
        definition.module = inch / definition.diametralPitch;
    else if (definition.GearInputType == GearInputType.CIRCULAR_PITCH && definition.module != definition.circularPitch / PI)
        definition.module = definition.circularPitch / PI;
    else if (definition.GearInputType == GearInputType.PITCH_DIAMETER && definition.module != definition.pitchCircleDiameter / definition.numTeeth)
        definition.module = definition.pitchCircleDiameter / definition.numTeeth;

    // Correct settings relationships if they are wrong.
    if (definition.diametralPitch != inch / definition.module)
        definition.diametralPitch = inch / definition.module;
    if (definition.circularPitch != definition.module * PI)
        definition.circularPitch = definition.module * PI;
    if (definition.pitchCircleDiameter != definition.numTeeth * definition.module)
        definition.pitchCircleDiameter = definition.numTeeth * definition.module;

    return definition;
}

annotation { "Table Type Name" : "Gears", "Icon" : icon::BLOB_DATA }
export const spurGearsTable = defineTable(function(context is Context, definition is map) returns Table
    precondition
    {
    }
    {
        const columnDefinitions = [
                tableColumnDefinition("quantity", "Qty"),
                tableColumnDefinition("numTeeth", "Teeth"),
                tableColumnDefinition("gearInputType", "Pitch type"),
                tableColumnDefinition("gearInputSize", "Pitch size"),
                tableColumnDefinition("pitchCircleDiameter", "Pitch diameter"),
                tableColumnDefinition("outerDiameter", "Outer diameter"),
                tableColumnDefinition("innerDiameter", "Inner diameter"),
                tableColumnDefinition("pressureAngle", "Pressure angle"),
            ];

        // Group by same values
        var uniqueGears = {};
        const partsWithGearAttributes = qHasAttribute("spurGear");

        for (var part in evaluateQuery(context, partsWithGearAttributes))
        {
            const gearAttributes = getAttributes(context, {
                        "entities" : part,
                        "name" : "spurGear"
                    });

            if (gearAttributes == [])
            {
                continue;
            }

            const attribute = gearAttributes[0];
            if (uniqueGears[attribute] == undefined)
            {
                uniqueGears[attribute] = [];
            }

            uniqueGears[attribute] = append(uniqueGears[attribute], part);
        }

        var rows = [];

        for (var gearEntry in uniqueGears)
        {
            const parts = gearEntry.value;
            var gearData = gearEntry.key;
            gearData.quantity = size(gearEntry.value);
            rows = append(rows, tableRow(gearData, qUnion(parts)));
        }

        return table("Gears", columnDefinitions, rows);
    });
