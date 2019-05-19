import adsk.core as adskc
import adsk.fusion as adskf
import adsk.cam as adskam
import traceback
import adsk


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

    # find root component and create sketches
    rootComp = design.rootComponent
