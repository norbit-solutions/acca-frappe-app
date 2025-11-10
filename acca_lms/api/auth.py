# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def on_user_login(login_manager):
	"""
	Enforce single device login
	Called on session creation (via hook in hooks.py)
	"""
	# Skip for Guest user
	if frappe.session.user == "Guest":
		return

	# Check if single device login is enabled
	settings = frappe.get_single("Mux Settings")
	if not settings.enable_single_device_login:
		return

	# Enforce single device
	enforce_single_device(frappe.session.user)


def enforce_single_device(user):
	"""
	Logout user from all other devices
	Keep only the current session active
	"""
	try:
		current_sid = frappe.session.sid

		# Get all other sessions for this user
		other_sessions = frappe.get_all(
			"Sessions",
			filters={
				"user": user,
				"sid": ["!=", current_sid]
			},
			pluck="sid"
		)

		# Delete all other sessions
		for sid in other_sessions:
			try:
				frappe.delete_doc("Sessions", sid, ignore_permissions=True, force=True)
			except:
				# Session might already be deleted
				pass

		frappe.db.commit()

		# Log activity
		frappe.log_error(
			f"User {user} logged in. {len(other_sessions)} other session(s) terminated.",
			"Single Device Login"
		)

	except Exception as e:
		frappe.log_error(f"Single device enforcement error: {str(e)}", "Auth")


@frappe.whitelist()
def get_active_sessions():
	"""
	Get all active sessions for current user
	For debugging/admin purposes
	"""
	if frappe.session.user == "Guest":
		return []

	try:
		sessions = frappe.get_all(
			"Sessions",
			filters={"user": frappe.session.user},
			fields=["sid", "lastupdate", "device"],
			order_by="lastupdate desc"
		)

		# Mark current session
		for session in sessions:
			session.is_current = (session.sid == frappe.session.sid)

		return sessions

	except Exception as e:
		frappe.log_error(f"Get sessions error: {str(e)}", "Auth")
		return []


@frappe.whitelist()
def logout_all_sessions():
	"""
	Logout from all devices (including current)
	User-initiated action
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not logged in"))

	try:
		# Get all sessions
		sessions = frappe.get_all(
			"Sessions",
			filters={"user": frappe.session.user},
			pluck="sid"
		)

		# Delete all sessions
		for sid in sessions:
			try:
				frappe.delete_doc("Sessions", sid, ignore_permissions=True, force=True)
			except:
				pass

		frappe.db.commit()

		return {
			"success": True,
			"message": _("Logged out from all devices"),
			"sessions_terminated": len(sessions)
		}

	except Exception as e:
		frappe.log_error(f"Logout all error: {str(e)}", "Auth")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def logout_other_sessions():
	"""
	Logout from all other devices (keep current session)
	User-initiated action
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Not logged in"))

	try:
		enforce_single_device(frappe.session.user)

		return {
			"success": True,
			"message": _("Logged out from all other devices")
		}

	except Exception as e:
		frappe.log_error(f"Logout others error: {str(e)}", "Auth")
		return {"success": False, "error": str(e)}
