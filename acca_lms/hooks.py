# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "acca_lms"
app_title = "ACCA LMS"
app_publisher = "NorBit Solutions"
app_description = "Secure video streaming Learning Management System with Mux integration"
app_icon = "octicon octicon-video"
app_color = "purple"
app_email = "info@norbitsolutions.com"
app_license = "MIT"
app_version = "0.0.1"

# Includes in <head>
# ------------------

# Include CSS files
app_include_css = [
    "/assets/acca_lms/css/landing.css",
    "/assets/acca_lms/css/course_detail.css",
    "/assets/acca_lms/css/video_player.css"
]

# Include JavaScript files
app_include_js = [
    "/assets/acca_lms/js/secure_video_player.js"
]

# Include Mux Player from CDN and enrollment handling
web_include_js = [
    "https://cdn.jsdelivr.net/npm/@mux/mux-player",
    "/assets/acca_lms/js/enrollment.js"
]

# Include CSS for web pages
web_include_css = [
    "/assets/acca_lms/css/landing.css",
    "/assets/acca_lms/css/course_detail.css",
    "/assets/acca_lms/css/video_player.css"
]

# Home Pages
# ----------

# Application home page (will be overridden by custom public homepage)
# home_page = "login"

# Website user home page (after login)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# Automatically create page for each record of DocType
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "acca_lms.install.before_install"
# after_install = "acca_lms.install.after_install"

# Desk Notifications
# -------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "acca_lms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# DocType JavaScript
# ------------------
# Custom JavaScript for specific doctypes
doctype_js = {
    "Course Lesson": "public/js/course_lesson.js"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"acca_lms.tasks.all"
# 	],
# 	"daily": [
# 		"acca_lms.tasks.daily"
# 	],
# 	"hourly": [
# 		"acca_lms.tasks.hourly"
# 	],
# 	"weekly": [
# 		"acca_lms.tasks.weekly"
# 	]
# 	"monthly": [
# 		"acca_lms.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "acca_lms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "acca_lms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "acca_lms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {
        "doctype": "{doctype_4}"
    }
]

# Authentication and authorization
# --------------------------------

# These will be called at the time of session creation
on_session_creation = [
    "acca_lms.api.auth.on_user_login"
]

# Hook to enforce single device login
# on_login = "acca_lms.api.auth.on_user_login"

# Fixtures
# --------
# Export fixtures to migrate custom fields
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name", "in", [
                    "Course Lesson-mux_section",
                    "Course Lesson-mux_asset_id",
                    "Course Lesson-mux_playback_id",
                    "Course Lesson-mux_upload_id",
                    "Course Lesson-mux_duration",
                    "Course Lesson-mux_status"
                ]
            ]
        ]
    }
]

# Configuration for docs
# --------------------

# For license information please see license.txt
