import logging
import re
from typing import Any, Text, Dict, List, Union, Optional
import spacy
from rasa_sdk import Action, Tracker
from rasa_sdk.events import Restarted, EventType, SlotSet, FollowupAction, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction, REQUESTED_SLOT
from templates.Web import QuickReply, Carousel
from templates.client_api import search, fetch_category_image, add_customer, send_email, \
    get_customer_id, get_orders
from templates.client_credentials import STORE_URL
from templates.dashboard import fncSaveCustomerDetails
from templates.otp import send_otp, resend_otp, verify_otp
from MessagingComponents import create_quick_replies
from selenium.webdriver.chrome.options import Options
import geocoder
from datetime import date
from selenium import webdriver
from bs4 import BeautifulSoup
import getpass
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import time
import requests
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
import requests
import json
import re

logger = logging.getLogger(__name__)
nlp = spacy.load("en_core_web_md")

latest_action = {}
latest_action["ACTION"] = {}
medical_shop_info = {}
medical_shop_info["OXYGEN"] = {}
medical_shop_info["AMBULANCE"] = {}
medical_shop_info["MEDICAL_STORE"] = {}
medical_shop_info["CONTACT_HOSPITAL"] = {}



def get_driver():
    driver = webdriver.Chrome(executable_path = 'chromedriver')
    return driver

def current_location():
    chrome_options = Options()
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    timeout = 20
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("https://mycurrentlocation.net/")
    wait = WebDriverWait(driver, timeout)
    longitude = driver.find_elements_by_xpath('//*[@id="longitude"]')
    longitude = [x.text for x in longitude]
    longitude = str(longitude[0])
    latitude = driver.find_elements_by_xpath('//*[@id="latitude"]')
    latitude = [x.text for x in latitude]
    latitude = str(latitude[0])
    driver.quit()
    return [latitude,longitude]

co_ordinates = current_location()

driver = get_driver()

# def current_location():
#     g = geocoder.ip('me')
#     return g.latlng

def named_entity_spacy_parser(text: str) -> Text:
    """
    This function extracts name from text and return it's value
    :param text: str
    :return: str
    """
    spacy_nlp = spacy.load('en_core_web_md')
    doc = spacy_nlp(text.strip())
    name = set()
    data = {}

    for i in doc.ents:
        entry = str(i.lemma_).lower()
        text = text.replace(str(i).lower(), "")

        # extract artifacts, events and natural phenomenon from text
        if i.label_ in ["ART", "EVE", "NAT", "PERSON"]:
            name.add(entry.title())
    data['name'] = list(name)
    try:
        return data['name'][0]
    except Exception as e:
        return text

class ActionMenu(Action):

    def name(self) -> Text:
        return "action_menu"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "Please select from the below options."
        menu = [
            ("🔎 Local Medical Stores", "postback", "/action_medicine_store"),
            ("Oxygen Tank/Refilling", "postback", "/action_oxygen"),
            ("🚑 Emergency Ambulance Services", "postback", "/action_ambulance"),
            ("Hospital Beds Enquiry", "postback", "/start_district_form"),
            ("🏥 Contact Hospital", "postback", "/action_contact_hospital"),
            ("💉 Vaccination", "web_url", "https://vincenzio-robertina.com/shipping/"),
            ("Preventive Medicines", "postback", "/action_preventive_medicines"),
            ("Support","postback","action_support"),
            ("👩‍⚕ Ask a Doctor ?","postback","/action_ask_doctor")
        ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []

class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "Hi I'm AngularStone 👨‍⚕️, here to help you out, in fight against Corona Virus. <br> Please select from the below options."
        menu = [
            ("🔎 Local Medical Stores", "postback", "/action_medicine_store"),
            ("Oxygen Tank/Refilling", "postback", "/action_oxygen"),
            ("🚑 Emergency Ambulance Services", "postback", "/action_ambulance"),
            ("Hospital Beds Enquiry", "postback", "/start_district_form"),
            ("🏥 Contact Hospital", "postback", "/action_contact_hospital"),
            ("💉 Vaccination", "web_url", "https://vincenzio-robertina.com/shipping/"),
            ("Preventive Medicines", "postback", "/action_preventive_medicines"),
            ("Support","postback","action_support"),
            ("👩‍⚕ Ask a Doctor ?","postback","/action_ask_doctor")
        ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []

class ActionSupport(Action):

    logger.info(msg="Class called: ActionContactUs")

    def name(self) -> Text:
        return "action_support"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "Welcome to AntiCovid Bot Support. Tell me how to help you."
        menu = [
            ("Contact Us", "postback", "/start_form"),
            ("Social Media", "postback", "/action_social_media"),
            ("Start Again", "postback", "/action_hello_world"),
        ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            elif item[1] == "web_url":
                qr.add_generic_(
                    type = "web_url",
                    text= text,
                    title = item[0],
                    web_url = item[2],
                    extension=item[3],
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []





class ActionSocialMedia(Action):

    logger.info(msg="Class called: ActionContactUs")

    def name(self) -> Text:
        return "action_social_media"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "Reach out us on social media 🌐"
        menu = [
            ("Facebook", "web_url", "https://www.facebook.com/vincenziorobertina/", False),
            ("Instagram", "web_url", "https://www.instagram.com/vincenziorobertina/?igshid=1hpdlsgjo9k3e", False),
            ("LinkedIn", "web_url", "https://twitter.com/VinRobertina?s=08", False),
            ("Start Again", "postback", "/action_hello_world"),
        ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            elif item[1] == "web_url":
                qr.add_generic_(
                    type = "web_url",
                    text= text,
                    title = item[0],
                    web_url = item[2],
                    extension=item[3],
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class FormContactUs(FormAction):

    def name(self) -> Text:
        return "form_contact_us"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill
           :param: tracker: Tracker
           :return: List[Text]
        """
        return ["name", "email", "phone_number"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """
            This function maps the slot values
            :return: Dict[Text, Union[Dict, List[Dict]]]
        """
        return {
            "name": self.from_text(not_intent=["chitchat"]),
            "email": self.from_text(not_intent=["chitchat"]),
            "phone_number": self.from_text(not_intent=["chitchat"]),
        }

    def validate_name(self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        name = named_entity_spacy_parser(value).lower()
        for i in name:
            if ord(i) >= ord('a') and ord(i) <= ord('z'):
                pass
            elif i == ' ':
                pass
            else:
                dispatcher.utter_message("Please don't use special characters in name")
                return {"name":None}
        return {"name":name}

    def validate_phone_number(self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        phone = re.findall(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]", value)
        if len(phone) != 0:
            phone = phone[0]
        try:
            if '+' in phone and len(phone) == 13 and type(int(phone.replace('+',''))) == int:
                return {"phone_number":phone}
        except Exception as e:
            dispatcher.utter_message("Please mention phone number in this format\n +918888888888")
            return {"phone_number":None}
        try:
            if '+' not in phone and len(phone) == 10 and type(int(phone)) == int:
                return {"phone_number":phone}
        except Exception as e:
            dispatcher.utter_message("Please mention phone number in this format\n +918888888888")
            return {"phone_number":None}

    def validate_email(self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        mail = value
        r = re.compile(r'[\w\.-]+@[\w\.-]+')
        if r.findall(mail) == []:
            dispatcher.utter_message("I am unable yo validate this email address, can you tell your email again.")
            return {"email":None}
        mail = r.findall(mail)[0].split('@')
        domain = mail[-1].split('.')
        if len(mail) != 2:
            dispatcher.utter_message("Try email in this format abc@gmail.com")
            return {"email":None}
        elif len(domain) != 2:
            dispatcher.utter_message("Try email in this format abc@gmail.com")
            return {"email":None}
        else:
            return {"email":value}


    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:

        """
            This function retrieves slots information and performs the next step
            :param: dispatcher: CollectingDispatcher
            :param: tracker: Tracker
            :param: domain: Dict[Text, Any]
            :return: AllslotReset(), FollowupAction('action_live_agent')
            """
        name = tracker.get_slot("name")
        email = tracker.get_slot("email")
        phone_number = tracker.get_slot("phone_number")
        dispatcher.utter_message(f"Received these details:- \n{name}\n{email}\n{phone_number}")
        dispatcher.utter_message("Thank You so much for details. Someone from our team will shortly contact you.")
        return [AllSlotsReset(),FollowupAction("action_social_media")]

class FormDistrict(FormAction):

    def name(self) -> Text:
        return "form_district"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill
           :param: tracker: Tracker
           :return: List[Text]
        """
        return ["district"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """
            This function maps the slot values
            :return: Dict[Text, Union[Dict, List[Dict]]]
        """
        return {
            "district": self.from_text(not_intent=["chitchat"]),
        }

    def validate_district(self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        District = ["ARARIA", "ARWAL", "AURANGABAD", "BANKA", "BEGUSARAI", "BHAGALPUR", "BHOJPUR", "BUXAR", "DARBHANGA",
                    "EAST CHAMPARAN", "GAYA", "GOPALGANJ", "JAMUI", "JEHANABAD", "KAIMUR", "KATIHAR", "KHAGARIA",
                    "KISHANGANJ", "LAKHISARAI", "MADHEPURA", "MADHUBANI", "MUNGER", "MUZAFFARPUR", "NALANDA", "NAWADA",
                    "PATNA", "PURNIA", "ROHTAS", "SAHARSA", "SAMASTIPUR", "SARAN", "SHEIKHPURA", "SHEOHAR", "SITAMARHI",
                    "SIWAN", "SUPAUL", "VAISHALI", "WEST CHAMPARAN"]

        if value.upper() in District:
            return {"district": District[District.index(value.upper())]}
        elif value.upper() not in District:
            for i in District:
                if value.upper() in i:
                    return {"district": i}
        return {"district": None}

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:

        """
            This function retrieves slots information and performs the next step
            :param: dispatcher: CollectingDispatcher
            :param: tracker: Tracker
            :param: domain: Dict[Text, Any]
            :return: AllslotReset(), FollowupAction('action_live_agent')
            """
        district = tracker.get_slot("district")

        dispatcher.utter_message(f"Received these details:- \n{district}\n")
        return [FollowupAction("action_hospital_bed")]


class ActionFallback(Action):

    def name(self) -> Text:
        return "action_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        doc = nlp(tracker.latest_message["text"])

        noun = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "PROPN"]]
        # No noun found in user input
        if len(noun) == 0:
            text = "I am sorry, I couldn't help you with that.<br>Try something else!"
            qr = QuickReply.QuickReply()
            qr.add_postback(text=text, title="Start Again", payload="/greet")
            #qr.add_postback(text=text, title="🖊️ Register Complain", payload="/register_complain")
            message = qr.get_qr()
            dispatcher.utter_message(json_message=message)
            return []
        products = search(' '.join([str(elem) for elem in noun]))
        if not products:
            text = "I am sorry, I couldn't help you with that.<br>Try something else!"
            qr = QuickReply.QuickReply()
            qr.add_postback(text=text, title="Start Again", payload="/action_hello_world")
            #qr.add_postback(text=text, title="🖊️ Register Complain", payload="/register_complain")
            message = qr.get_qr()
            dispatcher.utter_message(json_message=message)
            return []

        return []

class ActionMapRedirect1(Action):
    def name(self) -> Text:
        return "action_map_redirect_1"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        #print("I AM IN REDIRECT1")
        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[0]
            values = list(medical_shop_info["OXYGEN"].values())[0]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[0]
            values = list(medical_shop_info["AMBULANCE"].values())[0]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[0]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[0]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[0]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[0]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        # print(" DICTIONARY ",medical_shop_info)
        # print("MENU ",menu)
        # print(" TEXT ",text)
        # print(" LATEST ACTION ",latest_action["ACTION"])


        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []

class ActionMapRedirect2(Action):
    def name(self) -> Text:
        return "action_map_redirect_2"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[1]
            values = list(medical_shop_info["OXYGEN"].values())[1]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[1]
            values = list(medical_shop_info["AMBULANCE"].values())[1]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[1]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[1]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[1]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[1]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect3(Action):
    def name(self) -> Text:
        return "action_map_redirect_3"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[2]
            values = list(medical_shop_info["OXYGEN"].values())[2]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[2]
            values = list(medical_shop_info["AMBULANCE"].values())[2]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[2]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[2]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[2]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[2]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect4(Action):
    def name(self) -> Text:
        return "action_map_redirect_4"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[3]
            values = list(medical_shop_info["OXYGEN"].values())[3]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[3]
            values = list(medical_shop_info["AMBULANCE"].values())[3]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[3]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[3]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[3]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[3]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect5(Action):
    def name(self) -> Text:
        return "action_map_redirect_5"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[4]
            values = list(medical_shop_info["OXYGEN"].values())[4]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[4]
            values = list(medical_shop_info["AMBULANCE"].values())[4]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[4]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[4]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[4]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[4]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect6(Action):
    def name(self) -> Text:
        return "action_map_redirect_6"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[5]
            values = list(medical_shop_info["OXYGEN"].values())[5]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[5]
            values = list(medical_shop_info["AMBULANCE"].values())[5]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[5]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[5]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[5]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[5]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect7(Action):
    def name(self) -> Text:
        return "action_map_redirect_7"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[6]
            values = list(medical_shop_info["OXYGEN"].values())[6]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[6]
            values = list(medical_shop_info["AMBULANCE"].values())[6]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[6]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[6]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[6]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[6]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect8(Action):
    def name(self) -> Text:
        return "action_map_redirect_8"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[7]
            values = list(medical_shop_info["OXYGEN"].values())[7]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[7]
            values = list(medical_shop_info["AMBULANCE"].values())[7]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[7]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[7]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[7]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[7]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect9(Action):
    def name(self) -> Text:
        return "action_map_redirect_9"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[8]
            values = list(medical_shop_info["OXYGEN"].values())[8]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[8]
            values = list(medical_shop_info["AMBULANCE"].values())[8]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[8]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[8]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[8]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[8]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect10(Action):
    def name(self) -> Text:
        return "action_map_redirect_10"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[9]
            values = list(medical_shop_info["OXYGEN"].values())[9]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[9]
            values = list(medical_shop_info["AMBULANCE"].values())[9]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[9]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[9]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[9]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[9]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect11(Action):
    def name(self) -> Text:
        return "action_map_redirect_11"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[10]
            values = list(medical_shop_info["OXYGEN"].values())[10]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[10]
            values = list(medical_shop_info["AMBULANCE"].values())[10]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[10]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[10]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[10]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[10]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect12(Action):
    def name(self) -> Text:
        return "action_map_redirect_12"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[11]
            values = list(medical_shop_info["OXYGEN"].values())[11]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[11]
            values = list(medical_shop_info["AMBULANCE"].values())[11]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[11]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[11]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[11]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[11]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect13(Action):
    def name(self) -> Text:
        return "action_map_redirect_13"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[12]
            values = list(medical_shop_info["OXYGEN"].values())[12]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[12]
            values = list(medical_shop_info["AMBULANCE"].values())[12]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[12]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[12]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[12]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[12]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect14(Action):
    def name(self) -> Text:
        return "action_map_redirect_14"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[13]
            values = list(medical_shop_info["OXYGEN"].values())[13]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[13]
            values = list(medical_shop_info["AMBULANCE"].values())[13]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[13]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[13]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[13]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[13]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect15(Action):
    def name(self) -> Text:
        return "action_map_redirect_15"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[14]
            values = list(medical_shop_info["OXYGEN"].values())[14]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[14]
            values = list(medical_shop_info["AMBULANCE"].values())[14]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[14]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[14]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[14]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[14]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect16(Action):
    def name(self) -> Text:
        return "action_map_redirect_16"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[15]
            values = list(medical_shop_info["OXYGEN"].values())[15]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[15]
            values = list(medical_shop_info["AMBULANCE"].values())[15]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[15]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[15]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[15]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[15]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect17(Action):
    def name(self) -> Text:
        return "action_map_redirect_17"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[16]
            values = list(medical_shop_info["OXYGEN"].values())[16]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[16]
            values = list(medical_shop_info["AMBULANCE"].values())[16]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[16]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[16]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[16]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[16]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect18(Action):
    def name(self) -> Text:
        return "action_map_redirect_18"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[17]
            values = list(medical_shop_info["OXYGEN"].values())[17]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[17]
            values = list(medical_shop_info["AMBULANCE"].values())[17]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[17]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[17]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[17]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[17]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect19(Action):
    def name(self) -> Text:
        return "action_map_redirect_19"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[18]
            values = list(medical_shop_info["OXYGEN"].values())[18]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[18]
            values = list(medical_shop_info["AMBULANCE"].values())[18]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[18]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[18]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[18]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[18]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


class ActionMapRedirect20(Action):
    def name(self) -> Text:
        return "action_map_redirect_20"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = ""
        menu = []
        if latest_action["ACTION"] == "action_oxygen":
            keys = list(medical_shop_info["OXYGEN"].keys())[19]
            values = list(medical_shop_info["OXYGEN"].values())[19]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_ambulance":
            keys = list(medical_shop_info["AMBULANCE"].keys())[19]
            values = list(medical_shop_info["AMBULANCE"].values())[19]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        elif latest_action["ACTION"] == "action_medicine_store":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["MEDICAL_STORE"].keys())[19]
            values = list(medical_shop_info["MEDICAL_STORE"].values())[19]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]

        elif latest_action["ACTION"] == "action_contact_hospital":
            print("IN ELIF CONDITION ")
            keys = list(medical_shop_info["CONTACT_HOSPITAL"].keys())[19]
            values = list(medical_shop_info["CONTACT_HOSPITAL"].values())[19]
            dispatcher.utter_message(f"{keys} <br> Additional Info :- {values[0]} <br>")
            text = "<br>Please click on the below link to view it on map 🌍.<br>"
            menu = [
                ("Link to Google Map 🌍", "web_url", values[1]),
                ("Menu", "postback", "/action_menu")
            ]
        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False,
                )
        dispatcher.utter_message(json_message=qr.get_qr())
        return []


# class ActionController(Action):
#     def name(self) -> Text:
#         return "action_controller"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         print("Latest Intent",tracker.latest_message['intent'].get('name'))
#         if tracker.latest_message['intent'].get('name') == "action_map_redirect_1":
#             return [FollowupAction("action_map_redirect_1")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_2":
#             return [FollowupAction("action_map_redirect_2")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_3":
#             return [FollowupAction("action_map_redirect_3")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_4":
#             return [FollowupAction("action_map_redirect_4")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_5":
#             return [FollowupAction("action_map_redirect_5")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_6":
#             return [FollowupAction("action_map_redirect_6")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_7":
#             return [FollowupAction("action_map_redirect_7")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_8":
#             return [FollowupAction("action_map_redirect_8")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_9":
#             return [FollowupAction("action_map_redirect_9")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_10":
#             return [FollowupAction("action_map_redirect_10")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_11":
#             return [FollowupAction("action_map_redirect_11")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_12":
#             return [FollowupAction("action_map_redirect_12")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_13":
#             return [FollowupAction("action_map_redirect_13")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_14":
#             return [FollowupAction("action_map_redirect_14")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_15":
#             return [FollowupAction("action_map_redirect_15")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_16":
#             return [FollowupAction("action_map_redirect_16")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_17":
#             return [FollowupAction("action_map_redirect_17")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_18":
#             return [FollowupAction("action_map_redirect_18")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_19":
#             return [FollowupAction("action_map_redirect_19")]
#         elif tracker.latest_message['intent'].get('name') == "action_map_redirect_20":
#             return [FollowupAction("action_map_redirect_20")]

class ActionMedicalStore(Action):

    def name(self) -> Text:
        return "action_medicine_store"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_action["ACTION"] = tracker.latest_message['intent'].get('name')
        print("LATEST ACTION ",latest_action["ACTION"])
        if len(medical_shop_info["MEDICAL_STORE"]) == 0:

            driver.get(f"https://www.google.com/maps/@{co_ordinates[0]},{co_ordinates[1]},15z")
            time.sleep(2)
            search_box = driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys("Medical Stores near me")
            driver.find_element_by_xpath('//div[@class="xoLGzf-searchbutton-haAclf"]').click()
            time.sleep(3)

            scroll = 0
            while True:
                try:
                    bar = driver.find_element_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]')
                    break
                except Exception as e:
                    print("Finding Scroll Bar")
            while scroll < 10:
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', bar)
                scroll += 1

            medical_dic = {}
            for i in driver.find_elements_by_xpath(
                    '//div[@class="mapsConsumerUiSubviewSectionGm2Placeresultcontainer__result-container mapsConsumerUiSubviewSectionGm2Placeresultcontainer__one-action mapsConsumerUiSubviewSectionGm2Placeresultcontainer__wide-margin"]'):
                j_text = ""
                for j in i.text.split("\n")[1:]:
                    j_text += j.replace("Directions","").replace("Website","")

                link_text = ""

                for l_text in range(len(i.text.split("\n")[0].split(" "))):
                    if l_text < len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text] + "+"
                    if l_text == len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text]

                for link in driver.find_elements_by_xpath('//a[@class="place-result-container-place-link"]'):
                    if link_text in link.get_attribute("href"):
                        url = link.get_attribute("href")
                        break

                try:
                    print("DICTIONARY KEY ",i.text.split("\n")[0])
                    print("DICTIONARY VALUE ",[j_text, url])
                    medical_dic[i.text.split("\n")[0]] = [j_text, url]
                except Exception as e:
                    pass
                print("BUSINESS NAME:-",i.text.split("\n")[0], " & URL ", url ," TEXT ",j_text)

                medical_dic[i.text.split("\n")[0]] = [j_text, url]
                print("BUSINESS NAME:-",i.text.split("\n")[0], " & URL ", url ," TEXT ",j_text)

            print("MEDICAL DICTIONARY ",medical_dic)
            medical_shop_info["MEDICAL_STORE"] = medical_dic

        text = "Here are the search results :-"
        print("LEn of Medical Dictionary ",medical_shop_info)
        menu = []
        action_count = 1
        try:
            for i in medical_shop_info["MEDICAL_STORE"]:
                menu.append((i, "postback", f"/action_map_redirect_{str(action_count)}"))
                action_count += 1
        except Exception as e:
            print(e)
            print("IN EXCEPTION OF INDEX in medical_shop_info")

        menu.append(("Menu","postback","/action_menu"))

        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            elif item[1] == "web_url":
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []


class ActionOxygen(Action):

    def name(self) -> Text:
        medical_shop_info = {}
        return "action_oxygen"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_action["ACTION"] = tracker.latest_message['intent'].get('name')
        if len(medical_shop_info["OXYGEN"]) == 0:

            driver.get(f"https://www.google.com/maps/@{co_ordinates[0]},{co_ordinates[1]},15z")
            time.sleep(2)
            search_box = driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys("Oxygen Gas near me")
            driver.find_element_by_xpath('//div[@class="xoLGzf-searchbutton-haAclf"]').click()
            time.sleep(3)

            scroll = 0
            while scroll < 10:
                while True:
                    try:
                        bar = driver.find_element_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]')
                        break
                    except Exception as e:
                        print("Finding Scroll Bar")

                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', bar)
                scroll += 1

            medical_dic = {}
            for i in driver.find_elements_by_xpath(
                    '//div[@class="mapsConsumerUiSubviewSectionGm2Placeresultcontainer__result-container mapsConsumerUiSubviewSectionGm2Placeresultcontainer__one-action mapsConsumerUiSubviewSectionGm2Placeresultcontainer__wide-margin"]'):
                j_text = ""
                for j in i.text.split("\n")[1:]:
                    j_text += j.replace("Directions", "").replace("Website", "")

                link_text = ""
                for l_text in range(len(i.text.split("\n")[0].split(" "))):
                    if l_text < len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text] + "+"
                    if l_text == len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text]

                for link in driver.find_elements_by_xpath('//a[@class="place-result-container-place-link"]'):
                    if link_text in link.get_attribute("href"):
                        url = link.get_attribute("href")
                        break

                try:
                    medical_dic[i.text.split("\n")[0]] = [j_text, url]
                    print("BUSINESS NAME:-", i.text.split("\n")[0], " & URL ", url, " TEXT ", j_text)
                except Exception as e:
                    pass


            for i in driver.find_elements_by_xpath(
                    '//div[@class="mapsConsumerUiSubviewSectionGm2Placeresultcontainer__result-container mapsConsumerUiSubviewSectionGm2Placeresultcontainer__two-actions mapsConsumerUiSubviewSectionGm2Placeresultcontainer__wide-margin"]'):
                j_text = ""
                for j in i.text.split("\n")[1:]:
                    j_text += j

                link_text = ""
                for l_text in range(len(i.text.split("\n")[0].split(" "))):
                    if l_text < len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text] + "+"
                    if l_text == len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text]

                for link in driver.find_elements_by_xpath('//a[@class="place-result-container-place-link"]'):
                    if link_text in link.get_attribute("href"):
                        url = link.get_attribute("href")
                        break

                medical_dic[i.text.split("\n")[0]] = [j_text, url]
                print("BUSINESS NAME:-", i.text.split("\n")[0], " & URL ", url, " TEXT ", j_text)

            medical_shop_info["OXYGEN"] = medical_dic

        text = "Here are the search results :-"
        menu = []
        action_count = 1
        try:
            for i in medical_shop_info["OXYGEN"]:
                menu.append((i, "postback", f"/action_map_redirect_{str(action_count)}"))
                action_count += 1
        except Exception as e:
            print("IN EXCEPTION OF INDEX in medical_shop_info")

        menu.append(("Menu", "postback", "/action_menu"))

        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            elif item[1] == "web_url":
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []


class ActionRestart(Action):

    def name(self) -> Text:
        return "action_restart"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Conversation Restarted !")

        return [Restarted(), FollowupAction('action_hello_world')]


class ActionAmbulance(Action):

    def name(self) -> Text:
        medical_shop_info = {}
        return "action_ambulance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_action["ACTION"] = tracker.latest_message['intent'].get('name')
        print("LATEST ACTION ",latest_action["ACTION"])
        if len(medical_shop_info["AMBULANCE"]) == 0:

            driver.get(f"https://www.google.com/maps/@{co_ordinates[0]},{co_ordinates[1]},15z")
            time.sleep(2)
            search_box = driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys("Ambulance Service near me")
            driver.find_element_by_xpath('//div[@class="xoLGzf-searchbutton-haAclf"]').click()
            time.sleep(3)

            scroll = 0
            while scroll < 10:
                while True:
                    try:
                        bar = driver.find_element_by_xpath('//*[@id="pane"]/div/div[1]/div/div/div[4]/div[1]')
                        break
                    except Exception as e:
                        print("Finding Scroll Bar")

                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', bar)
                scroll += 1

            medical_dic = {}
            for i in driver.find_elements_by_xpath(
                    '//div[@class="mapsConsumerUiSubviewSectionGm2Placeresultcontainer__result-container mapsConsumerUiSubviewSectionGm2Placeresultcontainer__one-action mapsConsumerUiSubviewSectionGm2Placeresultcontainer__wide-margin"]'):
                j_text = ""
                for j in i.text.split("\n")[1:]:
                    j_text += j.replace("Directions", "").replace("Website", "")

                link_text = ""
                for l_text in range(len(i.text.split("\n")[0].split(" "))):
                    if l_text < len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text] + "+"
                    if l_text == len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text]

                for link in driver.find_elements_by_xpath('//a[@class="place-result-container-place-link"]'):
                    if link_text in link.get_attribute("href"):
                        url = link.get_attribute("href")
                        break

                try:
                    medical_dic[i.text.split("\n")[0]] = [j_text, url]
                except Exception as e:
                    pass
                print("BUSINESS NAME:-", i.text.split("\n")[0], " & URL ", url, " TEXT ", j_text)

            for i in driver.find_elements_by_xpath(
                    '//div[@class="mapsConsumerUiSubviewSectionGm2Placeresultcontainer__result-container mapsConsumerUiSubviewSectionGm2Placeresultcontainer__two-actions mapsConsumerUiSubviewSectionGm2Placeresultcontainer__wide-margin"]'):
                j_text = ""
                for j in i.text.split("\n")[1:]:
                    j_text += j

                link_text = ""
                for l_text in range(len(i.text.split("\n")[0].split(" "))):
                    if l_text < len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text] + "+"
                    if l_text == len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text]

                for link in driver.find_elements_by_xpath('//a[@class="place-result-container-place-link"]'):
                    if link_text in link.get_attribute("href"):
                        url = link.get_attribute("href")
                        break

                medical_dic[i.text.split("\n")[0]] = [j_text, url]
                print("BUSINESS NAME:-", i.text.split("\n")[0], " & URL ", url, " TEXT ", j_text)

            medical_shop_info["AMBULANCE"] = medical_dic

        text = "Here are the search results :-"
        menu = []
        action_count = 1
        try:
            for i in medical_shop_info["AMBULANCE"]:
                menu.append((i, "postback", f"/action_map_redirect_{str(action_count)}"))
                action_count += 1
        except Exception as e:
            print("IN EXCEPTION OF INDEX in medical_shop_info")

        menu.append(("Menu", "postback", "/action_menu"))

        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            elif item[1] == "web_url":
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []


class ActionHospitalBed(Action):
    def name(self) -> Text:
        return "action_hospital_bed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "Please select the bed category:-"
        quick_reply_buttons = [
            {
                "action_type": "postback",
                "title": "ICU Bed",
                "payload": "/action_icu_bed"
            },
            {
                "action_type": "postback",
                "title": "General Bed",
                "payload": "/action_general_bed"
            },
        ]
        dispatcher.utter_message(
            json_message=create_quick_replies(tracker.get_latest_input_channel(), text, quick_reply_buttons))

        return []


class ActionIcuBed(Action):
    def name(self) -> Text:
        return "action_icu_bed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        df = pd.read_html("https://covid19health.bihar.gov.in/DailyDashboard/BedsOccupied")
        df = df[0]
        hospital_detail = {}
        query = tracker.get_slot("district")
        for i in range(df.shape[0]):
            if df["District"][i] == query:
                hospital_detail[df["Facility Name"][i]] = [
                                                           df["Total ICU Beds"][i], df["ICU Beds Vacant"][i],
                                                           df["Contact"][i], df["Last Updated"][i]
                                                          ]

        text = "ICU bed information in selected district"
        dispatcher.utter_message(text=text)
        cr = Carousel.Carousel()
        category = []
        for i in hospital_detail:
            category.append((f"{i}:-<br>Total ICU Bed->{hospital_detail[i][0]}<br>Vacant->{hospital_detail[i][1]}<br>Contact-{hospital_detail[i][2]}<br>Last Updated->{hospital_detail[i][3]}", "https://covid19health.bihar.gov.in/DailyDashboard/BedsOccupied"))

        images = ["https://cdn.apollohospitals.com/dev-apollohospitals/2021/04/apolloprism-6076b56144ba8.jpg"]*len(category)

        for i in range(len(category)):
            cr.add_element(
                title=category[i][0],
                image_url=images[i],
                buttons=[{
                    "type": "web_url",
                    "url": category[i][1],
                    "title": "Show"
                }]
            )

        dispatcher.utter_message(json_message=cr.get_message())
        # Show menu after products
        text = "What else i can help you with? "
        menu = [
            ("Menu","postback", "/action_menu"),
            ("Social Media", "postback", "/action_social_media"),
        ]
        qr = QuickReply.QuickReply(text=text)
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []

class ActionGeneralBed(Action):
    def name(self) -> Text:
        return "action_general_bed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        df = pd.read_html("https://covid19health.bihar.gov.in/DailyDashboard/BedsOccupied")
        df = df[0]
        hospital_detail = {}
        query = tracker.get_slot("district")
        for i in range(df.shape[0]):
            if df["District"][i] == query:
                hospital_detail[df["Facility Name"][i]] = [
                                                           df["Total Beds"][i],df["Vacant"][i],
                                                           df["Contact"][i], df["Last Updated"][i]
                                                          ]

        text = "General bed information in selected district"
        dispatcher.utter_message(text=text)
        cr = Carousel.Carousel()
        category = []
        for i in hospital_detail:
            category.append((f"{i}:-<br>Total General Bed->{hospital_detail[i][0]}<br>Vacant->{hospital_detail[i][1]}<br>Contact-{hospital_detail[i][2]}<br>Last Updated->{hospital_detail[i][3]}", "https://covid19health.bihar.gov.in/DailyDashboard/BedsOccupied"))

        images = ["https://images-na.ssl-images-amazon.com/images/I/61aU0ZCFTqL._AC_SX355_.jpg"]*len(category)

        for i in range(len(category)):
            cr.add_element(
                title=category[i][0],
                image_url=images[i],
                buttons=[{
                    "type": "web_url",
                    "url": category[i][1],
                    "title": "Show"
                }]
            )

        dispatcher.utter_message(json_message=cr.get_message())
        # Show menu after products
        text = "What else i can help you with? "
        menu = [
            ("Menu","postback", "/action_menu"),
            ("Social Media", "postback", "/action_social_media"),
        ]
        qr = QuickReply.QuickReply(text=text)
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []


class ActionContactHospital(Action):
    def name(self) -> Text:
        return "action_contact_hospital"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        latest_action["ACTION"] = tracker.latest_message['intent'].get('name')
        print("LATEST ACTION ", latest_action["ACTION"])
        if len(medical_shop_info["CONTACT_HOSPITAL"]) == 0:

            driver.get(f"https://www.google.com/maps/@{co_ordinates[0]},{co_ordinates[1]},15z")
            time.sleep(2)
            search_box = driver.find_element_by_name("q")
            search_box.clear()
            search_box.send_keys("Hospitals near me")
            driver.find_element_by_xpath('//div[@class="searchbox-searchbutton-container"]').click()
            time.sleep(3)

            scroll = 0
            while scroll < 10:
                while True:
                    try:
                        bar = driver.find_element_by_xpath(
                            "/html/body/jsl/div[3]/div[9]/div[8]/div/div[1]/div/div/div[4]/div[1]")
                        break
                    except Exception as e:
                        print("Finding Scroll Bar")

                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', bar)
                scroll += 1

            medical_dic = {}
            for i in driver.find_elements_by_xpath(
                    '//div[@class="mapsConsumerUiSubviewSectionGm2Placeresultcontainer__result-container mapsConsumerUiSubviewSectionGm2Placeresultcontainer__one-action mapsConsumerUiSubviewSectionGm2Placeresultcontainer__wide-margin"]'):
                j_text = ""
                for j in i.text.split("\n")[1:]:
                    j_text += j.replace("Directions", "").replace("Website", "")

                link_text = ""
                for l_text in range(len(i.text.split("\n")[0].split(" "))):
                    if l_text < len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text] + "+"
                    if l_text == len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text]

                for link in driver.find_elements_by_xpath('//a[@class="place-result-container-place-link"]'):
                    if link_text in link.get_attribute("href"):
                        url = link.get_attribute("href")
                        break

                try:
                    medical_dic[i.text.split("\n")[0]] = [j_text, url]
                except Exception as e:
                    pass
                print("BUSINESS NAME:-", i.text.split("\n")[0], " & URL ", url, " TEXT ", j_text)

            for i in driver.find_elements_by_xpath(
                    '//div[@class="mapsConsumerUiSubviewSectionGm2Placeresultcontainer__result-container mapsConsumerUiSubviewSectionGm2Placeresultcontainer__two-actions mapsConsumerUiSubviewSectionGm2Placeresultcontainer__wide-margin"]'):
                j_text = ""
                for j in i.text.split("\n")[1:]:
                    j_text += j

                link_text = ""
                for l_text in range(len(i.text.split("\n")[0].split(" "))):
                    if l_text < len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text] + "+"
                    if l_text == len(i.text.split("\n")[0].split(" ")) - 1:
                        link_text += i.text.split("\n")[0].split(" ")[l_text]

                for link in driver.find_elements_by_xpath('//a[@class="place-result-container-place-link"]'):
                    if link_text in link.get_attribute("href"):
                        url = link.get_attribute("href")
                        break

                medical_dic[i.text.split("\n")[0]] = [j_text, url]
                print("BUSINESS NAME:-", i.text.split("\n")[0], " & URL ", url, " TEXT ", j_text)

            medical_shop_info["CONTACT_HOSPITAL"] = medical_dic

        text = "Here are the search results :-"
        menu = []
        action_count = 1
        try:
            for i in medical_shop_info["CONTACT_HOSPITAL"]:
                menu.append((i, "postback", f"/action_map_redirect_{str(action_count)}"))
                action_count += 1
        except Exception as e:
            print("IN EXCEPTION OF INDEX in medical_shop_info")

        menu.append(("Menu", "postback", "/action_menu"))

        qr = QuickReply.QuickReply()
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            elif item[1] == "web_url":
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []


class ActionPreventiveMedicines(Action):
    def name(self) -> Text:
        return "action_preventive_medicines"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "Please have a look on these products"
        dispatcher.utter_message(text=text)
        cr = Carousel.Carousel()

        category = [
            ("Shoulder Bags", "https://vincenzio-robertina.com/product-category/shoulder-bags/"),
            ("Totes", "https://vincenzio-robertina.com/product-category/totes/"),
            ("Cross Body Bags", "https://vincenzio-robertina.com/product-category/cross-body-bags/"),
            ("Evening Bags Clutches", "https://vincenzio-robertina.com/product-category/evening-bags-clutches/"),
        ]

        images = [
            "https://vincenzio-robertina.com/wp-content/uploads/2021/02/lillyshopper1.jpg",
            "https://vincenzio-robertina.com/wp-content/uploads/2021/02/darcitotebrown1.jpg",
            "https://vincenzio-robertina.com/wp-content/uploads/2021/02/3D4A0151.jpg",
            "https://vincenzio-robertina.com/wp-content/uploads/2021/02/3D4A0132.jpg"
        ]

        for i in range(len(category)):
            cr.add_element(
                title=category[i][0],
                image_url=images[i],
                buttons=[{
                    "type": "web_url",
                    "url": category[i][1],
                    "title": "Show"
                }]
            )

        dispatcher.utter_message(json_message=cr.get_message())
        # Show menu after products
        text = "What else i can help you with? "
        menu = [
            ("View All", "web_url", "https://vincenzio-robertina.com/product-category/handbag/"),
            ("Best Seller", "web_url", "https://vincenzio-robertina.com/bestseller-handbag/"),
            ("New Arrival", "web_url", "https://vincenzio-robertina.com/new-arrival-handbag/"),
            ("🛒 Cart", "web_url", "https://vincenzio-robertina.com/cart/"),
            ("Menu", "postback", "/action_social_media"),
            ("Social Media", "postback", "/action_social_media"),
            ("🔎 Track Order", "postback", "/action_social_media"),
        ]
        qr = QuickReply.QuickReply(text=text)
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []


class ActionAskDoctor(Action):
    def name(self) -> Text:
        return "action_ask_doctor"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = "Please have a look on these products which you can gift to someone special ❤"
        dispatcher.utter_message(text=text)
        cr = Carousel.Carousel()

        category = [
            ("Gift for her", "https://vincenzio-robertina.com/product-category/gift-for-her/"),
            ("Gift for him", "https://vincenzio-robertina.com/product-category/gift-for-him/"),
        ]

        images = [
            "https://vincenzio-robertina.com/wp-content/uploads/2021/01/gifts-for-her.jpg",
            "https://vincenzio-robertina.com/wp-content/uploads/2021/01/gifts-for-him.jpg"
        ]

        for i in range(len(category)):
            cr.add_element(
                title=category[i][0],
                image_url=images[i],
                buttons=[{
                    "type": "web_url",
                    "url": category[i][1],
                    "title": "Show"
                }]
            )

        dispatcher.utter_message(json_message=cr.get_message())
        # Show menu after products
        text = "What else i can help you with? "
        menu = [
            ("🛒 Cart", "web_url", "https://vincenzio-robertina.com/cart/"),
            ("Menu", "postback", "/action_social_media"),
            ("Social Media", "postback", "/action_social_media"),
            ("🔎 Track Order", "postback", "/action_social_media"),
        ]
        qr = QuickReply.QuickReply(text=text)
        for item in menu:
            if item[1] == "postback":
                qr.add_generic_(
                    type="postback",
                    text=text,
                    title=item[0],
                    payload=item[2]
                )
            else:
                qr.add_generic_(
                    type="web_url",
                    text=text,
                    title=item[0],
                    web_url=item[2],
                    extension=False
                )
        dispatcher.utter_message(json_message=qr.get_qr())

        return []