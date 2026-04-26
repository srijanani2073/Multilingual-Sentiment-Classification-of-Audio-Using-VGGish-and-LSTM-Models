import os
import cv2
import keras_ocr
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import re
import numpy as np
import time
import random
import requests
import xml.etree.ElementTree as ET
import json
from supabase import create_client, Client
from fpdf.enums import XPos, YPos
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from ultralytics import YOLO
from details_contact import handle_plate_violation
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="shapely")


ocr_pipeline = keras_ocr.pipeline.Pipeline()
license_plate_folder = "violations_snapshots/license_plates"
plate_model = YOLO("license.pt")  # or your actual path

def correct_license_plate(text):
    pattern = r"^[A-Z]{2}\d{1,2}[A-Z]{0,2}\d{3,4}$"
    if re.match(pattern, text):
        return text  
    corrections = {"S": "5", "O": "0", "I": "1", "B": "8", "G": "6", "Z": "2", "A": "4"}
    corrected_text = list(text)
    for i, char in enumerate(corrected_text):
        temp_text = corrected_text[:]
        temp_text[i] = corrections.get(char, char)
        temp_text = "".join(temp_text)
        if re.match(pattern, temp_text):
            corrected_text[i] = corrections.get(char, char)
    corrected_text = "".join(corrected_text)
    return corrected_text if re.match(pattern, corrected_text) else text

def read_plate_from_image(image_path, class_name = None):
    image = cv2.imread(image_path)
    results = plate_model(image)
    if not results or not results[0].boxes:
        print(f"No plate detected in {image_path}")
        return None

    x1, y1, x2, y2 = map(int, results[0].boxes.xyxy.cpu().numpy()[0])
    license_plate = image[y1:y2, x1:x2]

    if license_plate.shape[0] < 2 or license_plate.shape[1] < 2:
        print(f"Skipping invalid crop from {image_path} (shape: {license_plate.shape})")
        return None

    ocr_predictions = ocr_pipeline.recognize([license_plate])
    word_boxes = [(word, box) for word, box in ocr_predictions[0]]

    if len(word_boxes) == 1:
        recognized_text = word_boxes[0][0].upper()
    else:
        y_coords = [np.mean(box[:, 1]) for _, box in word_boxes]
        y_range = max(y_coords) - min(y_coords)
        if y_range > 5:
            kmeans = KMeans(n_clusters=2, n_init=10).fit(np.array(y_coords).reshape(-1, 1))
            labels = kmeans.labels_
            rows = {0: [], 1: []}
            for idx, (word, box) in enumerate(word_boxes):
                rows[labels[idx]].append((word, box))
            top_row, bottom_row = sorted(rows.values(), key=lambda row: np.mean([np.mean(box[:, 1]) for _, box in row]))
            top_sorted = sorted(top_row, key=lambda tup: np.mean(tup[1][:, 0]))
            bottom_sorted = sorted(bottom_row, key=lambda tup: np.mean(tup[1][:, 0]))
            sorted_predictions = top_sorted + bottom_sorted
        else:
            sorted_predictions = sorted(word_boxes, key=lambda tup: np.mean(tup[1][:, 0]))
        recognized_text = "".join([word for word, box in sorted_predictions]).upper()

    for junk in ["IND", "INO", "IN0"]:
        recognized_text = recognized_text.replace(junk, "")

    recognized_text = correct_license_plate(recognized_text)
    print(f"OCR result for {os.path.basename(image_path)}: {recognized_text}")
    violation_list = ["Without Helmet"]
    handle_plate_violation(recognized_text, violation_list)
    return recognized_text

def monitor_folder():
    print("OCR Monitoring started...")
    processed = set()

    while True:
        files = [f for f in os.listdir(license_plate_folder) if f.endswith((".jpg", ".png"))]
        for file in files:
            full_path = os.path.join(license_plate_folder, file)
            if full_path not in processed:
                read_plate_from_image(full_path)
                processed.add(full_path)
        time.sleep(2)

if __name__ == "__main__":
    monitor_folder()