# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class MuxSettings(Document):
	def validate(self):
		"""Validate settings before saving"""

		# Validate usage limits
		if self.enable_usage_limits:
			if not self.max_views_per_video or self.max_views_per_video < 1:
				frappe.throw("Max views per video must be at least 1")

			if not self.min_completion_percent or self.min_completion_percent < 1 or self.min_completion_percent > 100:
				frappe.throw("Minimum completion percent must be between 1 and 100")

		# Validate Mux credentials
		if self.mux_token_id and not self.get_password("mux_token_secret"):
			frappe.msgprint("Warning: Mux Token Secret is required if Token ID is provided", indicator="orange")

		if self.mux_signing_key_id and not self.get_password("mux_signing_key_private"):
			frappe.msgprint("Warning: Mux Signing Private Key is required if Signing Key ID is provided", indicator="orange")

	def on_update(self):
		"""Actions to perform after settings are updated"""
		# Clear cache to ensure new settings are used immediately
		frappe.cache().delete_value("mux_settings")
