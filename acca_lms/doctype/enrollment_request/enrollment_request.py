# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class EnrollmentRequest(Document):
	def validate(self):
		"""Validate enrollment request before saving"""
		# Prevent duplicate requests
		if self.is_new():
			existing = frappe.db.exists("Enrollment Request", {
				"student": self.student,
				"course": self.course,
				"status": ["in", ["Pending", "Approved"]],
				"name": ["!=", self.name]
			})
			if existing:
				frappe.throw(_("An enrollment request for this course already exists"))

		# Check if already enrolled
		if frappe.db.exists("LMS Enrollment", {
			"course": self.course,
			"member": self.student,
			"member_status": "Active"
		}):
			frappe.throw(_("Student is already enrolled in this course"))

	def on_update(self):
		"""Handle status changes"""
		if self.has_value_changed("status"):
			if self.status == "Approved":
				self.create_lms_enrollment()
				self.send_approval_email()
			elif self.status == "Rejected":
				self.send_rejection_email()

	def create_lms_enrollment(self):
		"""Create LMS Enrollment when request is approved"""
		try:
			# Check if enrollment already exists
			if frappe.db.exists("LMS Enrollment", {
				"course": self.course,
				"member": self.student
			}):
				frappe.msgprint(_("Enrollment already exists"), indicator="orange")
				return

			# Create enrollment
			enrollment = frappe.get_doc({
				"doctype": "LMS Enrollment",
				"course": self.course,
				"member": self.student,
				"member_status": "Active"
			})
			enrollment.insert(ignore_permissions=True)
			frappe.db.commit()

			frappe.msgprint(_("Enrollment created successfully"), indicator="green")

		except Exception as e:
			frappe.log_error(f"Failed to create enrollment: {str(e)}", "Enrollment Request")
			frappe.throw(_("Failed to create enrollment. Please try again."))

	def send_approval_email(self):
		"""Send approval notification to student"""
		try:
			course = frappe.get_doc("LMS Course", self.course)
			student = frappe.get_doc("User", self.student)

			subject = f"Enrollment Approved: {course.title}"
			message = f"""
				<h3>Enrollment Approved</h3>
				<p>Dear {student.full_name},</p>
				<p>Your enrollment request for <strong>{course.title}</strong> has been approved!</p>
				<p>You can now access the course and start learning.</p>
				<p><a href="{frappe.utils.get_url()}/courses/{course.name}" class="btn btn-primary">Go to Course</a></p>
				<br>
				<p>Happy Learning!</p>
				<p>ACCA LMS Team</p>
			"""

			frappe.sendmail(
				recipients=[student.email],
				subject=subject,
				message=message,
				header=["Enrollment Approved", "green"]
			)

		except Exception as e:
			frappe.log_error(f"Failed to send approval email: {str(e)}", "Enrollment Request")

	def send_rejection_email(self):
		"""Send rejection notification to student"""
		try:
			course = frappe.get_doc("LMS Course", self.course)
			student = frappe.get_doc("User", self.student)

			reason = self.admin_notes or "No specific reason provided."

			subject = f"Enrollment Request Update: {course.title}"
			message = f"""
				<h3>Enrollment Request Status</h3>
				<p>Dear {student.full_name},</p>
				<p>We regret to inform you that your enrollment request for <strong>{course.title}</strong> could not be approved at this time.</p>
				<p><strong>Reason:</strong> {reason}</p>
				<p>If you have any questions, please contact the administrator.</p>
				<br>
				<p>ACCA LMS Team</p>
			"""

			frappe.sendmail(
				recipients=[student.email],
				subject=subject,
				message=message,
				header=["Enrollment Request Update", "orange"]
			)

		except Exception as e:
			frappe.log_error(f"Failed to send rejection email: {str(e)}", "Enrollment Request")


def send_admin_notification(request_name):
	"""Send notification to admins about new enrollment request"""
	try:
		request = frappe.get_doc("Enrollment Request", request_name)
		course = frappe.get_doc("LMS Course", request.course)
		student = frappe.get_doc("User", request.student)

		# Get system managers
		admins = frappe.get_all(
			"Has Role",
			filters={"role": "System Manager", "parenttype": "User"},
			pluck="parent"
		)

		if not admins:
			return

		subject = f"New Enrollment Request: {course.title}"
		message = f"""
			<h3>New Enrollment Request</h3>
			<p><strong>Student:</strong> {student.full_name} ({student.email})</p>
			<p><strong>Course:</strong> {course.title}</p>
			<p><strong>Date:</strong> {frappe.utils.format_datetime(request.request_date)}</p>
			{f'<p><strong>Student Notes:</strong> {request.notes}</p>' if request.notes else ''}
			<p><a href="{frappe.utils.get_url()}/app/enrollment-request/{request.name}" class="btn btn-primary">View Request</a></p>
		"""

		frappe.sendmail(
			recipients=admins,
			subject=subject,
			message=message,
			header=["New Enrollment Request", "blue"]
		)

	except Exception as e:
		frappe.log_error(f"Failed to send admin notification: {str(e)}", "Enrollment Request")
