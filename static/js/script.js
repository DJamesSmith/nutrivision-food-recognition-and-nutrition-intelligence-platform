function getCookie(name) {
    let cookieValue = null
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim()
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}

const csrftoken = getCookie('csrftoken')

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method))
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
    }
})

// NV namespace: shared helpers used across predict/dataset-upload/training pages, so image validation, button loading states, error extraction and
// upload-progress/polling wiring are written once instead of being copy-pasted into every template's <script> block.
window.NV = window.NV || {}

NV.ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
NV.MAX_IMAGE_SIZE_MB = 10

// Fast client-side pre-check only — imaging.validators.validate_image_file
// on the server remains the authoritative check in every case.
NV.validateImageFile = function (file) {
    if (!file) {
        return 'Please choose an image file.'
    }
    const ext = '.' + file.name.toLowerCase().split('.').pop()
    if (!NV.ALLOWED_IMAGE_EXTENSIONS.includes(ext)) {
        return `Unsupported file type. Allowed: ${NV.ALLOWED_IMAGE_EXTENSIONS.join(', ')}`
    }
    if (file.size > NV.MAX_IMAGE_SIZE_MB * 1024 * 1024) {
        return `File exceeds ${NV.MAX_IMAGE_SIZE_MB} MB.`
    }
    return null
}

// Renders a live thumbnail preview as soon as a file is chosen. fileInputEl: a plain DOM <input type="file"> element (e.g. `this` from
// a change handler). imgSelector: a jQuery selector for the <img> to fill.
NV.previewImage = function (fileInputEl, imgSelector) {
    const file = fileInputEl.files && fileInputEl.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = e => $(imgSelector).attr('src', e.target.result).removeClass('d-none')
    reader.readAsDataURL(file)
}

// Disables a button and swaps its label while an AJAX call is in flight, remembering the original label so NV.resetButton can restore it exactly.
NV.setButtonLoading = function (selector, loadingText) {
    const $btn = $(selector)
    if ($btn.data('nv-original-text') === undefined) {
        $btn.data('nv-original-text', $btn.text())
    }
    $btn.prop('disabled', true).text(loadingText)
}

NV.resetButton = function (selector) {
    const $btn = $(selector)
    const original = $btn.data('nv-original-text')
    $btn.prop('disabled', false)
    if (original !== undefined) {
        $btn.text(original)
    }
}

// Pulls the {"status":"error","message":...} shape used by every API endpoint in this project out of a failed jqXHR, falling back to a
// generic message when the response isn't JSON (e.g. a 502 from a proxy).
NV.ajaxErrorMessage = function (xhr, fallback) {
    return (xhr && xhr.responseJSON && xhr.responseJSON.message) || fallback || 'Something went wrong. Please try again.'
}

// Returns an `xhr` factory for $.ajax that reports upload progress — used for the FormData image-upload endpoints (dataset images, predict).
NV.uploadProgressXhr = function (onProgress) {
    return function () {
        const xhr = new window.XMLHttpRequest()
        xhr.upload.addEventListener('progress', function (evt) {
            if (evt.lengthComputable) {
                onProgress(Math.round((evt.loaded / evt.total) * 100))
            }
        })
        return xhr
    }
}

// Generic status-polling helper: GETs `url` every `intervalMs`, handing the parsed {"data": ...} payload to onData, until isTerminal(data)
// returns true (e.g. a TrainingJob reaching COMPLETED/FAILED). Returns the interval handle in case the caller wants to clear it early.
NV.pollUntil = function (url, {onData, isTerminal, intervalMs = 4000}) {
    let handle = null
    function tick() {
        $.ajax({
            url: url,
            type: 'GET',
            success: function (response) {
                onData(response.data)
                if (isTerminal(response.data)) {
                    clearInterval(handle)
                }
            }
        })
    }
    handle = setInterval(tick, intervalMs)
    return handle
}

// Global loading indicator: a thin bar pinned to the top of the viewport that appears for the duration of any jQuery AJAX call, site-wide.
// Gives immediate feedback even before a specific button's own loading state kicks in (e.g. while validation/CSRF setup happens before the request actually fires).
$(function () {
    if ($('#nv-loading-bar').length === 0) {
        $('body').prepend('<div id="nv-loading-bar"></div>')
    }
})

$(document).ajaxStart(function () {
    $('#nv-loading-bar').addClass('nv-active')
})

$(document).ajaxStop(function () {
    $('#nv-loading-bar').removeClass('nv-active').css('width', '0')
})