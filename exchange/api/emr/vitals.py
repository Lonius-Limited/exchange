import frappe
from exchange.api.client_registry.utils import validate_patient
from exchange.api.utils import validate_facility_provider
from exchange.api.shr_fhir.observation import shr_post_vitals

@frappe.whitelist()
def post_vitals(payload):
	client_id = payload.get('client_id')
	validate_patient(client_id)
	facility_provider = validate_facility_provider(payload.get("facility_id"), payload.get("provider_id"))
	if not payload.get('date_time'):
		frappe.throw('Please provide the date and time that these vitals were taken')
	return shr_post_vitals(payload = payload, facility_provider = facility_provider)