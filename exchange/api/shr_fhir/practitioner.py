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
from fhir.resources.practitioner import Practitioner
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.identifier import Identifier
from fhir.resources.bundle import Bundle

shr = fhir_server_connect()

@frappe.whitelist()
def shr_process_provider(provider):
	provider_number = provider.get('pn')
	# pr_resources = shr.resources('Practitioner')
	# pr_obj = pr_resources.search(identifier__value = provider_number).first()
	# pr_with_id = Practitioner.parse_obj(pr_obj.serialize()) if pr_obj else None
	shr_provider_id = get_provider_shr_id(provider_number)
	if shr_provider_id:
		return shr_provider_id #_update_practitioner_details(shr = shr, practitioner = pr_with_id, payload = provider)
	
	practitioner = Practitioner()
	#PRACTITIONER WAS NOT FOUND IN THE DATABASE. SINCE WE HAVE THEIR DETAILS FROM THE PROVIDER REGISTRY, LETS REGISTER THEM IN THE SHR
	identifier = Identifier()
	identifier.value = provider_number
	identifier.system = 'https://provider-registry.lonius.cloud'
	identifier.use = "official"
	practitioner.identifier = [identifier]

	#SAVE THE NAME
	name = HumanName()
	name.use = "official"
	if provider.get('last_name'): name.family = provider.get('last_name')
	name.given = [provider.get('first_name') or "-", provider.get('middle_name') or "-"]
	practitioner.name = [name]

	#SAVE THE GENDER
	if provider.get('gender'): practitioner.gender = provider.get('gender').lower()

	#SAVE THE RECORD
	shr.resource('Practitioner',**json.loads(practitioner.json())).save()
 
	shr_provider_id = get_provider_shr_id(provider_number)
	return shr_provider_id

@frappe.whitelist()
def get_provider_shr_id(provider_registry_id):
	#FIND THE RECORD WE JUST SAVED (USING IDENTIFIER) AND RETURN ITS ID.
	filters = {}
	pr_search_bundle = fhir_server_get_resource(resourceType = f"Practitioner/_search?identifier={provider_registry_id}&_format=json", payload = filters)
	data = json.loads(pr_search_bundle.text)
	oneBundle = Bundle.parse_obj(data)
	matched_practitioner = None
	if oneBundle.entry is not None:
		matched_practitioner = oneBundle.entry[0].resource.id
	return matched_practitioner