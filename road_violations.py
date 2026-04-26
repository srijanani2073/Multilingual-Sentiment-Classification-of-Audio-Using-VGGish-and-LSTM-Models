import cv2
import os
import numpy as np
from ultralytics import YOLO
from ocr_backend import read_plate_from_image
import threading


class ObjectTracking:
    def __init__(self):
        self.saved_snapshots = set()
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.getcwd()

        self.bytetrack_yaml_path = os.path.join(base_dir, 'bytetrack.yaml')

        self.helmet_model = YOLO(os.path.join(base_dir, "Weights/helmet.pt"))
        self.phone_model = YOLO(os.path.join(base_dir, "Weights/phone.pt"))
        self.triple_model = YOLO(os.path.join(base_dir, "Weights/triple.pt"))
        self.seatbelt_model = YOLO(os.path.join(base_dir, "Weights/seatbelt.pt"))
        self.license_model = YOLO(os.path.join(base_dir, "Weights/license.pt"))
        self.yolo_model = YOLO("yolov8n.pt")

        self.target_classes = ["person", "bicycle", "car", "motorcycle", "truck"]
        self.snapshot_dir = 'violations_snapshots'
        self.license_dir = os.path.join(self.snapshot_dir, 'license_plates')
        os.makedirs(self.snapshot_dir, exist_ok=True)
        os.makedirs(self.license_dir, exist_ok=True)

    def process_frame(self, frame):
        violation_coords = []
        violation_classes = []

        yolo_results = self.yolo_model.track(
            source=frame, persist=True, tracker=self.bytetrack_yaml_path, verbose=False
        )[0]

        yolo_boxes = yolo_results.boxes
        detections = []
        has_motorbike = has_car_bus_truck = has_person = False

        if yolo_boxes:
            for i in range(len(yolo_boxes.cls)):
                cls_id = int(yolo_boxes.cls[i])
                class_name = self.yolo_model.names[cls_id]
                if class_name in self.target_classes:
                    object_id = int(yolo_boxes.id[i]) if yolo_boxes.id is not None else -1
                    bbox = yolo_boxes.xyxy[i].cpu().numpy()
                    detections.append((object_id, bbox, class_name))
                    if class_name == "motorcycle":
                        has_motorbike = True
                    elif class_name in ["car", "bus", "truck"]:
                        has_car_bus_truck = True
                    elif class_name == "person":
                        has_person = True

        # Helmet, Phone, Triple
        if has_motorbike and has_person:
            for model, target_class in [(self.helmet_model, "Without Helmet"),
                                        (self.phone_model, "Using Mobile"),
                                        (self.triple_model, "Triple Riding")]:
                results = model.track(source=frame, persist=True, tracker=self.bytetrack_yaml_path, verbose=False)[0]
                if results.boxes:
                    for i, cls_tensor in enumerate(results.boxes.cls):
                        class_name = model.names[int(cls_tensor)]
                        if class_name == target_class:
                            box = results.boxes.xyxy[i].cpu().numpy()
                            violation_coords.append(box)
                            violation_classes.append((class_name, model))

        # Seatbelt
        if has_car_bus_truck and has_person:
            results = self.seatbelt_model.track(source=frame, persist=True, tracker=self.bytetrack_yaml_path, verbose=False)[0]
            windshield_boxes, noseatbelt_boxes = [], []
            if results.boxes:
                for i, cls_tensor in enumerate(results.boxes.cls):
                    class_name = self.seatbelt_model.names[int(cls_tensor)]
                    box = results.boxes.xyxy[i].cpu().numpy()
                    if class_name == "windshield":
                        windshield_boxes.append(box)
                    elif class_name == "person-noseatbelt":
                        noseatbelt_boxes.append(box)

            for noseatbelt_box in noseatbelt_boxes:
                nx1, ny1, nx2, ny2 = noseatbelt_box
                inside = any(nx1 >= wx1 and ny1 >= wy1 and nx2 <= wx2 and ny2 <= wy2 for wx1, wy1, wx2, wy2 in windshield_boxes)
                if inside:
                    violation_coords.append(noseatbelt_box)
                    violation_classes.append(("person-noseatbelt", self.seatbelt_model))

        # Draw object boxes
        for obj_id, box, cls_name in detections:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{cls_name} ID: {obj_id}" if obj_id != -1 else cls_name
            cv2.putText(frame, label, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        for i, (class_name, _) in enumerate(violation_classes):
            vx1, vy1, vx2, vy2 = map(int, violation_coords[i])
            cv2.rectangle(frame, (vx1, vy1), (vx2, vy2), (255, 0, 0), 2)
            cv2.putText(frame, class_name, (vx1, vy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            if class_name == "person-noseatbelt":
                continue

            box = violation_coords[i]
            vx1, vy1, vx2, vy2 = box

            for obj_id, person_box, obj_class in detections:
                if obj_class != "person":
                    continue

                cx1, cy1, cx2, cy2 = person_box

                inter_x1 = max(vx1, cx1)
                inter_y1 = max(vy1, cy1)
                inter_x2 = min(vx2, cx2)
                inter_y2 = min(vy2, cy2)

                inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
                violation_area = (vx2 - vx1) * (vy2 - vy1)
                person_area = (cx2 - cx1) * (cy2 - cy1)

                overlap_percentage = inter_area / violation_area
                person_overlap_percentage = inter_area / person_area

                for _, vehicle_box, vehicle_class in detections:
                    if vehicle_class == "motorcycle":
                        mx1, my1, mx2, my2 = vehicle_box
                        vehicle_inter_x1 = max(cx1, mx1)
                        vehicle_inter_y1 = max(cy1, my1)
                        vehicle_inter_x2 = min(cx2, mx2)
                        vehicle_inter_y2 = min(cy2, my2)

                        vehicle_inter_area = max(0, vehicle_inter_x2 - vehicle_inter_x1) * max(0, vehicle_inter_y2 - vehicle_inter_y1)
                        vehicle_area = (mx2 - mx1) * (my2 - my1)
                        vehicle_overlap_percentage = vehicle_inter_area / vehicle_area

                        if overlap_percentage >= 0.7 and vehicle_overlap_percentage > 0.9:
                            crop = frame[int(cy1):int(cy2), int(cx1):int(cx2)]
                            if crop.size > 0 and crop.shape[0] > 50 and crop.shape[1] > 50:
                                snap_path = os.path.join(self.snapshot_dir, f"{class_name}_{obj_id}.jpg")
                                cv2.imwrite(snap_path, crop)
                                license_results = self.license_model.predict(crop, verbose=False)[0]
                                if license_results.boxes:
                                    for lic_box in license_results.boxes.xyxy.cpu().numpy():
                                        lx1, ly1, lx2, ly2 = map(int, lic_box)
                                        cv2.rectangle(crop, (lx1, ly1), (lx2, ly2), (0, 255, 255), 1)
                                        cv2.putText(crop, "license", (lx1, ly1 - 10), cv2.FONT_HERSHEY_PLAIN, 0.3, (0, 255, 255), 1)
                                    lic_path = os.path.join(self.license_dir, f"license_{class_name}_{obj_id}.jpg")
                                    snapshot_key = (class_name, obj_id)
                                    if snapshot_key in self.saved_snapshots:
                                         continue  # Already saved, skip it
                                    self.saved_snapshots.add(snapshot_key)
                                    cv2.imwrite(lic_path, crop)
                                    read_plate_from_image(lic_path, class_name)
                                    threading.Thread(target=self.process_snapshot, args=(crop, class_name)).start()


        for i, (class_name, _) in enumerate(violation_classes):
            if class_name == "person-noseatbelt":
                nx1, ny1, nx2, ny2 = violation_coords[i]
                for vehicle_id, vehicle_box, v_class in detections:
                    cx1, cy1, cx2, cy2 = vehicle_box

                    inter_x1 = max(nx1, cx1)
                    inter_y1 = max(ny1, cy1)
                    inter_x2 = min(nx2, cx2)
                    inter_y2 = min(ny2, cy2)

                    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
                    noseatbelt_area = (nx2 - nx1) * (ny2 - ny1)
                    iou = inter_area / noseatbelt_area

                    if iou > 0.3:
                        crop = frame[int(cy1):int(cy2), int(cx1):int(cx2)]
                        if crop.size > 0 and crop.shape[0] > 50 and crop.shape[1] > 50:
                            snap_path = os.path.join(self.snapshot_dir, f"{class_name}_{vehicle_id}.jpg")
                            cv2.imwrite(snap_path, crop)
                            license_results = self.license_model.predict(crop, verbose=False)[0]
                            if license_results.boxes:
                                for lic_box in license_results.boxes.xyxy.cpu().numpy():
                                    lx1, ly1, lx2, ly2 = map(int, lic_box)
                                    cv2.rectangle(crop, (lx1, ly1), (lx2, ly2), (0, 255, 255), 1)
                                    cv2.putText(crop, "license", (lx1, ly1 - 10), cv2.FONT_HERSHEY_PLAIN, 0.3, (0, 255, 255), 1)
                                lic_path = os.path.join(self.license_dir, f"license_{class_name}_{vehicle_id}.jpg")
                                snapshot_key = (class_name, obj_id)
                                if snapshot_key in self.saved_snapshots:
                                     continue  # Already saved, skip it
                                self.saved_snapshots.add(snapshot_key)
                                cv2.imwrite(lic_path, crop)
                                read_plate_from_image(lic_path, class_name)
                                #threading.Thread(target=self.process_snapshot, args=(crop, class_name)).start()

        return frame, "done"

    def generate_frames(self, video_source):
        cap = cv2.VideoCapture(video_source)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            processed_frame, _ = self.process_frame(frame)
            ret, jpeg = cv2.imencode('.jpg', processed_frame)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        cap.release()
