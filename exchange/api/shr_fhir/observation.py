import frappe
from datetime import datetime
from fhirpy.base.exceptions import (
	ResourceNotFound,
	OperationOutcome,
	MultipleResourcesFound,
	InvalidResponse
)
from exchange.api.shr_fhir.connect import fhir_server_connect
from exchange.api.client_registry.utils import validate_patient
from exchange.api.provider_registry.utils import validate_provider
from exchange.api.facility_registry.utils import validate_facility
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient

@frappe.whitelist()
def shr_post_vitals(payload):
	client_id = payload.get('client_id')
	validate_patient(client_id)
	validate_provider(payload.get('provider_id'))
	validate_facility(payload.get('facility_id'))
	if not payload.get('date_time'):
		frappe.throw('Please provide the date and time that these vitals were taken')
	shr = fhir_server_connect(use_async = False)
	patients = shr.resources('Patient')
	try:
		patient = patients.search(identifier = client_id).get()
		# patient_id = patient['id']
		observation = _generate_observation_bundle(shr, patient, payload)
		return observation
	except ResourceNotFound:
		frappe.throw('We could not find a client with that ID in the Shared Health Record Repository. Try registering the patient again.')
	except MultipleResourcesFound:
		#IDEALLY THIS SHOULD/WILL NEVER HAPPEN :)
		frappe.throw('Multiple patients with the same identifier were found in the Shared Health Record Repository!')
	except OperationOutcome as e:
		frappe.throw(f'There was an operational error: {e}')
	except InvalidResponse:
		frappe.throw('There was an error while trying to process the request. Try again later')
def _generate_observation_bundle(shr, patient, payload):
	vitals_elements = ["respiratory_rate", "heart_rate", "systolic_bp", "diastolic_bp", "body_temperature", "weight", "height", "oxygen_saturation"]
	# patient_id = patient
	hasMember = []
	for element in vitals_elements:
		if payload.get(element): 
			element_observaton = _save_single_observation(shr, patient, payload.get('date_time'), element, payload.get(element))
			element_observation_id = element_observaton['id']
			hasMember.append(
				{
					"reference": f"Observation/{element_observation_id}"
				}
			)
	observation = shr.resource('Observation')
	observation['status'] = 'final'
	observation['effectiveDateTime'] = payload.get('date_time')
	observation['issued'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
	observation['subject'] = patient.to_reference()
	observation['category'] = [
		{
			"coding": [
				{
				"system": "http://terminology.hl7.org/CodeSystem/observation-category",
				"code": "vital-signs",
				"display": "Vital Signs"
				}
			]
		}
	]
	observation['code'] = {
		"coding": [
			{
				"system": "http://loinc.org",
				"code": "85353-1",
				"display": "Vital signs, weight, height, head circumference, oxygen saturation and BMI panel"
			}
		],
		"text": "Vital signs Panel"
	}
	observation['hasMember'] = hasMember
	observation.save()
	return observation

def _save_single_observation(shr, patient, date_time, element, value):
	observation = shr.resource('Observation')
	observation['status'] = 'registered'
	observation['effectiveDateTime'] = date_time
	observation['issued'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
	observation['subject'] = patient.to_reference()
	observation['category'] = [
		{
			"coding": [
				{
				"system": "http://terminology.hl7.org/CodeSystem/observation-category",
				"code": "vital-signs",
				"display": "Vital Signs"
				}
			]
		}
	]
	code = _return_observation_code(element)
	if code: observation['code'] = code
	result = _return_observation_result(element, value)
	if result: observation['valueQuantity'] = result
	observation.save()
	return observation
	
def _return_observation_code(observation):
	if observation == 'body_temperature':
		return {
			"coding": [
				{
					"system": "http://acme.lab",
					"code": "BT",
					"display": "Body temperature"
				},
				{
					"system": "http://loinc.org",
					"code": "8310-5",
					"display": "Body temperature"
				},
				{
					"system": "http://loinc.org",
					"code": "8331-1",
					"display": "Oral temperature"
				},
				{
					"system": "http://snomed.info/sct",
					"code": "56342008",
					"display": "Temperature taking"
				}
			],
			"text": "Temperature"
		}
	elif observation == 'respiratory_rate':
		return {
			"coding": [
       			{
					"system": "http://loinc.org",
					"code": "9279-1",
					"display": "Respiratory Rate"
				}
            ],
			"text": "Respiratory Rate"
		}
	elif observation == 'heart_rate':
		return {
			"coding": [
       			{
					"system": "http://loinc.org",
					"code": "8867-4",
					"display": "Heart Rate"
				}
            ],
			"text": "Heart Rate"
		}
	elif observation == 'systolic_bp':
		return {
			"coding": [
       			{
					"system": "http://loinc.org",
					"code": "8480-6",
					"display": "Systolic Blood Pressure"
				}
            ],
			"text": "Systolic Blood Pressure"
		}
	elif observation == 'diastolic_bp':
		return {
			"coding": [
       			{
					"system": "http://loinc.org",
					"code": "8462-4",
					"display": "Diastolic Blood Pressure"
				}
            ],
			"text": "Diastolic Blood Pressure"
		}
	elif observation == 'weight':
		return {
			"coding": [
       			{
					"system": "http://loinc.org",
					"code": "29463-7",
					"display": "Body Weight"
				}
            ],
			"text": "Body Weight"
		}
	elif observation == 'height':
		return {
			"coding": [
       			{
					"system": "http://loinc.org",
					"code": "8302-2",
					"display": "Body Height"
				}
            ],
			"text": "Body Height"
		}
	elif observation == 'oxygen_saturation':
		return {
			"coding": [
       			{
					"system": "http://loinc.org",
					"code": "2708-6",
					"display": "Oxygen Saturation"
				}
            ],
			"text": "Oxygen Saturation"
		}
	else:
		return None

def _return_observation_result(observation, value):
	if observation == 'body_temperature':
		return {
			"value": value,
			"unit": "degrees C",
			"system": "http://unitsofmeasure.org",
			"code": "Cel"
		}
	elif observation == 'respiratory_rate':
		return {
			"value": value,
			"unit": "/min",
			"system": "http://unitsofmeasure.org",
			"code": "/min"
		}
	elif observation == 'heart_rate':
		return {
			"value": value,
			"unit": "/min",
			"system": "http://unitsofmeasure.org",
			"code": "/min"
		}
	elif observation == 'systolic_bp':
		return {
			"value": value,
			"unit": "mm[Hg]",
			"system": "http://unitsofmeasure.org",
			"code": "mm[Hg]"
		}
	elif observation == 'diastolic_bp':
		return {
			"value": value,
			"unit": "mm[Hg]",
			"system": "http://unitsofmeasure.org",
			"code": "mm[Hg]"
		}
	elif observation == 'weight':
		return {
			"value": value,
			"unit": "kg",
			"system": "http://unitsofmeasure.org",
			"code": "kg"
		}
	elif observation == 'height':
		return {
			"value": value,
			"unit": "cm",
			"system": "http://unitsofmeasure.org",
			"code": "cm"
		}
	elif observation == 'oxygen_saturation':
		return {
			"value": value,
			"unit": "%",
			"system": "http://unitsofmeasure.org",
			"code": "%"
		}
	else:
		return None