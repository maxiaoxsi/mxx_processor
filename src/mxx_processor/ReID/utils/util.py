import importlib
import random

def get_utils(id_dataset):
    current_package = __name__.rsplit('.', 1)[0]
    # print(current_package)
    # exit()
    module_name = f".{id_dataset}"
    module = importlib.import_module(module_name, package=current_package)
    return module

def add_img_by_score(img_matched_list, img):
    for (i, img_i) in enumerate(img_matched_list):
        if img.get_score() > img_i.get_score():
            img_matched_list.insert(i, img)
            return 
    img_matched_list.append(img)
    return

def select_matched_img(img_list, is_discard):
    if len(img_list) == 0:
        return None
    img = img_list[0]
    if is_discard:
        if random.random() < 0.2:
            img = None
    return img

def get_mark_direction(a, b):
        return (a * a) / (a * a + b * b)


def init_direction(smplx_para):
    import numpy as np

    root_pose = smplx_para['smplx_root_pose'][0]
    from scipy.spatial.transform import Rotation
    r = Rotation.from_rotvec(root_pose)
    rotation_matrix = r.as_matrix()
    vector_direction = np.array([0, 0, 1])
    vector_direction = np.dot(rotation_matrix, vector_direction)
    
    if vector_direction[2] < 0 and np.abs(vector_direction[2]) > np.abs(vector_direction[0]):
        direction = "front"
    elif vector_direction[2] > 0 and np.abs(vector_direction[2]) > np.abs(vector_direction[0]):
        direction = "back"
    elif vector_direction[0] < 0 and np.abs(vector_direction[0]) > np.abs(vector_direction[2]):
        direction = "left"
    elif vector_direction[0] > 0 and np.abs(vector_direction[0]) > np.abs(vector_direction[2]):
        direction = "right"
    
    if direction in ['front', 'back']:
        mark_direction = str(get_mark_direction(vector_direction[2], vector_direction[0]))
    elif direction in ['left', 'right']:
        mark_direction = str(get_mark_direction(vector_direction[0], vector_direction[2]))
    else:
        mark_direction = str(0)

    vector_direction = [str(item) for item in vector_direction]
    return direction, vector_direction, mark_direction