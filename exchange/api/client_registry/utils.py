import frappe

@frappe.whitelist()
def validate_patient(patient_id):
	#CONNECT TO THE CLIENT REGISTRY AND CHECK FOR EXISTENCE OF THE CLIENT ID
	return True

def post_client(payload):
	#CONNECT TO THE CLIENT REGISTRY AND RETURN A REGISTERED PATIENT/CLIENT WITH ID.
	payload.client_id = 200
	return payload