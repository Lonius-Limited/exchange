import frappe
from exchange.api.shr_fhir.organization import shr_process_organization

@frappe.whitelist()
def create_credentials(payload):
	payload = frappe._dict(payload)
	email, facility_name, facility_id = payload.get("email"), payload.get("facility_name"), payload.get("facility_id")
	if not email or not facility_name:
		frappe.throw("Please provide both the email and facility name in order to register.")
	frappe.only_for("System Manager")
	if frappe.db.exists("User", email, cache=True):
		return generate_api_keys(email)
	api_secret = frappe.generate_hash(length=15)
	api_key = frappe.generate_hash(length=15)
	args = {
		"doctype": "User",
		"send_welcome_email": 0,
		"email": email,
		"first_name": facility_name,
		"username": facility_id,
		"user_type": "System User",
		"api_secret": api_secret,
		"api_key": api_key,
		"enabled": True
	}
	user = frappe.get_doc(args)
	user.db_insert()
	role_args  = {
		"doctype": "Has Role",
		'docstatus': 0,
		'parent': email,
		'parentfield': 'roles',
		'parenttype': 'User',
		'role': 'System Manager'
	}
	frappe.get_doc(role_args).db_insert()
	user = frappe.get_doc("User", email, cache=False)
	user.api_secret = api_secret

	#REGISTER THE FACILITY IN THE SHR FOR FUTURE REFERENCES. (FHIR ORGANIZATION)
	shr_process_organization(user)
	return user
	# user = frappe.get_doc(dict(
	# 	doctype="User",
	# 	email=email,
	# 	first_name=facility_name,
	# 	send_welcome_email = False,
	# 	enabled = True,
	# 	api_secret = api_secret,
	# 	api_key = api_key
	# )).insert()
	# user.api_secret = api_secret
	# return user
	# user = frappe.new_doc("User")
	# user.email = email
	# user.send_welcome_email = False
	# user.first_name = facility_name
	# user.name = email
	# user.user_type = "System User"
	# user.append('roles',dict(role='System Manager'))
	# user.save(ignore_permissions=True)
	# return generate_api_keys(user)

def generate_api_keys(user):
	user_details = frappe.get_doc("User", user)
	api_secret = frappe.generate_hash(length=15)
	if not user_details.api_key:
		api_key = frappe.generate_hash(length=15)
		user_details.api_key = api_key
	user_details.api_secret = api_secret
	user_details.save()
	user_details.api_secret = api_secret
	return user_details

@frappe.whitelist()
def validate_facility(facility_id):
	this_user_data = frappe.get_doc("User", frappe.session.user)
	
 	#POST TO THE SHR FOR PROCESSING
	facility_shr_id = shr_process_organization(this_user_data)
	facility_name = this_user_data.get('first_name')
	return facility_shr_id, facility_name#payload[0].get('pn')