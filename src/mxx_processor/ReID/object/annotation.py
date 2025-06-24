import os
import yaml
import warnings
import numpy as np
from PIL import Image

'''
annotation for img in ReID datset
_keys: key for img.
    <list: <str>>
    ex: upper_clothing, bottoms, glasses, etc
_path_annot:
_path_log: log file
    <str>
    ex: './log.txt'
_annot: loaded from path_annot
    <dict: {<str>:<str>}>
'''
class Annotation:
    def __init__(self, dir_annot, path_annot, img, logger, is_check) -> None:
        self._keys = []
        self._init_keys()
        self._path_annot = path_annot
        self._img = img
        self._logger = logger
        self._annot = {}
        self._load_annot(dir_annot)

    def _init_keys(self):
        self._keys_bool = [
            "is_backpack", "is_shoulder_bag", "is_hand_carried", 
            "is_visible",
        ]
        
        self._keys_str = [
            "upper", "bottoms", 
            "width", "height", 
            "drn", "vec_drn", "mark_drn",
        ]
        self._keys = self._keys_bool + self._keys_str

    def _load_annot(self, dir_annot):
        if os.path.exists(self._path_annot):
            with open(self._path_annot, 'r') as f:
                self._annot = yaml.safe_load(f)
        else:
            if not os.path.exists(dir_annot):
                os.makedirs(dir_annot)
                self._save_annot()
            warnings.warn("mxx object annotation: annotation yaml file not exists, we have ceate empty one")
    
    def _save_annot(self):
        with open(self._path_annot, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                self._annot, 
                f, 
                allow_unicode=True, 
                default_flow_style=False,
                sort_keys=False 
            )

    def rename_key(self, key, key_new):
        if key not in self._annot:
            name_reid = self._img.get_name
            self._logger.warning(f"{name_reid} rename_key key:{key} miss")
            return
        item = self._annot[key]
        self._annot.pop(key, None)
        self._annot[key_new] = item 
        self._save_annot()

    def remove_key(self, key):
        
        if key not in self._annot:
            return
        self._annot.pop(key, None)
        self._save_annot()

    def __getitem__(self, idx):
        idx_smplx = f"{idx}_smplx"
        idx_vl = f"{idx}_vl"
        if idx in self._annot:
            annot = self._annot[idx]
        elif idx_smplx in self._annot:
            annot = self._annot[idx_smplx]
        elif idx_vl in self._annot:
            annot = self._annot[idx_vl]
        else:
            annot = "key error!"
            # raise Exception(f"annotation: search key:{idx} not exists in yaml file!")
        if idx in self._keys_str:
            return annot
        elif idx in self._keys_bool:
            if 'yes' in annot:
                return True
            if 'no' in annot:
                return False
            name_reid = self._img.get_name
            self._logger.warning(f"{name_reid} __getitem__ bool key get other annot:{idx}, {annot}")
            return True

    def keys(self):
        return self._keys
    
    # '''
    # use _check_ methods to init or maintain yaml file
    # '''
    # def _check_annot(self):
    #     self._check_keys()

    # def _check_keys(self):
    #     keys = []
    #     for key in self._keys:
    #         keys.append(key)
    #         keys.append(f"{key}_vl")
    #         keys.append(f"{key}_smplx")
    #     for key in self._annot:
    #         if key not in keys:
    #             self._annot.pop(key, None)
    
    # def _check_img(self, path_reid):
    #     path_reid = self.get_path("reid")
    #     img = Image.open(path_reid)
    #     self._annot["img_width"], self._annot["img_height"] = img.size

    # def _check_direction_smplx(self, path_smplx_paras):
    #     if not os.path.exists(path_smplx_paras):
    #         self._annot['direction_smplx'] = 'none'
    #         self._annot['mark_direction_smplx'] = "0"
    #         self._annot['vector_direction_smplx'] = ["0", "0", "1"]
    #     else:
    #         with np.load(path_smplx_paras) as smplx_para:
    #             from ..utils import init_direction
    #             (
    #                 self._annot['direction_smplx'], 
    #                 self._annot['vector_direction_smplx'], 
    #                 self._annot['mark_direction_smplx']
    #             ) = init_direction(smplx_para)