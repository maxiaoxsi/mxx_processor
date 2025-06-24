import os
import numpy as np
from .dataset import ReIDDataset
from torch.utils.data import ConcatDataset

class ReIDProcessor:
    def __init__(
        self, 
        path_cfg_list=None,
        dir_reid=None,
        dir_smplx=None,
        dir_dscrpt=None,
        dir_mask=None,
        dir_background=None,
        dir_foreground=None,
    ):
        dataset_list = []
        if path_cfg_list is not None:
            for path_cfg in path_cfg_list:
                dataset_list.append(ReIDDataset(path_cfg))
        dataset = ConcatDataset(dataset_list)
        print(len(dataset))
        


if __name__ == '__main__':
    processor = ReIDProcessor(
        dir_reid='/machangxiao/datasets/ReID/MSMT17/bounding_box_train',
        dir_smplx='/machangxiao/datasets/ReID_smpl/withyolo/MSMT17/MSMT17_withyolo/train'
    )

                

