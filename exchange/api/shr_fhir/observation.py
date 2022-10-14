import frappe
import asyncio
import json
from fhirpy.base.exceptions import (
	ResourceNotFound,
	OperationOutcome,
	MultipleResourcesFound,
	InvalidResponse,
)
from exchange.api.shr_fhir.connect import fhir_server_connect
from exchange.api.client_registry.utils import validate_patient
from exchange.api.provider_registry.utils import validate_provider
from exchange.api.facility_registry.utils import validate_facility
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient

@frappe.whitelist()
async def shr_post_vitals(payload):
	client_id = payload.get('client_id')
	validate_patient(client_id)
	validate_provider(payload.get('provider_id'))
	validate_facility(payload.get('facility_id'))
	if not payload.get('date_time'):
		frappe.throw('Please provide the date and time that these vitals were taken')
	shr = fhir_server_connect()
	patients = shr.resources('Patient')
	try:
		patient = await patients.search(identifier_system = 'https://client_registry.lonius.cloud',  identifier_value = client_id).get()
		patient_id = 200
		#observation = await _generate_observation_bundle(shr, patient_id, payload)
		return patient_id
	except ResourceNotFound:
		frappe.throw('We could not find a client with that ID in the Shared Health Record Repository. Try registering the patient again.')
	except MultipleResourcesFound:
		#IDEALLY THIS SHOULD/WILL NEVER HAPPEN :)
		frappe.throw('Multiple patients with the same identifier were found in the Shared Health Record Repository!')
	except OperationOutcome as e:
		frappe.throw(f'There was an operational error: {e}')
	except InvalidResponse:
		frappe.throw('There was an error while trying to process the request. Try again later')
async def _generate_observation_bundle(shr, patient, payload):
	# vitals_elements = ["respiratory_rate", "heart_rate", "systolic_bp", "diastolic_bp", "body_temperature", "weight", "height", "oxygen_saturation"]
	vitals_elements = ["body_temperature"]
	patient_id = patient
	hasMember = []
	for element in vitals_elements:
		if payload.get(element): 
			element_observaton = await _save_single_observation(shr, patient_id, payload.get('date_time'), element, payload.get(element))
			element_observation_id = element_observaton['id']
			hasMember.append(
				{
					"reference": f"Observation/{element_observation_id}"
				}
			)
	observation = shr.resource('Observation')
	observation['status'] = 'generated'
	observation['effectiveDateTime'] = date_time
	observation['subject'] = {
		'reference' : f'Patient/{patient_id}'
	}
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
	await observation.save()
	return observation

async def _save_single_observation(shr, patient_id, date_time, observation, value):
	observation = shr.resource('Observation')
	observation['status'] = 'registered'
	observation['effectiveDateTime'] = date_time
	observation['subject'] = {
		'reference' : f'Patient/{patient_id}'
	}
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
	code = _return_observation_code(observation)
	if code: observation['code'] = code
	result = _return_observation_result(observation, value)
	if result: observation['valueQuantity'] = result
	await observation.save()
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
	else:
		return None