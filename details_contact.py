import requests
import os
import xml.etree.ElementTree as ET
import json
import random
import datetime
from fpdf import FPDF
from supabase import create_client, Client
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

supabase_url = "https://tvyDUMMYlcsrfjbnm.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInRDUMMYVCJ9.eyJpc3MiOiJzdXDUMMYInJlZiI6InR2eW5veW9nanBDUMMYIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkyODM1NjYsImV4cCI6MjA2NDg1OTU2Nn0.jJFg8DUMMYEx5tZmzOTwlatjrEShBMs"               # Replace with your Supabase API Key
supabase: Client = create_client(supabase_url, supabase_key)

account_sid = "AC68bb90DUMMY1eb32d5bd613e6"
auth_token = "4db2301d8eDUMMY5c96430e93be0"
twilio_number = "+19867696769"

owner_names = ["Rajesh Kumar", "Priya Sharma", "Amit Verma", "Neha Singh", "Vikram Rao", "Anjali Mehta", "Rahul Nair", "Pooja Gupta", "Arjun Patel", "Meera Iyer", "Sri Janani", "Sanjana", "Archana"]

email_list = [
    "hourace@gmail.com", "rem@gmail.com",
    "h@gmail.com", "20@email.ac.in"
]
phone_list = [
    "+91 958", "+91521"
]
style = ["SUV", "Sedan", "Hatchback", "Bike"]

violation_fines = {
    "Without Helmet": 500,
    "Triple Riding": 1000,
    "Using Mobile": 1000,
    "No Seatbelt": 500,
    "Red Light Violation": 2000
}


def get_vehicle_details(license_plate: str, username="archanag.7203"):
    API_URL = "http://www.regcheck.org.uk/api/reg.asmx"
    username = "traDUMMYadsmth" 
    soap_request = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <CheckIndia xmlns="http://regcheck.org.uk">
          <RegistrationNumber>{license_plate}</RegistrationNumber>
          <username>{username}</username>
        </CheckIndia>
      </soap:Body>
    </soap:Envelope>"""
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://regcheck.org.uk/CheckIndia"
    }
    response = requests.post(API_URL, data=soap_request, headers=headers)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        ns = {"ns": "http://regcheck.org.uk"}
        json_data = root.find(".//ns:vehicleJson", namespaces=ns)
        if json_data is not None and json_data.text:
            import json
            vehicle_info = json.loads(json_data.text)
            owner = vehicle_info.get("Owner", "Not Available")
            plate = license_plate
            make = vehicle_info.get("CarMake", {}).get("CurrentTextValue", "Not Available")
            model = vehicle_info.get("CarModel", {}).get("CurrentTextValue", "Not Available")
            state = vehicle_info.get("Location", "Not Available")
            year = vehicle_info.get("RegistrationYear", "Not Available")
            #print("Vehicle Details:")
            #print(f"Owner Name: {owner}")
            #print(f"License Number: {plate}")
            #print(f"Make: {make}")
            #print(f"Model: {model}")
            #print(f"State: {state}")
            #print(f"Year of Registration: {year}")
            return json.loads(json_data.text)
        else:
            print("No vehicle data found!")
    else:
        print(f"API request failed! Status Code: {response.status_code}, Message: {response.text}")
    return {}

def log_vehicle_and_violations(plate, vehicle_info, violation_list):
    owner = vehicle_info.get("Owner", random.choice(owner_names)) or random.choice(owner_names)
    make = vehicle_info.get("CarMake", {}).get("CurrentTextValue", "Unknown")
    model = vehicle_info.get("CarModel", {}).get("CurrentTextValue", "Unknown")
    state = vehicle_info.get("Location", "Unknown")
    year = vehicle_info.get("RegistrationYear", "Unknown")

    record_info = {
        "plate": plate,
        "owner": owner,
        "state": state,
        "country": "India",
        "year": year,
        "make": make,
        "model": model,
        "email": random.choice(email_list),
        "phone": random.choice(phone_list),
    }

    supabase.table("vehicle_info").insert(record_info).execute()

    for violation in set(violation_list):
        supabase.table("vehicle_violations").insert({
                "plate": plate,
                "owner": owner,
                "violation": violation
        }).execute()

def fetch_vehicle_and_violations(plate):
    vehicle = supabase.table("vehicle_info").select("*").eq("plate", plate).execute().data
    if not vehicle:
        return None, None
    violations = supabase.table("vehicle_violations").select("violation").eq("plate", plate).execute().data
    return vehicle[0], [v['violation'] for v in violations]

def generate_challan(plate, vehicle_data, violations):
        license_plate = plate
        owner = vehicle_data["owner"]
        vehicle_type = vehicle_data["style"]
        state = vehicle_data["state"]
        year = vehicle_data["year"]
        phone = vehicle_data["phone"]
        email = vehicle_data["email"]
        make = vehicle_data["make"]
        model = vehicle_data["model"]
        vehicle = f"{make} {model}"

        total_fine = sum(violation_fines.get(v, 0) for v in violations)

        challan_no = f"{license_plate.replace(' ', '')}-{int(datetime.datetime.now().timestamp())}"
        ist_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        current_time = ist_time.strftime("%d-%m-%Y %H:%M:%S")

        pdf = FPDF()
        pdf.add_page()

        pdf.add_font("DejaVu", "", r"DejaVuSans.ttf")
        pdf.add_font("DejaVu", "B", r"DejaVuSans-Bold.ttf")

        pdf.set_font("DejaVu", "", 10)
        pdf.cell(100, 10, f"Issued on: {current_time} IST", align="L", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("DejaVu", "B", 16)
        pdf.cell(200, 10, "E-Challan", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_font("DejaVu", "", 12)
        pdf.ln(5)
        pdf.cell(200, 20, f"Challan no: {challan_no}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(100, 10, f"Owner: {owner}", align="L")
        pdf.cell(60, 10, f"License plate: {license_plate}", align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(100, 10, f"Phone: {phone}", align="L")
        pdf.cell(60, 10, f"Email: {email}", align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(100, 10, f"Vehicle type: {vehicle_type}", align="L")
        pdf.cell(60, 10, f"Vehicle: {vehicle}", align="L", new_x = "LMARGIN", new_y = "NEXT")
        pdf.cell(100, 10, f"State: {state}", align="L")
        pdf.cell(60, 10, f"Year: {year}", align="L", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(10)
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(200, 10, "VIOLATIONS", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 12)

        pdf.set_fill_color(200, 200, 200)
        pdf.cell(140, 10, "Violation", 1, align='C', fill=1)
        pdf.cell(50, 10, "Fine", 1, new_x="LMARGIN", new_y="NEXT", align='C', fill=1)

        for violation in violations:
            pdf.cell(140, 10, violation, 1)
            pdf.cell(50, 10, f"₹{violation_fines.get(violation, 0)}", 1, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("DejaVu", "B", 14)
        pdf.cell(140, 10, "Total", 1)
        pdf.cell(50, 10, f"₹{total_fine}", 1, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(15)
        pdf.set_font("DejaVu", "", 10)
        pdf.cell(200, 10, "Visit https://echallan.parivahan.gov.in/index/accused-challan to clear your fines.", new_x="LMARGIN")

        filename = f"e_challan_{license_plate}.pdf"
        pdf.output(filename)
        output_directory = "/Users/sjanani/Downloads/Traffic UI/echallan"
        filename = os.path.join("e_challan_{license_plate}.pdf")
        pdf.output(filename)
        print(f"E-Challan generated for {license_plate}: {filename}")
        
        return filename

def send_email(to_email, subject, body, attachment_path):
    msg = MIMEMultipart()
    msg['From'] = "roadsafetyjasviolater@gmail.com"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if not os.path.exists(attachment_path):
        print(f"Error: The file {attachment_path} does not exist.")
        return 

    with open(attachment_path, "rb") as file:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={attachment_path}")
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("roadsafetyjasviolater@gmail.com", "pzfs kosx lcou skzw")
    server.send_message(msg)
    server.quit()

def send_violation_sms(name, plate, violations, phone):
    client = TwilioClient(account_sid, auth_token)
    body = (
        f"Dear {name}, your vehicle {plate} has been issued a challan for {', '.join(violations)}. "
        "Visit https://echallan.parivahan.gov.in/index/accused-challan to clear your fines."
    )
    try:
        client.messages.create(body=body, from_=twilio_number, to=phone)
    except TwilioRestException as e:
        print(f"SMS Error: {e}")

def handle_plate_violation(plate_text: str, violation_list: list):
    vehicle_info = get_vehicle_details(plate_text)
    log_vehicle_and_violations(plate_text, vehicle_info, violation_list)
    vehicle_data, violations = fetch_vehicle_and_violations(plate_text)
    if not vehicle_data or not violations:
        print(f"Data missing for {plate_text}")
        return
    pdf_path = generate_challan(plate_text, vehicle_data, violations)
    send_email(vehicle_data["email"], "Your E-Challan Deatils", "Please find attached your challan. Kindly visit https://echallan.parivahan.gov.in/index/accused-challan to clear your fines.", pdf_path)
    send_violation_sms(vehicle_data["owner"], plate_text, violations, vehicle_data["phone"])

def process_plate(plate_text: str, violations: list):
    print(f"[INFO] Processing {plate_text} with violations: {violations}")
    try:
        handle_plate_violation(plate_text, violations)
        print(f"[SUCCESS] Processed {plate_text} successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to process {plate_text}: {e}")

