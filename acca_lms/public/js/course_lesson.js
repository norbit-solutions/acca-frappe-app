// Copyright (c) 2025, NorBit Solutions and contributors
// For license information, please see license.txt

/**
 * Course Lesson Form Customization
 * Adds video upload functionality for Mux integration
 */

frappe.ui.form.on('Course Lesson', {
	refresh: function(frm) {
		// Only show upload button for Video content type
		if (frm.doc.content_type === 'Video') {
			// Add upload button if no video exists
			if (!frm.doc.mux_asset_id) {
				frm.add_custom_button(__('Upload Video to Mux'), function() {
					upload_video_dialog(frm);
				}, __('Actions'));
			}

			// If video exists, show management buttons
			if (frm.doc.mux_asset_id) {
				// Check status button
				frm.add_custom_button(__('Check Status'), function() {
					check_video_status(frm);
				}, __('Actions'));

				// Delete video button
				frm.add_custom_button(__('Delete Video'), function() {
					delete_video(frm);
				}, __('Actions'));

				// Show processing status
				if (frm.doc.mux_status && frm.doc.mux_status !== 'ready') {
					frm.dashboard.set_headline_alert(
						'<div class="alert alert-warning">Video is processing. Status: ' + frm.doc.mux_status + '</div>'
					);
				} else if (frm.doc.mux_status === 'ready') {
					frm.dashboard.set_headline_alert(
						'<div class="alert alert-success">Video is ready for playback</div>'
					);
				}
			}
		}
	}
});

function upload_video_dialog(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Upload Video to Mux'),
		fields: [
			{
				fieldname: 'video_file',
				label: __('Select Video File'),
				fieldtype: 'Attach',
				reqd: 1,
				description: 'Supported formats: MP4, MOV, AVI, WebM'
			},
			{
				fieldname: 'info',
				fieldtype: 'HTML',
				options: '<p class="text-muted small">This will upload your video directly to Mux. Processing may take a few minutes.</p>'
			}
		],
		primary_action_label: __('Upload'),
		primary_action: function() {
			let values = d.get_values();
			if (!values.video_file) {
				frappe.msgprint(__('Please select a video file'));
				return;
			}
			d.hide();
			start_upload(frm, values.video_file);
		}
	});

	d.show();
}

function start_upload(frm, file_url) {
	frappe.show_alert({
		message: __('Preparing upload...'),
		indicator: 'blue'
	}, 3);

	// Step 1: Create direct upload URL
	frappe.call({
		method: 'acca_lms.api.mux_integration.create_direct_upload',
		callback: function(r) {
			if (r.message && r.message.success) {
				upload_to_mux(frm, file_url, r.message.upload_url, r.message.upload_id);
			} else {
				frappe.msgprint(__('Failed to create upload URL. Please check Mux Settings.'));
			}
		}
	});
}

function upload_to_mux(frm, file_url, upload_url, upload_id) {
	// Fetch file from Frappe
	fetch(file_url)
		.then(response => {
			if (!response.ok) {
				throw new Error('Failed to fetch file');
			}
			return response.blob();
		})
		.then(blob => {
			// Show progress dialog
			let progress_dialog = new frappe.ui.Dialog({
				title: __('Uploading Video'),
				fields: [
					{
						fieldname: 'progress_html',
						fieldtype: 'HTML',
						options: '<div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%">0%</div></div>'
					}
				],
				primary_action_label: __('Cancel'),
				primary_action: function() {
					if (xhr) {
						xhr.abort();
					}
					progress_dialog.hide();
				}
			});

			progress_dialog.show();

			let xhr = new XMLHttpRequest();

			// Track upload progress
			xhr.upload.addEventListener('progress', function(e) {
				if (e.lengthComputable) {
					let percent = Math.round((e.loaded / e.total) * 100);
					let progress_bar = progress_dialog.$wrapper.find('.progress-bar');
					progress_bar.css('width', percent + '%');
					progress_bar.text(percent + '%');
				}
			});

			// On upload complete
			xhr.addEventListener('load', function() {
				if (xhr.status === 200) {
					progress_dialog.hide();
					frappe.show_alert({
						message: __('Upload complete! Processing video...'),
						indicator: 'green'
					}, 5);

					// Complete the upload process
					setTimeout(() => {
						complete_upload(frm, upload_id);
					}, 3000);
				} else {
					progress_dialog.hide();
					frappe.msgprint(__('Upload failed. Please try again.'));
				}
			});

			// On error
			xhr.addEventListener('error', function() {
				progress_dialog.hide();
				frappe.msgprint(__('Upload failed. Please check your connection.'));
			});

			// Upload to Mux
			xhr.open('PUT', upload_url);
			xhr.send(blob);
		})
		.catch(error => {
			console.error('Upload error:', error);
			frappe.msgprint(__('Failed to prepare file for upload'));
		});
}

function complete_upload(frm, upload_id) {
	frappe.call({
		method: 'acca_lms.api.mux_integration.complete_upload',
		args: {
			upload_id: upload_id,
			lesson_name: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				frappe.show_alert({
					message: __('Video uploaded successfully!'),
					indicator: 'green'
				}, 5);
				frm.reload_doc();
			} else {
				frappe.msgprint(r.message.message || __('Failed to complete upload'));
			}
		}
	});
}

function check_video_status(frm) {
	frappe.call({
		method: 'acca_lms.api.mux_integration.get_upload_status',
		args: {
			asset_id: frm.doc.mux_asset_id
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				let status_html = `
					<p><strong>Status:</strong> ${r.message.status}</p>
					<p><strong>Duration:</strong> ${r.message.duration ? Math.round(r.message.duration) + 's' : 'N/A'}</p>
					<p><strong>Ready:</strong> ${r.message.ready ? 'Yes' : 'No'}</p>
				`;

				frappe.msgprint({
					title: __('Video Status'),
					message: status_html,
					indicator: r.message.ready ? 'green' : 'orange'
				});

				// Reload if status changed
				if (r.message.status !== frm.doc.mux_status) {
					setTimeout(() => frm.reload_doc(), 2000);
				}
			}
		}
	});
}

function delete_video(frm) {
	frappe.confirm(
		__('Are you sure you want to delete this video from Mux? This action cannot be undone.'),
		function() {
			frappe.call({
				method: 'acca_lms.api.mux_integration.delete_video',
				args: {
					asset_id: frm.doc.mux_asset_id
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __('Video deleted successfully'),
							indicator: 'green'
						}, 5);

						// Clear fields
						frm.set_value('mux_asset_id', '');
						frm.set_value('mux_playback_id', '');
						frm.set_value('mux_upload_id', '');
						frm.set_value('mux_status', '');
						frm.set_value('mux_duration', '');
						frm.save();
					} else {
						frappe.msgprint(__('Failed to delete video'));
					}
				}
			});
		}
	);
}
