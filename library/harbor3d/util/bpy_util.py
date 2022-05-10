import os
import glob
import sys
# try:
#         import bpy
# except:
#         pass

def subtract(base_file_name, subtract_file_name, export_file_name, path):
    pass
#     if not "bpy" in sys.modules:
#         return
#     base_mesh_name = base_file_name.split('.')[0].replace('_',' ').title()
#     subtract_mesh_name = subtract_file_name.split('.')[0].replace('_',' ').title()

#     while bpy.data.objects:
#         bpy.data.objects.remove(bpy.data.objects[0], do_unlink=True)
#     for item in bpy.data.meshes:
#         bpy.data.meshes.remove(item)

#     bpy.ops.import_mesh.stl(filepath=os.path.join(path, subtract_file_name))
#     bpy.ops.import_mesh.stl(filepath=os.path.join(path, base_file_name))
#     bpy.ops.object.modifier_add(type='BOOLEAN')
#     bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
#     bpy.context.object.modifiers["Boolean"].solver = 'EXACT'
#     bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[subtract_mesh_name]
#     bpy.ops.object.modifier_apply(modifier="Boolean")
#     bpy.data.meshes.remove(bpy.data.meshes[subtract_mesh_name])
#     bpy.ops.export_mesh.stl(filepath=os.path.join(path, export_file_name))

def union(file_names, export_file_name, path):
    pass
#     if not "bpy" in sys.modules:
#         return
#     for i in range(len(file_names)):
#         if i == 0:
#             while bpy.data.objects:
#                 bpy.data.objects.remove(bpy.data.objects[0], do_unlink=True)
#             for item in bpy.data.meshes:
#                 bpy.data.meshes.remove(item)
#             bpy.ops.import_mesh.stl(filepath=os.path.join(path, file_names[i]))
#         else:
#             bpy.ops.import_mesh.stl(filepath=os.path.join(path, file_names[i]))
#             bpy.ops.object.modifier_add(type='BOOLEAN')
#             bpy.context.object.modifiers["Boolean"].operation = 'UNION'
#             bpy.context.object.modifiers["Boolean"].solver = 'EXACT'
#             bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[file_names[i-1].split('.')[0].replace('_',' ').title()]
#             bpy.ops.object.modifier_apply(modifier="Boolean")
#             bpy.data.meshes.remove(bpy.data.meshes[file_names[i-1].split('.')[0].replace('_',' ').title()])
#     bpy.ops.export_mesh.stl(filepath=os.path.join(path, export_file_name))

def union_in_dir(dir_full_path, export_file_name_full_path):
    pass
#     if not "bpy" in sys.modules:
#         return
#     files = []
#     if os.path.exists(dir_full_path):
#         files = glob.glob(os.path.join(dir_full_path, "*.stl"))
#     for i in range(len(files)):
#         if i == 0:
#             while bpy.data.objects:
#                 bpy.data.objects.remove(bpy.data.objects[0], do_unlink=True)
#             for item in bpy.data.meshes:
#                 bpy.data.meshes.remove(item)
#             bpy.ops.import_mesh.stl(filepath=files[i])
#         else:
#             bpy.ops.import_mesh.stl(filepath=files[i])
#             bpy.ops.object.modifier_add(type='BOOLEAN')
#             bpy.context.object.modifiers["Boolean"].operation = 'UNION'
#             bpy.context.object.modifiers["Boolean"].solver = 'EXACT'
#             bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[full_path_to_obj_key(files[i-1])]
#             bpy.ops.object.modifier_apply(modifier="Boolean")
#             bpy.data.objects.remove(bpy.data.objects[full_path_to_obj_key(files[i-1])], do_unlink=True)
#     bpy.ops.export_mesh.stl(filepath=export_file_name_full_path, check_existing=False)

def filename_to_obj_key(filename):
    return filename.split('.')[0].replace('_',' ').title()

def full_path_to_obj_key(full_path):
    return filename_to_obj_key(full_path.split(os.sep)[-1])

#  Alternatively, you can copy and run below on Blender Script Console
# -------------------------------
# import os
# import glob
# import sys

# def union_in_dir(dir_full_path, export_file_name_full_path):
#     if not "bpy" in sys.modules:
#         return
#     files = []
#     if os.path.exists(dir_full_path):
#         files = glob.glob(os.path.join(dir_full_path, "*.stl"))
#     for i in range(len(files)):
#         if i == 0:
#             while bpy.data.objects:
#                 bpy.data.objects.remove(bpy.data.objects[0], do_unlink=True)
#             for item in bpy.data.meshes:
#                 bpy.data.meshes.remove(item)
#             bpy.ops.import_mesh.stl(filepath=files[i])
#         else:
#             bpy.ops.import_mesh.stl(filepath=files[i])
#             bpy.ops.object.modifier_add(type='BOOLEAN')
#             bpy.context.object.modifiers["Boolean"].operation = 'UNION'
#             bpy.context.object.modifiers["Boolean"].solver = 'EXACT'
#             bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[full_path_to_obj_key(files[i-1])]
#             bpy.ops.object.modifier_apply(modifier="Boolean")
#             bpy.data.objects.remove(bpy.data.objects[full_path_to_obj_key(files[i-1])], do_unlink=True)
#     bpy.ops.export_mesh.stl(filepath=export_file_name_full_path, check_existing=False)

# def filename_to_obj_key(filename):
#     return filename.split('.')[0].replace('_',' ').title()

# def full_path_to_obj_key(full_path):
#     return filename_to_obj_key(full_path.split(os.sep)[-1])

# union_in_dir(r"divided_folder_full_path", r"output_stl_full_path")
