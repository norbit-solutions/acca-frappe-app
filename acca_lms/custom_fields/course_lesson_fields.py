# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	"""Add Mux-related custom fields to Course Lesson DocType"""

	custom_fields = {
		"Course Lesson": [
			{
				"fieldname": "mux_section",
				"label": "Mux Video Details",
				"fieldtype": "Section Break",
				"insert_after": "youtube",
				"depends_on": "eval:doc.content_type=='Video'",
				"collapsible": 0
			},
			{
				"fieldname": "mux_asset_id",
				"label": "Mux Asset ID",
				"fieldtype": "Data",
				"read_only": 1,
				"insert_after": "mux_section",
				"description": "Unique identifier for the video asset in Mux"
			},
			{
				"fieldname": "mux_playback_id",
				"label": "Mux Playback ID",
				"fieldtype": "Data",
				"read_only": 1,
				"insert_after": "mux_asset_id",
				"description": "Playback ID for generating signed URLs"
			},
			{
				"fieldname": "mux_upload_id",
				"label": "Mux Upload ID",
				"fieldtype": "Data",
				"read_only": 1,
				"hidden": 1,
				"insert_after": "mux_playback_id",
				"description": "Direct upload ID for tracking upload progress"
			},
			{
				"fieldname": "mux_duration",
				"label": "Duration (seconds)",
				"fieldtype": "Int",
				"read_only": 1,
				"insert_after": "mux_upload_id",
				"description": "Video duration in seconds"
			},
			{
				"fieldname": "mux_status",
				"label": "Processing Status",
				"fieldtype": "Select",
				"options": "Pending\nProcessing\nReady\nError",
				"read_only": 1,
				"insert_after": "mux_duration",
				"description": "Current processing status of the video in Mux"
			}
		]
	}

	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()

	print("Custom fields for Course Lesson created successfully!")


def setup_custom_fields():
	"""Called during installation"""
	execute()
