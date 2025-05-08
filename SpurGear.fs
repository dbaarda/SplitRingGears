FeatureScript 1301;
import(path : "onshape/std/common.fs", version : "1301.0");
import(path : "onshape/std/table.fs", version : "1301.0");
icon::import(path : "84e649fcf78ef2cf627fcf5e", version : "4adb2fbb86b2ebf683c17b68");

annotation { "Feature Type Name" : "Spur Gear", "Feature Name Template" : "Spur Gear (#teeth teeth)", "Editing Logic Function" : "editGearLogic", "Icon" : icon::BLOB_DATA }
export const SpurGear = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Number of teeth" }
        isInteger(definition.numTeeth, TEETH_BOUNDS);

        annotation { "Name" : "Input type" }
        definition.GearInputType is GearInputType;

        if (definition.GearInputType == GearInputType.module)
        {
            annotation { "Name" : "Module" }
            isLength(definition.module, MODULE_BOUNDS);
        }

        if (definition.GearInputType == GearInputType.diametralPitch)
        {
            annotation { "Name" : "Diametral pitch" }
            isReal(definition.diametralPitch, POSITIVE_REAL_BOUNDS);
        }

        if (definition.GearInputType == GearInputType.circularPitch)
        {
            annotation { "Name" : "Circular pitch" }
            isLength(definition.circularPitch, LENGTH_BOUNDS);
        }

        annotation { "Name" : "Pitch circle diameter" }
        isLength(definition.pitchCircleDiameter, LENGTH_BOUNDS);

        annotation { "Name" : "Pressure angle" }
        isAngle(definition.pressureAngle, PRESSURE_ANGLE_BOUNDS);

        annotation { "Name" : "Root fillet", "Default" : RootFilletType.third, "UIHint" : "SHOW_LABEL" }
        definition.rootFillet is RootFilletType;

        annotation { "Name" : "Chamfer", "Default" : false }
        definition.chamfer is boolean;

        if (definition.chamfer)
        {
            annotation { "Group Name" : "Chamfer", "Collapsed By Default" : false, "Driving Parameter" : "chamfer" }
            {
                // Copied from the Chamfer feature
                annotation { "Name" : "Chamfer type", "Default" : GearChamferType.OFFSET_ANGLE }
                definition.chamferType is GearChamferType;

                //first quantity input (length)
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

                //opposite direction button
                if (definition.chamferType == GearChamferType.OFFSET_ANGLE ||
                    definition.chamferType == GearChamferType.TWO_OFFSETS)
                {
                    annotation { "Name" : "Opposite direction", "Default" : false, "UIHint" : "OPPOSITE_DIRECTION" }
                    definition.oppositeDirection is boolean;
                }

                //second quantity input (length or angle depending on type)
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

        annotation { "Name" : "Profile offsets" }
        definition.offset is boolean;

        if (definition.offset)
        {
            annotation { "Group Name" : "Offsets", "Collapsed By Default" : false, "Driving Parameter" : "offset" }
            {
                annotation { "Name" : "Backlash" }
                isLength(definition.backlash, BACKLASH_BOUNDS);

                annotation { "Name" : "Dedendum", "Default" : DedendumFactor.d250, "UIHint" : "SHOW_LABEL" }
                definition.dedendumFactor is DedendumFactor;

                annotation { "Name" : "Root diameter" }
                isLength(definition.offsetClearance, ZERO_DEFAULT_LENGTH_BOUNDS);

                annotation { "Name" : "Tip diameter" }
                isLength(definition.offsetDiameter, ZERO_DEFAULT_LENGTH_BOUNDS);

                annotation { "Name" : "Clocking angle" }
                isAngle(definition.offsetAngle, ANGLE_360_ZERO_DEFAULT_BOUNDS);
            }
        }

        annotation { "Name" : "Helical" }
        definition.helical is boolean;

        if (definition.helical)
        {
            annotation { "Group Name" : "Helical", "Collapsed By Default" : false, "Driving Parameter" : "helical" }
            {
                annotation { "Name" : "Angle" }
                isAngle(definition.helixAngle, HELIX_ANGLE_BOUNDS);

                annotation { "Name" : "Handedness" }
                definition.handedness is HelixDirection;

                annotation { "Name" : "Double helix" }
                definition.double is boolean;
            }
        }

        annotation { "Name" : "Move origin" }
        definition.centerPoint is boolean;

        if (definition.centerPoint)
        {
            annotation { "Group Name" : "Center point", "Collapsed By Default" : false, "Driving Parameter" : "centerPoint" }
            {
                annotation { "Name" : "Sketch vertex or mate connector", "Filter" : (EntityType.VERTEX && SketchObject.YES) || BodyType.MATE_CONNECTOR, "MaxNumberOfPicks" : 1 }
                definition.center is Query;
            }
        }

        annotation { "Name" : "Depth" }
        isLength(definition.gearDepth, BLEND_BOUNDS);

        annotation { "Name" : "Depth direction", "UIHint" : "OPPOSITE_DIRECTION" }
        definition.flipGear is boolean;
    }

    {
        // diameters in gear definition
        var offsetDiameter = 0 * meter;
        var offsetClearance = 0 * meter;
        var offsetAngle = 0 * degree;
        var backlash = 0 * meter;
        var dedendumFactor = 1.25;

        if (definition.offset)
        {
            offsetDiameter = definition.offsetDiameter;
            offsetClearance = definition.offsetClearance;
            offsetAngle = definition.offsetAngle;
            backlash = definition.backlash;

            if (definition.dedendumFactor == DedendumFactor.d157)
                dedendumFactor = 1.157;

            if (definition.dedendumFactor == DedendumFactor.d200)
                dedendumFactor = 1.2;
        }

        if (definition.centerHole && definition.centerHoleDia >= definition.pitchCircleDiameter - 4 * definition.module)
        {
            throw regenError("Center hole diameter must be less than the root diameter", ["centerHoleDia"]);
        }

        if (definition.key && definition.keyHeight / 2 + definition.centerHoleDia >= definition.pitchCircleDiameter - 4 * definition.module)
        {
            throw regenError("Center hole diameter plus Key height must be less than the root diameter", ["keyHeight"]);
        }

        const addendum = definition.module + offsetDiameter;
        const dedendum = dedendumFactor * definition.module + offsetClearance;
        const base = definition.pitchCircleDiameter * cos(definition.pressureAngle);

        // angle between root of teeth
        const alpha = sqrt(definition.pitchCircleDiameter ^ 2 - base ^ 2) / base * radian - definition.pressureAngle;
        const beta = 360 / (4 * definition.numTeeth) * degree - alpha;

        // if no center vertex selected build gear on the front plane at the origin
        var location = vector(0, 0, 0) * meter;
        var sketchPlane = plane(location, vector(0, -1, 0), vector(1, 0, 0));

        // else find location of selected vertex and its sketch plane or use mate connector to create a new sketch for the gear profile
        if (definition.centerPoint)
        {
            try silent
            {
                sketchPlane = evPlane(context, { "face" : definition.center });
                location = sketchPlane.origin;
            }
            catch
            {
                sketchPlane = evOwnerSketchPlane(context, { "entity" : definition.center });
                location = evVertexPoint(context, { "vertex" : definition.center });
            }
        }

        const gearSketch = newSketchOnPlane(context, id + "gearSketch", { "sketchPlane" : sketchPlane });
        const center = worldToPlane(sketchPlane, location);

        // create the outer diameter circle
        const outerRadius = definition.pitchCircleDiameter / 2 + addendum;
        const innerRadius = definition.pitchCircleDiameter / 2 - dedendum;
        skCircle(gearSketch, "addendum", { "center" : center, "radius" : outerRadius });


        if (definition.centerHole)
        {

            if (definition.key)
            {
                var keyVector = vector(0, 1);
                var perpKeyVector = vector(-1, 0);
                var keyHeight = (definition.keyHeight + definition.centerHoleDia) / 2;

                var points = [
                    center - (definition.keyWidth / 2) * perpKeyVector,
                    center - (definition.keyWidth / 2) * perpKeyVector + keyHeight * keyVector,
                    center + (definition.keyWidth / 2) * perpKeyVector + keyHeight * keyVector,
                    center + (definition.keyWidth / 2) * perpKeyVector];

                for (var i = 0; i < size(points); i += 1)
                {
                    skLineSegment(gearSketch, "line" ~ i, { "start" : points[i], "end" : points[(i + 1) % size(points)] });
                }
            }

            // center hole circle sketch
            skCircle(gearSketch, "Center", {
                        "center" : center,
                        "radius" : definition.centerHoleDia / 2 });
        }
        skSolve(gearSketch);

        opExtrude(context, id + "extrude1", {
                    "entities" : qSketchRegion(id + "gearSketch", true),
                    "direction" : sketchPlane.normal * (definition.flipGear ? -1 : 1),
                    "endBound" : BoundingType.BLIND,
                    "endDepth" : definition.gearDepth });

        if (definition.chamfer)
        {
            definition.entities = qLargest(qCreatedBy(id + "extrude1", EntityType.EDGE));
            opChamfer(context, id + "chamfer1", definition);
        }

        const toothSketch = newSketchOnPlane(context, id + "toothSketch", { "sketchPlane" : sketchPlane });

        // build involute splines for each tooth
        var involute1 = [];
        var involute2 = [];

        for (var t = 0; t <= 2; t += (1 / 50)) // (1/50) is the involute spline tolerance
        {
            // involute definition math
            var angle = (t + (backlash / cos(definition.pressureAngle)) / definition.pitchCircleDiameter / 2) * radian;
            var offset = beta + offsetAngle;
            var ca = cos(angle + offset);
            var sa = sin(angle + offset);
            var cab = cos(offset - beta * 2 - angle);
            var sab = sin(offset - beta * 2 - angle);
            var point1;
            var point2;

            if (base >= definition.pitchCircleDiameter - 2 * dedendum && t == 0) // special case when base cylinder diameter is greater than dedendum
            {
                // calculate involute spline point
                point1 = vector((definition.pitchCircleDiameter / 2 - dedendum) * ca, (definition.pitchCircleDiameter / 2 - dedendum) * sa);
                point2 = vector((definition.pitchCircleDiameter / 2 - dedendum) * cab, (definition.pitchCircleDiameter / 2 - dedendum) * sab);
            }
            else
            {
                point1 = vector(base * 0.5 * (ca + t * sa), base * 0.5 * (sa - t * ca));
                point2 = vector(base * 0.5 * (cab - t * sab), base * 0.5 * (sab + t * cab));
            }

            // and add to array
            involute1 = append(involute1, point1 + center);
            involute2 = append(involute2, point2 + center);

            // if involute points go outside the outer diameter of the gear then stop
            if (sqrt(point1[0] ^ 2 + point1[1] ^ 2) >= (definition.pitchCircleDiameter / 2 + addendum))
                break;
        }

        // create involute sketch splines
        skFitSpline(toothSketch, "spline1", { "points" : involute1 });
        skFitSpline(toothSketch, "spline2", { "points" : involute2 });

        const regionPoint = center + vector((definition.pitchCircleDiameter / 2 - dedendum + 0.1 * millimeter) * cos(offsetAngle), (definition.pitchCircleDiameter / 2 - dedendum + 0.1 * millimeter) * sin(offsetAngle));

        skCircle(toothSketch, "addendum", { "center" : center, "radius" : outerRadius });
        skCircle(toothSketch, "dedendum", { "center" : center, "radius" : innerRadius });
        skCircle(toothSketch, "fillet", { "center" : regionPoint, "radius" : 0.1 * millimeter, "construction" : true });

        skConstraint(toothSketch, "fix1", { "constraintType" : ConstraintType.FIX, "localFirst" : "dedendum" });
        skConstraint(toothSketch, "fix2", { "constraintType" : ConstraintType.FIX, "localFirst" : "spline1" });
        skConstraint(toothSketch, "fix3", { "constraintType" : ConstraintType.FIX, "localFirst" : "spline2" });
        skConstraint(toothSketch, "tangent1", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "fillet", "localSecond" : "dedendum" });
        skConstraint(toothSketch, "tangent2", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "fillet", "localSecond" : "spline1" });
        skConstraint(toothSketch, "tangent3", { "constraintType" : ConstraintType.TANGENT, "localFirst" : "fillet", "localSecond" : "spline2" });

        skSolve(toothSketch);

        opExtrude(context, id + "tooth", {
                    "entities" : qContainsPoint(qCreatedBy(id + "toothSketch", EntityType.FACE), planeToWorld(sketchPlane, regionPoint)),
                    "direction" : sketchPlane.normal * (definition.flipGear ? -1 : 1),
                    "endBound" : BoundingType.BLIND,
                    "endDepth" : definition.gearDepth });

        const filletEdges = qClosestTo(qNonCapEntity(id + "tooth", EntityType.EDGE), location);

        var rootFilletRadius = evCurveDefinition(context, { "edge" : sketchEntityQuery(id + "toothSketch", EntityType.EDGE, "fillet") }).radius;

        if (definition.rootFillet == RootFilletType.none)
            rootFilletRadius = 0;

        if (definition.rootFillet == RootFilletType.third)
            rootFilletRadius /= 1.5;

        if (definition.rootFillet == RootFilletType.quarter)
            rootFilletRadius /= 2;

        if (rootFilletRadius > 0)
        {
            opFillet(context, id + "fillet", { "entities" : filletEdges, "radius" : rootFilletRadius });
        }

        if (definition.helical)
        {
            var profileFace = qCapEntity(id + "tooth", CapType.START, EntityType.FACE);
            var helicalPitch = (PI * definition.pitchCircleDiameter) / tan(definition.helixAngle);
            var clockwise = definition.handedness == HelixDirection.CW;

            if (definition.double)
                clockwise = !clockwise;

            if (definition.flipGear && definition.double)
                clockwise = !clockwise;

            opHelix(context, id + "helix", {
                        "direction" : sketchPlane.normal * (definition.flipGear ? -1 : 1),
                        "axisStart" : location,
                        "startPoint" : location + sketchPlane.x * definition.pitchCircleDiameter / 2,
                        "interval" : [0, definition.gearDepth / helicalPitch / (definition.double ? 2 : 1)],
                        "clockwise" : clockwise,
                        "helicalPitch" : helicalPitch,
                        "spiralPitch" : 0 * meter });

            opSweep(context, id + "toothHelix", {
                        "profiles" : profileFace,
                        "path" : qCreatedBy(id + "helix", EntityType.EDGE) });

            opDeleteBodies(context, id + "deleteTooth", {
                        "entities" : qUnion([qCreatedBy(id + "tooth"), qCreatedBy(id + "helix")]) });

            if (definition.double)
            {
                opPattern(context, id + "mirror", {
                            "entities" : qCreatedBy(id + "toothHelix", EntityType.BODY),
                            "transforms" : [mirrorAcross(evPlane(context, { "face" : qCapEntity(id + "toothHelix", CapType.END, EntityType.FACE) }))],
                            "instanceNames" : ["1"] });

                opBoolean(context, id + "double", {
                            "tools" : qUnion([qCreatedBy(id + "toothHelix", EntityType.BODY), qCreatedBy(id + "mirror", EntityType.BODY)]),
                            "operationType" : BooleanOperationType.UNION });
            }
        }

        var tools = qUnion([qCreatedBy(id + "tooth", EntityType.BODY), qCreatedBy(id + "toothHelix", EntityType.BODY)]);
        var transforms = [];
        var instanceNames = [];

        for (var i = 1; i < definition.numTeeth; i += 1)
        {
            var instanceTransform = rotationAround(line(location, sketchPlane.normal), i * (360 / definition.numTeeth) * degree);
            transforms = append(transforms, instanceTransform);
            instanceNames = append(instanceNames, "" ~ i);
        }

        opPattern(context, id + "pattern", {
                    "entities" : tools,
                    "transforms" : transforms,
                    "instanceNames" : instanceNames });

        opBoolean(context, id + "hobbed", {
                    "tools" : qUnion([tools, qCreatedBy(id + "pattern", EntityType.BODY)]),
                    "targets" : qCreatedBy(id + "extrude1", EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });

        // Remove sketch entities - no longer required
        opDeleteBodies(context, id + "delete", {
                    "entities" : qUnion([qCreatedBy(id + "gearSketch"), qCreatedBy(id + "toothSketch")]) });

        // created PCD sketch
        const PCDSketch = newSketchOnPlane(context, id + "PCDsketch", { "sketchPlane" : sketchPlane });

        skCircle(PCDSketch, "PCD", {
                    "center" : center,
                    "radius" : definition.pitchCircleDiameter / 2,
                    "construction" : true });

        skSolve(PCDSketch);

        var attribute = makeGearAttribute(definition, outerRadius * 2, innerRadius * 2);

        setAttribute(context, { "entities" : qBodyType(qCreatedBy(id, EntityType.BODY), BodyType.SOLID), "attribute" : attribute });

        setFeatureComputedParameter(context, id, { "name" : "teeth", "value" : definition.numTeeth });
    });

export function editGearLogic(context is Context, id is Id, oldDefinition is map, definition is map, isCreating is boolean, specifiedParameters is map, hiddenBodies is Query) returns map
{
    // isCreating is required in the function definition for edit logic to work when editing an existing feature
    if (oldDefinition.numTeeth != definition.numTeeth)
    {
        definition.module = definition.pitchCircleDiameter / definition.numTeeth;
        definition.circularPitch = definition.module * PI;
        definition.diametralPitch = 1 * inch / definition.module;
        return definition;
    }

    if (oldDefinition.circularPitch != definition.circularPitch)
    {
        definition.module = definition.circularPitch / PI;
        definition.pitchCircleDiameter = (definition.circularPitch * definition.numTeeth) / PI;
        definition.diametralPitch = 1 * inch / definition.module;
        return definition;
    }

    if (oldDefinition.pitchCircleDiameter != definition.pitchCircleDiameter)
    {
        definition.module = definition.pitchCircleDiameter / definition.numTeeth;
        definition.circularPitch = (PI * definition.pitchCircleDiameter) / definition.numTeeth;
        definition.diametralPitch = 1 * inch / definition.module;
        return definition;
    }

    if (oldDefinition.module != definition.module)
    {
        definition.circularPitch = definition.module * PI;
        definition.pitchCircleDiameter = definition.numTeeth * definition.module;
        definition.diametralPitch = 1 * inch / definition.module;
        return definition;
    }

    if (oldDefinition.diametralPitch != definition.diametralPitch)
    {
        definition.circularPitch = PI / (definition.diametralPitch / inch);
        definition.module = definition.circularPitch / PI;
        definition.pitchCircleDiameter = (definition.circularPitch * definition.numTeeth) / PI;
        return definition;
    }

    return definition;
}

const TEETH_BOUNDS =
{
            (unitless) : [4, 25, 1000]
        } as IntegerBoundSpec;

const PRESSURE_ANGLE_BOUNDS =
{
            (degree) : [12, 20, 35]
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

export enum GearInputType
{
    annotation { "Name" : "Module" }
    module,
    annotation { "Name" : "Diametral pitch" }
    diametralPitch,
    annotation { "Name" : "Circular pitch" }
    circularPitch
}

export enum RootFilletType
{
    annotation { "Name" : "None" }
    none,
    annotation { "Name" : "1/4" }
    quarter,
    annotation { "Name" : "1/3" }
    third,
    annotation { "Name" : "Full" }
    full
}

export enum DedendumFactor
{
    annotation { "Name" : "1.157 x addendum" }
    d157,
    annotation { "Name" : "1.20 x addendum" }
    d200,
    annotation { "Name" : "1.25 x addendum" }
    d250
}

export enum GearChamferType
{
    annotation { "Name" : "Equal distance" }
    EQUAL_OFFSETS,
    annotation { "Name" : "Two distances" }
    TWO_OFFSETS,
    annotation { "Name" : "Distance and angle" }
    OFFSET_ANGLE,
    annotation { "Hidden" : true }
    RAW_OFFSET
}

export enum HelixDirection
{
    annotation { "Name" : "Clockwise" }
    CW,
    annotation { "Name" : "Counterclockwise" }
    CCW
}

export type GearAttribute typecheck canBeGearAttribute;

export predicate canBeGearAttribute(value)
{
    value is map;
}

function makeGearAttribute(definition is map, outerDiameter is ValueWithUnits, innerDiameter is ValueWithUnits) returns GearAttribute
{
    return {
        "outerDiameter" : outerDiameter,
        "innerDiameter" : innerDiameter,
        "pitchCircleDiameter" : definition.pitchCircleDiameter,
        "numTeeth" : definition.numTeeth,
        "pressureAngle" : definition.pressureAngle,
    } as GearAttribute; // TODO: center hole, chamfer, helical
}

annotation { "Table Type Name" : "Gears", "Icon" : icon::BLOB_DATA }
export const spurGearsTable = defineTable(function(context is Context, definition is map) returns Table
    precondition
    {
        // Define the parameters of the table type
    }
    {
        var columnDefinitions = [
            tableColumnDefinition("quantity", "Qty."),
            tableColumnDefinition("numTeeth", "Teeth"),
            tableColumnDefinition("pitchCircleDiameter", "Pitch diameter"),
            tableColumnDefinition("outerDiameter", "OD"),
            tableColumnDefinition("innerDiameter", "Inner teeth diameter"),
            tableColumnDefinition("pressureAngle", "Pressure angle"),
        ];

        // Group by same values
        var uniqueGears = {};
        var partsWithGearAttributes = qAttributeQuery({} as GearAttribute);
        for (var part in evaluateQuery(context, partsWithGearAttributes))
        {
            const gearAttributes = getAttributes(context, {
                    "entities" : part,
                    "attributePattern" : {} as GearAttribute
            });
            if (gearAttributes == [])
            {
                continue;
            }
            const attribute = gearAttributes[0];
            // TODO: use tolerant comparision, only considering relevant inputs
            if (uniqueGears[attribute] == undefined)
            {
                uniqueGears[attribute] = [ part ];
                continue;
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
