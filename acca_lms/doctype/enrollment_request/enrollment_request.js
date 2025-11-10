// Copyright (c) 2025, NorBit Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('Enrollment Request', {
	refresh: function(frm) {
		// Show action buttons based on status
		if (frm.doc.status === 'Pending') {
			// Approve button
			frm.add_custom_button(__('Approve'), function() {
				frappe.confirm(
					__('Are you sure you want to approve this enrollment request?'),
					function() {
						frm.set_value('status', 'Approved');
						frm.save();
					}
				);
			}).addClass('btn-primary');

			// Reject button
			frm.add_custom_button(__('Reject'), function() {
				frappe.prompt(
					{
						label: __('Rejection Reason'),
						fieldname: 'reason',
						fieldtype: 'Small Text',
						reqd: 1
					},
					function(values) {
						frm.set_value('status', 'Rejected');
						frm.set_value('admin_notes', values.reason);
						frm.save();
					},
					__('Reject Enrollment Request')
				);
			}).addClass('btn-danger');
		}

		// Set indicator color based on status
		if (frm.doc.status === 'Approved') {
			frm.dashboard.set_headline_alert('<div class="alert alert-success">Enrollment Approved</div>');
		} else if (frm.doc.status === 'Rejected') {
			frm.dashboard.set_headline_alert('<div class="alert alert-danger">Enrollment Rejected</div>');
		} else if (frm.doc.status === 'Pending') {
			frm.dashboard.set_headline_alert('<div class="alert alert-warning">Pending Approval</div>');
		}
	},

	// Update payment status indicator
	payment_status: function(frm) {
		frm.refresh();
	}
});
