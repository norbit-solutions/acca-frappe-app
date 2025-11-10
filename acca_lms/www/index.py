# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def get_context(context):
	"""Landing page context"""
	context.no_cache = 1

	# Featured courses (limit to 3)
	context.featured_courses = frappe.get_all(
		"LMS Course",
		filters={"published": 1, "upcoming": 0},
		fields=["name", "title", "short_introduction", "image", "level"],
		order_by="creation desc",
		limit=3
	) or []

	# Add lesson count for featured courses
	for course in context.featured_courses:
		course.lesson_count = frappe.db.count("Course Lesson", {"course": course.name})

	# All published courses for browse section
	context.all_courses = frappe.get_all(
		"LMS Course",
		filters={"published": 1, "upcoming": 0},
		fields=["name", "title", "short_introduction", "image", "level"],
		order_by="creation desc",
		limit=6
	) or []

	# Add lesson count
	for course in context.all_courses:
		course.lesson_count = frappe.db.count("Course Lesson", {"course": course.name})

	# Statistics
	context.stats = {
		"total_courses": frappe.db.count("LMS Course", {"published": 1}),
		"total_students": frappe.db.count("LMS Enrollment", {"member_status": "Active"}),
		"total_lessons": frappe.db.count("Course Lesson")
	}

	return context
