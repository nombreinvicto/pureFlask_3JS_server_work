import sys
import os


## declare global variables

install_base_dir = r"C:\Users\mhasa\AppData\Local\Autodesk\webdeploy\production"
interpreter_dirs = os.listdir(install_base_dir)
lib_list = [
    'flask',
    'flask_cors',
    'requests',
    'psutil',
    'numpy',
    "pandas",
    "tensorflow==2.0.0",
    "nltk==3.5.0"
]

install_dir = None

# find out which dir Python is installed in
for interpreter_dir in interpreter_dirs:
    target_dir = os.path.join(install_base_dir, interpreter_dir, 'Python')

    if (os.path.lexists(target_dir)) and \
            "python.exe" in os.listdir(target_dir):
        install_dir = target_dir

# by now it has been decided which dir libs will be installed
if not install_dir:
    print(f'[INFO] Could not find fully qualified Python interpreter. '
          f'Exiting the system.....')
    sys.exit(-1)

# if everything goes well, install the libs
exec_line = f"{install_dir}" + "//python.exe " + "-m pip install " \
            + " ".join([lib for lib in lib_list])

try:
    print(f'[INFO] Attempting to install libraries ======> {lib_list} .....')
    os.system(exec_line)
    print(f'[INFO] Installation Completed Successfully.....')
    sys.exit()
except Exception as msg:
    print(f'[INFO] Installation Failed.....')
    print(msg)
    sys.exit(-1)
