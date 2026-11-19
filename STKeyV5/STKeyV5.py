"""Build the STKey v5 Craftsman snowthrower key in a new Fusion design."""

import math
import re
import traceback

import adsk.core
import adsk.fusion


PARAMETERS = (
    ('stem_length', '34 mm', 'Insertion blade length'),
    ('stem_width', '9.5 mm', 'Insertion blade width'),
    ('stem_thickness', '4.1 mm', 'Stem rail thickness'),
    ('stem_edge_rim', '1.4 mm', 'Outer rail width and pocket depth'),
    ('stem_internal_width', 'stem_width - 2 * stem_edge_rim', 'Recessed web width'),
    ('stem_internal_thickness', 'stem_thickness - 2 * stem_edge_rim', 'Recessed web thickness'),
    ('stem_cutout_start', '22 mm', 'Locking window start from guard datum'),
    ('stem_cutout_size', '6 mm', 'Square locking window side'),
    ('stem_tip_diamond_len', '5.5 mm', 'Tip reinforcement length'),
    ('stem_tip_diamond_thk', '2.6 mm', 'Tip reinforcement thickness'),
    ('stem_notch_start', '14 mm', 'Detent ramp start from guard datum'),
    ('stem_notch_depth', '1 mm', 'Detent ramp rise above web floor'),
    ('stem_notch_span', '4 mm', 'Curved detent ramp length'),
    ('stem_notch_taper', '4 mm', 'Linear detent return length'),
    ('stem_chamfer', '0.5 mm', 'Radius of the tip corner fillets'),
    ('guard_length', '3 mm', 'Stop collar axial thickness'),
    ('guard_width', '18 mm', 'Stop collar width'),
    ('guard_height', '11 mm', 'Stop collar height'),
    ('guard_corner_rad', '1.5 mm', 'Stop collar corner radius'),
    ('handle_length', '24 mm', 'Grip length'),
    ('handle_width', '27 mm', 'Rear grip width'),
    ('handle_neck_width', '12 mm', 'Front grip width'),
    ('handle_height', '17 mm', 'Rear grip thickness'),
    ('handle_min_height', '9.5 mm', 'Front grip thickness'),
    ('handle_pocket_depth', '2 mm', 'Pocket floor offset from maximum half-height'),
    ('lanyard_hole_dia', '4.5 mm', 'Lanyard hole diameter'),
)

F = adsk.fusion
C = adsk.core
POINT = C.Point3D.create
VALUE = C.ValueInput.createByString
NEW_BODY = F.FeatureOperations.NewBodyFeatureOperation
CUT = F.FeatureOperations.CutFeatureOperation
TOL = 0.01  # cm, for solid edge selection


def collection(items):
    result = C.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Model:
    def __init__(self, design):
        self.design = design

    def length(self, expression):
        # Resolve named parameters for numeric seed geometry. Keep the original
        # expressions for the driving dimensions and feature extents.
        def substitute(match):
            token = match.group()
            parameter = self.design.userParameters.itemByName(token)
            return f'({parameter.value:.15g} cm)' if parameter else token

        numeric = re.sub(r'\b[A-Za-z_][A-Za-z_0-9]*\b', substitute, expression)
        units = self.design.unitsManager
        require(units.isValidExpression(numeric, 'mm'),
                f'Invalid seed expression: {expression} ({numeric})')
        return units.evaluateExpression(numeric, 'mm')

    def component(self, name):
        occurrence = self.design.rootComponent.occurrences.addNewComponent(C.Matrix3D.create())
        occurrence.component.name = name
        return occurrence.component

    def sketch(self, component, plane, name):
        sketch = component.sketches.add(plane)
        sketch.name = name
        return sketch

    def vertex(self, sketch, u, v, axes, offset=0):
        # Map the requested model axes into Fusion's actual sketch orientation.
        xyz = [0.0, 0.0, 0.0]
        xyz[axes[0]] = self.length(u)
        xyz[axes[1]] = self.length(v)
        xyz[3 - sum(axes)] = offset
        point = sketch.modelToSketchSpace(POINT(*xyz))
        lengths = (u, v)
        basis = []
        for axis in axes:
            direction = [0.0, 0.0, 0.0]
            direction[axis] = 1.0
            tip = sketch.modelToSketchSpace(POINT(*direction))
            origin = sketch.modelToSketchSpace(POINT(0, 0, 0))
            basis.append((tip.x - origin.x, tip.y - origin.y))
        expressions = tuple(
            lengths[0] if abs(basis[0][index]) > 0.5 else lengths[1]
            for index in range(2)
        )
        return POINT(point.x, point.y, 0), expressions

    def constrain_vertex(self, sketch, vertex, point, expressions):
        origin = sketch.originPoint
        gx = sketch.geometricConstraints
        dims = sketch.sketchDimensions
        orientations = F.DimensionOrientations
        for coordinate, expression, alignment, orientation, label in (
            (point.x, expressions[0], gx.addVerticalPoints,
             orientations.HorizontalDimensionOrientation, POINT(point.x / 2, point.y + 0.25, 0)),
            (point.y, expressions[1], gx.addHorizontalPoints,
             orientations.VerticalDimensionOrientation, POINT(point.x + 0.25, point.y / 2, 0)),
        ):
            if abs(coordinate) < 1e-8:
                alignment(origin, vertex)
            else:
                signed_expression = expression if self.length(expression) > 0 else f'-({expression})'
                first, second = (origin, vertex) if coordinate > 0 else (vertex, origin)
                try:
                    dimension = dims.addDistanceDimension(first, second, orientation, label)
                    dimension.parameter.expression = signed_expression
                except RuntimeError as exc:
                    raise RuntimeError(
                        f'{sketch.name}: could not constrain point ({point.x:g}, {point.y:g}) cm '
                        f'with {signed_expression!r} ({orientation}).'
                    ) from exc

    def loop(self, sketch, coordinates, axes=(0, 1), offset=0, arc=None):
        vertices = [self.vertex(sketch, u, v, axes, offset) for u, v in coordinates]
        # Dimension independent vertices before connecting them with curves.
        points = []
        for point, expressions in vertices:
            vertex = sketch.sketchPoints.add(point)
            self.constrain_vertex(sketch, vertex, point, expressions)
            points.append(vertex)
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            if arc is not None and index == arc[0]:
                midpoint, _ = self.vertex(sketch, arc[1], arc[2], axes, offset)
                curve = sketch.sketchCurves.sketchArcs.addByThreePoints(start, midpoint, end)
            else:
                sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
        if arc is not None:
            text_point = POINT(midpoint.x + 0.3, midpoint.y + 0.3, 0)
            dimension = sketch.sketchDimensions.addRadialDimension(curve, text_point)
            dimension.parameter.expression = arc[3]

    def rectangle(self, sketch, left, right, half_width, axes=(0, 1)):
        self.loop(sketch, [
            (left, f'-({half_width})'), (right, f'-({half_width})'),
            (right, half_width), (left, half_width),
        ], axes)

    def trapezoid(self, sketch, front, rear, front_half, rear_half, axes=(0, 1), offset=0):
        self.loop(sketch, [
            (front, front_half), (rear, rear_half),
            (rear, f'-({rear_half})'), (front, f'-({front_half})'),
        ], axes, offset)

    def profile(self, sketch, loops=1):
        matches = [profile for profile in sketch.profiles if profile.profileLoops.count == loops]
        require(len(matches) == 1, f'{sketch.name}: expected one profile with {loops} loop(s).')
        return matches[0]

    def extrude(self, component, sketch, name, distance, operation, loops=1, direction=None):
        features = component.features.extrudeFeatures
        setup = features.createInput(self.profile(sketch, loops), operation)
        if direction is None:
            require(setup.setSymmetricExtent(VALUE(distance), True), f'{name}: invalid symmetric extent.')
        else:
            extent = F.DistanceExtentDefinition.create(VALUE(distance))
            require(setup.setOneSideExtent(extent, direction), f'{name}: invalid one-side extent.')
        if operation == CUT:
            setup.participantBodies = [component.bRepBodies.item(0)]
        feature = features.add(setup)
        require(feature, f'{name}: extrusion failed.')
        feature.name = name
        return feature

    def direction(self, sketch, axis, sign):
        origin = sketch.sketchToModelSpace(POINT(0, 0, 0)).asArray()
        normal_point = sketch.sketchToModelSpace(POINT(0, 0, 1)).asArray()
        if (normal_point[axis] - origin[axis]) * sign > 0:
            return F.ExtentDirections.PositiveExtentDirection
        return F.ExtentDirections.NegativeExtentDirection

    def fillet(self, component, name, radius, select_edge, expected):
        body = component.bRepBodies.item(0)
        edges = [edge for edge in body.edges if select_edge(edge.boundingBox)]
        require(len(edges) == expected, f'{name}: expected {expected} edges, found {len(edges)}.')
        features = component.features.filletFeatures
        setup = features.createInput()
        setup.edgeSetInputs.addConstantRadiusEdgeSet(collection(edges), VALUE(radius), False)
        feature = features.add(setup)
        require(feature, f'{name}: fillet failed.')
        feature.name = name

    def vertical_corners(self, component, name, radius, x, half_width):
        def matches(box):
            lo, hi = box.minPoint, box.maxPoint
            return (
                abs(lo.x - x) < TOL and abs(hi.x - x) < TOL
                and abs(hi.y - lo.y) < TOL and abs(abs(lo.y) - half_width) < TOL
                and hi.z - lo.z > TOL
            )
        self.fillet(component, name, radius, matches, 2)

    def stem(self):
        component = self.component('STEM')
        outline = self.sketch(component, component.xYConstructionPlane, 'StemSize')
        self.rectangle(outline, '0 mm', 'stem_length', 'stem_width / 2')
        self.rectangle(outline, 'stem_cutout_start', 'stem_cutout_start + stem_cutout_size',
                       'stem_cutout_size / 2')
        self.extrude(component, outline, 'Stem blank and retention window',
                     'stem_thickness', NEW_BODY, loops=2)

        recess = self.sketch(component, component.xZConstructionPlane, 'StemCuts')
        web = 'stem_internal_thickness / 2'
        start = 'stem_notch_start'
        crest = f'{start} + stem_notch_span'
        end = f'{crest} + stem_notch_taper'
        upper = 'stem_thickness / 2 + 1 mm'
        tip_end = 'stem_length - 0.5 mm'
        tip_start = f'{tip_end} - stem_tip_diamond_len'
        tip_peak = f'{tip_end} - stem_tip_diamond_len / 2'
        radius = '(stem_notch_span * stem_notch_span + stem_notch_depth * stem_notch_depth) / (2 * stem_notch_depth)'
        r = self.length(radius)
        half_span = self.length('stem_notch_span / 2')
        rise = half_span ** 2 / (r + math.sqrt(r ** 2 - half_span ** 2))
        self.loop(recess, [
            ('0 mm', web), (start, web), (crest, f'{web} + stem_notch_depth'),
            (end, web), (tip_start, web), (tip_peak, 'stem_tip_diamond_thk / 2'),
            (tip_end, web), ('stem_length', web), ('stem_length', upper), ('0 mm', upper),
        ], axes=(0, 2), arc=(1, f'{start} + stem_notch_span / 2',
                             f'{web} + {rise * 10:.12g} mm', radius))
        cut = self.extrude(component, recess, 'Upper web recess', 'stem_internal_width', CUT)
        mirrors = component.features.mirrorFeatures
        setup = mirrors.createInput(collection([cut]), component.xYConstructionPlane)
        setup.patternComputeOption = F.PatternComputeOptions.IdenticalPatternCompute
        mirror = mirrors.add(setup)
        require(mirror, 'Lower web recess: mirror failed.')
        mirror.name = 'Lower web recess'
        self.vertical_corners(component, 'Stem tip corner fillets', 'stem_chamfer',
                              self.length('stem_length'), self.length('stem_width / 2'))
        return component

    def guard(self):
        component = self.component('GUARD')
        outline = self.sketch(component, component.yZConstructionPlane, 'GuardSize')
        half_width = self.length('guard_width / 2')
        half_height = self.length('guard_height / 2')
        width_point = outline.modelToSketchSpace(POINT(0, half_width, 0))
        corner = outline.modelToSketchSpace(POINT(0, half_width, half_height))
        center = outline.originPoint.geometry
        sketch_lines = outline.sketchCurves.sketchLines
        left, right = sorted((corner.x, 2 * center.x - corner.x))
        low, high = sorted((corner.y, 2 * center.y - corner.y))
        corners = [
            outline.sketchPoints.add(POINT(x, y, 0))
            for x, y in ((left, low), (right, low), (right, high), (left, high))
        ]
        constraints = outline.geometricConstraints
        edges = []
        for index, start in enumerate(corners):
            end = corners[(index + 1) % len(corners)]
            edge = sketch_lines.addByTwoPoints(start, end)
            align = constraints.addHorizontal if index % 2 == 0 else constraints.addVertical
            require(align(edge), 'GuardSize: could not align rectangle edge.')
            edges.append(edge)

        diagonal = sketch_lines.addByTwoPoints(corners[0], corners[2])
        diagonal.isConstruction = True
        require(constraints.addMidPoint(outline.originPoint, diagonal),
                'GuardSize: could not anchor the rectangle midpoint.')
        width_is_horizontal = abs(width_point.x - center.x) > abs(width_point.y - center.y)
        orientations = F.DimensionOrientations
        for horizontal, edge in ((True, edges[0]), (False, edges[1])):
            start, end = edge.startSketchPoint, edge.endSketchPoint
            a, b = start.geometry, end.geometry
            reverse = a.x > b.x if horizontal else a.y > b.y
            if reverse:
                start, end = end, start
            if horizontal:
                direction = orientations.HorizontalDimensionOrientation
                label = POINT((a.x + b.x) / 2, a.y + (0.25 if a.y > 0 else -0.25), 0)
            else:
                direction = orientations.VerticalDimensionOrientation
                label = POINT(a.x + (0.25 if a.x > 0 else -0.25), (a.y + b.y) / 2, 0)
            expression = 'guard_width' if horizontal == width_is_horizontal else 'guard_height'
            dimension = outline.sketchDimensions.addDistanceDimension(start, end, direction, label)
            dimension.parameter.expression = expression
        self.extrude(component, outline, 'Guard blank', 'guard_length', NEW_BODY,
                     direction=self.direction(outline, 0, -1))
        length = self.length('guard_length')

        def axial(box):
            lo, hi = box.minPoint, box.maxPoint
            return (
                abs(lo.x + length) < TOL and abs(hi.x) < TOL
                and hi.y - lo.y < TOL and hi.z - lo.z < TOL
            )
        self.fillet(component, 'Guard perimeter fillets', 'guard_corner_rad', axial, 4)
        return component

    def pocket(self, component, sign, front, rear, front_half, rear_half):
        side = 'Upper' if sign > 0 else 'Lower'
        floor = 'handle_height / 2 - handle_pocket_depth'
        offset = floor if sign > 0 else f'-({floor})'
        planes = component.constructionPlanes
        setup = planes.createInput()
        require(setup.setByOffset(component.xYConstructionPlane, VALUE(offset)),
                f'{side} pocket: invalid offset plane.')
        plane = planes.add(setup)
        plane.name = f'{side} pocket floor'
        sketch = self.sketch(component, plane, f'{side}PocketSketch')
        z = self.length(offset)
        self.trapezoid(sketch, front, rear, front_half, rear_half, offset=z)
        self.extrude(component, sketch, f'{side} grip pocket', 'handle_pocket_depth + 1 mm',
                     CUT, direction=self.direction(sketch, 2, sign))

    def handle(self):
        component = self.component('HANDLE')
        front = '-guard_length'
        rear = '-(guard_length + handle_length)'
        side = self.sketch(component, component.xZConstructionPlane, 'SideCut')
        self.trapezoid(side, front, rear, 'handle_min_height / 2', 'handle_height / 2', (0, 2))
        self.extrude(component, side, 'Tapered handle blank', 'handle_width', NEW_BODY)

        trim = self.sketch(component, component.xYConstructionPlane, 'TopCutSketch')
        self.rectangle(trim, f'{rear} - 1.5 mm', f'{front} + 1.5 mm', '(handle_width + 3 mm) / 2')
        self.trapezoid(trim, front, rear, 'handle_neck_width / 2', 'handle_width / 2')
        self.extrude(component, trim, 'Handle side trim', 'handle_height + 2 mm', CUT, loops=2)

        pocket_front_half = '(handle_neck_width - 4 mm) / 2'
        pocket_rear_half = (
            f'{pocket_front_half} + (handle_width - handle_neck_width) / 2'
            ' * (handle_length - 5 mm) / handle_length'
        )
        for sign in (1, -1):
            self.pocket(component, sign, f'{front} - 2.5 mm', f'{rear} + 2.5 mm',
                        pocket_front_half, pocket_rear_half)
        self.vertical_corners(component, 'Handle rear corner fillets', '2.5 mm',
                              self.length(rear), self.length('handle_width / 2'))

        hole = self.sketch(component, component.xYConstructionPlane, 'LanyardHoleSketch')
        center, expressions = self.vertex(hole, '-(guard_length + handle_length * 0.65)',
                                          '0 mm', (0, 1))
        circle = hole.sketchCurves.sketchCircles.addByCenterRadius(
            center, self.length('lanyard_hole_dia / 2'))
        self.constrain_vertex(hole, circle.centerSketchPoint, center, expressions)
        dimension = hole.sketchDimensions.addDiameterDimension(
            circle, POINT(center.x + 0.3, center.y + 0.3, 0))
        dimension.parameter.expression = 'lanyard_hole_dia'
        self.extrude(component, hole, 'Lanyard through-hole', 'handle_height + 2 mm', CUT)
        return component


def validate(design, components):
    issues = []
    if design.designType != F.DesignTypes.ParametricDesignType:
        issues.append('The design is not parametric.')
    for name, _, _ in PARAMETERS:
        if design.userParameters.itemByName(name) is None:
            issues.append(f'Missing parameter {name}.')
    root = design.rootComponent
    if root.occurrences.count != 3 or root.bRepBodies.count or root.sketches.count:
        issues.append('Expected exactly three child components and an empty root.')
    for component, expected_name in zip(components, ('STEM', 'GUARD', 'HANDLE')):
        if component.name != expected_name:
            issues.append(f'Expected component {expected_name}, found {component.name}.')
        if component.bRepBodies.count != 1:
            issues.append(f'{component.name}: expected one body.')
        elif not (component.bRepBodies.item(0).isValid and component.bRepBodies.item(0).isSolid):
            issues.append(f'{component.name}: body is not a valid closed solid.')
        for sketch in component.sketches:
            label = f'{component.name}/{sketch.name}'
            # Compute All does not necessarily refresh the sketch constraint analysis.
            compute_sketch = getattr(sketch, 'compute', None)
            if compute_sketch is not None and not compute_sketch():
                issues.append(f'{label}: sketch constraint analysis failed to refresh.')
            if not sketch.isFullyConstrained:
                free_entities = []
                for kind, entities in (
                    ('point', sketch.sketchPoints),
                    ('line', sketch.sketchCurves.sketchLines),
                    ('arc', sketch.sketchCurves.sketchArcs),
                    ('circle', sketch.sketchCurves.sketchCircles),
                ):
                    for index, entity in enumerate(entities, start=1):
                        if not entity.isFullyConstrained:
                            free_entities.append(f'{kind} {index}')
                detail = ', '.join(free_entities) or 'no individual free entities reported'
                issues.append(f'{label}: sketch is underconstrained ({detail}).')
    unhealthy = (F.FeatureHealthStates.WarningFeatureHealthState, F.FeatureHealthStates.ErrorFeatureHealthState)
    for item in design.timeline:
        if item.healthState in unhealthy:
            entity = item.entity
            detail = getattr(entity, 'errorOrWarningMessage', '')
            issues.append(f'Timeline item {item.index + 1} ({item.name}): {detail or item.healthState}')
    require(not issues, 'Fusion validation failed:\n' + '\n'.join(issues))


def run(_context):
    app = C.Application.get()
    ui = app.userInterface
    try:
        app.documents.add(C.DocumentTypes.FusionDesignDocumentType)
        design = F.Design.cast(app.activeProduct)
        require(design, 'Open the Fusion Design workspace before running this script.')
        design.designType = F.DesignTypes.ParametricDesignType
        for name, expression, description in PARAMETERS:
            design.userParameters.add(name, VALUE(expression), 'mm', description)

        model = Model(design)
        components = (model.stem(), model.guard(), model.handle())
        require(design.computeAll(), 'Fusion could not recompute the design.')
        validate(design, components)
        for component in components:
            for sketch in component.sketches:
                sketch.isVisible = False
            for plane in component.constructionPlanes:
                plane.isLightBulbOn = False
        app.activeViewport.fit()
        ui.messageBox('STKey v5 built and validated. Adjust dimensions under Modify > Change Parameters.')
    except Exception:
        ui.messageBox('STKey v5 could not finish. The new design is open for inspection.\n\n'
                      + traceback.format_exc())
