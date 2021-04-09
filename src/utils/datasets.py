import cv2
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
from torch.utils.data import Dataset

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
        Open image of the given index and crop the face part
        according to the bounding box coordinates.
        """
        image = self.df.iloc[index]
        path = image['path']
        img = cv2.imread(path)[:, :, ::-1]

        if self.same:
            img = cv2.resize(img, self.size)
            img = img.transpose((2, 0, 1))
            img = (img / 255).astype('float32')
            return img

        frame = np.zeros((self.size[0], self.size[1], 3))
        h, w, _ = img.shape
        src_ratio = w/h

        if src_ratio > self.dest_ratio:
            new_w = self.size[1]
            new_h = int(self.size[1] / src_ratio)
            img = cv2.resize(img, (new_w, new_h))
            s = int((self.size[0] - new_h)/2)
            e = s + new_h
            frame[s:e, :, :] = img
        else:
            new_h = self.size[0]
            new_w = int(self.size[0] * src_ratio)
            img = cv2.resize(img, (new_w, new_h))
            s = int((self.size[1] - new_w)/2)
            e = s + new_w
            frame[:, s:e, :] = img

        frame = (frame / 255).astype('float32')
        frame = frame.transpose((2, 0, 1))
        return frame

class FaceDataset(Dataset):
    """
    A class for iterating over all faces
    specified in a csv file.
    The path of csv file is passed to the constructor. 
    """
    def __init__(self, csv_file):
        """
        Initialize dataset by reading a given csv file.
        This file is supposed to contain the bounding box
        of faces in images.
        """
        self.df = pd.read_csv(csv_file)

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
        x_from = max(face['x_from_per'] * img.shape[1] // 100, 0)
        x_to = min(face['x_to_per'] * img.shape[1] // 100, img.shape[1])
        y_from = max(face['y_from_per'] * img.shape[0] // 100, 0)
        y_to = min(face['y_to_per'] * img.shape[0] // 100, img.shape[1])
        face = img[y_from:y_to, x_from:x_to, :]
        face = cv2.resize(face, (112, 112))
        face = face.transpose((2, 0, 1))
        face = (face / 255).astype('float32')
        return face

def test_img_ds():

    path = './results/diff-ratios-paths/paths_1_9_.csv'
    ds = ImageDataset(path, size=(1080, 1920), same=False)
    for i, _ in enumerate(ds):
        if i == 3:
            break

if __name__ == "__main__":
    test_img_ds()
