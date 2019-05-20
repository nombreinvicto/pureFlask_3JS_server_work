import adsk.core as adskc
import adsk.fusion as adskf
import adsk.cam as adskam
import traceback
import adsk

unit_to_cm_factors = {
    'm': 100,
    'mm': 0.1,
    'in': 2.54,
    'ft': 30.48
}


def run(context):
    # this function sets up documents and initialises design global vars
    global app, ui, doc, products, design, designProduct, rootComp

    # setting up app and document
    app = adskc.Application.get()
    ui = app.userInterface
    doc = app.activeDocument
    products = doc.products

    # get design product
    designProduct = products.itemByProductType('DesignProductType')
    design = adskf.Design.cast(designProduct)

    # create units mgr object
    unitsMgr = design.unitsManager

    defaultUnits = unitsMgr.defaultLengthUnits


    # find root component and create sketches
    rootComp = design.rootComponent

    # now get the params
    params = rootComp.modelParameters

    for param in params:
        tparam = param  # type: adskf.Parameter

        tparam.value = tparam.value + 10 * unit_to_cm_factors.get(defaultUnits)
        adsk.doEvents()
