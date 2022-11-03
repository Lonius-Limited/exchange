import frappe
from exchange.api.facility_registry.utils import validate_facility
from exchange.api.provider_registry.utils import validate_provider

def validate_facility_provider(facility_id, provider_id):
	facility_data = validate_facility(facility_id)
	provider_data = validate_provider(provider_id)
	if facility_data[0]:
		if provider_data[0]:
			return facility_data[0], facility_data[1], provider_data[0], provider_data[1]
		else:
			frappe.throw('The Provider is either not registered in the Provider Registry or is not authorized to transact through this Exchange.')
	else:
		frappe.throw('The Facility is either not registered in the Facility Registry or is not authorized to transact through this Exchange.')

def log_connection(category, provider_id, provider, client_id, client, description):
	frappe.get_doc({
		'doctype': 'Connection Log',
		'category': category,
		'facility': frappe.session.user,
		'provider_id': provider_id,
		'provider': provider,
		'client_id': client_id,
		'client': client,
		'details': description
	}).insert()
	return