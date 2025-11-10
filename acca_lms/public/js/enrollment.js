// Copyright (c) 2025, NorBit Solutions and contributors
// For license information, please see license.txt

/**
 * Enrollment handling for public website
 */

frappe.provide('acca.enrollment');

acca.enrollment = {
	/**
	 * Request enrollment in a course
	 */
	requestEnrollment: function(course_name, notes) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: 'acca_lms.api.enrollment.request_enrollment',
				args: {
					course: course_name,
					notes: notes || ''
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						resolve(r.message);
					} else {
						reject(r.message);
					}
				},
				error: function(err) {
					reject(err);
				}
			});
		});
	},

	/**
	 * Get enrollment status for a course
	 */
	getEnrollmentStatus: function(course_name) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: 'acca_lms.api.enrollment.get_enrollment_status',
				args: {
					course: course_name
				},
				callback: function(r) {
					if (r.message) {
						resolve(r.message);
					} else {
						reject('Failed to get status');
					}
				},
				error: function(err) {
					reject(err);
				}
			});
		});
	},

	/**
	 * Cancel enrollment request
	 */
	cancelRequest: function(request_id) {
		return new Promise((resolve, reject) => {
			frappe.confirm(
				__('Are you sure you want to cancel this enrollment request?'),
				function() {
					frappe.call({
						method: 'acca_lms.api.enrollment.cancel_enrollment_request',
						args: {
							request_id: request_id
						},
						callback: function(r) {
							if (r.message && r.message.success) {
								resolve(r.message);
							} else {
								reject(r.message);
							}
						},
						error: function(err) {
							reject(err);
						}
					});
				}
			);
		});
	},

	/**
	 * Show enrollment request dialog with notes
	 */
	showEnrollmentDialog: function(course_name, course_title) {
		let d = new frappe.ui.Dialog({
			title: __('Request Enrollment'),
			fields: [
				{
					fieldname: 'course_info',
					fieldtype: 'HTML',
					options: `<p>You are requesting enrollment for:<br><strong>${course_title}</strong></p>`
				},
				{
					fieldname: 'notes',
					fieldtype: 'Small Text',
					label: __('Notes (Optional)'),
					description: 'Any message you want to send to the administrator'
				}
			],
			primary_action_label: __('Submit Request'),
			primary_action: function(values) {
				d.hide();

				frappe.show_alert({
					message: __('Submitting request...'),
					indicator: 'blue'
				}, 3);

				acca.enrollment.requestEnrollment(course_name, values.notes)
					.then(function(response) {
						frappe.show_alert({
							message: response.message,
							indicator: 'green'
						}, 5);

						// Reload page after 2 seconds
						setTimeout(function() {
							location.reload();
						}, 2000);
					})
					.catch(function(error) {
						frappe.show_alert({
							message: error.message || 'Failed to submit request',
							indicator: 'red'
						}, 5);
					});
			}
		});

		d.show();
	}
};

// Make it globally available
window.requestEnrollment = function(course_name, course_title) {
	if (course_title) {
		acca.enrollment.showEnrollmentDialog(course_name, course_title);
	} else {
		acca.enrollment.requestEnrollment(course_name)
			.then(function(response) {
				frappe.show_alert({
					message: response.message,
					indicator: 'green'
				}, 5);
				setTimeout(function() {
					location.reload();
				}, 2000);
			})
			.catch(function(error) {
				frappe.show_alert({
					message: error.message || 'Failed to submit request',
					indicator: 'red'
				}, 5);
			});
	}
};
