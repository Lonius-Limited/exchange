import frappe
# import asyncio
import json
import re
from fhir.resources.patient import Patient
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.identifier import Identifier

from exchange.api.connect import fhir_server_connect

def validate_date(the_date, throw=False):
	if not the_date:
		return False
	the_date = the_date.strip()
	match = re.match(r"(?:19\d{2}|20[01][0-9]|2020)[-/.](?:0[1-9]|1[012])[-/.](?:0[1-9]|[12][0-9]|3[01])", the_date)
	if not match and throw:
		frappe.throw(
			frappe._("{0} is not a valid Date. Provide it in the format YYYY-MM-DD").format(the_date)
		)

	return bool(match)

def update_patient_details(shr, patient, first_name, gender, birth_date, last_name, middle_name, phone, email):
	patient.name[0].given[0] = first_name
	patient.name[0].given[1] = middle_name
	patient.name[0].family = last_name
	patient.gender = gender
	validate_date(birth_date, True)
	patient.birthDate = birth_date
	patient.telecom[0].value = phone
	patient.telecom[1].value = email
	shr.resource('Patient',**json.loads(patient.json())).save()
	return patient

@frappe.whitelist()
def register_patient(
	patient_id = 100,
	first_name = "John",
	gender = "female",
	birth_date = "1990-01-03",
	last_name = "Doe",
	middle_name = "Sang",
	phone = "0777723456",
	email = ""
	):
	shr = fhir_server_connect()
	patient = Patient()

	#SEARCH FOR PATIENT WITH SAME ID. IF EXISTING, DO AN UPDATE INSTEAD.
	patients_resources = shr.resources('Patient')
	patient_with_id_obj = patients_resources.search(identifier__value = patient_id).first()
	patient_with_id = Patient.parse_obj(patient_with_id_obj.serialize()) if patient_with_id_obj else None
	if patient_with_id: 
		return update_patient_details(shr = shr, patient = patient_with_id, first_name = first_name, gender = gender, birth_date = birth_date, last_name = last_name,
			middle_name = middle_name, phone = phone, email = email or f'{patient_id}@lonius.co.ke'
		)
	#SAVE THE ID
	identifier = Identifier()
	identifier.value = patient_id
	identifier.use = "official"
	patient.identifier = [identifier]
	
	#VALIDATE THE DATE AND SAVE
	validate_date(birth_date, True)
	patient.birthDate = birth_date

	#SAVE THE GENDER
	patient.gender = gender

	#SAVE THE NAME
	name = HumanName()
	name.use = "official"
	name.family = last_name or "familyname"
	name.given = [first_name or "givenname1", middle_name or "givenname2"]
	patient.name = [name]

	#SAVE THE PHONE AND EMAIL
	telecom_phone = ContactPoint()
	telecom_phone.system = 'phone'
	telecom_phone.use = 'mobile'
	telecom_phone.value = phone or '0700 123 456'

	#EMAIL
	if frappe.utils.validate_email_address(email) == '' and email != '':
		frappe.throw("The email address is not valid")
	telecom_email = ContactPoint()
	telecom_email.system = 'email'
	telecom_email.use = 'home'
	telecom_email.value = email or f'{patient_id}@lonius.co.ke'
	patient.telecom = [telecom_phone, telecom_email]

	#SAVE THE RECORD
	shr.resource('Patient',**json.loads(patient.json())).save()
	return patient