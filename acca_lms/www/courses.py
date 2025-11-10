# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def get_context(context):
	"""Course listing page context"""
	context.no_cache = 1

	# Get all published courses
	courses = frappe.get_all(
		"LMS Course",
		filters={"published": 1, "upcoming": 0},
		fields=["name", "title", "short_introduction", "image", "level"],
		order_by="creation desc"
	)

	# Add lesson count and duration for each course
	for course in courses:
		course.lesson_count = frappe.db.count("Course Lesson", {"course": course.name})

		# Calculate total duration
		total_duration = frappe.db.sql("""
			SELECT SUM(duration)
			FROM `tabCourse Lesson`
			WHERE course = %s
		""", course.name)[0][0] or 0

		course.duration = total_duration

	context.courses = courses
	context.total_courses = len(courses)

	return context
