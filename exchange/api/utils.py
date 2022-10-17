import frappe
from exchange.api.facility_registry.utils import validate_facility
from exchange.api.provider_registry.utils import validate_provider

def validate_facility_provider(facility_id, provider_id):
    if validate_facility(facility_id):
        if validate_provider(provider_id):
            return True
        else:
            frappe.throw('The Provider is either not registered in the Provider Registry or is not authorized to transact through this Exchange.')
    else:
        frappe.throw('The Facility is either not registered in the Facility Registry or is not authorized to transact through this Exchange.')