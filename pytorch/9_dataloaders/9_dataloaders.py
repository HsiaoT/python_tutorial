# -*- coding: utf-8 -*-
# refer to https://pytorch.org/tutorials/beginner/data_loading_tutorial.html
"""
pytorch.ipynb

Automatically generated by Colaboratory.

"""
import pandas as pd
import numpy as np

# PART 1: read CSV and reshape annotations into 68x2 Array
# ==================================
landmarks_frame = pd.read_csv("/content/faces/face_landmarks.csv")
# print(landmarks_frame)
#                            image_name  part_0_x  ...  part_67_x  part_67_y
# 0                 0805personali01.jpg        27  ...         84        134
# ..                                ...       ...  ...        ...        ...
# 64                    matt-mathes.jpg        85  ...        141        235
# ..                                ...       ...  ...        ...        ...

n = 65
img_name = landmarks_frame.iloc[n,0]
landmarks = landmarks_frame.iloc[n, 1:]
landmarks = np.asarray(landmarks)
landmarks = landmarks.astype("float").reshape(-1,2)  # -1: value is inferred from the length of the array and remaining dimension

print('Image name: {}'.format(img_name))              # person-7.jpg
print('Landmarks shape: {}'.format(landmarks.shape))  # (68, 2)
print('First 4 Landmarks: {}'.format(landmarks[:4]))  # [[32. 65.], [33. 76.], [34. 86.], [34. 97.]]
print('x position of First 4 Landmarks: {}'.format(landmarks[:4, 0]))  # [32. 33. 34. 34.]


# PART 2: define a helper function to show an image with landmarks
# ==================================
import matplotlib.pyplot as plt
from skimage import io, transform
import os

def show_landmarks(image, landmarks):
    """Show image with landmarks"""
    plt.imshow(image)
    plt.scatter(landmarks[:, 0], landmarks[:, 1], s=10, marker='.', c='r') # s: marker size, c: color, 
    plt.pause(0.001)  # pause a bit so that plots are updated

plt.figure()
show_landmarks(io.imread(os.path.join("/content/faces/", img_name)),
               landmarks)

# PART 3: create a custom dataset class
# ==================================
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils
import torch

# create a custom dataset which inherit Dataset and override below methods:
# __len__: return the size of the dataset
# __getitem__: to support indexing (to get ith sample)

# read the csv in __init__ but leave the reading of images to __getitem__. 
# This is memory efficient


class FaceLandmarksDataset(Dataset):
  def __init__(self, csv_file, root_dir, transform=None):
    self.landmarks_frame = pd.read_csv(csv_file)
    self.root_dir = root_dir
    self.transform = transform

  def __len__(self):
    return len(self.landmarks_frame)
  
  def __getitem__(self, idx):
    if torch.is_tensor(idx):
      idx = idx.tolist()
    
    img_name = os.path.join(self.root_dir, self.landmarks_frame.iloc[idx, 0])
    image = io.imread(img_name)
    landmarks = self.landmarks_frame.iloc[idx,1:]
    landmarks = np.array([landmarks])
    landmarks = landmarks.astype("float").reshape(-1,2)
    sample = {"image": image, "landmarks": landmarks}

    if self.transform:
      sample = self.transform(sample)
    return sample

face_dataset = FaceLandmarksDataset(csv_file="/content/faces/face_landmarks.csv",
                                    root_dir="/content/faces/")
for i in range(3):
    sample = face_dataset[i]   # sample is a dict: {"image": image, "landmarks": landmarks}
    print("Sample#", i, "image shape:", sample['image'].shape, "landmarks shape:",sample['landmarks'].shape)
    show_landmarks(**sample)   # equal to: show_landmarks(sample['image'], sample["landmarks"])

# PART 4: define Transforms
# ==================================
# Rescale: resize the image
# RandomCrop: it's for data augmentation
# ToTensor: convert numpy image to torch image (swap axes)

class Rescale(object):
  def __init__(self, output_size):
    assert isinstance(output_size, (int, tuple))
    self.output_size = output_size
  
  def __call__(self, sample):
    image, landmarks = sample["image"], sample["landmarks"]

    h,w = image.shape[:2]
    if isinstance(self.output_size, int):           # int
      if h>w:
        new_h, new_w = self.output_size * h / w, self.output_size
      else:
        new_h, new_w = self.output_size, self.output_size * w / h
    else:                                           # tuple
      new_h, new_w = self.output_size
    
    new_h, new_w = int(new_h), int(new_w)           # Integer argument required for resize
    img = transform.resize(image, (new_h, new_w))
    landmarks = landmarks * [new_w/w, new_h/h]

    return {"image":img, "landmarks":landmarks}

class RandomCrop(object):
  def __init__(self, output_size):
    assert isinstance(output_size, (int, tuple))
    if isinstance(output_size, int):                # int
      self.output_size= (output_size, output_size)
    else:
      assert len(output_size) == 2                  # tuple
      self.output_size = output_size
  
  def __call__(self, sample):
    image, landmarks = sample["image"], sample["landmarks"]

    h,w = image.shape[:2]
    new_h, new_w = self.output_size

    top = np.random.randint(0, h-new_h)
    left = np.random.randint(0, w-new_w)

    image = image[top:top+new_h, left:left+new_w]
    landmarks = landmarks - [left, top]
    return {"image": image, "landmarks": landmarks}

class ToTensor(object):
  def __call__(self, sample):
    image, landmarks = sample["image"], sample["landmarks"]

    # numpy image: H x W x C
    # torch image: C x H x W
    image = image.transpose((2,0,1))
    return {"image": torch.from_numpy(image), 
            "landmarks": torch.from_numpy(landmarks)}

composed = transforms.Compose([Rescale(256),
                               RandomCrop(224)])

# sample = face_dataset[65]
# scale = Rescale(256)
# transformed_sample = scale(sample)
# show_landmarks(**transformed_sample)

# crop = RandomCrop(128)
# transformed_sample = crop(sample)
# show_landmarks(**transformed_sample)

# PART 5: iterating transforms through the dataset
# ==================================
transformed_dataset = FaceLandmarksDataset(csv_file="/content/faces/face_landmarks.csv",
                                    root_dir="/content/faces/",
                                    transform=transforms.Compose([
                                               Rescale(256),
                                               RandomCrop(224),
                                               ToTensor()
                                               ]))
i = 0
sample = transformed_dataset[i]
print(i, "image shape:", sample['image'].shape, "landmarks shape:",sample['landmarks'].shape)
# 0 image shape: torch.Size([3, 224, 224]) landmarks shape: torch.Size([68, 2])

# PART 6: dataloader
# ==================================

dataloader = DataLoader(transformed_dataset, batch_size=4, shuffle=True, num_workers=0)
# num_workers (int, optional): how many subprocesses to use for data 
# loading. 0 means that the data will be loaded in the main process. (default: 0)

for i_batch, sample_batched in enumerate(dataloader):
  print(i_batch, sample_batched['image'].size(), sample_batched['landmarks'].size())
  # 0 torch.Size([4, 3, 224, 224]) torch.Size([4, 68, 2])
  
  if i_batch == 2:
    break