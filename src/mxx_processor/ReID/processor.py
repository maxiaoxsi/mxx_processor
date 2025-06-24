import os
import numpy as np
from .dataset import ReIDDataset


class ReIDProcessor:
    def __init__(
        self, 
        dataset_list=None,
        dataset:ReIDDataset=None,
    ):
        if dataset_list is not None:
            self._dataset_list = dataset_list
        else:
            self._dataset_list = []
        if dataset is not None:
            self._dataset_list.append(dataset)

    def rename_key_annot(self, key, key_new):
        for dataset in self._dataset_list:
            dataset.rename_key_annot(key, key_new)
    
    def remove_key_annot(self, key):
        for dataset in self._dataset_list:
            dataset.remove_key_annot(key)


                

