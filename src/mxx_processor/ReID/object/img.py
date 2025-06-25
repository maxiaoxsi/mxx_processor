import torch
import os
import random
from PIL import Image
import yaml
import os
import warnings
import numpy as np
from .annotation import Annotation


class Img:
    def __init__(self, dir_sub, name, suff, is_smplx, id_video, 
                    idx_frame, dataset, person, logger, is_check_annot) -> None:
        self._dir = dir_sub
        self._name = name
        self._suff = suff
        self._id_video = id_video
        self._idx_frame = idx_frame
        self._is_smplx = is_smplx
        self._dataset = dataset
        self._person = person
        self._logger = logger
        self._annot = Annotation(
            dir_annot=self.get_dir('annot'),
            path_annot=self.get_path('annot'), 
            img=self,
            logger=self._logger, 
            is_check=is_check_annot,
        )

    def __getitem__(self, idx):
        return self._annot[idx]

    def get_dir(self, tgt):
        dir_base = self._dataset.get_dir(tgt)
        if '_' in tgt:
            dir_insert = tgt.split('_')[-1]
        else:
            dir_insert = ''
        return os.path.join(dir_base, self._dir, dir_insert)

    def get_path(self, tgt):
        dir_tgt = self.get_dir(tgt)
        if tgt == 'annot':
            suff = 'yaml'
        elif tgt == 'smplx_smplx':
            suff = 'npz'
        else:
            suff = self._suff
        name = f"{self._name}.{suff}"
        return os.path.join(dir_tgt, name)

    def get_name(self):
        return self._name

    def get_name_img(self):
        return f"{self._name}.{self._suff}"

    def get_img_pil(self, type):
        """Return the image as a PIL Image object."""
        path = self.get_path(type)
        if path is None:
            return None
        if not os.path.exists(path):
            return None
        return Image.open(path)

    def get_id_video(self):
        return self._id_video
    
    def get_idx_frame(self):
        return self._idx_frame

    def get_score(self):
        return self._score 

    '''
    is smplx img exists
    '''
    def is_smplx(self):
        return self._is_smplx
    
    '''
    is img belong to a video
    '''
    def is_video(self):
        return self._idx_frame is not None


    '''
    riding has to be the same
    '''
    def is_match_tgt(self, img_tgt):
        if self['riding'] != img_tgt['riding']:
            return False
        if self['hand-carried'] != img_tgt['hand-carried']:
            return False
        self._refresh_score(img_tgt)
        return True

    
    def calib_score(self, img_tgt):
        self._score = float(self['mark_drn'] or 0.0)
        if self['riding'] == img_tgt['riding']:
            self._score = self._score + 2
        if self['hand-carried'] == img_tgt['hand-carried']:
            self._score = self._score + 2
        return
    
    def keys(self):
        return self._annot.keys()
    
    def get_key_bool_list(self):
        return self._annot.get_key_bool_list()
    
    def get_key_str_list(self):
        return self._annot.get_key_str_list()

    def rename_key_annot(self, key, key_new):
        self._annot.rename_key(key, key_new)

    def remove_key_annot(self, key):
        self._annot.remove_key(key)
















    @staticmethod
    def get_dscrpt_list(img_list):
        dscrpt_list = []
        for img in img_list:
            if img is not None:
                dscrpt = img._get_dscrpt()
            else:
                dscrpt = {}
            dscrpt_list.append(dscrpt)
        return dscrpt_list
            
    @staticmethod
    def get_img_pil_list(img_list, type_img):
        return [
            img.get_img_pil(type_img) if img is not None else None
            for img in img_list 
        ]

    @staticmethod
    def get_img_tensor(img_pil_list, transforms_img, img_size, seed = None):
        if seed is not None:
            random.seed(seed)
        w, h = img_size
        img_tensor_list = [
            transforms_img(img) 
            if img is not None
            else torch.zeros([3, h, w])
            for img in img_pil_list
        ]
        for idx, img_tensor in enumerate(img_tensor_list):
            if torch.all(img_tensor == img_tensor.flatten()[0]):
                img_tensor_list[idx] = torch.zeros_like(img_tensor)
        return torch.stack(img_tensor_list, dim=0)













    def get_text_upper_cloth(self):
        text_color_upper_cloth = self.get_dscrpt_item('color_upper_vl')
        text_upper_cloth = self.get_dscrpt_item('upper_vl')
        if text_color_upper_cloth in text_upper_cloth:
            return text_upper_cloth
        return f"{text_color_upper_cloth} {text_upper_cloth}"

    def get_text_bottom(self):
        text_color_bottom = self.get_dscrpt_item('color_bottoms_vl')
        text_bottom = self.get_dscrpt_item('bottoms_vl')
        if text_color_bottom in text_bottom:
            return text_bottom
        if text_bottom in text_color_bottom:
            return text_color_bottom
        return f"{text_color_bottom} {text_bottom}"

    def get_text_backpack(self):
        if self.is_match_dscrpt('backpack_vl'):
            return f", with a backpack"
        return ""

    def get_text_hand_carried(self):
        if self.is_match_dscrpt('hand-carried_vl'):
            return f", with a hand-carried item"
        return ""

    def get_text_drn(self):
        if self.is_match_dscrpt('riding_vl'):
            text_walk = 'riding'
        else:
            text_walk = 'walking'
        drn = self._dscrpt['drn']
        if drn == 'none':
            drn = self._dscrpt['drn_vl']
        if drn == 'left':
            return f', {text_walk} from right to left'
        if drn == 'right':
            return f', {text_walk} from left to right'
        if drn == 'front':
            return f', {text_walk} toward the camera'
        if drn == 'back':
            return f', {text_walk} away from the camera'
        return f', {text_walk} {drn}'

    def get_text_tgt(self):
        text_upper_cloth = self.get_text_upper_cloth()
        text_bottom = self.get_text_bottom()
        text_backpack = self.get_text_backpack()
        text_hand_carried = self.get_text_hand_carried()
        text_drn = self.get_text_drn()
        text = f'a photo of a people wearing {text_upper_cloth} and {text_bottom}{text_backpack}{text_hand_carried}{text_drn}.'
        # a photo of a people wearing red t-shirt and dark shorts, with a backpack, walking from left to right
        return text

    def get_text_ref(self):
        text_upper_cloth = self.get_text_upper_cloth()
        text_bottom = self.get_text_bottom()
        text_backpack = self.get_text_backpack()
        text_hand_carried = self.get_text_hand_carried()
        text = f'a photo of a people wearing {text_upper_cloth} and {text_bottom}{text_backpack}{text_hand_carried}.'
        # a photo of a people wearing red t-shirt and dark shorts, with a backpack,
        return text  
    

    def _match_color(self, color, color_tgt, cloth, cloth_tgt):
        if color in cloth_tgt:
            self._score = self._score + 1
        elif color_tgt in cloth:
            self._score = self._score + 1
        elif color in color_tgt:
            self._score = self._score + 1
        elif color_tgt in color:
            self._score = self._score + 1