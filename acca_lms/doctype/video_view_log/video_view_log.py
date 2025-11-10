# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class VideoViewLog(Document):
	def before_insert(self):
		"""Set default view status"""
		if not self.view_status:
			self.view_status = "Started"

		# Calculate completion percent if we have the data
		if self.duration_watched and self.total_duration and self.total_duration > 0:
			self.completion_percent = (self.duration_watched / self.total_duration) * 100

	def before_save(self):
		"""Update completion percent before saving"""
		if self.duration_watched and self.total_duration and self.total_duration > 0:
			self.completion_percent = (self.duration_watched / self.total_duration) * 100

			# Auto-mark as completed if above threshold
			settings = frappe.get_single("Mux Settings")
			min_percent = settings.min_completion_percent or 80

			if self.completion_percent >= min_percent:
				self.view_completed = 1
				if self.view_status != "Completed":
					self.view_status = "Completed"

	def after_insert(self):
		"""Update lesson progress in LMS if completed"""
		if self.view_completed:
			self.update_lesson_progress()

	def on_update(self):
		"""Update lesson progress when view is marked complete"""
		if self.has_value_changed("view_completed") and self.view_completed:
			self.update_lesson_progress()

	def update_lesson_progress(self):
		"""Mark lesson as complete in Frappe LMS"""
		try:
			# Check if LMS Course Progress exists
			if not frappe.db.exists("LMS Course Progress", {
				"member": self.user,
				"lesson": self.lesson
			}):
				# Get course from lesson
				lesson = frappe.get_doc("Course Lesson", self.lesson)
				if lesson and lesson.course:
					# Create course progress entry
					progress = frappe.get_doc({
						"doctype": "LMS Course Progress",
						"member": self.user,
						"course": lesson.course,
						"lesson": self.lesson,
						"status": "Complete"
					})
					progress.insert(ignore_permissions=True)
					frappe.db.commit()
		except Exception as e:
			frappe.log_error(f"Failed to update lesson progress: {str(e)}", "Video View Log")
