# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

@frappe.whitelist()
def request_enrollment(course, notes=None):
	"""
	Create enrollment request
	Called from course detail page
	"""
	# Authentication check
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to request enrollment"))

	# Validate course exists
	if not frappe.db.exists("LMS Course", course):
		frappe.throw(_("Course not found"))

	# Check if already enrolled
	existing_enrollment = frappe.db.exists("LMS Enrollment", {
		"course": course,
		"member": frappe.session.user,
		"member_status": "Active"
	})

	if existing_enrollment:
		return {
			"success": False,
			"message": _("You are already enrolled in this course")
		}

	# Check if request already exists
	existing_request = frappe.db.exists("Enrollment Request", {
		"course": course,
		"student": frappe.session.user,
		"status": ["in", ["Pending", "Approved"]]
	})

	if existing_request:
		return {
			"success": False,
			"message": _("You already have a pending enrollment request for this course")
		}

	# Create request
	try:
		request = frappe.get_doc({
			"doctype": "Enrollment Request",
			"student": frappe.session.user,
			"course": course,
			"status": "Pending",
			"notes": notes or ""
		})
		request.insert(ignore_permissions=True)
		frappe.db.commit()

		# Send notification to admins
		from acca_lms.doctype.enrollment_request.enrollment_request import send_admin_notification
		send_admin_notification(request.name)

		return {
			"success": True,
			"message": _("Enrollment request submitted successfully"),
			"request_id": request.name
		}

	except Exception as e:
		frappe.log_error(f"Enrollment request error: {str(e)}", "Enrollment API")
		return {
			"success": False,
			"message": _("Failed to submit enrollment request. Please try again.")
		}


@frappe.whitelist()
def get_enrollment_status(course):
	"""
	Get enrollment status for current user and course
	Returns: enrolled, pending, rejected, or none
	"""
	if frappe.session.user == "Guest":
		return {
			"status": "none",
			"message": _("Please login")
		}

	# Check enrollment
	enrollment = frappe.db.exists("LMS Enrollment", {
		"course": course,
		"member": frappe.session.user,
		"member_status": "Active"
	})

	if enrollment:
		return {
			"status": "enrolled",
			"message": _("You are enrolled in this course")
		}

	# Check request
	request = frappe.db.get_value("Enrollment Request", {
		"course": course,
		"student": frappe.session.user,
		"status": ["in", ["Pending", "Approved", "Rejected"]]
	}, ["name", "status"], as_dict=True)

	if request:
		if request.status == "Pending":
			return {
				"status": "pending",
				"message": _("Your enrollment request is pending approval"),
				"request_id": request.name
			}
		elif request.status == "Approved":
			return {
				"status": "approved",
				"message": _("Your enrollment has been approved"),
				"request_id": request.name
			}
		elif request.status == "Rejected":
			return {
				"status": "rejected",
				"message": _("Your enrollment request was rejected"),
				"request_id": request.name
			}

	return {
		"status": "none",
		"message": _("Not enrolled")
	}


@frappe.whitelist()
def cancel_enrollment_request(request_id):
	"""
	Cancel a pending enrollment request
	"""
	try:
		request = frappe.get_doc("Enrollment Request", request_id)

		# Check ownership
		if request.student != frappe.session.user and not frappe.has_permission("Enrollment Request", "write"):
			frappe.throw(_("You don't have permission to cancel this request"))

		# Can only cancel pending requests
		if request.status != "Pending":
			frappe.throw(_("Only pending requests can be cancelled"))

		request.status = "Cancelled"
		request.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": True,
			"message": _("Enrollment request cancelled")
		}

	except Exception as e:
		frappe.log_error(f"Cancel request error: {str(e)}", "Enrollment API")
		return {
			"success": False,
			"message": _("Failed to cancel request")
		}


@frappe.whitelist()
def get_my_enrollments():
	"""
	Get all enrollments for current user
	"""
	if frappe.session.user == "Guest":
		return []

	enrollments = frappe.get_all(
		"LMS Enrollment",
		filters={
			"member": frappe.session.user,
			"member_status": "Active"
		},
		fields=["name", "course", "creation"],
		order_by="creation desc"
	)

	# Get course details
	for enrollment in enrollments:
		course = frappe.get_doc("LMS Course", enrollment.course)
		enrollment.course_title = course.title
		enrollment.course_image = course.image
		enrollment.course_url = f"/courses/{course.name}"

	return enrollments


@frappe.whitelist()
def get_my_requests():
	"""
	Get all enrollment requests for current user
	"""
	if frappe.session.user == "Guest":
		return []

	requests = frappe.get_all(
		"Enrollment Request",
		filters={"student": frappe.session.user},
		fields=["name", "course", "status", "request_date"],
		order_by="request_date desc"
	)

	# Get course details
	for request in requests:
		course = frappe.get_doc("LMS Course", request.course)
		request.course_title = course.title
		request.course_image = course.image

	return requests
