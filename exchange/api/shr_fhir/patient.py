import frappe
# import asyncio
import json
import re
from fhirpy.base.exceptions import (
	ResourceNotFound,
	OperationOutcome,
	MultipleResourcesFound,
	InvalidResponse
)
from exchange.api.shr_fhir.connect import fhir_server_connect, fhir_server_get_resource
from fhir.resources.patient import Patient
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.identifier import Identifier
from fhir.resources.bundle import Bundle

shr = fhir_server_connect()

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

def update_patient_details(shr, patient, payload):
	try:
		if payload.get('first_name'): patient.name[0].given[0] = payload.get("first_name") or '-'
		if payload.get('middle_name'): patient.name[0].given[1] = payload.get("middle_name") or '-'
		if payload.get('last_name'): patient.name[0].family = payload.get("last_name") or '-'
		if payload.get('gender'): patient.gender = payload.get('gender').lower()
		birth_date = payload.get('birth_date')
		if birth_date:
			validate_date(birth_date, True)
			patient.birthDate = birth_date
		patient.telecom[0].value = payload.get("phone") or '-'
		client_id = payload.get('client_id')
		patient.telecom[1].value = payload.get("email") or f'{client_id}@lonius.co.ke'
		shr.resource('Patient',**json.loads(patient.json())).save()
		#GET PATIENT DETAILS (JSON)
		patient_id = patient.id
		# patient_data = _get_patient(patient_id)
		#GET EVERYTHING ABOUT THIS PATIENT AND RETURN.
		filters = {}
		patient_data = fhir_server_get_resource(resourceType = f"Patient/{patient_id}/$everything?_format=json", payload = filters)
		# bundle = Bundle()
		# frappe.msgprint(patient_data)
		# processed_patient_data = bundle.parse_obj(patient_data.json())
		return json.loads(patient_data.text)
	except ResourceNotFound as e:
		frappe.throw(f'{e}.')
	except MultipleResourcesFound as e:
		frappe.throw(f'{e}.')
	except OperationOutcome as e:
		frappe.throw(f'There was an operational error: {e}')
	except InvalidResponse as e:
		frappe.throw(f'{e}.')

@frappe.whitelist()
def shr_post_patient(payload, facility_provider):
	patient = Patient()

	#SEARCH FOR PATIENT WITH SAME ID. IF EXISTING, DO AN UPDATE INSTEAD.
	client_id = payload.get('client_id')
	# frappe.msgprint('CLIENT: ' + client_id)
	patients_resources = shr.resources('Patient')
	patient_with_id_obj = patients_resources.search(identifier__value = client_id).first()
	patient_with_id = Patient.parse_obj(patient_with_id_obj.serialize()) if patient_with_id_obj else None
	if patient_with_id: 
		return update_patient_details(shr = shr, patient = patient_with_id, payload = payload)
	#SAVE THE ID
	identifier = Identifier()
	identifier.value = client_id
	identifier.system = 'https://client-registry.lonius.cloud'
	identifier.use = "official"
	patient.identifier = [identifier]
	
	#VALIDATE THE DATE AND SAVE
	birth_date = payload.get('birth_date')
	if birth_date:
		validate_date(birth_date, True)
		patient.birthDate = birth_date

	#SAVE THE GENDER
	if payload.get('gender'): patient.gender = payload.get('gender').lower()

	#SAVE THE NAME
	name = HumanName()
	name.use = "official"
	if payload.get('last_name'): name.family = payload.get('last_name')
	name.given = [payload.get('first_name') or "-", payload.get('middle_name') or "-"]
	patient.name = [name]

	#SAVE THE PHONE AND EMAIL
	telecom_phone = ContactPoint()
	telecom_phone.system = 'phone'
	telecom_phone.use = 'mobile'
	telecom_phone.value = payload.get('phone') or '-'

	#EMAIL
	if frappe.utils.validate_email_address(payload.get('email')) == '' and payload.get('email'):
		frappe.throw("The email address is not valid")
	telecom_email = ContactPoint()
	telecom_email.system = 'email'
	telecom_email.use = 'home'
	telecom_email.value = payload.get('email') or f'{client_id}@lonius.co.ke'
	patient.telecom = [telecom_phone, telecom_email]

	#SAVE THE RECORD
	shr.resource('Patient',**json.loads(patient.json())).save()
	# patients_resources = shr.resources('Patient')
	# patient_with_id_obj = patients_resources.search(identifier__value = client_id).first()
	# patient_with_id = Patient.parse_obj(patient_with_id_obj.serialize()) if patient_with_id_obj else None
	return patient

def _get_patient(patient_id):
	patient = shr.reference('Patient', patient_id).to_resource() #shr.resources('Patient')
	# patient.search(_id=patient_id)
	return patient