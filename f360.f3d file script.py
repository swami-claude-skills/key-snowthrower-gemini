import adsk.core, adsk.fusion, adsk.cam, traceback


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = "STKey_V5_GoldStandard"

        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        rootComp = design.rootComponent

        # =========================================================
        # 1. MASTER USER PARAMETERS (29 Parametric Expressions)
        # =========================================================
        userParams = design.userParameters
        base_params = [
            ("stem_length", 33.5, "mm", "Total insertion blade length from guard front datum"),
            ("stem_width", 9.5, "mm", "Transverse outer width of stem blade"),
            ("stem_thickness", 4.1, "mm", "Vertical outer thickness of stem rails"),
            ("stem_edge_rim", 1.4, "mm", "Outer perimeter wall thickness bordering recessed web"),
            ("stem_cutout_start", 22.0, "mm", "Axial distance from guard face to locking window start"),
            ("stem_cutout_size", 6.0, "mm", "Square retention locking window dimension"),
            ("stem_tip_diamond_len", 5.5, "mm", "Axial length of tip diamond (X = 28.00 to 33.50 mm)"),
            ("stem_notch_start", 14.0, "mm", "Axial distance to concave detent arc start"),
            ("stem_notch_depth", 1.0, "mm", "Nominal detent depth reference"),
            ("stem_notch_span", 4.0, "mm", "Axial arc span of concave detent (X = 14.00 to 18.00 mm)"),
            ("stem_notch_taper", 4.0, "mm", "Linear chisel taper from X = 18.00 to 22.00 mm"),
            ("stem_chamfer", 0.5, "mm", "Reserved reference parameter"),
            ("guard_length", 3.0, "mm", "Axial thickness of stop collar"),
            ("guard_width", 18.0, "mm", "Transverse width of stop collar"),
            ("guard_height", 11.0, "mm", "Vertical height of stop collar"),
            ("guard_corner_rad", 1.5, "mm", "Axial corner fillet radius on guard collar"),
            ("guard_perimeter_rad", 1.0, "mm", "Front and rear outer perimeter fillet radius on guard collar"),
            ("handle_guard_offset", 1.75, "mm", "Equal shoulder step inset from guard collar on all 4 sides"),
            ("handle_length", 24.0, "mm", "Axial length of ergonomic grip section"),
            ("handle_width", 27.0, "mm", "Maximum rear transverse width of grip section"),
            ("handle_height", 17.0, "mm", "Maximum rear vertical thickness of grip section"),
            ("handle_pocket_depth", 2.0, "mm", "Sloped finger grip pocket depth per face"),
            ("lanyard_hole_dia", 9.0, "mm", "Through-hole diameter for tether cord or clip"),
            ("junction_fillet_rad", 0.25, "mm", "Stress-relief fillet at component seams, inner web corners, and outer stem rails")
        ]

        for name, val, unit, comment in base_params:
            userParams.add(name, adsk.core.ValueInput.createByReal(val / 10.0), unit, comment)

        # Linked formula parameters
        userParams.add("stem_internal_width", adsk.core.ValueInput.createByString("stem_width - (2 * stem_edge_rim)"), "mm", "Recessed web pocket width (6.70 mm)")
        userParams.add("stem_internal_thickness", adsk.core.ValueInput.createByString("stem_thickness - (2 * stem_edge_rim)"), "mm", "Recessed web base thickness (1.30 mm)")
        userParams.add("stem_tip_diamond_thk", adsk.core.ValueInput.createByString("stem_thickness"), "mm", "Peak thickness at X = 30.75 mm for single-plane nose (4.10 mm)")
        userParams.add("handle_neck_width", adsk.core.ValueInput.createByString("guard_width - (2 * handle_guard_offset)"), "mm", "Equal 1.75 mm inset neck width (14.50 mm)")
        userParams.add("handle_min_height", adsk.core.ValueInput.createByString("guard_height - (2 * handle_guard_offset)"), "mm", "Equal 1.75 mm inset neck height (7.50 mm)")

        def create_subcomponent(name):
            occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            comp.name = name
            return occ, comp

        # =========================================================
        # 2. COMPONENT 1: STEM (+Y / +Z QUADRANT -> DOUBLE MIRROR)
        # =========================================================
        stemOcc, stemComp = create_subcomponent("STEM")
        sSketches = stemComp.sketches
        sExtrudes = stemComp.features.extrudeFeatures

        # Sketch 1: StemSize (+Y Quadrant Plan Envelope + Half Locking Window)
        stemSize = sSketches.add(stemComp.xYConstructionPlane)
        stemSize.name = "StemSize"
        sl = stemSize.sketchCurves.sketchLines
        sd = stemSize.sketchDimensions
        sc = stemSize.geometricConstraints

        sBot = sl.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(3.35, 0, 0))
        sRight = sl.addByTwoPoints(sBot.endSketchPoint, adsk.core.Point3D.create(3.35, 0.475, 0))
        sTop = sl.addByTwoPoints(sRight.endSketchPoint, adsk.core.Point3D.create(0, 0.475, 0))
        sLeft = sl.addByTwoPoints(sTop.endSketchPoint, sBot.startSketchPoint)

        sc.addCoincident(sBot.startSketchPoint, stemSize.originPoint)
        sc.addHorizontal(sBot)
        sc.addVertical(sRight)
        sc.addHorizontal(sTop)
        sc.addVertical(sLeft)

        sd.addDistanceDimension(sBot.startSketchPoint, sBot.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(1.675, -0.15, 0)).parameter.expression = "stem_length"
        sd.addDistanceDimension(sRight.startSketchPoint, sRight.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(3.6, 0.24, 0)).parameter.expression = "stem_width / 2"

        # Quadrant Locking Window (X = 22.0 to 28.0 mm, Y = 0 to 3.0 mm)
        wBot = sl.addByTwoPoints(adsk.core.Point3D.create(2.2, 0, 0), adsk.core.Point3D.create(2.8, 0, 0))
        wRight = sl.addByTwoPoints(wBot.endSketchPoint, adsk.core.Point3D.create(2.8, 0.3, 0))
        wTop = sl.addByTwoPoints(wRight.endSketchPoint, adsk.core.Point3D.create(2.2, 0.3, 0))
        wLeft = sl.addByTwoPoints(wTop.endSketchPoint, wBot.startSketchPoint)

        sc.addCoincident(wBot.startSketchPoint, sBot)
        sc.addCoincident(wBot.endSketchPoint, sBot)
        sc.addVertical(wRight)
        sc.addHorizontal(wTop)
        sc.addVertical(wLeft)

        sd.addDistanceDimension(stemSize.originPoint, wBot.startSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(1.1, -0.1, 0)).parameter.expression = "stem_cutout_start"
        sd.addDistanceDimension(wBot.startSketchPoint, wBot.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(2.5, -0.1, 0)).parameter.expression = "stem_cutout_size"
        sd.addDistanceDimension(wRight.startSketchPoint, wRight.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(2.95, 0.15, 0)).parameter.expression = "stem_cutout_size / 2"

        stemProf = max([p for p in stemSize.profiles], key=lambda pr: pr.areaProperties().area)
        sExtIn = sExtrudes.createInput(stemProf, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        sExtIn.setDistanceExtent(False, adsk.core.ValueInput.createByString("stem_thickness / 2"))
        stemBody = sExtrudes.add(sExtIn).bodies.item(0)
        stemBody.name = "StemBody"

        # Sketch 2: StemCuts (+Z Quadrant XZ Elevation: Concave Detent + Double-Chisel Window + Single-Plane Nose)
        stemCuts = sSketches.add(stemComp.xZConstructionPlane)
        stemCuts.name = "StemCuts"
        cl = stemCuts.sketchCurves.sketchLines
        ca = stemCuts.sketchCurves.sketchArcs
        cd = stemCuts.sketchDimensions
        cc = stemCuts.geometricConstraints

        cAxisXZ = cl.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(3.5, 0, 0))
        cAxisXZ.isConstruction = True
        cc.addCoincident(cAxisXZ.startSketchPoint, stemCuts.originPoint)
        cc.addHorizontal(cAxisXZ)

        # Profile A: Web + Concave Detent + Front Chisel + Window Full Clearance (X = 0 to 28.0 mm)
        p0 = adsk.core.Point3D.create(0, -0.065, 0)
        p1 = adsk.core.Point3D.create(1.4, -0.065, 0)
        p2 = adsk.core.Point3D.create(1.6, -0.030, 0)  # Concave valley at Z = 0.30 mm (0.60 mm full bridge)
        p3 = adsk.core.Point3D.create(1.8, -0.065, 0)
        p4 = adsk.core.Point3D.create(2.2, 0.0, 0)     # Front chisel edge at Z = 0
        p5 = adsk.core.Point3D.create(2.8, 0.0, 0)     # Rear chisel edge at Z = 0
        pTop28 = adsk.core.Point3D.create(2.8, -0.25, 0)
        pTop0 = adsk.core.Point3D.create(0, -0.25, 0)

        l1 = cl.addByTwoPoints(p0, p1)
        a1 = ca.addByThreePoints(l1.endSketchPoint, p2, p3)
        l2 = cl.addByTwoPoints(a1.endSketchPoint, p4)
        l3 = cl.addByTwoPoints(l2.endSketchPoint, p5)
        lR28 = cl.addByTwoPoints(l3.endSketchPoint, pTop28)
        lT28 = cl.addByTwoPoints(lR28.endSketchPoint, pTop0)
        lL0 = cl.addByTwoPoints(lT28.endSketchPoint, l1.startSketchPoint)

        cc.addHorizontal(l1)
        cc.addHorizontal(lT28)
        cc.addVertical(lL0)
        cc.addVertical(lR28)
        cc.addCoincident(a1.endSketchPoint, l1)
        cc.addCoincident(l2.endSketchPoint, cAxisXZ)
        cc.addCoincident(l3.endSketchPoint, cAxisXZ)

        cd.addDistanceDimension(stemCuts.originPoint, l1.startSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(0, 0.1, 0)).parameter.expression = "0 mm"
        cd.addDistanceDimension(stemCuts.originPoint, l1.startSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-0.2, -0.03, 0)).parameter.expression = "stem_internal_thickness / 2"
        cd.addDistanceDimension(l1.startSketchPoint, l1.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(0.7, 0.15, 0)).parameter.expression = "stem_notch_start"
        cd.addDistanceDimension(l1.endSketchPoint, a1.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(1.6, 0.15, 0)).parameter.expression = "stem_notch_span"
        cd.addDistanceDimension(a1.endSketchPoint, l2.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(2.0, 0.15, 0)).parameter.expression = "stem_notch_taper"
        cd.addDistanceDimension(l3.startSketchPoint, l3.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(2.5, 0.15, 0)).parameter.expression = "stem_cutout_size"
        cd.addDistanceDimension(stemCuts.originPoint, lT28.startSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-0.3, -0.15, 0)).parameter.expression = "stem_thickness"

        # Profile B: Inner Tip Diamond Rising to Full Rail Height at X = 30.75 mm
        pPeak = adsk.core.Point3D.create(3.075, -0.205, 0)
        pTop3075 = adsk.core.Point3D.create(3.075, -0.25, 0)

        lDiaUp = cl.addByTwoPoints(l3.endSketchPoint, pPeak)
        lR3075 = cl.addByTwoPoints(lDiaUp.endSketchPoint, pTop3075)
        lT3075 = cl.addByTwoPoints(lR3075.endSketchPoint, lR28.endSketchPoint)

        cc.addVertical(lR3075)
        cc.addHorizontal(lT3075)
        cd.addDistanceDimension(l3.endSketchPoint, lDiaUp.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(2.94, 0.15, 0)).parameter.expression = "stem_tip_diamond_len / 2"
        cd.addDistanceDimension(stemCuts.originPoint, lDiaUp.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(3.15, -0.1, 0)).parameter.expression = "stem_tip_diamond_thk / 2"

        # Profile C: Full-Width Single-Plane Nose Slope (X = 30.75 to 33.50 mm)
        pNose = adsk.core.Point3D.create(3.35, 0.0, 0)
        pTop335 = adsk.core.Point3D.create(3.35, -0.25, 0)

        lNoseSlope = cl.addByTwoPoints(lDiaUp.endSketchPoint, pNose)
        lR335 = cl.addByTwoPoints(lNoseSlope.endSketchPoint, pTop335)
        lT335 = cl.addByTwoPoints(lR335.endSketchPoint, lR3075.endSketchPoint)

        cc.addCoincident(lNoseSlope.endSketchPoint, cAxisXZ)
        cc.addVertical(lR335)
        cc.addHorizontal(lT335)
        cd.addDistanceDimension(lDiaUp.endSketchPoint, lNoseSlope.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(3.21, 0.15, 0)).parameter.expression = "stem_tip_diamond_len / 2"

        stem_profs = sorted([p for p in stemCuts.profiles], key=lambda pr: pr.boundingBox.minPoint.x)
        abCol = adsk.core.ObjectCollection.create()
        abCol.add(stem_profs[0])
        abCol.add(stem_profs[1])

        cutABIn = sExtrudes.createInput(abCol, adsk.fusion.FeatureOperations.CutFeatureOperation)
        cutABIn.setDistanceExtent(False, adsk.core.ValueInput.createByString("stem_internal_width / 2"))
        cutABIn.participantBodies = [stemBody]
        sExtrudes.add(cutABIn)

        cutCIn = sExtrudes.createInput(stem_profs[2], adsk.fusion.FeatureOperations.CutFeatureOperation)
        cutCIn.setDistanceExtent(False, adsk.core.ValueInput.createByString("stem_width / 2"))
        cutCIn.participantBodies = [stemBody]
        sExtrudes.add(cutCIn)

        # =========================================================
        # 3. COMPONENT 2: GUARD (+Y / +Z QUADRANT -> DOUBLE MIRROR)
        # =========================================================
        guardOcc, guardComp = create_subcomponent("GUARD")
        gSketches = guardComp.sketches
        gExtrudes = guardComp.features.extrudeFeatures
        gFillets = guardComp.features.filletFeatures

        guardSize = gSketches.add(guardComp.yZConstructionPlane)
        guardSize.name = "GuardSize"
        gl = guardSize.sketchCurves.sketchLines
        gd = guardSize.sketchDimensions
        gc = guardSize.geometricConstraints

        gBot = gl.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(-0.55, 0, 0))
        gRight = gl.addByTwoPoints(gBot.endSketchPoint, adsk.core.Point3D.create(-0.55, 0.9, 0))
        gTop = gl.addByTwoPoints(gRight.endSketchPoint, adsk.core.Point3D.create(0, 0.9, 0))
        gLeft = gl.addByTwoPoints(gTop.endSketchPoint, gBot.startSketchPoint)

        gc.addCoincident(gBot.startSketchPoint, guardSize.originPoint)
        gc.addHorizontal(gBot)
        gc.addVertical(gRight)
        gc.addHorizontal(gTop)
        gc.addVertical(gLeft)

        gd.addDistanceDimension(gBot.startSketchPoint, gBot.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(-0.27, -0.15, 0)).parameter.expression = "guard_height / 2"
        gd.addDistanceDimension(gRight.startSketchPoint, gRight.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-0.75, 0.45, 0)).parameter.expression = "guard_width / 2"

        gExtIn = gExtrudes.createInput(guardSize.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        gExtIn.setDistanceExtent(False, adsk.core.ValueInput.createByString("-guard_length"))
        guardBody = gExtrudes.add(gExtIn).bodies.item(0)
        guardBody.name = "GuardBody"

        gCornerEdges = adsk.core.ObjectCollection.create()
        for edge in guardBody.edges:
            bb = edge.boundingBox
            if abs(bb.minPoint.x - (-0.3)) < 0.01 and abs(bb.maxPoint.x - 0.0) < 0.01:
                if bb.minPoint.y > 0.85 and bb.minPoint.z > 0.50:
                    gCornerEdges.add(edge)
        if gCornerEdges.count > 0:
            fIn = gFillets.createInput()
            fIn.addConstantRadiusEdgeSet(gCornerEdges, adsk.core.ValueInput.createByString("guard_corner_rad"), False)
            gFillets.add(fIn)

        # =========================================================
        # 4. COMPONENT 3: HANDLE (+Y / +Z QUADRANT -> DOUBLE MIRROR)
        # =========================================================
        handleOcc, handleComp = create_subcomponent("HANDLE")
        hSketches = handleComp.sketches
        hExtrudes = handleComp.features.extrudeFeatures
        hFillets = handleComp.features.filletFeatures

        # Sketch 4: SideCut (+Z Quadrant XZ Taper: Z = 3.75 mm neck to Z = 8.50 mm rear)
        sideCut = hSketches.add(handleComp.xZConstructionPlane)
        sideCut.name = "SideCut"
        hl = sideCut.sketchCurves.sketchLines
        hd = sideCut.sketchDimensions
        hc = sideCut.geometricConstraints

        hAxisXZ = hl.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(-3.0, 0, 0))
        hAxisXZ.isConstruction = True
        hc.addCoincident(hAxisXZ.startSketchPoint, sideCut.originPoint)
        hc.addHorizontal(hAxisXZ)

        hbBase = hl.addByTwoPoints(adsk.core.Point3D.create(-0.3, 0, 0), adsk.core.Point3D.create(-2.7, 0, 0))
        hbBack = hl.addByTwoPoints(hbBase.endSketchPoint, adsk.core.Point3D.create(-2.7, -0.85, 0))
        hbTop = hl.addByTwoPoints(hbBack.endSketchPoint, adsk.core.Point3D.create(-0.3, -0.375, 0))
        hbFront = hl.addByTwoPoints(hbTop.endSketchPoint, hbBase.startSketchPoint)

        hc.addCoincident(hbBase.startSketchPoint, hAxisXZ)
        hc.addHorizontal(hbBase)
        hc.addVertical(hbBack)
        hc.addVertical(hbFront)

        hd.addDistanceDimension(sideCut.originPoint, hbBase.startSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(-0.15, 0.15, 0)).parameter.expression = "guard_length"
        hd.addDistanceDimension(hbBase.startSketchPoint, hbBase.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(-1.5, 0.15, 0)).parameter.expression = "handle_length"
        hd.addDistanceDimension(hbFront.startSketchPoint, hbFront.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-0.15, -0.2, 0)).parameter.expression = "handle_min_height / 2"
        hd.addDistanceDimension(hbBack.startSketchPoint, hbBack.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-2.9, -0.4, 0)).parameter.expression = "handle_height / 2"

        hBaseIn = hExtrudes.createInput(sideCut.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        hBaseIn.setDistanceExtent(False, adsk.core.ValueInput.createByString("handle_width / 2"))
        handleBody = hExtrudes.add(hBaseIn).bodies.item(0)
        handleBody.name = "HandleBody [KEY]"

        # Sketch 5: TopCutSketch (+Y Quadrant Plan Wedge Trim: Y = 7.25 mm neck to Y = 13.50 mm rear)
        topCut = hSketches.add(handleComp.xYConstructionPlane)
        topCut.name = "TopCutSketch"
        tl = topCut.sketchCurves.sketchLines
        td = topCut.sketchDimensions
        tc = topCut.geometricConstraints

        hAxisXY = tl.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(-3.0, 0, 0))
        hAxisXY.isConstruction = True
        tc.addCoincident(hAxisXY.startSketchPoint, topCut.originPoint)
        tc.addHorizontal(hAxisXY)

        wHyp = tl.addByTwoPoints(adsk.core.Point3D.create(-0.3, 0.725, 0), adsk.core.Point3D.create(-2.7, 1.35, 0))
        wTop = tl.addByTwoPoints(wHyp.endSketchPoint, adsk.core.Point3D.create(-0.3, 1.5, 0))
        wRight = tl.addByTwoPoints(wTop.endSketchPoint, wHyp.startSketchPoint)

        tc.addHorizontal(wTop)
        tc.addVertical(wRight)
        td.addDistanceDimension(topCut.originPoint, wRight.startSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(-0.15, 1.65, 0)).parameter.expression = "guard_length"
        td.addDistanceDimension(wTop.startSketchPoint, wTop.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(-1.5, 1.65, 0)).parameter.expression = "handle_length"
        td.addDistanceDimension(hAxisXY.startSketchPoint, wHyp.startSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-0.15, 0.35, 0)).parameter.expression = "handle_neck_width / 2"
        td.addDistanceDimension(hAxisXY.startSketchPoint, wHyp.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-2.9, 0.7, 0)).parameter.expression = "handle_width / 2"
        td.addDistanceDimension(hAxisXY.startSketchPoint, wTop.startSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-2.9, 1.42, 0)).parameter.expression = "(handle_width / 2) + 1.5 mm"

        trimCutIn = hExtrudes.createInput(topCut.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        trimCutIn.setDistanceExtent(False, adsk.core.ValueInput.createByString("handle_height"))
        trimCutIn.participantBodies = [handleBody]
        hExtrudes.add(trimCutIn)

        # Sketch 6: PocketPlan (+Y Quadrant Sloped Finger Pocket)
        pocketPlan = hSketches.add(handleComp.xYConstructionPlane)
        pocketPlan.name = "PocketPlan"
        pl = pocketPlan.sketchCurves.sketchLines
        pd = pocketPlan.sketchDimensions
        pc = pocketPlan.geometricConstraints

        pAxisXY = pl.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(-3.0, 0, 0))
        pAxisXY.isConstruction = True
        pc.addCoincident(pAxisXY.startSketchPoint, pocketPlan.originPoint)
        pc.addHorizontal(pAxisXY)

        ppBase = pl.addByTwoPoints(adsk.core.Point3D.create(-0.7, 0, 0), adsk.core.Point3D.create(-2.4, 0, 0))
        ppBack = pl.addByTwoPoints(ppBase.endSketchPoint, adsk.core.Point3D.create(-2.4, 1.1, 0))
        ppSlope = pl.addByTwoPoints(ppBack.endSketchPoint, adsk.core.Point3D.create(-0.7, 0.55, 0))
        ppFront = pl.addByTwoPoints(ppSlope.endSketchPoint, ppBase.startSketchPoint)

        pc.addCoincident(ppBase.startSketchPoint, pAxisXY)
        pc.addHorizontal(ppBase)
        pc.addVertical(ppBack)
        pc.addVertical(ppFront)

        pd.addDistanceDimension(pocketPlan.originPoint, ppBase.startSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(-0.35, -0.15, 0)).parameter.expression = "7.0 mm"
        pd.addDistanceDimension(pocketPlan.originPoint, ppBase.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(-1.2, -0.15, 0)).parameter.expression = "24.0 mm"
        pd.addDistanceDimension(ppFront.startSketchPoint, ppFront.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-0.55, 0.27, 0)).parameter.expression = "5.5 mm"
        pd.addDistanceDimension(ppBack.startSketchPoint, ppBack.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-2.55, 0.55, 0)).parameter.expression = "11.0 mm"

        topSlantFace = next((f for f in handleBody.faces if f.boundingBox.minPoint.z > 0.35 and (f.boundingBox.maxPoint.z - f.boundingBox.minPoint.z) > 0.3), None)
        if topSlantFace:
            pCut = hExtrudes.createInput(pocketPlan.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
            pCut.startExtent = adsk.fusion.FromEntityStartDefinition.create(topSlantFace, adsk.core.ValueInput.createByReal(0))
            pCut.setDistanceExtent(False, adsk.core.ValueInput.createByString("-handle_pocket_depth"))
            pCut.participantBodies = [handleBody]
            hExtrudes.add(pCut)

        # Quadrant rear vertical corner fillet (2.50 mm)
        hRearEdge = adsk.core.ObjectCollection.create()
        for edge in handleBody.edges:
            bb = edge.boundingBox
            if abs(bb.minPoint.x - (-2.7)) < 0.01 and abs(bb.maxPoint.x - (-2.7)) < 0.01 and bb.minPoint.y > 1.30:
                hRearEdge.add(edge)
        if hRearEdge.count > 0:
            hfIn = hFillets.createInput()
            hfIn.addConstantRadiusEdgeSet(hRearEdge, adsk.core.ValueInput.createByReal(0.25), False)
            hFillets.add(hfIn)

        # =========================================================
        # 5. TWO-AXIS MIRROR (XY & XZ) -> FULL SYMMETRIC BODIES
        # =========================================================
        def mirror_two_axes(comp, body):
            mFeats = comp.features.mirrorFeatures
            bCol1 = adsk.core.ObjectCollection.create()
            bCol1.add(body)
            mXY = mFeats.createInput(bCol1, comp.xYConstructionPlane)
            mXY.isCombine = True
            mFeats.add(mXY)

            bCol2 = adsk.core.ObjectCollection.create()
            bCol2.add(body)
            mXZ = mFeats.createInput(bCol2, comp.xZConstructionPlane)
            mXZ.isCombine = True
            mFeats.add(mXZ)

        mirror_two_axes(stemComp, stemBody)
        mirror_two_axes(guardComp, guardBody)
        mirror_two_axes(handleComp, handleBody)

        # =========================================================
        # 6. LANYARD HOLE + BOOLEAN COMBINE + FINISHING FILLETS
        # =========================================================
        lanyardSketch = hSketches.add(handleComp.xYConstructionPlane)
        lanyardSketch.name = "LanyardHoleSketch"
        lcir = lanyardSketch.sketchCurves.sketchCircles
        ld = lanyardSketch.sketchDimensions
        lc = lanyardSketch.geometricConstraints

        lAxis = lanyardSketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(-2.7, 0, 0))
        lAxis.isConstruction = True
        lc.addCoincident(lAxis.startSketchPoint, lanyardSketch.originPoint)
        lc.addHorizontal(lAxis)

        holeCir = lcir.addByCenterRadius(adsk.core.Point3D.create(-1.86, 0, 0), 0.45)
        lc.addCoincident(holeCir.centerSketchPoint, lAxis)
        ld.addDiameterDimension(holeCir, adsk.core.Point3D.create(-2.0, 0.55, 0)).parameter.expression = "lanyard_hole_dia"
        ld.addDistanceDimension(lanyardSketch.originPoint, holeCir.centerSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(-0.9, -0.45, 0)).parameter.expression = "guard_length + (handle_length * 0.65)"

        holeCutIn = hExtrudes.createInput(lanyardSketch.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
        holeCutIn.setSymmetricExtent(adsk.core.ValueInput.createByString("handle_height + 2 mm"), True)
        holeCutIn.participantBodies = [handleBody]
        hExtrudes.add(holeCutIn)

        # 0.40 mm lanyard hole rim fillet
        holeEdges = adsk.core.ObjectCollection.create()
        for edge in handleBody.edges:
            if edge.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType and abs(edge.geometry.radius - 0.45) < 0.01:
                holeEdges.add(edge)
        if holeEdges.count > 0:
            hrIn = hFillets.createInput()
            hrIn.addConstantRadiusEdgeSet(holeEdges, adsk.core.ValueInput.createByReal(0.04), False)
            hFillets.add(hrIn)

        # 1.00 mm Outer Handle Grip Border Fillet (before combining with Guard)
        handleBorderEdges = adsk.core.ObjectCollection.create()
        for edge in handleBody.edges:
            bb = edge.boundingBox
            if bb.minPoint.x < -0.31:
                if abs(abs(bb.minPoint.y) - 1.35) < 0.01 or abs(abs(bb.maxPoint.y) - 1.35) < 0.01 or abs(bb.minPoint.x - (-2.7)) < 0.01:
                    if edge.geometry.curveType != adsk.core.Curve3DTypes.Circle3DCurveType:
                        handleBorderEdges.add(edge)
        if handleBorderEdges.count > 0:
            hbIn = hFillets.createInput()
            hbIn.addConstantRadiusEdgeSet(handleBorderEdges, adsk.core.ValueInput.createByReal(0.10), False)
            hFillets.add(hbIn)

        # Boolean Combine (Join) STEM + GUARD into HandleBody [KEY]
        combFeats = handleComp.features.combineFeatures
        toolBodies = adsk.core.ObjectCollection.create()
        toolBodies.add(stemBody.createForAssemblyContext(stemOcc))
        toolBodies.add(guardBody.createForAssemblyContext(guardOcc))

        combIn = combFeats.createInput(handleBody.createForAssemblyContext(handleOcc), toolBodies)
        combIn.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        combIn.isKeepToolBodies = False
        combFeats.add(combIn)

        # Finishing Fillets on Unified HandleBody [KEY]
        unifiedBody = handleComp.bRepBodies.item(0)
        guardPerimEdges = adsk.core.ObjectCollection.create()
        reliefEdges = adsk.core.ObjectCollection.create()

        for edge in unifiedBody.edges:
            bb = edge.boundingBox
            min_x, max_x = bb.minPoint.x, bb.maxPoint.x
            min_y, max_y = bb.minPoint.y, bb.maxPoint.y
            min_z, max_z = bb.minPoint.z, bb.maxPoint.z

            # 1.00 mm Guard outer perimeter loops at X = 0.00 mm and X = -3.00 mm
            if (abs(min_x) < 0.005 and abs(max_x) < 0.005 and (max_y > 0.85 or max_z > 0.50)):
                guardPerimEdges.add(edge)
            elif (abs(min_x - (-0.3)) < 0.005 and abs(max_x - (-0.3)) < 0.005 and (max_y > 0.85 or max_z > 0.50)):
                guardPerimEdges.add(edge)

            # 0.25 mm Stress-relief fillets: component seams, stem inner pocket/lip edges, and stem outer rails
            at_stem_guard = abs(min_x) < 0.005 and abs(max_x) < 0.005 and max_y <= 0.48 and max_z <= 0.21
            at_guard_handle = abs(min_x - (-0.3)) < 0.005 and abs(max_x - (-0.3)) < 0.005 and max_y <= 0.73 and max_z <= 0.38
            at_stem_inner = (min_x >= -0.005 and max_x <= 3.08 and abs(abs(min_y) - 0.335) < 0.005 and abs(abs(max_y) - 0.335) < 0.005)
            at_stem_outer = (min_x >= -0.005 and max_x <= 3.08 and abs(abs(min_y) - 0.475) < 0.005 and abs(abs(max_y) - 0.475) < 0.005 and abs(abs(min_z) - 0.205) < 0.005)

            if at_stem_guard or at_guard_handle or at_stem_inner or at_stem_outer:
                reliefEdges.add(edge)

        if guardPerimEdges.count > 0:
            gpIn = hFillets.createInput()
            gpIn.addConstantRadiusEdgeSet(guardPerimEdges, adsk.core.ValueInput.createByString("guard_perimeter_rad"), False)
            hFillets.add(gpIn)

        if reliefEdges.count > 0:
            rfIn = hFillets.createInput()
            rfIn.addConstantRadiusEdgeSet(reliefEdges, adsk.core.ValueInput.createByString("junction_fillet_rad"), False)
            hFillets.add(rfIn)

        # =========================================================
        # 7. EXPORT NATIVE .F3D ARCHIVE DIALOG
        # =========================================================
        fileDlg = ui.createFileDialog()
        fileDlg.isMultiSelectEnabled = False
        fileDlg.title = "Save STKey V5 Gold Standard (.f3d)"
        fileDlg.filter = "Fusion 360 Archive Files (*.f3d)"
        fileDlg.initialFilename = "STKey_V5_GoldStandard.f3d"
        if fileDlg.showSave() == adsk.core.DialogResults.DialogOK:
            exportMgr = design.exportManager
            f3dOptions = exportMgr.createFusionArchiveExportOptions(fileDlg.filename)
            exportMgr.execute(f3dOptions)
            ui.messageBox(f"STKey V5 Gold Standard built and exported to:\n{fileDlg.filename}")
        else:
            ui.messageBox("STKey V5 Gold Standard built cleanly! (.f3d export skipped)")

    except:
        if ui:
            ui.messageBox("Script Failed:\n{}".format(traceback.format_exc()))
