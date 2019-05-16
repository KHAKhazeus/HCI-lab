#!flask/bin/python
################################################################################################################################
# ------------------------------------------------------------------------------------------------------------------------------
# This file implements the REST layer. It uses flask micro framework for server implementation. Calls from front end reaches 
# here as json and being branched out to each projects. Basic level of validation is also being done in this file. #                                                                                                                                  	       
# -------------------------------------------------------------------------------------------------------------------------------
################################################################################################################################
from flask import Flask, jsonify, abort, request, make_response, url_for, redirect, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename
import os
import shutil
import pickle
import numpy as np
from search import recommend, recommend_with_filter
from load_filter import getFilterDict
import tarfile
from datetime import datetime
from scipy import ndimage
from scipy.misc import imsave

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
from tensorflow.python.platform import gfile

app = Flask(__name__, template_folder="./static", static_folder="./static")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
auth = HTTPBasicAuth()
filterDict = getFilterDict()

def iter_files(rootDir):
    all_files = []
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            file_name = os.path.join(root, file)
            all_files.append(file_name)
        for dirname in dirs:
            iter_files(dirname)
    return all_files

img_files = iter_files('database/dataset')
num_images = len(img_files)

# ==============================================================================================================================
#                                                                                                                              
#    Loading the extracted feature vectors for image retrieval                                                                 
#                                                                          						        
#                                                                                                                              
# ==============================================================================================================================
extracted_features = np.zeros((num_images, 2048), dtype=np.float32)
with open('saved_features_recom.txt') as f:
    for i, line in enumerate(f):
        extracted_features[i, :] = line.split()
print("loaded extracted_features")


# ==============================================================================================================================
#                                                                                                                              
#  This function is used to do the image search/image retrieval
#                                                                                                                              
# ==============================================================================================================================
@app.route('/imgUpload', methods=['GET', 'POST'])
# def allowed_file(filename):
#    return '.' in filename and \
#           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_img():
    print("image upload")
    result = 'static/result'
    if not gfile.Exists(result):
        os.mkdir(result)
    shutil.rmtree(result)

    if request.method == 'POST' or request.method == 'GET':
        print(request.method)
        print(request.form.get("filterParam"))

        # check if the post request has the file part
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)


        if request.form.get("filterParam") == None or len(request.form.get("filterParam")) == 0:
            noFilter = True
        else:
            noFilter = False


        file = request.files['file']
        print(file.filename)
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '' or request.form.get("number") == None:
            print('No selected file')
            return redirect(request.url)
        images = {}
        if file:  # and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            inputloc = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            needList = request.form.get("filterParam")
            number = request.form.get("number")
            print(number)
            if needList.find("all") != -1:
                noFilter = True
            if (noFilter):
                recommend(inputloc, extracted_features, int(number))
            else:
                needList = request.form.get("filterParam")
                recommend_with_filter(inputloc, extracted_features, needList, int(number))
            # os.remove(inputloc)
            image_path = "/static/result"
            image_list = [os.path.join(image_path, file) for file in os.listdir(result)
                          if not file.startswith('.')]

                # for(image in image_list):
            baseId = 'image'
            nowNum = 0
            print(len(image_list))
            while nowNum < int(number):
                images[baseId + str(nowNum)] = image_list[nowNum]
                nowNum += 1

            with open('recom_distance.pickle', 'rb') as f:
                recom_distance = pickle.load(f)
            images['recom_distance'] = recom_distance
        return jsonify(images)


# ==============================================================================================================================
#                                                                                                                              
#                                           Main function                                                        	            #						     									       
#  				                                                                                                
# ==============================================================================================================================
@app.route("/")
def main():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
