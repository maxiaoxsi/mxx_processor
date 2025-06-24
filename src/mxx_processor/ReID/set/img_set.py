import random
# import torch
from .set_base import SetBase
from ..object import Img
from ..utils.util import select_matched_img, add_img_by_score
from tqdm import tqdm



class ImgSet(SetBase):
    def __init__(self) -> None:
        super().__init__()
        self._list_visible = []
        self._list_infrared = []
        self._imgList_drn_dict = {
            'front': [],
            'back': [],
            'left': [],
            'right': []
        }
        
    def add_img(self, img):
        """Add an image to the set, categorizing it as visible or infrared."""
        name_img = img.get_name_img()
        self.add_item(name_img, img)
        if img["is_visible"]:
            self._list_visible.append(img)
            if img["drn"] in self._imgList_drn_dict:
                self._imgList_drn_dict[img["drn"]].append(img)
        else:
            self._list_infrared.append(img)

    def get_img_ref(self, img_tgt, stage, is_discard):
        img_ref_list = []
        imgList_matched_dict = {}
        for drn in ["front", "left", "back", "right"]:
            img_list_matched = self.get_img_matched_list(
                drn = drn,
                img_tgt=img_tgt,
            )
            imgList_matched_dict[drn] = img_list_matched
            img_ref = select_matched_img(img_list_matched, is_discard)
            img_ref_list.append(img_ref)
        return img_ref_list, imgList_matched_dict

    def get_img_matched_list(self, drn, img_tgt):
        img_list = self._imgList_drn_dict[drn]
        img_matched_list = []
        for img in img_list:
            img.calib_score(img_tgt)
            add_img_by_score(img_matched_list, img)
        return img_matched_list

    def get_img_tgt(self, idx_img_tgt, stage):
        if isinstance(idx_img_tgt, str):
            return self[idx_img_tgt]
        img_list = self._list
        if stage == 3:
            img_list = self._list_infrared
        if len(img_list) == 0:
            raise Exception("img_set: img_list empty!")
        if idx_img_tgt < 0:
            idx_img_tgt = random.randint(0, len(img_list) - 1)
        idx_img_tgt = idx_img_tgt % len(img_list)
        return img_list[idx_img_tgt]
    
    def rename_key_annot(self, key, key_new):
        for img in tqdm(self._list):
            img.rename_key_annot(key, key_new)

    def remove_key_annot(self, key):
        for img in tqdm(self._list):
            img.remove_key_annot(key)
    