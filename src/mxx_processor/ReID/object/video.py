from .img import Img
import random


class Video:
    def __init__(self) -> None:
        self._img_list = []
        self._img_dict = {}

    def add_img(self, img: Img):
        idx_frame = int(img.get_idx_frame())
        self._img_dict[idx_frame] = img

    def _init_img_list(self):
        for i in range(len(self._img_dict)):
            if i + 1 in self._img_dict:
                self._img_list.append(self._img_dict[i + 1])


    def get_img_tgt_list(self, idx_img_tgt, n_frame):
        if len(self._img_list) == 0:
            self._init_img_list()
        if len(self._img_list) == 0:
            print("img_list empty")
            return []
        if n_frame < 0:
            n_frame = 10
        if idx_img_tgt > 0:
            frame_st = idx_img_tgt % len(self._img_list)
        else:
            if n_frame < len(self._img_list):
                frame_st = random.randint(0, len(self._img_list) - n_frame)
            else:
                frame_st = 0
        ans = self._img_list[frame_st: frame_st + n_frame]
        for i in range(n_frame - len(ans)):
            ans.append(self._img_list[-1])
        return ans
        