from .set_base import SetBase
from ..object.video import Video

import random

class VideoSet(SetBase):
    def __init__(self) -> None:
        super().__init__()

    def add_img(self, img):
        id_video = img.get_id_video()
        if id_video in self._dict:
            video = self._dict[id_video]
            video.add_img(img)
        else:
            video = Video()
            video.add_img(img)
            self.add_item(id_video, video)

    def get_img_tgt_list(self, idx_video_tgt, idx_img_tgt, n_frame):
        if idx_video_tgt < 0:
            idx_video_tgt = random.randint(0, len(self._list) - 1)
        else:
            idx_video_tgt = idx_video_tgt % len(self._list)
        video = self._list[idx_video_tgt]
        return video.get_img_tgt_list(idx_img_tgt, n_frame)