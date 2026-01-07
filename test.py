import torch
print(f'GPU可用: {torch.cuda.is_available()}')
print(f'显卡: {torch.cuda.get_device_name(0)}')