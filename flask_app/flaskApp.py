from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import os, json, time


cadMetaDataPath = os.path.dirname(__file__) + r'\stl'
#lcnc_upload_url = "http://pocketncsim.ngrok.io/lcnc_upload"
lcnc_upload_url = "http://152.1.58.35:3296/lcnc_upload"
flask_app = Flask(__name__)
CORS(flask_app)
flask_app_PORT = 6923
flask_app.jinja_env.globals['timestamp'] = int(time.time())
flaskKwargs = {'debug': False, 'host': '0.0.0.0',
               'port': flask_app_PORT}


@flask_app.route('/')
def get_home_page():
    return render_template('index.html', title='Fusion 3JS Server')


@flask_app.route('/public')
def get_static_assets():
    fileList = os.listdir(cadMetaDataPath)
    return json.dumps(fileList)


@flask_app.route('/get_stl_file/<file_name>')
def get_stl_data(file_name):
    res = send_from_directory(cadMetaDataPath, file_name)
    res.cache_control.max_age = 1
    return res


@flask_app.route('/cadmeta/<file_name>')
def get_cad_meta_data(file_name):
    min_max_jsonFileName = file_name[0:-4] + '_min_max' + '.json'
    value_jsonFileName = file_name[0:-4] + '_value' + '.json'

    try:
        with open(cadMetaDataPath + '\\' + min_max_jsonFileName,
                  'r') as f1:
            c1 = f1.read()
            j1 = json.loads(c1)

        with open(cadMetaDataPath + '\\' + value_jsonFileName,
                  'r') as f2:
            c2 = f2.read()
            j2 = json.loads(c2)

        for key, val in j2.items():
            j1[key]["currentValue"] = val

        return json.dumps(j1)
    except Exception as msg:
        return json.dumps(str(msg))
