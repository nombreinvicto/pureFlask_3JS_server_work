import os

p1 = os.path.dirname(os.path.dirname(__file__))
p2 = p1 + r'/flask_app/stl'

print(os.path.join(p2, '1001.nc'))
