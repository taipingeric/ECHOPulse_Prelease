# import sys
# import os
# import torch
# import torch.distributed as dist
# import torch.multiprocessing as mp
# from torch.nn.parallel import DistributedDataParallel as DDP
# from torch.utils.data.distributed import DistributedSampler

# # GPU 설정
# SELECTED_GPUS = [0, 1]
# os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, SELECTED_GPUS))

# parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
# sys.path.append(parent_dir)

# from phenaki_pytorch.cvivit import CViViT
# from phenaki_pytorch.phenaki_pytorch_ekg import MaskGit, Phenaki
# from phenaki_pytorch.phenaki_trainer_ekg import PhenakiTrainer

# def setup(rank, world_size):
#     os.environ['MASTER_ADDR'] = 'localhost'
#     os.environ["MASTER_PORT"] = "12345"

#     if torch.cuda.is_available():
#         backend = "nccl"
#     else:
#         backend = "gloo"

#     dist.init_process_group(backend=backend, rank=rank, world_size=world_size)
    
#     torch.cuda.set_device(rank)
#     torch.manual_seed(42)
#     torch.cuda.manual_seed_all(42)

#     print(f"Setup completed for rank {rank}. Backend: {backend}")

# def cleanup():
#     dist.destroy_process_group()

# def main(rank, world_size):
    
#     setup(rank, world_size)
    
#     print(f"Process {rank}: Setup completed")
    
#     cvivit = CViViT(
#         dim=512,
#         codebook_size=8192,
#         image_size=128,
#         patch_size=8,
#         local_vgg=True,
#         wandb_mode='disabled',
#         temporal_patch_size=2,
#         spatial_depth=4,
#         temporal_depth=4,
#         dim_head=64,
#         heads=8,
#         ff_mult=4,
#         commit_loss_w=1.,
#         gen_loss_w=1.,
#         perceptual_loss_w=1.,
#         i3d_loss_w=1.,
#         recon_loss_w=10.,
#         use_discr=0,
#         gp_weight=10
#     ).to(rank)

#     cvivit.load('/home/local/PARTNERS/sk1064/project/EchoHub/phenaki/CVIVIT_results/ckpt_accelerate_3500/pytorch_model.bin')
    
#     maskgit = MaskGit(
#         num_tokens = 8192,
#         max_seq_len = 2048,
#         dim = 512,
#         dim_context = 768,
#         depth = 6,
#     ).to(rank)

#     phenaki = Phenaki(
#         cvivit = cvivit,
#         maskgit = maskgit
#     ).to(rank)

#     trainer = PhenakiTrainer(
#         phenaki = phenaki,
#         folder =  '/raid/home/CAMCA/sk1064/us/cleaned/subset_apical/',
#         train_on_images = False,
#         batch_size = 10,
#         grad_accum_every = 1,
#         num_frames = 11,
#         sample_num_frames = None,
#         train_lr = 1e-4,
#         train_num_steps = 1_000_000,
#         max_grad_norm = None,
#         ema_update_every = 10,
#         ema_decay = 0.995,
#         adam_betas = (0.9, 0.99),
#         wd = 0,
#         save_and_sample_every = 500,
#         num_samples = 25,
#         results_folder = '/home/local/PARTNERS/sk1064/project/EchoHub/phenaki/ckpt/phenaki_ekg/',
#         split_batches = True,
#         convert_image_to = None,
#         sample_texts_file_path = '/home/local/PARTNERS/sk1064/project/EchoHub/phenaki/RT_instructions.txt',
#         losses_file_folder = '/home/local/PARTNERS/sk1064/project/EchoHub/phenaki/phenaki_ekg_results',
#         rank = rank,
#         world_size = world_size
#     )

#     # PhenakiTrainer 클래스에 wrap_distributed 메서드가 없다면 삭제
#     trainer.wrap_distributed()
    
#     trainer.train()

#     cleanup()

# if __name__ == "__main__":
#     world_size = len(SELECTED_GPUS)
#     print("WORLD SIZE", world_size)
#     mp.spawn(main, args=(world_size,), nprocs=world_size, join=True)
    
import sys
import os

# os.environ["CUDA_VISIBLE_DEVICES"] = "7"  # GPU 1만 사용하도록 설정
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# Add the parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
sys.path.append(parent_dir)

import torch
from phenaki_pytorch.cvivit import CViViT
from phenaki_pytorch.cvivit_trainer import CViViTTrainer
from phenaki_pytorch.phenaki_pytorch_ekg import MaskGit, Phenaki
from phenaki_pytorch.phenaki_trainer_ekg import PhenakiTrainer

from torch.nn import DataParallel

cvivit = CViViT(
    dim=512,  # embedding size
    codebook_size=8192,  # codebook size # original 65536 # re
    image_size=128,  # H,W
    patch_size=8,  # spatial patch size
    local_vgg=True,
    wandb_mode='disabled',
    temporal_patch_size=2,  # temporal patch size
    spatial_depth=4,  # nb of layers in the spatial transfo
    temporal_depth=4,  # nb of layers in the temporal transfo
    dim_head=64,  # hidden size in transfo
    heads=8,  # nb of heads for multi head transfo
    ff_mult=4,  # 32 * 64 = 2048 MLP size in transfo out
    commit_loss_w=1.,  # commit loss weight
    gen_loss_w=1.,  # generator loss weight
    perceptual_loss_w=1.,  # vgg loss weight
    i3d_loss_w=1.,  # i3d loss weight
    recon_loss_w=10.,  # reconstruction loss weight
    use_discr=0,  # whether to use a stylegan loss or not
    gp_weight=10
    
)

# load pretrained natural image dataset
cvivit.load('/raid/home/CAMCA/yl463/Video/CVIVIT/pytorch_model.bin')
# cvivit.load('/raid/home/CAMCA/yl463/Video/results/ckpt_accelerate_20/pytorch_model.bin')


maskgit = MaskGit(
    num_tokens = 8192,  #set the same number with the codebook_size
    max_seq_len = 2048,
    dim = 512,
    dim_context = 768,
    depth = 6,
)

phenaki = Phenaki(
    cvivit = cvivit,
    maskgit = maskgit
).cuda()

trainer = PhenakiTrainer(
    phenaki = phenaki,
    folder =  '',
    train_on_images = False,
    batch_size = 50,
    grad_accum_every = 1,
    num_frames = 11,
    sample_num_frames = None,
    train_lr = 1e-4,
    train_num_steps = 1000_002,
    max_grad_norm = None,
    ema_update_every = 10,
    ema_decay = 0.995,
    adam_betas = (0.9, 0.99),
    wd = 0,
    save_and_sample_every = 10000,
    num_samples = 25,
    results_folder = '',
    amp = True,
    fp16 = True,
    split_batches = True,
    convert_image_to = None,
    sample_texts_file_path = '',  # path to a text file with video captions, delimited by newline
    losses_file_folder = '',
)

# trainin step2 
trainer.train()

