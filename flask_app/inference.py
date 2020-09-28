# do the necessary imports

import os
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

pad_max_length = 4
part_categories = ['bearing', 'bolt', 'collet', 'spring', 'sprocket']

# find the cad part types
cwd = r"C:\Users\mhasa\AppData\Roaming\Autodesk\Autodesk Fusion 360\MyScripts\PureFlask_3JS_server\flask_app"
save_path = r"C:\Users\mhasa\AppData\Roaming\Autodesk\Autodesk Fusion 360\MyScripts\PureFlask_3JS_server\flask_app\nlp_model"

cad_dir = f"{cwd}\\static\\cad_repo"
part_types = str(os.listdir(cad_dir))

# load the keras trained model
with open(f'{save_path}//tokenizer.pickle', 'rb') as handle:
    loaded_tokenizer = pickle.load(handle)

# load the keras model
loaded_model = load_model(f"{save_path}//nlp_model.h5")
