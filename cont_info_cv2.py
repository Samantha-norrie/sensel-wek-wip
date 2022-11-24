#TODO Clean up libraries
import argparse
import sys
import json
import os
sys.path.append('../../sensel-lib-wrappers/sensel-lib-python')
import sensel
import binascii
import threading
import time
import cv2
import numpy
import matplotlib.pyplot as plt
import os
import pickle
import PIL
from pythonosc import udp_client
import socket, select
from time import gmtime, strftime
from random import randint

def openSensel():
    handle = None
    (error, device_list) = sensel.getDeviceList()
    if device_list.num_devices != 0:
        (error, handle) = sensel.openDeviceByID(device_list.devices[0].idx)
    return handle

def initFrame():
    error = sensel.setFrameContent(handle, sensel.FRAME_CONTENT_PRESSURE_MASK)
    (error, frame) = sensel.allocateFrameData(handle)
    error = sensel.startScanning(handle)
    return frame
    
def scanFrame(frame, info):
    error = sensel.readSensor(handle)
    #(error, num_frames) = sensel.getNumAvailableFrames(handle)

    error = sensel.getFrame(handle, frame)

    #Create nested array of force data
    new_frame_scan = []

    row= []
    for n in range(info.num_rows*info.num_cols):
        if n %info.num_cols-1 == 0:
            new_frame_scan.append(row.copy())
            row = []
        force = frame.force_array[n]
        row.append(force)

    return new_frame_scan

def create_image_from_nested_arr(arr):

    found_force = False

    #TODO Incorporate RGBA instead of RGB
    im = PIL.Image.new(mode="RGB", size=(info.num_cols, info.num_rows))

    #string_message = ""
    for j in range(0, len(arr)):
        for k in range(0, len(arr[j])):
            if arr[j][k] <= 1:
                im.putpixel((k, j), (255,255,255))
                #string_message += " "
            else:

                found_force = True
                im.putpixel((k, j), (0,0,255))
                #string_message += "1"
                #print("in here")

    if found_force:
    #im.show()
    #im_arr = numpy.array(im)
    #result, imgencode = cv2.imencode('.jpg', im_arr)
    #data = numpy.array(imgencode)

    #message = im.tobytes()
    #print(message)
    #return message
        im.save("new_image_1.png")
        return "new_image_1.png"
    return None

def get_values_with_cv2(im_name):
    print("in")
    im = cv2.imread(im_name)
    # orig_image = cv2.imread(im)
    image_gray  = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    image_rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    press_data = cv2.CascadeClassifier('cascade.xml')

    found_presses = press_data.detectMultiScale(image_gray, minSize=(5, 5))
    amount_found = len(found_presses)
    x_value = 0
    y_value = 0
    if amount_found != 0:
        for (x, y, width, height) in found_presses:
            print("x", x)
            print("y", y)
            x_value = x
            y_value = y
            print("width", width)
            print("height", height)
            print("done")
            cv2.rectangle(image_rgb, (x, y), (x + height, y + width),
            (0, 255, 0), 5)
    #image_rgb.show()
    window_name = 'Image'
    # if amount_found >= 1:
    if x_value != 0 and y_value != 0:
        return [x_value, y_value]
    return None
    # plt.subplot(1, 1, 1)
    # plt.imshow(image_rgb)
    # plt.show()
    #     time.sleep(2)
    #     plt.close()
    #cv2.imshow(window_name, image_rgb)
    #os.remove(im_name)

    # for i in range(0, 100):
    #     if not os.path.exists("new_image2" + str(i) +".png"):

    #         image_rgb.save("new_image2" + str(i) + ".png")
if __name__ == "__main__":

    # Set up ports
    HOST = '127.0.0.1'
    PORT = 6448

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=HOST,
    help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=PORT,
    help="The port the OSC server is listening on")
    args = parser.parse_args()
    print(f'setting up UDP client on {args.ip}:{args.port}')
    client = udp_client.SimpleUDPClient(args.ip, args.port)
    #client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #client.connect((args.ip, args.port))

    # Set up Sensel
    handle = openSensel()
    frame = initFrame()
    (error, info) = sensel.getSensorInfo(handle)
    
    while True:

        # get nested array data from press on Sensel 
        recording_data = scanFrame(frame, info)
    
        image = create_image_from_nested_arr(recording_data)
        if image != None:
            coordinates = get_values_with_cv2(image)
            if coordinates != None:
                print("coordinates",  float(coordinates[0]), float(coordinates[1]))
                # client.send_message("/wek/inputs", float(coordinates[0]))
                client.send_message("/wek/inputs", [float(coordinates[0]), float(coordinates[1])])
        #msg = "/wek/inputs".encode()
        #assert client.send(msg) == len(msg)
                print(f'sent frame to {args.ip}:{args.port}')
            os.remove(image)
    #TODO write code for proper closing
    closeSensel(frame)