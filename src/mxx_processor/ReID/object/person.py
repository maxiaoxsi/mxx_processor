from .img import Img
from ..set.img_set import ImgSet
from ..set.video_set import VideoSet
import random

'''
person in ReID dataset.
person._id: <str> match ReID dataset like 0001, 0002
img_set: <list: <object.img>>, img for person
video_set: <list: <object.video>>, video for person
'''
class Person:
    def __init__(self, id) -> None:
        self._id = id
        self._img_set = ImgSet()
        self._video_set = VideoSet()

    def get_id(self):
        return self._id

    def add_img(self, img:Img):
        """Add an image to the person's set."""
        if img.is_smplx():
            self._img_set.add_img(img)
        if img.is_video():
            self._video_set.add_img(img)

    def is_img_set_empty(self):
        return len(self._img_set) == 0

    def get_img_set_keys(self):
        return self._img_set.keys()

    def get_sample(self, idx_video_tgt, idx_img_tgt, n_frame, stage):
        """Get a sample from the person's imgSet or videoSet"""
        """stage1: img, text: visible infrared"""
        """stage2: video"""
        """stage3: infrared only"""
        if stage in [1, 3]:
            img_ref_list, img_tgt_list = self._get_imgList_from_img_set(
                stage=stage, 
                idx_img_tgt=idx_img_tgt
            )
        if stage in [2]:
            img_ref_list, img_tgt_list = self._get_imgList_from_video_set(
                stage=stage, 
                idx_video_tgt=idx_video_tgt,
                idx_img_tgt=idx_img_tgt,
                n_frame=n_frame
            )
        img_ref_pil_list = Img.get_img_pil_list(img_ref_list, "reid")
        img_tgt_pil_list = Img.get_img_pil_list(img_tgt_list, "reid")
        # imgList_depth_pil = Img.get_imgList_pil(img_ref_list, "depth")
        img_smplx_pil_list = Img.get_img_pil_list(img_tgt_list, "smplx_guidance")
        img_mask_pil_list = Img.get_img_pil_list(img_tgt_list, "mask")
        img_foreground_pil_list = Img.get_img_pil_list(img_tgt_list, "foreground")
        img_background_pil_list = Img.get_img_pil_list(img_tgt_list, "background")
        text_ref = img_tgt_list[0].get_text_ref()
        text_tgt = img_tgt_list[0].get_text_tgt()
        dscrpt_ref_list = Img.get_dscrpt_list(img_ref_list)
        dscrpt_tgt_list = Img.get_dscrpt_list(img_tgt_list)
        return {
            'img_ref_pil_list':img_ref_pil_list,
            'img_tgt_pil_list':img_tgt_pil_list,
            'img_smplx_pil_list':img_smplx_pil_list,
            'img_mask_pil_list':img_mask_pil_list,
            'img_foreground_pil_list':img_foreground_pil_list,
            'img_background_pil_list':img_background_pil_list,
            'text_ref_list':[text_ref],
            'text_tgt_list':[text_tgt],
            'dscrpt_ref_list':dscrpt_ref_list,
            'dscrpt_tgt_list':dscrpt_tgt_list
        }       

    def _get_imgList_from_img_set(self, stage, idx_img_tgt, is_discard):
        img_tgt = self._img_set.get_img_tgt(
            stage=stage,
            idx_img_tgt=idx_img_tgt,
        )

        img_ref_list, imgList_matched_dict = self._img_set.get_img_ref(
            stage=stage, 
            img_tgt=img_tgt, 
            is_discard=is_discard
        )
        
        img_tgt_list = [img_tgt]
        return img_ref_list, img_tgt_list, imgList_matched_dict

    def _get_imgList_from_video_set(self, stage, idx_video_tgt, idx_img_tgt, n_frame):
        img_ref_list = self._img_set.get_img_ref_list(stage=stage)
        img_tgt_list = self._video_set.get_img_tgt_list(
            idx_video_tgt=idx_video_tgt,
            idx_img_tgt=idx_img_tgt,
            n_frame=n_frame
        )
        return img_ref_list, img_tgt_list
    
    def __getitem__(self, idx):
        return self._img_set[idx]
    
    def get_video(self, idx):
        return self._video_set[idx]

























    

    
    
        
    
    def _get_imgList_stage2(self, num_img_ref = 4, idx_tgt = -1, nframe = -1):
        img_ref_list = self._imgSet.get_img_ref_list(num_img_ref=num_img_ref, stage=1)
        img_tgt_list = self._videoSet.get_img_tgt_list(idx_tgt=idx_tgt, nframe=nframe)
        if random.random() < 0.5:
            img_ref_list.append(img_tgt_list[0])
        else:
            img_ref_list.append(None)
        return img_ref_list, img_tgt_list

    def _get_imgList_stage3(self, num_img_ref = 4, idx_tgt = -1):
        img_ref_list = self._imgSet.get_img_ref_list(
            stage=3,
            num_img_ref=num_img_ref,
        )
        img_tgt_list = self._imgSet.get_img_tgt_list(
            stage = 3,
            idx_tgt = idx_tgt,
        )
        return img_ref_list, img_tgt_list
        