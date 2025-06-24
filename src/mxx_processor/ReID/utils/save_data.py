import os
import torchvision.transforms as transforms
import shutil
from PIL import Image
import yaml

def save_item(dataset, id_person, idx_video_tgt, idx_img_tgt, dir_base):
    person = dataset._person_set[id_person]
    sample = person.get_sample(
        idx_video_tgt=idx_video_tgt,
        idx_img_tgt=idx_img_tgt,
        n_frame=dataset.get_n_frame(),
        stage=dataset.get_stage()
    )
    img_ref_pil_list = sample["img_ref_pil_list"]
    img_tgt_pil_list = sample["img_tgt_pil_list"]
    img_smplx_pil_list = sample["img_smplx_pil_list"]
    img_mask_pil_list = sample["img_mask_pil_list"]
    img_foreground_pil_list = sample["img_foreground_pil_list"]
    img_background_pil_list = sample["img_background_pil_list"]
    text_ref_list = sample["text_ref_list"]
    text_tgt_list = sample["text_tgt_list"]
    dscrpt_ref_list = sample["dscrpt_ref_list"]
    dscrpt_tgt_list = sample["dscrpt_tgt_list"]
    save_img_pil(img_ref_pil_list, dscrpt_ref_list, dir_base, "reid")
    save_img_pil(img_tgt_pil_list, dscrpt_tgt_list, dir_base, "tgt")
    save_img_pil(img_smplx_pil_list, dscrpt_tgt_list, dir_base, "smplx")
    save_img_pil(img_mask_pil_list, dscrpt_tgt_list, dir_base, "mask")
    save_img_pil(img_background_pil_list, dscrpt_tgt_list, dir_base, "background")
    save_img_pil(img_foreground_pil_list, dscrpt_tgt_list, dir_base, "foreground")
    save_dscrpt_list(dscrpt_ref_list, dir_base, "dscrpt_ref")
    save_dscrpt_list(dscrpt_tgt_list, dir_base, "dscrpt_tgt")


def save_sample(sample, dir_base, is_norm):
        img_ref_tensor = sample['img_ref_tensor']
        img_reid_tensor = sample['img_reid_tensor']
        img_tgt_tensor = sample['img_tgt_tensor']
        img_smplx_tensor = sample['img_smplx_tensor']
        img_background_tensor = sample['img_background_tensor']
        text_ref_list = sample['text_ref_list']
        text_tgt_list = sample['text_tgt_list']
        save_img_tensor(img_ref_tensor, dir_base, "ref", True, is_norm)
        save_img_tensor(img_reid_tensor, dir_base, "reid", True, is_norm)
        save_img_tensor(img_tgt_tensor, dir_base, "tgt", True, is_norm)
        save_img_tensor(img_ref_tensor, dir_base, "ref", True, is_norm)
        save_img_tensor(img_smplx_tensor, dir_base, "smplx", True, is_norm)
        save_img_tensor(img_background_tensor, dir_base, "background", True, is_norm)
        save_text_list(text_ref_list, dir_base, 'ref', False)
        save_text_list(text_tgt_list, dir_base, 'tgt', False)



def save_text_list(text_list, dir_base, dir_sub, is_rm):
    dir_save = os.path.join(dir_base, dir_sub)
    if os.path.exists(dir_save) and is_rm:
        shutil.rmtree(dir_save)
    for (i, text) in enumerate(text_list):
        path_save = os.path.join(dir_save, f"text_{i}.txt")
        with open(path_save, 'w') as f:
            f.write(text)

def save_dscrpt_list(dscrpt_list, dir_base, dir_sub, is_clean=True):
    dir_save = os.path.join(dir_base, dir_sub)
    if not os.path.exists(dir_save):
        os.makedirs(dir_save)
    if is_clean:
        import shutil
        shutil.rmtree(dir_save)
        os.makedirs(dir_save)
    for i, dscrpt in enumerate(dscrpt_list):
        path_save = os.path.join(dir_save, f"dscrpt_{i}.yaml")
        with open(path_save, 'w', encoding='utf-8') as f:
            yaml.dump(
                dscrpt, 
                f, 
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False 
            )

def save_img_pil(img_pil_list, dscrpt_list, dir_base, dir_sub, is_clean=True):
    dir_save = os.path.join(dir_base, dir_sub)
    if not os.path.exists(dir_save):
        os.makedirs(dir_save)
    if is_clean:
        import shutil
        shutil.rmtree(dir_save)
        os.makedirs(dir_save)
        
    for (i, (img_pil, dscrpt)) in enumerate(zip(img_pil_list, dscrpt_list)):
        path_img = os.path.join(dir_save, f"img_{i}.jpg")
        if img_pil == None:
            if dscrpt is not None and "width" in dscrpt and "height" in dscrpt:
                width = dscrpt["width"]
                height = dscrpt["height"]
            else:
                width = 64
                height = 128
            img_pil = Image.new('RGB', (width, height), color='black')
        img_pil.save(path_img)

def save_img_tensor(img_tensor, dir_base, dir_sub, is_rm, is_norm):
    dir_save = os.path.join(dir_base, dir_sub)
    if os.path.exists(dir_save) and is_rm:
        shutil.rmtree(dir_save)
    if not os.path.exists(dir_save):
        os.makedirs(dir_save)    
    if (len(img_tensor.shape) == 3):
        img_tensor = img_tensor.squeeze(0)
    if is_norm:
        to_pil = transforms.Compose([
            transforms.Normalize(mean=[-1], std=[2]),
            # transforms.Lambda(lambda x: x[:, :256, :256]),
            transforms.ToPILImage(),
        ])
    else:
        to_pil = transforms.ToPILImage()
    for i in range(img_tensor.shape[0]):
        img = img_tensor[i]
        img_pil = to_pil(img)
        path_img = os.path.join(dir_save, f"img_{i}.jpg")
        img_pil.save(path_img)

