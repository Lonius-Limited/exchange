import frappe, requests, json
from fhirpy import AsyncFHIRClient
from fhirpy import SyncFHIRClient

fhir_api_key = frappe.db.get_single_value('Exchange Settings', 'shr_key') or "api_key"
fhir_api_secret = frappe.db.get_single_value('Exchange Settings', 'shr_secret') or "api_secret"
fhir_shr_endpoint = frappe.db.get_single_value('Exchange Settings', 'shr_search_endpoint') or "https://shr.loniushealth.com/fhir"

@frappe.whitelist()
def fhir_server_connect(use_async = False):
	if use_async:
		return AsyncFHIRClient(fhir_shr_endpoint, authorization=f'Bearer {fhir_api_key}:{fhir_api_secret}')
	return SyncFHIRClient(url= fhir_shr_endpoint, extra_headers={fhir_api_key:fhir_api_secret})

@frappe.whitelist()
def fhir_server_get_resource(resourceType, payload):
	headers =  {
		'Content-Type': 'application/json',#'application/fhir+json;charset=UTF-8',
		'Authorization': f'token {fhir_api_key}:{fhir_api_secret}'
	}
	fhir_shr_endpoint_resource = f'{fhir_shr_endpoint}/{resourceType}'
	# frappe.msgprint('URL: '+ fhir_shr_endpoint_resource)
	cr_data = requests.get(fhir_shr_endpoint_resource, params=payload, headers=headers)
	# payload = json.loads(cr_data.text)#.get('message')#cr_data.json()
	# frappe.msgprint(payload)
	# payload.update(client_id, payload.get('client_id') or 201)
	return cr_data