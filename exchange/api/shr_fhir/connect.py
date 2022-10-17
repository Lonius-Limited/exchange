import frappe
from fhirpy import AsyncFHIRClient
from fhirpy import SyncFHIRClient

@frappe.whitelist()
def fhir_server_connect(use_async = False):
	fhir_api_key = frappe.db.get_single_value('Exchange Settings', 'shr_key') or "api_key"
	fhir_api_secret = frappe.db.get_single_value('Exchange Settings', 'shr_secret') or "api_secret"
	exchange_url = frappe.db.get_single_value('Exchange Settings', 'exchange_url') or "https://shr.loniushealth.com/fhir"
	if use_async:
		return AsyncFHIRClient(exchange_url, authorization=f'Bearer {fhir_api_key}:{fhir_api_secret}')
	return SyncFHIRClient(url= exchange_url, extra_headers={fhir_api_key:fhir_api_secret})