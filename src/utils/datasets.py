
# TODO: For cleaner code, instead of writing datasets this way, writh transform objects, compose them and apply them.

import cv2
import math
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader

class ImageDataset():
    """
    A class for iterating over all images
    specified in a csv file.
    The path of csv file is passed to the constructor.
    """

    def __init__(self, csv_file, size=None, same=False):
        """
        Initialize dataset by reading a given csv file.
        This file is supposed to contain the path of an image
        """
        self.df = pd.read_csv(csv_file)
        self.size = size
        self.dest_ratio = size[1] / size[0]
        self.same = same

    def __len__(self):
        """
        Total number of images specified in the csv file.
        """
        return len(self.df)

    def __getitem__(self, index):
        """
        Open image of the given index and resize it.
        If needed, add black pixels to keep aspect ratio intact. 
        """
        image = self.df.iloc[index]
        path = image['path']
        img = cv2.imread(path)[:, :, ::-1]

        if self.same:
            img = cv2.resize(img, self.size)
            return img, path, img.shape[0], img.shape[1]
            
        h, w, _ = img.shape
        src_ratio = w/h
        new_h, new_w = None, None
        if src_ratio > self.dest_ratio:
            new_w = self.size[1]
            new_h = int(self.size[1] / src_ratio)
            img = cv2.resize(img, (new_w, new_h))
            pads1 = math.floor((self.size[0] - new_h)/2)
            pads2 = math.ceil((self.size[0] - new_h)/2)
            img = np.pad(img, ((pads1, pads2), (0, 0), (0, 0)), mode='constant', constant_values=0)
        else:
            new_h = self.size[0]
            new_w = int(self.size[0] * src_ratio)
            img = cv2.resize(img, (new_w, new_h))
            pads1 = math.floor((self.size[1] - new_w)/2)
            pads2 = math.ceil((self.size[1] - new_w)/2)
            img = np.pad(img, ((0, 0), (pads1, pads2), (0, 0)), mode='constant', constant_values=0)

        return img, path, new_h, new_w

class FaceDataset(Dataset):
    """
    A class for iterating over all faces
    specified in a csv file.
    The path of csv file is passed to the constructor. 
    """
    def __init__(self, csv_file, talk=False, face_size=(112, 112), margin=0):
        """
        Initialize dataset by reading a given csv file.
        This file is supposed to contain the bounding box
        of faces in images.
        """
        self.df = pd.read_csv(csv_file)
        self.talk = talk
        self.face_size = face_size
        self.margin = margin

    def __len__(self):
        """
        Total number of faces specified in the csv file.
        """
        return len(self.df)

    def __getitem__(self, index):
        """
        Open image of the given index and crop the face part
        according to the bounding box coordinates.
        """
        face = self.df.iloc[index]
        path = face['image_path']
        img = cv2.imread(path)[:, :, ::-1]
        x_from = max(face['x_from_per'] * img.shape[1] // 100 - self.margin, 0)
        x_to = min(face['x_to_per'] * img.shape[1] // 100 + self.margin, img.shape[1])
        y_from = max(face['y_from_per'] * img.shape[0] // 100 - self.margin, 0)
        y_to = min(face['y_to_per'] * img.shape[0] // 100 + self.margin, img.shape[1])
        face = img[y_from:y_to, x_from:x_to, :]
        face = cv2.resize(face, (self.face_size[0], self.face_size[0]))
        # plt.imshow(face)
        # plt.show()
        face = face.transpose((2, 0, 1))
        face = (face / 255).astype('float32')
        if self.talk:
            return face, path
        return face

class Pagination():

    def __init__(self, files, page_size=10):
        self.cum_sizes = [0]
        self.page_size = page_size
        self.files = files
        for file_name in files:
            self.cum_sizes.append(self.cum_sizes[-1] + int(file_name.split('_')[-2]))

    def total_pages(self):
        return math.ceil(self.cum_sizes[-1] / self.page_size)

    def page(self, idx):
        beginning = (idx - 1) * self.page_size
        file_number = 0
        for cum_size in self.cum_sizes[1:]:
            if beginning >= cum_size:
                file_number += 1
            else:
                break
        return self.get_data(file_number, beginning - self.cum_sizes[file_number], self.page_size)

    def get_data(self, file_number, index, num):
        df = pd.read_csv(self.files[file_number])
        if len(df) > index + num:
            return df.iloc[index:index+num]
        if len(self.files) == file_number + 1:
            return df.iloc[index:]
        remainning = num - (self.cum_sizes[file_number + 1] - self.cum_sizes[file_number] - index)
        return df.iloc[index:].append(self.get_data(file_number+1, 0, remainning), ignore_index=True)
        

def test_img_ds():
    path = './results/diff-ratios-paths/paths_1_9_.csv'
    ds = ImageDataset(path, size=(1080, 1920), same=False)
    dl = DataLoader(ds, batch_size=2, shuffle=False)
    for A in dl:
        print(A[1])
        break

def test_pagination():
    files = ['./results/lfw-paths/paths_{}_50_.csv'.format(i) for i in range(1, 265)] + [
        './results/lfw-paths/paths_265_33_.csv']
    pgn = Pagination(files, page_size=65)
    x = pgn.page(204)
    print(x)

if __name__ == "__main__":
    # test_img_ds()
    test_pagination()
