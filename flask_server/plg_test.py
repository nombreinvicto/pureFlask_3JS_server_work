import os

# p1 = os.path.dirname(os.path.dirname(__file__))
# p2 = p1 + r'/flask_app/stl'
#
# print(os.path.join(p2, '1001.nc'))
#
# global_ngc_file_name = '1001'
# global_output_folder = os.path.dirname(
#     os.path.dirname(__file__)) + r'/flask_app/stl'
#
# src = os.path.join(global_output_folder,
#                                global_ngc_file_name + '.nc')
# dst = os.path.join(global_output_folder,
#                                global_ngc_file_name + '.kutty')
# #
# # with open(
# #         os.path.join(global_output_folder,
# #                      global_ngc_file_name + '.nc'),
# #         'r') as file:
# #     f = file.readlines()
# #     print(f)
#
# if global_ngc_file_name+'.kutty' in os.listdir(global_output_folder):
#     os.remove(dst)
#     print("File existed")
#
# os.rename(src, dst)


ff = open("halamecha.txt", "w+")
ff.write("This is a line")
ff.close()
