import frappe
import requests, json
from exchange.api.shr_fhir.practitioner import shr_process_provider

@frappe.whitelist()
def validate_provider(provider_id):
	#CONNECT TO THE PROVIDER REGISTRY AND CHECK FOR EXISTENCE OF A VALID PROVIDER BASED ON THEIR REGULATORY NUMBER
	#THE PROVIDER REGISTRY SHOULD VALIDATE LICENCE VALIDITY BEFORE RETURNING TRUE
	pr_api_key = frappe.db.get_single_value('Exchange Settings', 'provider_key') or "api_key"
	pr_api_secret = frappe.db.get_single_value('Exchange Settings', 'provider_secret') or "api_secret"
	api_url = frappe.db.get_single_value('Exchange Settings', 'provider_search_endpoint')
	headers =  {
		'Content-Type': 'application/json',
		'Authorization': f'token {pr_api_key}:{pr_api_secret}'
	}
	payload = {
		'param': provider_id,
		'filters': '{"type": "rin", "status": "Active"}'
	}
	cr_data = requests.post(api_url, json=payload, headers=headers)
	payload = json.loads(cr_data.text).get('message')#cr_data.json()
	# frappe.msgprint(payload)
	if payload and payload[0] and payload[0].get('pn') and payload[0].get('pn') is not None:
		#POST TO THE SHR FOR PROCESSING
		provider_shr_id = shr_process_provider(payload[0])
		f_name, m_name, l_name = payload[0].get('first_name'), payload[0].get('middle_name'), payload[0].get('last_name')
		provider_name = f"{f_name} {m_name} {l_name}"
		return provider_shr_id, provider_name#payload[0].get('pn')
	else:
		return False