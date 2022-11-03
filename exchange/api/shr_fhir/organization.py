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
from fhir.resources.organization import Organization
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.identifier import Identifier
from fhir.resources.bundle import Bundle

shr = fhir_server_connect()

@frappe.whitelist()
def shr_process_organization(facility):
	facility_number = facility.get('username')
	# pr_resources = shr.resources('Practitioner')
	# pr_obj = pr_resources.search(identifier__value = provider_number).first()
	# pr_with_id = Practitioner.parse_obj(pr_obj.serialize()) if pr_obj else None
	shr_organization_id = get_facility_shr_id(facility_number)
	if shr_organization_id:
		return shr_organization_id #_update_practitioner_details(shr = shr, practitioner = pr_with_id, payload = provider)
	
	organization = Organization()
	#PRACTITIONER WAS NOT FOUND IN THE DATABASE. SINCE WE HAVE THEIR DETAILS FROM THE PROVIDER REGISTRY, LETS REGISTER THEM IN THE SHR
	identifier = Identifier()
	identifier.value = facility_number
	identifier.system = 'https://facility-register.lonius.cloud'
	identifier.use = "official"
	organization.identifier = [identifier]

	#SAVE THE NAME
	organization.name = facility.get('first_name')

	#SAVE THE RECORD
	shr.resource('Organization',**json.loads(organization.json())).save()
 
	shr_organization_id = get_facility_shr_id(facility_number)
	return shr_organization_id

@frappe.whitelist()
def get_facility_shr_id(facility_registry_id):
	#FIND THE RECORD WE JUST SAVED (USING IDENTIFIER) AND RETURN ITS ID.
	filters = {}
	pr_search_bundle = fhir_server_get_resource(resourceType = f"Organization/_search?identifier={facility_registry_id}&_format=json", payload = filters)
	data = json.loads(pr_search_bundle.text)
	oneBundle = Bundle.parse_obj(data)
	matched_organization = None
	if oneBundle.entry is not None:
		matched_organization = oneBundle.entry[0].resource.id
	return matched_organization