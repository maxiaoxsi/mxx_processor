from mxx_processor import ReIDProcessor, ReIDDataset

if __name__ == '__main__':
    dataset_market = ReIDDataset(
        path_cfg='./humandataset_market_train.yaml',
        img_size_pad=(512, 512),
        stage=1,             
    )
    processor = ReIDProcessor(dataset=dataset_market)
    # processor.remove_key_annot("bottoms_vl")
    # processor.remove_key_annot("upper_vl")
    # processor.rename_key_annot("style_bottoms_vl", "bottoms_vl")
    processor.rename_key_annot("hand_carried_vl", "is_hand_carried_vl")


    # processor.remove_key_annot("color_upper_vlstyle_bottoms_vl")
    # processor.rename_key_annot("direction", "direction_smplx")
    # processor.rename_key_annot("riding_vl", "is_riding_vl")
    # processor.rename_key_annot("vec_drn_smplx", "vec_drn_smplx")
    # processor.rename_key_annot("mark_drn_smplx", "mark_drn_smplx")
    # processor.rename_key_annot("direction_smplx", "drn_smplx")
    # processor.rename_key_annot("direction_vl", "drn_vl")




