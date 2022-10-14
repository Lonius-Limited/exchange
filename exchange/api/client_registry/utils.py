import frappe

@frappe.whitelist()
def validate_patient(client_id):
	#CONNECT TO THE CLIENT REGISTRY AND CHECK FOR EXISTENCE OF THE CLIENT ID
	return True

def post_client(payload):
	#CONNECT TO THE CLIENT REGISTRY AND RETURN A REGISTERED PATIENT/CLIENT WITH ID.
	payload.client_id = payload.get('client_id') or 200
	return payload