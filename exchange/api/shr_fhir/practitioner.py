import frappe
# import asyncio
import json

@frappe.whitelist()
def validate_practitioner(patient_id):
    #CONNECT TO THE PROVIDER REGISTRY AND CHECK FOR EXISTENCE OF THE CLIENT ID
    return True