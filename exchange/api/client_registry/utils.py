import frappe
import requests
import json

@frappe.whitelist()
def validate_patient(client_id):
	#CONNECT TO THE CLIENT REGISTRY AND CHECK FOR EXISTENCE OF THE CLIENT ID
	return True

def post_client(payload):
	#CONNECT TO THE CLIENT REGISTRY AND RETURN A REGISTERED PATIENT/CLIENT WITH ID.
	# payload.client_id = payload.get('client_id') or 200
	# frappe.msgprint(payload)
	cr_api_key = frappe.db.get_single_value('Exchange Settings', 'client_key') or "api_key"
	cr_api_secret = frappe.db.get_single_value('Exchange Settings', 'client_secret') or "api_secret"
	api_url = frappe.db.get_single_value('Exchange Settings', 'client_search_endpoint')
	headers =  {
		'Content-Type': 'application/json',
		'Authorization': f'token {cr_api_key}:{cr_api_secret}'
	}
	payload = {'payload': payload}
	cr_data = requests.post(api_url, json=payload, headers=headers)
	payload = json.loads(cr_data.text).get('message')#cr_data.json()
	frappe.msgprint(payload)
	# payload.update(client_id, payload.get('client_id') or 201)
	return payload