# do the necessary imports

import os
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

# find the cad part types
cwd = r"C:\Users\mhasa\AppData\Roaming\Autodesk\Autodesk Fusion 360\MyScripts\PureFlask_3JS_server\flask_app"
cad_dir = f"{cwd}\\static\\cad_repo"
part_types = str(os.listdir(cad_dir))
