# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def get_context(context):
	"""Course detail page context"""
	context.no_cache = 1

	# Get course name from URL
	course_name = frappe.form_dict.course

	if not course_name:
		frappe.throw(_("Course not found"), frappe.DoesNotExistError)

	# Get course
	try:
		course = frappe.get_doc("LMS Course", course_name)
	except:
		frappe.throw(_("Course not found"), frappe.DoesNotExistError)

	# Check if published
	if not course.published or course.upcoming:
		frappe.throw(_("Course not available"), frappe.PermissionError)

	context.course = course

	# User enrollment status
	context.is_enrolled = False
	context.enrollment_requested = False
	context.request_status = None
	context.show_login_prompt = False

	if frappe.session.user == "Guest":
		context.show_login_prompt = True
	else:
		# Check enrollment
		context.is_enrolled = bool(frappe.db.exists(
			"LMS Enrollment",
			{
				"course": course_name,
				"member": frappe.session.user,
				"member_status": "Active"
			}
		))

		# Check pending request
		if not context.is_enrolled:
			request = frappe.db.get_value(
				"Enrollment Request",
				{
					"course": course_name,
					"student": frappe.session.user,
					"status": ["in", ["Pending", "Approved"]]
				},
				["name", "status"],
				as_dict=True
			)

			if request:
				context.enrollment_requested = True
				context.request_status = request.status

	# Get course outline (chapters and lessons)
	context.chapters = get_course_outline(course_name)

	# Calculate course stats
	context.total_lessons = sum([len(ch.get('lessons', [])) for ch in context.chapters])
	context.total_duration = sum([ch.get('total_duration', 0) for ch in context.chapters])

	# Format duration
	if context.total_duration > 0:
		hours = int(context.total_duration / 3600)
		minutes = int((context.total_duration % 3600) / 60)
		context.formatted_duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
	else:
		context.formatted_duration = "N/A"

	return context


def get_course_outline(course_name):
	"""Get course chapters with lessons"""
	chapters = frappe.get_all(
		"Course Chapter",
		filters={"course": course_name},
		fields=["name", "title", "description"],
		order_by="idx asc"
	)

	for chapter in chapters:
		# Get lessons in chapter
		lessons = frappe.get_all(
			"Course Lesson",
			filters={"chapter": chapter.name},
			fields=[
				"name",
				"title",
				"content_type",
				"duration",
				"include_in_preview"
			],
			order_by="idx asc"
		)

		chapter['lessons'] = lessons
		chapter['lesson_count'] = len(lessons)
		chapter['total_duration'] = sum([l.duration or 0 for l in lessons])

	return chapters
