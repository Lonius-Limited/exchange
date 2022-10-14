import frappe

@frappe.whitelist()
def create_credentials(payload):
	payload = frappe._dict(payload)
	email, facility_name = payload.get("email"), payload.get("facility_name")
	if not email or not facility_name:
		frappe.throw("Please provide both the email and facility name in order to register.")
	frappe.only_for("System Manager")
	if frappe.db.exists("User", email, cache=True):
		return generate_api_keys(email)
	user = frappe.get_doc(
		dict(doctype="User", email=email, first_name=facility_name, send_welcome_email = False, user_type = "System User")
	)
	user.db_insert()

	# user = frappe.new_doc("User")
	# user.email = email
	# user.send_welcome_email = False
	# user.first_name = facility_name
	# user.name = email
	# user.user_type = "System User"
	user.append('roles',dict(role='System Manager'))
	user.save(ignore_permissions=True)
	return generate_api_keys(user)

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