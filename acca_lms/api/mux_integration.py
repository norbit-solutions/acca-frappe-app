# -*- coding: utf-8 -*-
# Copyright (c) 2025, NorBit Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import mux_python
import jwt
import time
import base64
from frappe import _

# ============================================================================
# MUX CLIENT CONFIGURATION
# ============================================================================

def get_mux_configuration():
	"""Get Mux API configuration from settings"""
	settings = frappe.get_single("Mux Settings")

	if not settings.mux_token_id or not settings.get_password("mux_token_secret"):
		frappe.throw(_("Mux credentials not configured. Please configure in Mux Settings."))

	configuration = mux_python.Configuration()
	configuration.username = settings.mux_token_id
	configuration.password = settings.get_password("mux_token_secret")

	return configuration


def get_mux_client():
	"""Get Mux Assets API client"""
	configuration = get_mux_configuration()
	return mux_python.AssetsApi(mux_python.ApiClient(configuration))


def get_mux_uploads_client():
	"""Get Mux Direct Uploads API client"""
	configuration = get_mux_configuration()
	return mux_python.DirectUploadsApi(mux_python.ApiClient(configuration))


# ============================================================================
# DIRECT UPLOAD OPERATIONS
# ============================================================================

@frappe.whitelist()
def create_direct_upload():
	"""
	Create Mux direct upload URL
	Returns URL where browser can upload video directly to Mux
	"""
	try:
		uploads_api = get_mux_uploads_client()

		# Create upload with signed playback policy
		create_upload_request = mux_python.CreateUploadRequest(
			new_asset_settings=mux_python.CreateAssetRequest(
				playback_policy=[mux_python.PlaybackPolicy.SIGNED],
				mp4_support="standard"
			),
			cors_origin="*",  # In production, restrict to your domain
			timeout=7200  # 2 hours
		)

		upload = uploads_api.create_direct_upload(create_upload_request)

		return {
			"success": True,
			"upload_url": upload.data.url,
			"upload_id": upload.data.id
		}

	except Exception as e:
		frappe.log_error(f"Mux upload error: {str(e)}", "Mux Integration")
		frappe.throw(_("Failed to create upload URL. Please check Mux Settings."))


@frappe.whitelist()
def complete_upload(upload_id, lesson_name):
	"""
	Finalize upload and link to lesson
	Called after video upload completes
	"""
	try:
		uploads_api = get_mux_uploads_client()
		assets_api = get_mux_client()

		# Get upload status
		upload = uploads_api.get_direct_upload(upload_id)

		if upload.data.status != "asset_created":
			return {
				"success": False,
				"message": _("Upload still processing. Please wait...")
			}

		# Get asset details
		asset_id = upload.data.asset_id
		asset = assets_api.get_asset(asset_id)

		# Get signed playback ID
		playback_id = None
		for pid in asset.data.playback_ids:
			if pid.policy == "signed":
				playback_id = pid.id
				break

		if not playback_id:
			frappe.throw(_("No signed playback ID found"))

		# Update lesson
		lesson = frappe.get_doc("Course Lesson", lesson_name)
		lesson.mux_asset_id = asset_id
		lesson.mux_playback_id = playback_id
		lesson.mux_upload_id = upload_id
		lesson.mux_status = asset.data.status

		if asset.data.duration:
			lesson.mux_duration = int(asset.data.duration)
			lesson.duration = int(asset.data.duration)

		lesson.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": True,
			"asset_id": asset_id,
			"playback_id": playback_id,
			"status": asset.data.status
		}

	except Exception as e:
		frappe.log_error(f"Complete upload error: {str(e)}", "Mux Integration")
		frappe.throw(_("Failed to complete upload"))


@frappe.whitelist()
def get_upload_status(asset_id):
	"""Check Mux processing status"""
	try:
		assets_api = get_mux_client()
		asset = assets_api.get_asset(asset_id)

		return {
			"success": True,
			"status": asset.data.status,
			"duration": asset.data.duration,
			"ready": asset.data.status == "ready"
		}

	except Exception as e:
		frappe.log_error(f"Get status error: {str(e)}", "Mux Integration")
		return {"success": False, "error": str(e)}


# ============================================================================
# SIGNED PLAYBACK URL GENERATION
# ============================================================================

@frappe.whitelist()
def generate_signed_url(lesson_name, playback_id=None):
	"""
	Generate signed playback URL with security checks
	Main function called by video player
	"""
	# Authentication check
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to watch videos"))

	# Get lesson
	lesson = frappe.get_doc("Course Lesson", lesson_name)

	if not playback_id:
		playback_id = lesson.mux_playback_id

	if not playback_id:
		frappe.throw(_("Video not available"))

	# Guard: Only serve when asset is ready
	if lesson.mux_status != "ready":
		frappe.throw(_("Video is still processing. Please try again later."))

	# Security checks
	if not check_lesson_access(lesson):
		frappe.throw(_("You don't have access to this lesson"))

	# Usage limit check
	settings = frappe.get_single("Mux Settings")
	if settings.enable_usage_limits:
		if not check_usage_limit(lesson_name):
			remaining = get_remaining_views(lesson_name)
			frappe.throw(_("View limit reached. Remaining views: {0}").format(remaining))

	# Generate token
	token = generate_playback_token(playback_id, lesson_name)

	# Log view
	log_video_view(lesson_name, "started")

	return {
		"success": True,
		"playback_url": f"https://stream.mux.com/{playback_id}.m3u8?token={token}",
		"playback_id": playback_id,
		"playback_token": token,
		"remaining_views": get_remaining_views(lesson_name) if settings.enable_usage_limits else None
	}


def generate_playback_token(playback_id, lesson_name):
	"""Generate JWT token for signed playback"""
	settings = frappe.get_single("Mux Settings")

	signing_key_id = settings.mux_signing_key_id
	signing_key_private = settings.get_password("mux_signing_key_private")

	if not signing_key_id or not signing_key_private:
		frappe.throw(_("Mux signing keys not configured"))

	expiration = int(time.time()) + 7200  # 2 hours

	payload = {
		"sub": playback_id,
		"aud": "v",
		"exp": expiration
	}

	headers = {"kid": signing_key_id}

	# Add watermark data if enabled
	if settings.enable_watermark:
		user = frappe.get_doc("User", frappe.session.user)
		mobile = getattr(user, "mobile_no", None)

		payload["viewer_user_id"] = frappe.session.user
		payload["viewer_mobile"] = mobile or "N/A"
		payload["issued_at_ts"] = int(time.time())

	# Decode private key if base64 encoded
	try:
		decoded_key = base64.b64decode(signing_key_private)
	except Exception:
		decoded_key = signing_key_private  # Assume raw PEM

	# Generate JWT
	token = jwt.encode(payload, decoded_key, algorithm="RS256", headers=headers)

	return token


# ============================================================================
# ACCESS CONTROL
# ============================================================================

def check_lesson_access(lesson):
	"""
	Check if user can access lesson
	Allows preview lessons without enrollment
	"""
	# Check if it's a preview lesson
	if lesson.include_in_preview:
		return True

	# Check enrollment
	course = lesson.course
	enrollment = frappe.db.exists(
		"LMS Enrollment",
		{
			"course": course,
			"member": frappe.session.user,
			"member_status": "Active"
		}
	)

	return bool(enrollment)


def check_usage_limit(lesson_name):
	"""Check if user has views remaining"""
	settings = frappe.get_single("Mux Settings")
	max_views = settings.max_views_per_video or 2
	min_pct = settings.min_completion_percent or 80

	# Count completed views
	view_count = frappe.db.count(
		"Video View Log",
		{
			"lesson": lesson_name,
			"user": frappe.session.user,
			"view_completed": 1,
			"completion_percent": [">=", min_pct]
		}
	)

	return view_count < max_views


def get_remaining_views(lesson_name):
	"""Get number of views remaining for user"""
	settings = frappe.get_single("Mux Settings")
	max_views = settings.max_views_per_video or 2
	min_pct = settings.min_completion_percent or 80

	# Count completed views
	view_count = frappe.db.count(
		"Video View Log",
		{
			"lesson": lesson_name,
			"user": frappe.session.user,
			"view_completed": 1,
			"completion_percent": [">=", min_pct]
		}
	)

	return max(0, max_views - view_count)


# ============================================================================
# VIEW LOGGING
# ============================================================================

def log_video_view(lesson_name, status="started"):
	"""Log video view for analytics and usage tracking"""
	try:
		# Get lesson to fetch duration
		lesson = frappe.get_doc("Course Lesson", lesson_name)

		view_log = frappe.get_doc({
			"doctype": "Video View Log",
			"lesson": lesson_name,
			"user": frappe.session.user,
			"view_date": frappe.utils.now(),
			"ip_address": frappe.local.request_ip,
			"device_info": frappe.local.request.headers.get("User-Agent", ""),
			"view_status": status.title(),
			"total_duration": lesson.duration or 0
		})
		view_log.insert(ignore_permissions=True)
		frappe.db.commit()

	except Exception as e:
		frappe.log_error(f"Failed to log view: {str(e)}", "Mux Integration")


# ============================================================================
# VIDEO MANAGEMENT
# ============================================================================

@frappe.whitelist()
def delete_video(asset_id):
	"""Delete video from Mux"""
	try:
		assets_api = get_mux_client()
		assets_api.delete_asset(asset_id)

		return {"success": True, "message": _("Video deleted successfully")}

	except Exception as e:
		frappe.log_error(f"Delete video error: {str(e)}", "Mux Integration")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_video_analytics(asset_id):
	"""Get video analytics from Mux (placeholder for future implementation)"""
	# This would use Mux Data API to get detailed analytics
	# For now, we rely on our own Video View Log
	try:
		return {
			"success": True,
			"message": "Analytics available in Video View Log"
		}
	except Exception as e:
		return {"success": False, "error": str(e)}
