import os
import pathlib

def renameImages(datasetDir, train_batch_size, output_name):

    images = os.listdir(datasetDir)

    i = 1
    j = 1
    group = 1

    for image in images:

        ext = pathlib.Path(image).suffix.strip().lower()

        if ext != '.jpg':

            raise ValueError('Only jpg images are allowed')

        os.rename(f"{datasetDir}/{image}", f"{datasetDir}/group-{group}-{i}-{output_name}-{j}{ext}")  

        if(i == train_batch_size):

            i = 1

            group = group + 1
        
        else:

            i = i + 1

        j = j + 1