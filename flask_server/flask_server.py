app = None
ui = None
handlers = []
stopFlag = None
myCustomEvent = 'MyCustomEventId'
customEvent = None
flaskServerReplyBit = False
addInsPanel = None
server_thread = None
server_process = None
app_run_tracker = False
flask_server_to_3js_reply = None
localhost = "http://192.168.0.10:6923"

try:
    from pureFlask_3JS_Server.flask_app \
        import flask_app, cadMetaDataPath, flaskKwargs, \
        flask_app_PORT, lcnc_upload_url
    import adsk, adsk.core, adsk.fusion, adsk.cam, traceback
    from flask import request
    import threading, json, requests, time, os

    app = adsk.core.Application.get()
    ui = app.userInterface
except:
    if ui:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# flask related things
def shutdown_server():
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func is None:
        raise RuntimeError
    shutdown_func()


@flask_app.route('/fusion360', methods=['POST'])
def fusion360():
    global flaskServerReplyBit, flask_server_to_3js_reply

    args = request.get_json()  # returns a dict
    app.fireCustomEvent(myCustomEvent, json.dumps(args))

    # wait till the model updates then reply to CAD server
    while not flaskServerReplyBit:
        pass
    flaskServerReplyBit = False

    # now send the file to LCNC
    return flask_server_to_3js_reply


@flask_app.route('/shutdown', methods=['POST'])
def stop_server():
    shutdown_server()
    return "shutting down server"


@flask_app.route('/send_gcode_to_lcnc')
def send_gcode():
    p1 = os.path.dirname(os.path.dirname(__file__))
    p2 = p1 + r'/flask_app/stl'

    with open(p2 + r"/flowsnake.ngc") as file:
        files = {'file': file}
        r = requests.post(lcnc_upload_url, files=files)
        return r.text  # reply to be sent back to 3js


# the event handler that responds to the custom event being fired

class ThreadEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CustomEventArgs):
        try:
            # Make sure a command isn'server_thread running before
            # changes are made.
            global flaskServerReplyBit, flask_server_to_3js_reply
            if ui.activeCommand != 'SelectCommand':
                ui.commandDefinitions.itemById(
                    'SelectCommand').execute()

            # change the workspace first and show the design ws
            ws = ui.workspaces.itemById('FusionSolidEnvironment')
            ws.activate()

            # Get the value from JSON data passed through the event.
            doc = app.activeDocument
            products = doc.products
            designProduct = products.itemByProductType(
                'DesignProductType')

            eventArgs = json.loads(args.additionalInfo)
            design = adsk.fusion.Design.cast(designProduct)
            rootComp = design.rootComponent
            fileName = None
            outJsonMetaData = {}

            # check if the file is the same as that one loaded in F360
            doc_name = eventArgs['filename'][0:-4]
            if app.activeDocument.name != doc_name:
                flask_server_to_3js_reply = 'F360 active document ' \
                                            'incompatible \n with current STL file'
                flaskServerReplyBit = True
                return

            for key, val in eventArgs.items():
                # Set the parameter value.
                if key != 'filename':
                    outJsonMetaData[key] = val
                    newValue = float(val)
                    param = design.rootComponent.modelParameters.itemByName(
                        key)
                    if not param:
                        flask_server_to_3js_reply = "No model present in F360 \n" \
                                                    "Parameter change attempt failed"
                        flaskServerReplyBit = True
                        return
                    param.value = newValue
                    adsk.doEvents()
                else:
                    fileName = val

            # Save the file as STL.
            exportMgr = adsk.fusion.ExportManager.cast(
                design.exportManager)
            stlOptions = exportMgr.createSTLExportOptions(rootComp)
            stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
            stlOptions.filename = cadMetaDataPath + r"\\" \
                                  + fileName[0:-3] + 'stl'
            exportMgr.execute(stlOptions)

            # dump new metadata
            with open(cadMetaDataPath + r"\\"
                      + fileName[0:-4] + '_value' + '.json',
                      'w') as outfile:
                json.dump(outJsonMetaData, outfile)
            # allow the flask server to reply now
            flask_server_to_3js_reply = "F360 Param Change Successful"
            flaskServerReplyBit = True
        except:
            if ui:
                ui.messageBox(
                    'Failed:\n{}'.format(traceback.format_exc()))


class FlaskThreeJSButtonPressedHandler(
    adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CommandCreatedEventArgs):
        try:
            global app_run_tracker, server_thread

            # get the command that was created
            cmd = adsk.core.Command.cast(args.command)

            # get the inputs collection
            inputs = cmd.commandInputs

            # start the flask server thread
            if not app_run_tracker:
                # thread paradigm
                server_thread = threading.Thread(target=flask_app.run,
                                                 kwargs=flaskKwargs)
                server_thread.setDaemon(True)
                server_thread.start()
                app_run_tracker = not app_run_tracker  # convert to True
                ui.messageBox('FusionThreeJS Server started at: ' +
                              str(flask_app_PORT))
            else:
                # stop the server on second press
                go_stop_server()
        except:
            if ui:
                ui.messageBox(
                    'Failed:\n{}'.format(traceback.format_exc()))


def go_stop_server():
    global app_run_tracker
    # only stop server on repress of addin button
    # dont execute when user turning off addin via dialog
    r = requests.post(url=localhost + "/shutdown")
    ui.messageBox(str(r.text) + '\n' +
                  'please make sure to stop the addin from scripts '
                  'toolbar')
    # turn to false again ready for next repress of addin button
    app_run_tracker = not app_run_tracker

    while server_thread.is_alive():
        # keep on looping until thread exits
        pass


def attach_addin_button():
    # get the command definition
    commDefs = ui.commandDefinitions

    # add a button command def
    flaskThreeJSButtDef = commDefs.addButtonDefinition(
        'flaskThreeJSButtDefID',
        'Start 3JS Server!',
        'starts a Flask server that serves a 3JS front end app controlling '
        + 'models in Fusion 360 in real time.',
        'resources'
    )

    # grab the correct toolbar panel to add the button to
    global addInsPanel
    addInsPanel = ui.allToolbarPanels.itemById(
        'SolidScriptsAddinsPanel')
    flaskThreeJSButt = addInsPanel.controls.addCommand(
        flaskThreeJSButtDef,
        'flaskThreeJSButtID'
    )
    flaskThreeJSButt.isPromoted = True
    flaskThreeJSButt.isPromotedByDefault = True

    # connect to the command created event handler
    flaskThreeJSButtHandler = FlaskThreeJSButtonPressedHandler()
    flaskThreeJSButtDef.commandCreated.add(flaskThreeJSButtHandler)
    handlers.append(flaskThreeJSButtHandler)


def run(context):
    try:
        # Register the custom event and connect the handler
        global customEvent, server_thread, server_process
        customEvent = app.registerCustomEvent(myCustomEvent)
        onThreadEvent = ThreadEventHandler()
        customEvent.add(onThreadEvent)
        handlers.append(onThreadEvent)

        # add addin buttons to the toolbar
        attach_addin_button()

        ui.messageBox('FusionThreeJS Addin Initiated')
    except:
        if ui:
            ui.messageBox(
                'Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        global app_run_tracker
        # delete buttons
        addinButt = ui.commandDefinitions.itemById(
            'flaskThreeJSButtDefID')
        if addinButt:
            addinButt.deleteMe()

        # get and delete the controls
        ctrl = addInsPanel.controls.itemById('flaskThreeJSButtDefID')
        if ctrl:
            ctrl.deleteMe()

        customEvent.remove(handlers[0])
        app.unregisterCustomEvent(myCustomEvent)
        ui.messageBox('FusionThreeJS Addin Stopped. \n' +
                      'Addon reload can only occur with next Fusion restart.')

        if app_run_tracker:  # is true when server is running
            # will stop server if it has not been already turned
            # off by the user
            go_stop_server()
    except:
        if ui:
            ui.messageBox(
                'Failed:\n{}'.format(traceback.format_exc()))
