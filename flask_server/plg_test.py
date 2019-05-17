import os

p1 = os.path.dirname(os.path.dirname(__file__))
p2 = p1 + r'/flask_app/stl'

print(os.path.join(p2, '1001.nc'))

global_ngc_file_name = '1001'
global_output_folder = os.path.dirname(
    os.path.dirname(__file__)) + r'/flask_app/stl'

c = os.path.join(global_output_folder,
                               global_ngc_file_name + '.nc')

with open(
        os.path.join(global_output_folder,
                     global_ngc_file_name + '.nc'),
        'r') as file:
    f = file.readlines()
    print(f)