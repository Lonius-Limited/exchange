import frappe
# from fhirpy import AsyncFHIRClient
from fhirpy import SyncFHIRClient

@frappe.whitelist()
def fhir_server_connect():
	fhir_api_key = frappe.db.get_single_value('Exchange Settings', 'shr_key') or "api_key"
	fhir_api_secret = frappe.db.get_single_value('Exchange Settings', 'shr_secret') or "api_secret"
	return SyncFHIRClient(url='http://hie.loniushealth.com:8081/fhir', extra_headers={fhir_api_key:fhir_api_secret})