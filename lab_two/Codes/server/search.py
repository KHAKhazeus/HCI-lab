################################################################################################################################
# This function implements the image search/retrieval .
# inputs: Input location of uploaded image, extracted vectors
# 
################################################################################################################################
import random
import tensorflow as tf
import numpy as np
import os
import scipy.io
import time
from datetime import datetime
from scipy import ndimage
from scipy.misc import imsave 
from scipy.spatial.distance import cosine
#import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
import pickle
from load_filter import getFilterDict
from PIL import Image
import gc
import os
from tempfile import TemporaryFile
from tensorflow.python.platform import gfile
BOTTLENECK_TENSOR_NAME = 'pool_3/_reshape:0'
BOTTLENECK_TENSOR_SIZE = 2048
MODEL_INPUT_WIDTH = 299
MODEL_INPUT_HEIGHT = 299
MODEL_INPUT_DEPTH = 3
JPEG_DATA_TENSOR_NAME = 'DecodeJpeg/contents:0'
RESIZED_INPUT_TENSOR_NAME = 'ResizeBilinear:0'
MAX_NUM_IMAGES_PER_CLASS = 2 ** 27 - 1  # ~134M

#show_neighbors(random.randint(0, len(extracted_features)), indices, neighbor_list)
filterDict = getFilterDict()
def get_all_similar(image_data, pred, pred_final, needList, number):
    acceptedId = []
    needString = needList
    needIDset = []
    for element in needString.split(','):
        needIDset.append(element)
    for word in needIDset:
        if word == "all":
            continue
        subList = filterDict[word]
        acceptedId += subList.tolist()
    acceptedId = list(map(lambda x: str(int(x)), acceptedId))
    print("total data", len(pred))
    print(image_data.shape)
    # for i in pred:
    # print(i.shape)
    # break
    os.mkdir('static/result')

    # cosine calculates the cosine distance, not similiarity. Hence no need to reverse list
    k_ind_distance = [cosine(image_data, pred_row) \
                      for ith_row, pred_row in enumerate(pred)]
    k_ind_distance = list(filter(lambda x: x != 0, k_ind_distance))
    top_k_ind = np.argsort(k_ind_distance)
    # print(top_k_ind)
    imgNumber = 0
    correspondingDict = {}
    print(len(top_k_ind), len(pred_final))
    for i, neighbor in enumerate(top_k_ind):
        baseleftId = "image"
        name = pred_final[neighbor]
        tokens = name.split("/")
        img_name = tokens[-1]
        if imgNumber == number:
            break
        id = img_name.split('.')[0]
        id = id[2:]
        if id in acceptedId:
            image = ndimage.imread(pred_final[neighbor])
            # timestr = datetime.now().strftime("%Y%m%d%H%M%S")
            # name= timestr+"."+str(i)
            print(img_name)
            name = 'static/result/' + img_name
            correspondingDict[name] = [str(imgNumber + 1) + ':  ', k_ind_distance[neighbor]]
            imsave(name, image)
            imgNumber += 1
    with open('recom_distance.pickle', 'wb') as f:
        pickle.dump(correspondingDict, f)
    print(imgNumber)

def get_top_k_similar(image_data, pred, pred_final, k):
        print("total data",len(pred))
        print(image_data.shape)
        #for i in pred:
        #print(i.shape)
                #break
        os.mkdir('static/result')
        
    # cosine calculates the cosine distance, not similiarity. Hence no need to reverse list
        k_ind_distance = [cosine(image_data, pred_row) \
                            for ith_row, pred_row in enumerate(pred)]
        k_ind_distance = list(filter(lambda x: x != 0, k_ind_distance))
        top_k_ind = np.argsort(k_ind_distance)[:k]
        print(top_k_ind)

        correspondingDict = {}
        for i, neighbor in enumerate(top_k_ind):

            image = ndimage.imread(pred_final[neighbor])
            #timestr = datetime.now().strftime("%Y%m%d%H%M%S")
            #name= timestr+"."+str(i)
            name = pred_final[neighbor]
            tokens = name.split("/")
            img_name = tokens[-1]
            print(img_name)
            name = 'static/result/'+img_name
            correspondingDict[name] = [str(i) + ':  ', k_ind_distance[neighbor]]
            imsave(name, image)
        with open('recom_distance.pickle', 'wb') as f:
            pickle.dump(correspondingDict, f)

                
def create_inception_graph():
  """"Creates a graph from saved GraphDef file and returns a Graph object.

  Returns:
    Graph holding the trained Inception network, and various tensors we'll be
    manipulating.
  """
  with tf.Session() as sess:
    model_filename = os.path.join(
        'imagenet', 'classify_image_graph_def.pb')
    with gfile.FastGFile(model_filename, 'rb') as f:
      graph_def = tf.GraphDef()
      graph_def.ParseFromString(f.read())
      bottleneck_tensor, jpeg_data_tensor, resized_input_tensor = (
          tf.import_graph_def(graph_def, name='', return_elements=[
              BOTTLENECK_TENSOR_NAME, JPEG_DATA_TENSOR_NAME,
              RESIZED_INPUT_TENSOR_NAME]))
  return sess.graph, bottleneck_tensor, jpeg_data_tensor, resized_input_tensor

def run_bottleneck_on_image(sess, image_data, image_data_tensor,
                            bottleneck_tensor):
 
    bottleneck_values = sess.run(
            bottleneck_tensor,
            {image_data_tensor: image_data})
    bottleneck_values = np.squeeze(bottleneck_values)
    return bottleneck_values

def recommend(imagePath, extracted_features, number):
        tf.reset_default_graph()

        config = tf.ConfigProto(
            device_count = {'GPU': 0}
        )

        sess = tf.Session(config=config)
        graph, bottleneck_tensor, jpeg_data_tensor, resized_image_tensor = (create_inception_graph())
        image_data = gfile.FastGFile(imagePath, 'rb').read()
        features = run_bottleneck_on_image(sess, image_data, jpeg_data_tensor, bottleneck_tensor)	

        with open('neighbor_list_recom.pickle','rb') as f:
            neighbor_list = pickle.load(f)
        print("loaded images")
        get_top_k_similar(features, extracted_features, neighbor_list, k=number)


def recommend_with_filter(imagePath, extracted_features, needList, number):
    tf.reset_default_graph()

    config = tf.ConfigProto(
        device_count={'GPU': 0}
    )

    sess = tf.Session(config=config)
    graph, bottleneck_tensor, jpeg_data_tensor, resized_image_tensor = (create_inception_graph())
    image_data = gfile.FastGFile(imagePath, 'rb').read()
    features = run_bottleneck_on_image(sess, image_data, jpeg_data_tensor, bottleneck_tensor)

    with open('neighbor_list_recom.pickle', 'rb') as f:
        neighbor_list = pickle.load(f)
    print("loaded images")
    get_all_similar(features, extracted_features, neighbor_list, needList, number)