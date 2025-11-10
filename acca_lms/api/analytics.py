# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

@frappe.whitelist()
def log_progress(lesson, duration_watched, current_position):
	"""
	Update video view progress
	Called periodically by video player (every 30 seconds)
	"""
	try:
		# Find latest view log for this user and lesson
		view_log = frappe.db.get_value(
			"Video View Log",
			{
				"lesson": lesson,
				"user": frappe.session.user,
				"view_status": ["in", ["Started", "In Progress"]]
			},
			["name"],
			order_by="view_date desc"
		)

		if view_log:
			# Update existing log
			doc = frappe.get_doc("Video View Log", view_log)
			doc.duration_watched = float(duration_watched)
			doc.current_position = float(current_position)
			doc.view_status = "In Progress"
			doc.save(ignore_permissions=True)
			frappe.db.commit()

			return {"success": True}

		return {"success": False, "message": "No active view log found"}

	except Exception as e:
		frappe.log_error(f"Log progress error: {str(e)}", "Analytics API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def mark_complete(lesson, duration_watched):
	"""
	Mark video as completed
	Called when video playback ends
	"""
	try:
		# Find latest view log
		view_log = frappe.db.get_value(
			"Video View Log",
			{
				"lesson": lesson,
				"user": frappe.session.user
			},
			["name"],
			order_by="view_date desc"
		)

		if view_log:
			doc = frappe.get_doc("Video View Log", view_log)
			doc.duration_watched = float(duration_watched)
			doc.view_completed = 1
			doc.view_status = "Completed"
			doc.save(ignore_permissions=True)
			frappe.db.commit()

			# Get remaining views
			settings = frappe.get_single("Mux Settings")
			remaining = None

			if settings.enable_usage_limits:
				from acca_lms.api.mux_integration import get_remaining_views
				remaining = get_remaining_views(lesson)

			return {
				"success": True,
				"views_remaining": remaining
			}

		return {"success": False, "message": "No view log found"}

	except Exception as e:
		frappe.log_error(f"Mark complete error: {str(e)}", "Analytics API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_lesson_analytics(lesson):
	"""
	Get analytics for a specific lesson
	Admin/Instructor only
	"""
	if not frappe.has_permission("Video View Log", "read"):
		frappe.throw(_("Permission denied"))

	try:
		# Total views
		total_views = frappe.db.count("Video View Log", {"lesson": lesson})

		# Completed views
		completed_views = frappe.db.count("Video View Log", {
			"lesson": lesson,
			"view_completed": 1
		})

		# Unique viewers
		unique_viewers = frappe.db.sql("""
			SELECT COUNT(DISTINCT user)
			FROM `tabVideo View Log`
			WHERE lesson = %s
		""", lesson)[0][0]

		# Average completion rate
		avg_completion = frappe.db.sql("""
			SELECT AVG(completion_percent)
			FROM `tabVideo View Log`
			WHERE lesson = %s AND completion_percent IS NOT NULL
		""", lesson)[0][0] or 0

		# Get lesson details
		lesson_doc = frappe.get_doc("Course Lesson", lesson)

		return {
			"success": True,
			"lesson_title": lesson_doc.title,
			"total_views": total_views,
			"completed_views": completed_views,
			"unique_viewers": unique_viewers,
			"avg_completion_percent": round(avg_completion, 2),
			"completion_rate": round((completed_views / total_views * 100), 2) if total_views > 0 else 0
		}

	except Exception as e:
		frappe.log_error(f"Get analytics error: {str(e)}", "Analytics API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_course_analytics(course):
	"""
	Get analytics for all lessons in a course
	Admin/Instructor only
	"""
	if not frappe.has_permission("Video View Log", "read"):
		frappe.throw(_("Permission denied"))

	try:
		# Get all lessons in course
		lessons = frappe.get_all(
			"Course Lesson",
			filters={"course": course},
			fields=["name", "title"]
		)

		analytics = []
		for lesson in lessons:
			lesson_stats = get_lesson_analytics(lesson.name)
			if lesson_stats.get("success"):
				analytics.append(lesson_stats)

		# Overall course stats
		total_enrollments = frappe.db.count("LMS Enrollment", {
			"course": course,
			"member_status": "Active"
		})

		return {
			"success": True,
			"course": course,
			"total_enrollments": total_enrollments,
			"lesson_analytics": analytics
		}

	except Exception as e:
		frappe.log_error(f"Get course analytics error: {str(e)}", "Analytics API")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_user_watch_history(limit=20):
	"""
	Get watch history for current user
	"""
	if frappe.session.user == "Guest":
		return []

	try:
		history = frappe.get_all(
			"Video View Log",
			filters={"user": frappe.session.user},
			fields=[
				"name",
				"lesson",
				"lesson_title",
				"view_date",
				"duration_watched",
				"view_completed",
				"completion_percent"
			],
			order_by="view_date desc",
			limit=limit
		)

		# Add course info
		for item in history:
			lesson = frappe.get_doc("Course Lesson", item.lesson)
			item.course = lesson.course
			item.course_title = frappe.db.get_value("LMS Course", lesson.course, "title")

		return history

	except Exception as e:
		frappe.log_error(f"Get watch history error: {str(e)}", "Analytics API")
		return []


@frappe.whitelist()
def export_analytics(course=None, from_date=None, to_date=None):
	"""
	Export analytics data to Excel
	Admin/Instructor only
	"""
	if not frappe.has_permission("Video View Log", "export"):
		frappe.throw(_("Permission denied"))

	try:
		filters = {}

		if course:
			# Get lessons in course
			lessons = frappe.get_all("Course Lesson", filters={"course": course}, pluck="name")
			filters["lesson"] = ["in", lessons]

		if from_date:
			filters["view_date"] = [">=", from_date]

		if to_date:
			if "view_date" in filters:
				filters["view_date"] = ["between", [from_date, to_date]]
			else:
				filters["view_date"] = ["<=", to_date]

		# Get data
		data = frappe.get_all(
			"Video View Log",
			filters=filters,
			fields=[
				"name",
				"lesson",
				"lesson_title",
				"user",
				"user_name",
				"view_date",
				"duration_watched",
				"completion_percent",
				"view_completed",
				"view_status",
				"ip_address"
			],
			order_by="view_date desc"
		)

		return {
			"success": True,
			"data": data,
			"count": len(data)
		}

	except Exception as e:
		frappe.log_error(f"Export analytics error: {str(e)}", "Analytics API")
		return {"success": False, "error": str(e)}
