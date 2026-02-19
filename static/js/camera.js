'use strict';

/**
 * camera.js  –  BLO Voter Verification
 *
 * Buttons expected per form:
 *   .main-camera-btn    → 📷 Camera   (open)
 *   .switch-camera-btn  → 🔄 Switch
 *   .close-camera-btn   → ✕ Close
 *   .capture-btn        → 📸 Capture
 *
 * Elements expected per form:
 *   .camera-preview     → <video>
 *   .camera-canvas      → <canvas>  (hidden, used for capture)
 *   .camera-snapshot    → <img>     (shows captured still at 1:1)
 *   input[name="photo"] → receives the captured File
 */

const cameraState = new WeakMap(); // form → { stream, facing }

/* ── Helpers ─────────────────────────────────────────────── */

function getEls(btn) {
    const form = btn.closest('form');
    return {
        form,
        video:      form.querySelector('.camera-preview'),
        canvas:     form.querySelector('.camera-canvas'),
        snapshot:   form.querySelector('.camera-snapshot'),
        fileIn:     form.querySelector('input[type="file"]'),
        openBtn:    form.querySelector('.main-camera-btn'),
        switchBtn:  form.querySelector('.switch-camera-btn'),
        closeBtn:   form.querySelector('.close-camera-btn'),
        captureBtn: form.querySelector('.capture-btn'),
    };
}

function showCameraUI(els) {
    els.video.style.display      = 'block';
    els.switchBtn.style.display  = 'inline-flex';
    els.closeBtn.style.display   = 'inline-flex';
    els.captureBtn.style.display = 'inline-flex';
    els.openBtn.style.display    = 'none';
}

function hideCameraUI(els) {
    els.video.style.display      = 'none';
    els.switchBtn.style.display  = 'none';
    els.closeBtn.style.display   = 'none';
    els.captureBtn.style.display = 'none';
    els.openBtn.style.display    = 'inline-flex';
}

async function startStream(els, facingMode) {
    // Stop existing stream
    const state = cameraState.get(els.form) || {};
    if (state.stream) state.stream.getTracks().forEach(t => t.stop());

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: { ideal: facingMode }, aspectRatio: 1 },
            audio: false,
        });
        els.video.srcObject = stream;
        await els.video.play();
        cameraState.set(els.form, { stream, facing: facingMode });
        return true;
    } catch (err) {
        alert('Camera error: ' + (err.message || err.name));
        return false;
    }
}

function stopStream(els) {
    const state = cameraState.get(els.form);
    if (state && state.stream) {
        state.stream.getTracks().forEach(t => t.stop());
    }
    els.video.srcObject = null;
    cameraState.set(els.form, null);
}

/* ── Public API ──────────────────────────────────────────── */

window.toggleCamera = async function (btn) {
    const els    = getEls(btn);
    const facing = (cameraState.get(els.form) || {}).facing || 'environment';
    const ok     = await startStream(els, facing);
    if (ok) showCameraUI(els);
};

window.switchCamera = async function (btn) {
    const els    = getEls(btn);
    const state  = cameraState.get(els.form) || {};
    const next   = (state.facing || 'environment') === 'environment' ? 'user' : 'environment';
    await startStream(els, next);
};

window.capturePhoto = function (btn) {
    const els = getEls(btn);
    const { video, canvas, snapshot, fileIn } = els;

    // Draw square crop from center of video
    const size = Math.min(video.videoWidth, video.videoHeight);
    const sx   = (video.videoWidth  - size) / 2;
    const sy   = (video.videoHeight - size) / 2;

    canvas.width  = size;
    canvas.height = size;
    canvas.getContext('2d').drawImage(video, sx, sy, size, size, 0, 0, size, size);

    // Show snapshot preview
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    snapshot.src           = dataUrl;
    snapshot.style.display = 'block';

    // Inject as File into the file input
    canvas.toBlob(blob => {
        const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
        const dt   = new DataTransfer();
        dt.items.add(file);
        fileIn.files = dt.files;
    }, 'image/jpeg', 0.92);

    // Flash border green briefly
    snapshot.style.borderColor = '#0d9488';
    setTimeout(() => { snapshot.style.borderColor = ''; }, 500);
};

window.closeCamera = function (btn) {
    const els = getEls(btn);
    stopStream(els);
    hideCameraUI(els);
    // keep snapshot visible if already captured
};

// Stop all streams on page unload
window.addEventListener('pagehide', () => {
    document.querySelectorAll('.camera-preview').forEach(video => {
        if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    });
});