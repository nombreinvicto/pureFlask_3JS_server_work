app = None
ui = None
handlers = []
stopFlag = None
paramChangeCustomEventId = 'paramChangeEventId'
toolpathGenerateCustomEventId = 'toolpathGenerateEventId'
paramChangeCustomEvent = None
toolpathGenerateCustomEvent = None
invalid_toolpath_flag = None
flaskServerReplyBit = False
addInsPanel = None
server_thread = None
server_process = None
app_run_tracker = False
flask_server_to_3js_reply = None
global_ngc_file_name = '1001'
global_ngc_file_name_export = ''
global_fusion_open_document_name = ''
send_gcode_to_lcnc_flag = False
ngrok_process_name = "ngrok.exe"
unit_to_cm_factors = {
    'm': 100,
    'mm': 0.1,
    'in': 2.54,
    'ft': 30.48,
    'cm': 1
}

try:
    from pureFlask_3JS_Server.flask_app \
        import flask_app, \
        cadMetaDataPath, \
        flaskKwargs, \
        flask_app_PORT, \
        lcnc_upload_url
    from flask import request
    import adsk, adsk.core, adsk.fusion, adsk.cam, traceback
    import threading, \
        json, \
        requests, \
        time, \
        os, \
        socket, \
        webbrowser, \
        psutil

    app = adsk.core.Application.get()
    ui = app.userInterface
except:
    if ui:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# import dependant global variables
global_output_folder = os.path.dirname(
    os.path.dirname(__file__)) + r'/flask_app/stl'
local_ip_addr = socket.gethostbyname(socket.gethostname())
localhost = "http://" + local_ip_addr + ":" + str(flask_app_PORT)
masked_local_host = "http://f360app.ngrok.io"


# flask related things
def shutdown_server_and_ngrok():
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func is None:
        raise RuntimeError
    shutdown_func()

    for procs in psutil.process_iter():
        if ngrok_process_name == procs.name():
            procs.kill()


@flask_app.route('/fusion360', methods=['POST'])
def fusion360():
    global flaskServerReplyBit, flask_server_to_3js_reply

    args = request.get_json()  # returns a dict
    app.fireCustomEvent(paramChangeCustomEventId, json.dumps(args))

    # wait till the model updates then reply to CAD server
    while not flaskServerReplyBit:
        pass
    flaskServerReplyBit = False

    # now send the file to LCNC
    return flask_server_to_3js_reply


@flask_app.route('/shutdown', methods=['POST'])
def stop_server():
    shutdown_server_and_ngrok()
    return "shutting down server"


@flask_app.route('/send_gcode_to_lcnc')
def send_gcode():
    global send_gcode_to_lcnc_flag, invalid_toolpath_flag
    try:
        if app.activeDocument.name != \
                global_fusion_open_document_name:
            return 'F360 active document incompatible \n ' \
                   'with current STL file or no param \n ' \
                   'change has still been made to model.'

        app.fireCustomEvent(toolpathGenerateCustomEventId,
                            json.dumps({'a': 0}))

        while not send_gcode_to_lcnc_flag:
            pass
        send_gcode_to_lcnc_flag = False

        # first check if invalid toolpath
        if invalid_toolpath_flag:
            invalid_toolpath_flag = None
            return "Invalid toolpath generated for operations.\n" \
                   "Please make sure geometry is valid."

        # first rename the g code file to be exported
        src = os.path.join(global_output_folder,
                           global_ngc_file_name + '.ngc')
        dst = os.path.join(global_output_folder,
                           global_ngc_file_name_export)

        if global_ngc_file_name_export \
                in os.listdir(global_output_folder):
            os.remove(dst)  # delete the already existing file

        os.rename(src, dst)

        # now open the renamed file and export it to LCNC
        with open(os.path.join(dst), 'r') as file:
            files = {'file': file}
            r = requests.post(lcnc_upload_url, files=files)
            return r.text  # reply to be sent back to 3js
        # edit for trial with pocketnc
        # with open(os.path.join(global_output_folder,
        #                        '1001.ngc'), 'r') as file:
        #     files = {'file': file}
        #     r = requests.post(lcnc_upload_url, files=files)
        #     return r.text  # reply to be sent back to 3js

    except Exception as msg:
        return str(msg)


@flask_app.route('/currentOpenDoc')
def getCurrentDoc():
    try:
        return str(app.activeDocument.name)

    except:
        if ui:
            ui.messageBox(
                'Failed:\n{}'.format(traceback.format_exc()))


# event handler to handle parameter change command from 3JS
class ParamChangeEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CustomEventArgs):
        try:
            # Make sure a command isn'server_thread running before
            # changes are made.
            global flaskServerReplyBit, \
                flask_server_to_3js_reply, \
                global_ngc_file_name_export, \
                global_fusion_open_document_name

            if ui.activeCommand != 'SelectCommand':
                ui.commandDefinitions \
                    .itemById('SelectCommand').execute()

            # change the workspace first and show the design ws
            ws = ui.workspaces.itemById('FusionSolidEnvironment')
            ws.activate()

            # Get the value from JSON data passed through the event.
            doc = app.activeDocument
            products = doc.products
            designProduct = products \
                .itemByProductType('DesignProductType')

            eventArgs = json.loads(args.additionalInfo)  # type: dict
            design = adsk.fusion.Design.cast(designProduct)
            unitsMgr = design.unitsManager
            defaultUnits = unitsMgr.defaultLengthUnits
            allComponents = design.allComponents
            rootComp = design.rootComponent
            fileName = None
            outJsonMetaData = {}

            # check if the file is the same as that one loaded in F360
            doc_name = eventArgs['filename'][0:-4]
            global_fusion_open_document_name = doc_name
            if app.activeDocument.name != doc_name:
                flask_server_to_3js_reply = \
                    'F360 active document ' \
                    'incompatible \n with current STL file'
                flaskServerReplyBit = True
                return

            tcomp = allComponents.itemByName('part')
            params = tcomp.modelParameters
            # first we need to have the model parameter names
            # arranged in the right sequence
            sequenced_param_list = []
            for param in params:
                if param.comment != 'no':
                    sequenced_param_list.append(str(param.name))

            for key in sequenced_param_list:
                newValue = float(eventArgs.get(key))
                outJsonMetaData[key] = newValue
                param = params.itemByName(key)
                if not param:
                    flask_server_to_3js_reply = \
                        "No model present in F360 \n" \
                        "Parameter change attempt failed"
                    flaskServerReplyBit = True
                    return
                param.value = newValue * unit_to_cm_factors.get(defaultUnits)
                # adsk.doEvents()  # guess this is async func
                # time.sleep(1)
            fileName = eventArgs.get('filename')

            global_ngc_file_name_export = \
                fileName[0:-4].replace(" ", "") + ".ngc"
            # Save the file as STL.
            exportMgr = adsk.fusion.ExportManager.cast(
                design.exportManager)
            stlOptions = exportMgr.createSTLExportOptions(tcomp)
            stlOptions.meshRefinement = adsk.fusion \
                .MeshRefinementSettings.MeshRefinementMedium
            stlOptions.filename = cadMetaDataPath + r"\\" \
                                  + fileName[0:-3] + 'stl'
            exportMgr.execute(stlOptions)

            # dump new metadata
            with open(cadMetaDataPath + r"\\"
                      + fileName[0:-4] + '_value' + '.json', 'w') as outfile:
                json.dump(outJsonMetaData, outfile)
            # allow the flask server to reply now
            flask_server_to_3js_reply = "F360 Param Change Successful"
            flaskServerReplyBit = True
        except:
            if ui:
                ui.messageBox(
                    'Failed:\n{}'.format(traceback.format_exc()))


# event handler to handle toolpath regenration request from 3JS
class RegenerateToolPathEventHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CustomEventArgs):
        global send_gcode_to_lcnc_flag, flask_server_to_3js_reply, invalid_toolpath_flag
        try:
            # change the workspace to CAM ws
            designWs = ui.workspaces.itemById(
                'FusionSolidEnvironment')
            camWs = ui.workspaces.itemById('CAMEnvironment')
            camWs.activate()

            # now regenerate all toolpaths
            doc = app.activeDocument
            products = doc.products
            camProduct = products.itemByProductType('CAMProductType')
            cam = adsk.cam.CAM.cast(camProduct)

            if not cam:
                ui.messageBox(
                    'No CAM data exists in the active document.')
                return

            # Verify that there are any setups.
            if cam.allOperations.count == 0:
                ui.messageBox(
                    'No CAM operations exist in the active document.')
                return

            future = cam.generateAllToolpaths(False)

            # create the progress dialog
            progress = ui.createProgressDialog()
            progress.isCancelButtonShown = False
            progress.show('ToolPath Generation Progress',
                          'Generating Toolpaths', 0, 10)

            n = 0
            start = time.time()
            while not future.isGenerationCompleted:
                # since toolpaths are calculated in parallel,
                # loop the progress bar while the toolpaths
                # are being generated but none are yet complete.
                # increment the progress value every .125 seconds.
                if time.time() - start > .125:
                    start = time.time()
                    n += 1
                    progress.progressValue = n
                    adsk.doEvents()
                if n > 10:
                    n = 0
            progress.hide()

            # now check if there are invalid toolpaths
            for oper in cam.allOperations:
                if not oper.isToolpathValid:
                    invalid_toolpath_flag = True
                    send_gcode_to_lcnc_flag = True
                    designWs.activate()
                    return

            # now post the NC files
            # specify the program name
            programName = global_ngc_file_name

            # specify the destination folder
            outputFolder = global_output_folder

            # specify a post configuration to use
            postConfig = cam.genericPostFolder + '/' + 'pocket nc.cps'

            # specify the NC file output units
            units = adsk.cam.PostOutputUnitOptions.DocumentUnitsOutput

            # create the POST input object
            postInput = adsk.cam.PostProcessInput.create(
                programName, postConfig, outputFolder, units)
            postInput.isOpenInEditor = False

            # post all toolpaths in the document
            cam.postProcessAll(postInput)
            designWs.activate()

            # wait for some time. probably saving file is async func
            time.sleep(5)
            send_gcode_to_lcnc_flag = True


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

            # start the flask server thread
            if not app_run_tracker:
                server_thread = threading.Thread(target=flask_app.run,
                                                 kwargs=flaskKwargs)
                server_thread.setDaemon(True)
                server_thread.start()

                # start the ngrok thread
                ngrok_thread = threading.Thread(
                    target=start_ngrok_process)
                ngrok_thread.setDaemon(True)
                ngrok_thread.start()

                app_run_tracker = not app_run_tracker
                ui.messageBox('FusionThreeJS Server started at -> '
                              '\n' + localhost +
                              '\n' + masked_local_host)
                webbrowser.open_new_tab(url=localhost)
            else:
                # stop the server on second press
                go_stop_server()
        except:
            if ui:
                ui.messageBox(
                    'Failed:\n{}'.format(traceback.format_exc()))


# all auxiliary utility functions below
# stops the server
def go_stop_server():
    global app_run_tracker
    # only stop server on repress of addin button
    # dont execute when user turning off addin via dialog
    r = requests.post(url=localhost + "/shutdown")
    # ui.messageBox(str(r.text))
    # turn to false again ready for next repress of addin button
    app_run_tracker = not app_run_tracker

    while server_thread.is_alive():
        # keep on looping until thread exits
        pass


# attaches the buttons to the toolbar
def attach_addin_button():
    # get the command definition
    commDefs = ui.commandDefinitions

    # add a button command def
    flaskThreeJSButtDef = commDefs.addButtonDefinition(
        'flaskThreeJSButtDefID',
        'Start CMaaS Server!',
        'starts a Flask server that serves a 3JS front end app '
        'controlling models in Fusion 360 in real time.',
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


# start ngrok process
def start_ngrok_process():
    try:
        os.system(
            'ngrok http --subdomain=f360app ' + str(flask_app_PORT))
    except:
        pass


def run(context):
    try:
        # Register the custom event and connect the handler
        global paramChangeCustomEvent, server_thread, \
            toolpathGenerateCustomEvent

        paramChangeCustomEvent = app.registerCustomEvent(
            paramChangeCustomEventId)

        toolpathGenerateCustomEvent = app.registerCustomEvent(
            toolpathGenerateCustomEventId)

        onThreadEvent = ParamChangeEventHandler()
        paramChangeCustomEvent.add(onThreadEvent)
        handlers.append(onThreadEvent)

        onThreadEvent2 = RegenerateToolPathEventHandler()
        toolpathGenerateCustomEvent.add(onThreadEvent2)
        handlers.append(onThreadEvent2)

        # add addin buttons to the toolbar
        attach_addin_button()

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

        paramChangeCustomEvent.remove(handlers[0])
        app.unregisterCustomEvent(paramChangeCustomEventId)

        toolpathGenerateCustomEvent.remove(handlers[1])
        app.unregisterCustomEvent(toolpathGenerateCustomEventId)

        # ui.messageBox('FusionThreeJS Addin Stopped. \n' +
        #               'Addon reload can only occur with next Fusion restart.')
        if app_run_tracker:  # is true when server is running
            # will stop server if it has not been already turned
            # off by the user
            go_stop_server()
    except:
        if ui:
            ui.messageBox(
                'Failed:\n{}'.format(traceback.format_exc()))
