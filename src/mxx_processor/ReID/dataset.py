import os
import time
import random
import yaml
from PIL import Image
from tqdm import tqdm
from torch.utils.data import Dataset
import numpy as np
import torchvision.transforms as transforms
import torchvision.transforms.functional as F
from .utils.save_data import save_img_pil, save_dscrpt_list, save_img_tensor, save_text_list

from .utils import get_utils
from .set import PersonSet, ImgSet
from .object import Person, Img
from ..log.logger import logger

class ReIDDataset(Dataset):
    def __init__(
        self,
        path_cfg, # yaml
        path_log="./log.txt",
        is_save=True,
        is_check_annot=False,
        width_scale=(1, 1),
        height_scale=(1, 1),
        img_size_pad=(512, 512),
        stage = 1,
        n_frame = 10,
        n_img = ('', ''),
    ) -> None:
        self._img_size_pad=img_size_pad
        self._stage=stage
        self._n_frame = n_frame
        self._logger = logger(path_log=path_log)

        cfg = self._load_cfg(path_cfg)
        self._dir = cfg['dir']
        self._id = cfg["id_dataset"]
        self._visible = cfg["visible"]

        self._init_transforms(width_scale, height_scale)

        path_cache = cfg["path_cache"]

        # load cache or init cache and save
        if path_cache is None or not os.path.exists(path_cache):
            cache = self._init_cache()
            if path_cache is not None and is_save:
                import pickle
                with open(path_cache, 'wb') as f:
                    pickle.dump(cache, f)
        else:
            import pickle
            with open(path_cache, 'rb') as f:
                cache = pickle.load(f)

        # init person_set, img_set with cache
        self._person_set = PersonSet()
        self._img_set = ImgSet()

        n_img_st = 0 if n_img[0] == '' else n_img[0]
        n_img_ed = len(cache['img']) if n_img[1] == '' else n_img[1]
        if n_img_st >= 0 and n_img_ed > 0 and n_img_st <= n_img_ed:
            cache['img'] = cache['img'][n_img_st:n_img_ed]
        
        self._init_set(cache, is_check_annot=is_check_annot)
        print(f"load {self.get_num_img()} imgs from dataset:{self._id}")

    def __len__(self):
        return len(self._person_set)

    def __getitem__(self, idx):
        return self.get_item(
            id_person=idx,
            idx_img_tgt=-1,
            idx_video_tgt=-1,
        )

    def get_item(self, id_person, idx_img_tgt, idx_video_tgt):
        person = self._person_set[id_person]
        if not isinstance(person, Person):
            return None
        sample = person.get_sample(
            idx_img_tgt=idx_img_tgt,
            idx_video_tgt=idx_video_tgt,
            n_frame=self._n_frame,
            stage=self._stage
        )
        seed = int(time.time())
        img_ref_tensor = self.get_img_tensor(
            img_pil_list=sample['img_ref_pil_list'], 
            type_transforms="ref", 
            img_size=self._img_size_pad,
            seed=seed, 
        )
        img_reid_tensor = self.get_img_tensor(
            img_pil_list=sample['img_ref_pil_list'], 
            type_transforms="reid", 
            img_size=(128, 256)
        )
        seed = int(time.time())
        img_tgt_tensor = self.get_img_tensor(
            img_pil_list=sample['img_tgt_pil_list'], 
            type_transforms="tgt", 
            seed=seed, 
            img_size=self._img_size_pad
        )
        img_smplx_tensor = self.get_img_tensor(
            img_pil_list=sample['img_smplx_pil_list'], 
            type_transforms="smplx", 
            seed=seed, 
            img_size=self._img_size_pad
        )
        img_background_tensor = self.get_img_tensor(
            img_pil_list=sample['img_background_pil_list'], 
            type_transforms="background", 
            seed=seed, 
            img_size=self._img_size_pad
        )
        return  {
            "img_ref_tensor": img_ref_tensor,
            "img_reid_tensor": img_reid_tensor,
            "img_tgt_tensor": img_tgt_tensor,
            'img_smplx_tensor': img_smplx_tensor,
            "img_background_tensor": img_background_tensor,
            'text_ref_list': sample['text_ref_list'],
            'text_tgt_list': sample['text_tgt_list'],
        }
    
    def get_img_tensor(self, img_pil_list, type_transforms, img_size, seed = None):
        if type_transforms in ["ref", "tgt", "background", "smplx"]:
            img_tensor = Img.get_img_tensor(
                img_pil_list=img_pil_list,
                transforms_img=self._transforms_aug_norm_pad, 
                img_size=img_size,
                seed=seed,
            )
        elif type_transforms == "reid":
            img_tensor = Img.get_img_tensor(
                img_pil_list=img_pil_list, 
                transforms_img=self._transforms_reid, 
                img_size=img_size,
                seed=seed,
            )
        # elif type_transforms == "":
        #     img_tensor = Img.get_img_tensor(
        #         img_pil_list=img_pil_list,
        #         transforms_img=self._transforms_aug_pad,
        #         img_size=img_size,
        #         seed=seed,
        #     )
        else:
            raise ValueError(f"Unknown type_transforms: {type_transforms}")
        return img_tensor

    def _load_cfg(self, path_cfg):
        if not os.path.exists(path_cfg):
            raise Exception("dataset cfg file not found!")
        with open(path_cfg, 'r') as f:
            cfg = yaml.safe_load(f)
        if 'dir' not in cfg:
            raise Exception("dir not in dataset cfg file!")
        self._check_cfg_dir(cfg['dir']['reid'])
        self._check_cfg_dir(cfg['dir']['smplx'])
        self._check_cfg_dir(cfg['dir']['annot'])
        self._check_cfg_dir(cfg['dir']['mask'])
        return cfg

    def _check_cfg_dir(self, dir):
        if not os.path.exists(dir):
            raise Exception(f"dir:{dir} not exists!")

    def _analyse_id_dataset(self, dir_reid):
        if "market" in dir_reid.lower():
            return "market"
        if "mars" in dir_reid.lower():
            return "market"
        if "msmt17" in dir_reid.lower():
            return "msmt17"

    def _init_transforms(self, width_scale, height_scale):
        class Scale2D:
            def __init__(self, width, height, interpolation=Image.BILINEAR):
                self.width = width
                self.height = height
                self.interpolation = interpolation
            def __call__(self, img):
                w, h = img.size
                if h == self.height and w == self.width:
                    return img
                return img.resize((self.width, self.height), self.interpolation)

        class Scale1D:
            def __init__(self, size_tgt, interpolation=Image.BILINEAR):
                self._size_tgt = size_tgt
                self._interpolation = interpolation
            
            def __call__(self, img):
                w, h = img.size
                if w > h:
                    width_tgt = self._size_tgt
                    height_tgt = int(self._size_tgt / w * h)
                else:
                    width_tgt = int(self._size_tgt / h * w)
                    height_tgt = self._size_tgt
                return img.resize((width_tgt, height_tgt), self._interpolation)

        class RandomCrop:
            def __init__(self, width_scale, height_scale):
                self._width_scale = width_scale
                self._height_scale = height_scale

            def _getPoint(self, scale, w):
                w_min, w_max = int(w * scale[0]), int(w * scale[1])
                w_target = random.randint(w_min, w_max)
                w_start = random.randint(0, w - w_target)
                w_end = w_start + w_target
                return w_start, w_end
            
            def __call__(self, img):
                w, h = img.size
                w_start, w_end = self._getPoint(self._width_scale, w)
                h_start, h_end = self._getPoint(self._height_scale, h)
                return img.crop((w_start, h_start, w_end, h_end))

        class PadToBottomRight:
            def __init__(self, target_size, fill=0):
                self.target_size = target_size  # 目标尺寸 (W, H)
                self.fill = fill  # 填充值

            def __call__(self, img):
                """
                img: Tensor of shape [C, H, W]
                Returns: Padded Tensor of shape [C, target_H, target_W]
                """
                _, h, w = img.shape
                pad_w = max(self.target_size[0] - w, 0)  # 右侧需填充的宽度
                pad_h = max(self.target_size[1] - h, 0)  # 底部需填充的高度
                padding = (0, 0, pad_w, pad_h)  
                img_padded = F.pad(img, padding, fill=self.fill)
                return img_padded

        self._transforms_aug_norm_pad = transforms.Compose(
            [
                RandomCrop(width_scale, height_scale),
                Scale1D(self._img_size_pad[0]),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5]),
                PadToBottomRight(target_size=self._img_size_pad, fill=0),
            ]
        )

        self._transforms_aug_pad = transforms.Compose(
            [
                RandomCrop(width_scale, height_scale),
                Scale1D(self._img_size_pad[0]),
                transforms.ToTensor(),
                PadToBottomRight(target_size=self._img_size_pad, fill=0),
            ]
        )

        self._transforms_reid=transforms.Compose(
            [
                Scale2D(128, 256),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5],std=[0.5]),
                # transforms.Normalize(mean=[0.485, 0.456, 0.406],std=[0.229, 0.224, 0.225]),
            ]
        )

    def _init_cache(self):
        cache = {'img':[]}
        imgLoader = get_utils(id_dataset=self._id)
        for root, dirs, files in os.walk(self._dir["reid"]):
            dir_sub = root[len(self._dir["reid"]) + 1:]
            for file in files:
                if file.endswith(('.jpg', '.png')):
                    name_file = file.split('/')[-1]
                    suff_file = name_file.split('.')[-1]
                    name_file = name_file.split('.')[0]
                    id_person = imgLoader.load_id_person(name_file, dir_sub)
                    if not id_person.isdigit() or int(id_person) <= 0:
                        continue
                    idx_frame = imgLoader.load_idx_frame(name_file)
                    id_video = imgLoader.load_id_video(name_file)
                    
                    path_smplx_guid = os.path.join(self._dir["smplx"], 
                        dir_sub, 'guidance', f'{name_file}.{suff_file}')
                    has_smplx = os.path.exists(path_smplx_guid)
                    img_dict = {
                        'dir':dir_sub,
                        'name':name_file,
                        'suff':suff_file,
                        'id_person':id_person,
                        'has_smplx':has_smplx,
                        'idx_frame':idx_frame,
                        'id_video':id_video,
                    }
                    cache['img'].append(img_dict)
        return cache

    def _init_set(self, cache, is_check_annot):
        print(f"load dataset: {self._id}")
        for img_dict in tqdm(cache['img']):
            id_person = img_dict['id_person']
            if id_person not in self._person_set:
                person = Person(id_person)
                self._person_set.add_person(person)
            else:
                person = self._person_set[id_person]
            img = Img(
                dir_sub=img_dict["dir"],
                name=img_dict["name"],
                suff=img_dict["suff"],
                is_smplx=img_dict["has_smplx"],
                id_video=img_dict["id_video"],
                idx_frame=img_dict["idx_frame"],
                dataset=self,
                person=person,
                logger=self._logger,
                is_check_annot=is_check_annot,
            )
            person.add_img(img)
            self._img_set.add_item(f"{img_dict['name']}.{img_dict['suff']}", img)
        self._person_set.check_empty_item()

    def get_n_frame(self):
        return self._n_frame
    
    def get_stage(self):
        return self._stage

    def get_dir(self, type_tgt):
        if type_tgt in self._dir:
            return self._dir[type_tgt]
        type_tgt_sub = type_tgt.split('_')[0]
        if type_tgt_sub in self._dir:
            return self._dir[type_tgt_sub]
        raise Exception(f"dataset:unkown dir type:{type_tgt}")

    def get_visible(self):
        return self._visible

    def get_num_img(self):
        return len(self._img_set)
    
    def get_person_keys(self):
        return self._person_set.keys()
    
    def get_person(self, id_person):
        return self._person_set[id_person]
    
    def get_n_img(self):
        return len(self._img_set)
    
    def rename_key_annot(self, key, key_new):
        self._img_set.rename_key_annot(key, key_new)

    def remove_key_annot(self, key):
        self._img_set.remove_key_annot(key)