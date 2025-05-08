/*
    Spur Gear

    This custom feature creates mathematically correct
    spur gears with optional center bore hole and keyway.

    Version 1 - May 22, 2016 - Neil Cooke, Onshape Inc.
*/

FeatureScript 336;
import(path : "onshape/std/geometry.fs", version : "336.0");

annotation { "Feature Type Name" : "Spur Gear", "Feature Name Template" : "Spur Gear (#teeth teeth)", "Filter Selector" : "fs", "Editing Logic Function" : "editGearLogic" }
export const SpurGear = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        // this hidden field is used to name the feature in the "Feature Name Template"
        // the value for "teeth" is calculated and set in the "Editing Logic Function"
        annotation { "Name" : "teeth", "UIHint" : "ALWAYS_HIDDEN" }
        definition.teeth is string; //used to name the feature only

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

        annotation { "Name" : "Center hole" }
        definition.centerHole is boolean;

        if (definition.centerHole)
        {
            annotation { "Name" : "Hole diameter" }
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

        annotation { "Name" : "Select origin position" }
        definition.centerPoint is boolean;

        if (definition.centerPoint)
        {
            annotation { "Name" : "Sketch vertex for center", "Filter" : EntityType.VERTEX && SketchObject.YES, "MaxNumberOfPicks" : 1 }
            definition.center is Query;
        }

        annotation { "Name" : "Extrude depth" }
        isLength(definition.gearDepth, BLEND_BOUNDS);

        annotation { "Name" : "Extrude direction", "UIHint" : "OPPOSITE_DIRECTION" }
        definition.flipGear is boolean;

        annotation { "Name" : "Offset" }
        definition.offset is boolean;

        if (definition.offset)
        {
            annotation { "Name" : "Root diameter" }
            isLength(definition.offsetClearance, ZERO_DEFAULT_LENGTH_BOUNDS);

            annotation { "Name" : "Outside diameter" }
            isLength(definition.offsetDiameter, ZERO_DEFAULT_LENGTH_BOUNDS);

            annotation { "Name" : "Tooth angle" }
            isAngle(definition.offsetAngle, ANGLE_360_ZERO_DEFAULT_BOUNDS);
        }
    }

    {
        // diameters in gear definition
        var offsetDiameter = 0 * meter;
        var offsetClearance = 0 * meter;
        var offsetAngle = 0 * degree;

        if (definition.offset)
        {
            offsetDiameter = definition.offsetDiameter;
            offsetClearance = definition.offsetClearance;
            offsetAngle = definition.offsetAngle;
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
        const dedendum = 1.25 * definition.module + offsetClearance;
        const base = definition.pitchCircleDiameter * cos(definition.pressureAngle);

        // angle between root of teeth
        const alpha = sqrt(definition.pitchCircleDiameter ^ 2 - base ^ 2) / base * radian - definition.pressureAngle;
        const beta = 360 / (4 * definition.numTeeth) * degree - alpha;

        // if no center vertex selected build gear on the front plane at the origin
        var location = vector(0, 0, 0) * meter;
        var sketchPlane = plane(location, vector(0, -1, 0), vector(1, 0, 0));
        var center3D = location;

        // else find location of selected vertex and its sketch plane and create a new sketch for the gear profile
        if (definition.centerPoint)
        {
            location = evaluateQuery(context, definition.center)[0];
            sketchPlane = evOwnerSketchPlane(context, { "entity" : location });
            center3D = evVertexPoint(context, { "vertex" : location });
        }

        const gearSketch = newSketchOnPlane(context, id + "gearSketch", { "sketchPlane" : sketchPlane });
        const center2D = worldToPlane(sketchPlane, center3D);

        // create the outer diameter circle
        skCircle(gearSketch, "addendum", {
                    "center" : center2D,
                    "radius" : definition.pitchCircleDiameter / 2 + addendum
                });

        var nameId = 1;
        var filletEdges = [];
        var regionPoint;

        // build involute splines for each tooth
        for (var teeth = 0; teeth < definition.numTeeth; teeth += 1)
        {
            var involute1 = [];
            var involute2 = [];
            var arcDone = false;

            for (var t = 0; t <= 2; t += (1 / 20)) // (1/20) is the involute spline tolerance
            {
                // involute definition math
                var angle = t * radian;
                var offset = ((360 / definition.numTeeth) * PI * teeth) / 180 * radian + beta + offsetAngle;
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
                involute1 = append(involute1, point1 + center2D);
                involute2 = append(involute2, point2 + center2D);

                if (!arcDone) // create base arc between involutes once per tooth
                {
                    var mid = getArcMidPoint(center2D, point2 + center2D, point1 + center2D); // sketch arc is arc 3 points so need addtional point on arc

                    if (mid != undefined) // if no base cylinder present (due to pressure angle), don't draw it
                    {
                        skArc(gearSketch, "arc" ~ nameId, {
                                    "start" : point2 + center2D,
                                    "mid" : mid,
                                    "end" : point1 + center2D
                                });
                    }

                    // find points in 3D space where edges need to be filleted later
                    filletEdges = append(filletEdges, toWorldVector(planeToCSys(sketchPlane), point2 + center2D, definition.gearDepth, definition.flipGear));
                    filletEdges = append(filletEdges, toWorldVector(planeToCSys(sketchPlane), point1 + center2D, definition.gearDepth, definition.flipGear));

                    // find area to extrude
                    regionPoint = vector(point1[0] * 0.95 + center2D[0], point1[1] * 0.95 + center2D[1], 0 * meter);
                    arcDone = true;
                }

                // if involute points go outside the outer diameter of the gear then stop
                if (sqrt(point1[0] ^ 2 + point1[1] ^ 2) >= (definition.pitchCircleDiameter / 2 + addendum))
                    break;
            }

            // create involute sketch splines
            skFitSpline(gearSketch, "spline-a" ~ nameId, {
                        "points" : involute1
                    });
            skFitSpline(gearSketch, "spline-b" ~ nameId, {
                        "points" : involute2
                    });

            // increment name ID to ensure unique IDs for each sketch entity
            nameId += 1;
        }

        if (definition.centerHole)
        {
            if (definition.key)
            {
                var keyVector = vector(0, 1);
                var perpKeyVector = vector(-1, 0);
                var keyHeight = (definition.keyHeight + definition.centerHoleDia) / 2;

                var points = [
                    center2D - (definition.keyWidth / 2) * perpKeyVector,
                    center2D - (definition.keyWidth / 2) * perpKeyVector + keyHeight * keyVector,
                    center2D + (definition.keyWidth / 2) * perpKeyVector + keyHeight * keyVector,
                    center2D + (definition.keyWidth / 2) * perpKeyVector];

                for (var i = 0; i < size(points); i += 1)
                {
                    skLineSegment(gearSketch, "line" ~ nameId,
                            { "start" : points[i],
                                "end" : points[(i + 1) % size(points)]
                            });
                    nameId += 1;
                }
            }

            // center hole circle sketch
            skCircle(gearSketch, "Center", {
                        "center" : center2D,
                        "radius" : definition.centerHoleDia / 2
                    });
        }
        skSolve(gearSketch);

        extrude(context, id + "extrude1", {
                    "entities" : qContainsPoint(qCreatedBy(id + "gearSketch", EntityType.FACE), toWorld(planeToCSys(sketchPlane), regionPoint)),
                    "endBound" : BoundingType.BLIND,
                    "depth" : definition.gearDepth,
                    "oppositeDirection" : definition.flipGear
                });

        var filletEdges3D = [];

        for (var i = 0; i < size(filletEdges); i += 1)
        {
            // Find the edges that intersect the points previously collected
            filletEdges3D = append(filletEdges3D, qContainsPoint(qCreatedBy(id + "extrude1", EntityType.EDGE), filletEdges[i]));
        }

        const filletRadius = norm(filletEdges[1] - filletEdges[0]) / 3; // arbitrary fillet size = one third the distance between the edges

        if (filletRadius >= 0.2 * millimeter) // arbitrary small size assuming tooling cannot hold a fillet radius smaller than this
        {
            try(opFillet(context, id + "fillet1", {
                            "entities" : qUnion(filletEdges3D),
                            "radius" : filletRadius
                        }));
        }

        // Remove sketch entities - no longer required
        opDeleteBodies(context, id + "delete", { "entities" : qCreatedBy(id + "gearSketch") });

        // created PCD sketch
        const PCDSketch = newSketchOnPlane(context, id + "PCDsketch", { "sketchPlane" : sketchPlane });
        skCircle(PCDSketch, "PCD", {
                    "center" : center2D,
                    "radius" : definition.pitchCircleDiameter / 2,
                    "construction" : true
                });
        skSolve(PCDSketch);

    }, {});

function getArcMidPoint(center is Vector, start is Vector, end is Vector)
{
    // need to convert 2D vectors back to 3D for vector angle calculation
    const center3D = vector(center[0], center[1], 0 * meter);
    const start3D = vector(start[0], start[1], 0 * meter);
    const end3D = vector(end[0], end[1], 0 * meter);

    const angle = vectorAngle(center3D - start3D, center3D - end3D) / 2;
    // if angle is less than zero then arc was flipped
    if (angle <= 0 * radian)
        return;
    start = center - start;

    var ca = cos(angle); // in radians
    var sa = sin(angle);
    return center - vector(ca * start[0] - sa * start[1], sa * start[0] + ca * start[1]);
}

function vectorAngle(vector1 is Vector, vector2 is Vector)
{
    // function assumes vectors are on a 2D plane so Z is always zero and the normal vector is always [0, 0, 1]
    return atan2(dot(vector(0, 0, 1), cross(vector1, vector2)), dot(vector1, vector2));
}

function toWorldVector(csys is CoordSystem, point is Vector, depth is map, direction is boolean) returns Vector
{
    var dir = direction ? -1 : 1;
    var vector3D = vector(point[0], point[1], dir * depth / 2);
    return toWorld(csys, vector3D);
}

export function editGearLogic(context is Context, id is Id, oldDefinition is map, definition is map, isCreating is boolean, specifiedParameters is map, hiddenBodies is Query) returns map
{
    // isCreating is required in the function definition for edit logic to work when editing an existing feature
    if (oldDefinition.numTeeth != definition.numTeeth)
    {
        definition.module = definition.pitchCircleDiameter / definition.numTeeth;
        definition.circularPitch = definition.module * PI;
        definition.diametralPitch = 1 * inch / definition.module;
        definition.teeth = toString(definition.numTeeth); //to name the feature
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
            "min" : 4,
            "max" : 250,
            (unitless) : [4, 25, 250]
        } as IntegerBoundSpec;

const PRESSURE_ANGLE_BOUNDS =
{
            "min" : 12 * degree,
            "max" : 35 * degree,
            (degree) : [12, 20, 35]
        } as AngleBoundSpec;

const MODULE_BOUNDS =
{
            "min" : -TOLERANCE.zeroLength * meter,
            "max" : 500 * meter,
            (meter) : [1e-5, 0.001, 500],
            (centimeter) : 0.1,
            (millimeter) : 1.0,
            (inch) : 0.04
        } as LengthBoundSpec;

const CENTERHOLE_BOUNDS =
{
            "min" : -TOLERANCE.zeroLength * meter,
            "max" : 500 * meter,
            (meter) : [1e-5, 0.01, 500],
            (centimeter) : 1.0,
            (millimeter) : 10.0,
            (inch) : 0.375
        } as LengthBoundSpec;

const KEY_BOUNDS =
{
            "min" : -TOLERANCE.zeroLength * meter,
            "max" : 500 * meter,
            (meter) : [1e-5, 0.003, 500],
            (centimeter) : 0.3,
            (millimeter) : 3.0,
            (inch) : 0.125
        } as LengthBoundSpec;

export enum GearInputType
{
    annotation { "Name" : "Module" }
    module,
    annotation { "Name" : "Diametral pitch" }
    diametralPitch,
    annotation { "Name" : "Circular pitch" }
    circularPitch
}
