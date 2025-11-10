// Copyright (c) 2025, NorBit Solutions and contributors
// For license information, please see license.txt

frappe.provide('acca.video');

/**
 * Secure Video Player Component
 * Handles Mux video playback with security features:
 * - Signed playback URLs
 * - Dynamic watermarking
 * - Usage tracking
 * - Security measures (no download, no screenshot)
 */
acca.video.SecurePlayer = class SecurePlayer {
	constructor(options) {
		this.container = options.container;
		this.lesson_name = options.lesson_name;
		this.playback_id = options.playback_id;
		this.enable_watermark = options.enable_watermark || false;
		this.watermark_text = options.watermark_text || '';

		this.player = null;
		this.furthest_point = 0;
		this.watch_start_time = null;
		this.total_watch_time = 0;
		this.last_update = Date.now();

		this.init();
	}

	async init() {
		try {
			// Get signed playback URL
			const response = await frappe.call({
				method: 'acca_lms.api.mux_integration.generate_signed_url',
				args: {
					lesson_name: this.lesson_name,
					playback_id: this.playback_id
				}
			});

			if (response.message && response.message.success) {
				this.setupPlayer(response.message);
			} else {
				this.showError('Failed to load video');
			}
		} catch (error) {
			console.error('Player init error:', error);
			this.showError('Failed to initialize video player');
		}
	}

	setupPlayer(videoData) {
		// Clear container
		this.container.innerHTML = '';

		// Create wrapper
		const wrapper = document.createElement('div');
		wrapper.className = 'secure-video-wrapper';

		// Create Mux player element
		const playerEl = document.createElement('mux-player');
		playerEl.setAttribute('playback-id', this.playback_id);

		// Set playback token
		if (videoData.playback_token) {
			playerEl.setAttribute('playback-token', videoData.playback_token);
		}

		// Metadata
		playerEl.setAttribute('metadata-video-title', this.lesson_name);
		playerEl.setAttribute('metadata-viewer-user-id', frappe.session.user);

		// Security settings
		playerEl.setAttribute('playsinline', '');
		playerEl.controlsList = 'nodownload';
		playerEl.disablePictureInPicture = true;

		// Disable right-click
		playerEl.addEventListener('contextmenu', (e) => {
			e.preventDefault();
			frappe.show_alert({
				message: __('Right-click disabled'),
				indicator: 'red'
			}, 2);
			return false;
		});

		wrapper.appendChild(playerEl);
		this.container.appendChild(wrapper);
		this.player = playerEl;

		// Add watermark if enabled
		if (this.enable_watermark && this.watermark_text) {
			this.addWatermark();
		}

		// Setup analytics
		this.setupAnalytics();

		// Additional security
		this.setupSecurityMeasures();
	}

	addWatermark() {
		const watermark = document.createElement('div');
		watermark.className = 'video-watermark';
		watermark.textContent = this.watermark_text;

		// Position randomly
		this.positionWatermark(watermark);

		// Reposition every 5 seconds with timestamp
		setInterval(() => {
			this.positionWatermark(watermark);
			const ts = new Date().toLocaleTimeString();
			watermark.textContent = `${this.watermark_text} • ${ts}`;
		}, 5000);

		this.container.appendChild(watermark);
	}

	positionWatermark(watermark) {
		const x = Math.random() * 70 + 10; // 10-80%
		const y = Math.random() * 70 + 10;
		watermark.style.left = x + '%';
		watermark.style.top = y + '%';
	}

	setupAnalytics() {
		let lastSentAt = Date.now();

		// Track play
		this.player.addEventListener('play', () => {
			this.watch_start_time = Date.now();
			this.last_update = Date.now();
		});

		// Track pause
		this.player.addEventListener('pause', () => {
			if (this.watch_start_time) {
				const duration = (Date.now() - this.watch_start_time) / 1000;
				this.total_watch_time += duration;
				this.watch_start_time = null;
			}
		});

		// Track time updates
		this.player.addEventListener('timeupdate', () => {
			const now = Date.now();
			const elapsed = (now - this.last_update) / 1000;

			if (elapsed > 0.4) {
				this.total_watch_time += elapsed;
				this.last_update = now;
			}

			// Send progress update every 30 seconds
			if (now - lastSentAt >= 30000) {
				lastSentAt = now;
				this.sendProgressUpdate();
			}
		});

		// Track completion
		this.player.addEventListener('ended', () => {
			this.markComplete();
		});

		// Send on page unload
		window.addEventListener('beforeunload', () => {
			if (this.total_watch_time > 5) {
				this.sendProgressUpdate(true);
			}
		});
	}

	sendProgressUpdate(sync = false) {
		const data = {
			lesson: this.lesson_name,
			duration_watched: Math.round(this.total_watch_time),
			current_position: Math.round(this.player.currentTime || 0)
		};

		if (sync) {
			// Use sendBeacon for synchronous sending on unload
			const blob = new Blob([JSON.stringify(data)], {type: 'application/json'});
			navigator.sendBeacon(
				'/api/method/acca_lms.api.analytics.log_progress',
				blob
			);
		} else {
			frappe.call({
				method: 'acca_lms.api.analytics.log_progress',
				args: data,
				freeze: false
			});
		}
	}

	markComplete() {
		const duration = Math.round(this.total_watch_time);

		frappe.call({
			method: 'acca_lms.api.analytics.mark_complete',
			args: {
				lesson: this.lesson_name,
				duration_watched: duration
			},
			callback: (r) => {
				if (!(r.message && r.message.success)) return;

				frappe.show_alert({
					message: __('Lesson completion recorded'),
					indicator: 'green'
				}, 5);

				// Check view limit
				if (r.message.views_remaining !== undefined) {
					if (r.message.views_remaining === 0) {
						frappe.show_alert({
							message: __('View limit reached for this lesson'),
							indicator: 'red'
						}, 5);
					} else {
						frappe.show_alert({
							message: __('Views remaining: {0}', [r.message.views_remaining]),
							indicator: 'orange'
						}, 5);
					}
				}
			}
		});
	}

	setupSecurityMeasures() {
		// Disable PrintScreen
		document.addEventListener('keydown', (e) => {
			if (e.key === 'PrintScreen') {
				e.preventDefault();
				frappe.show_alert({
					message: __('Screenshots not allowed'),
					indicator: 'red'
				}, 3);
			}
		});

		// Prevent dragging
		this.player.addEventListener('dragstart', (e) => {
			e.preventDefault();
		});

		// Prevent copy
		this.player.addEventListener('copy', (e) => {
			e.preventDefault();
		});
	}

	showError(message) {
		this.container.innerHTML = `
			<div class="video-error">
				<i class="fa fa-exclamation-triangle fa-3x"></i>
				<p>${message}</p>
			</div>
		`;
	}

	destroy() {
		if (this.player) {
			this.player.pause();
			this.player.remove();
		}
		this.sendProgressUpdate(true);
	}
};

// Make it globally available
window.SecureVideoPlayer = acca.video.SecurePlayer;
