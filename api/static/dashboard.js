// Dashboard-specific behaviour: chart rendering and scan controls.
// Uses data attributes rendered by the template and the /status and /scan API endpoints.

(function () {
  function getDbI18n() {
    var el = document.getElementById('db-dashboard-i18n-data');
    if (!el || !el.textContent) return {};
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return {};
    }
  }

  function getChartElements() {
    var canvas = document.getElementById('progress-chart');
    var emptyEl = document.getElementById('chart-empty');
    var raw = canvas ? canvas.getAttribute('data-chart') || '[]' : '[]';
    var data;
    try {
      data = JSON.parse(raw);
      if (!Array.isArray(data)) data = [];
    } catch (e) {
      data = [];
    }
    return { canvas: canvas, emptyEl: emptyEl, chartData: data };
  }

  function initChart() {
    var i18n = getDbI18n();
    var parts = getChartElements();
    var canvas = parts.canvas;
    var emptyEl = parts.emptyEl;
    var chartData = parts.chartData;

    if (typeof Chart !== 'undefined') {
      Chart.defaults.color = '#8b949e';
      Chart.defaults.borderColor = '#2d3a4d';
      Chart.defaults.font.family = 'system-ui, -apple-system, sans-serif';
    }

    if (!canvas) {
      if (emptyEl) emptyEl.style.display = 'block';
      return;
    }

    if (chartData.length > 0 && typeof Chart !== 'undefined') {
      if (emptyEl) emptyEl.style.display = 'none';
      var labels = chartData.map(function (d) { return d.label; });
      var findings = chartData.map(function (d) { return d.total_findings; });
      var scores = chartData.map(function (d) { return d.score; });
      var labelTotal = i18n.chart_total || 'Total findings';
      var labelRisk = i18n.chart_risk || 'Risk score (0–100)';
      var yTotal = i18n.chart_y_total || labelTotal;
      var yRisk = i18n.chart_y_risk || 'Risk score';
      new Chart(canvas, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: labelTotal,
              data: findings,
              borderColor: 'rgb(88, 166, 255)',
              backgroundColor: 'rgba(88, 166, 255, 0.1)',
              fill: true,
              yAxisID: 'y'
            },
            {
              label: labelRisk,
              data: scores,
              borderColor: 'rgb(243, 133, 81)',
              backgroundColor: 'rgba(243, 133, 81, 0.1)',
              fill: true,
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 2,
          interaction: { mode: 'index', intersect: false },
          plugins: { legend: { position: 'top' } },
          scales: {
            y: {
              type: 'linear',
              display: true,
              position: 'left',
              title: { display: true, text: yTotal },
              min: 0,
              ticks: { precision: 0 }
            },
            y1: {
              type: 'linear',
              display: true,
              position: 'right',
              title: { display: true, text: yRisk },
              min: 0,
              max: 100,
              grid: { drawOnChartArea: false }
            }
          }
        }
      });
    } else {
      if (emptyEl) emptyEl.style.display = 'block';
      canvas.style.display = 'none';
    }
  }

  function initScanControls() {
    var i18n = getDbI18n();
    var btn = document.getElementById('btn-start-scan');
    var feedback = document.getElementById('scan-feedback');
    var feedbackGuide = document.getElementById('scan-feedback-guide');
    var statusRunning = document.getElementById('status-running');
    var statusSession = document.getElementById('status-session');
    var statusFindings = document.getElementById('status-findings');

    function pollStatus() {
      fetch('/status')
        .then(function (r) { return r.json(); })
        .then(function (d) {
          var runLabel = i18n.status_running || 'Running';
          var idleLabel = i18n.status_idle || 'Idle';
          if (statusRunning) statusRunning.textContent = d.running ? runLabel : idleLabel;
          if (statusSession) statusSession.textContent = d.current_session_id || '\u2014';
          if (statusFindings) statusFindings.textContent = d.findings_count;
          if (d.running) {
            if (btn) btn.disabled = true;
            setTimeout(pollStatus, 2000);
          } else {
            if (btn) btn.disabled = false;
            if (document.getElementById('stat-db')) {
              location.reload();
            }
          }
        })
        .catch(function () {
          // Silent failure; do not spam the UI.
        });
    }

    if (btn) {
      btn.addEventListener('click', function () {
        var tenantInput = document.getElementById('scan-tenant');
        var tenant = (tenantInput && tenantInput.value && tenantInput.value.trim())
          ? tenantInput.value.trim()
          : null;
        var techInput = document.getElementById('scan-technician');
        var technician = (techInput && techInput.value && techInput.value.trim())
          ? techInput.value.trim()
          : null;
        var scanCompressedEl = document.getElementById('scan-compressed');
        var scanCompressed = scanCompressedEl && scanCompressedEl.checked;
        var contentTypeEl = document.getElementById('scan-content-type');
        var contentTypeCheck = contentTypeEl && contentTypeEl.checked;
        var scanStegoEl = document.getElementById('scan-stego');
        var scanStego = scanStegoEl && scanStegoEl.checked;
        var jurisdictionHintEl = document.getElementById('scan-jurisdiction-hint');
        var jurisdictionHint = jurisdictionHintEl && jurisdictionHintEl.checked;
        var validateCryptoEl = document.getElementById('scan-validate-crypto');
        var validateCrypto = validateCryptoEl && validateCryptoEl.checked;

        var starting = i18n.starting || 'Starting\u2026';
        if (feedback) feedback.textContent = starting;
        if (feedbackGuide) { feedbackGuide.textContent = ''; feedbackGuide.style.display = 'none'; }
        if (btn) btn.disabled = true;
        var body = {};
        if (tenant != null) body.tenant = tenant;
        if (technician != null) body.technician = technician;
        if (scanCompressed) body.scan_compressed = true;
        if (contentTypeCheck) body.content_type_check = true;
        if (scanStego) body.scan_for_stego = true;
        if (jurisdictionHint) body.jurisdiction_hint = true;
        if (validateCrypto) body.validate_crypto = true;

        var opts = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        };

        fetch('/scan', opts)
          .then(function (r) {
            if (!r.ok) {
              var err = new Error('Request failed: ' + r.status + ' ' + (r.statusText || ''));
              err.status = r.status;
              err.response = r;
              throw err;
            }
            return r.json();
          })
          .then(function (d) {
            if (feedback) {
              var sid = (d.session_id || '').slice(0, 16);
              var pref = i18n.started_prefix || 'Started:';
              feedback.textContent = pref + ' ' + (sid ? sid + '\u2026' : '');
            }
            if (feedbackGuide) { feedbackGuide.textContent = ''; feedbackGuide.style.display = 'none'; }
            pollStatus();
          })
          .catch(function (e) {
            if (btn) btn.disabled = false;
            var msg = e.message || String(e);
            var guide = '';
            if (e.status === 409) {
              msg = i18n.err_scan_progress || msg;
              guide = i18n.err_scan_progress_guide || '';
            } else if (e.status === 429) {
              msg = i18n.err_rate || msg;
              guide = i18n.err_rate_guide || '';
            } else if (e.status === 401 || e.status === 403) {
              var authTemplate = i18n.err_auth || 'Not authorized ({code}).';
              msg = authTemplate.replace('{code}', String(e.status));
              guide = i18n.err_auth_guide || '';
            } else if (!e.status && !e.response) {
              guide = i18n.err_network_guide || '';
            } else if (e.status >= 500) {
              guide = i18n.err_server_guide || '';
            }
            var what = i18n.err_what || 'What to do:';
            var errPrefix = i18n.err_prefix || 'Error:';
            function showError(displayMsg, displayGuide) {
              if (feedback) feedback.textContent = errPrefix + ' ' + (displayMsg || msg);
              if (feedbackGuide) {
                feedbackGuide.textContent = displayGuide || guide ? what + ' ' + (displayGuide || guide) : '';
                feedbackGuide.style.display = (displayGuide || guide) ? 'block' : 'none';
              }
            }
            if (e.response) {
              e.response.text().then(function (t) {
                var displayMsg = msg;
                var displayGuide = guide;
                try {
                  var j = JSON.parse(t);
                  if (j.detail) {
                    if (typeof j.detail === 'string') displayMsg = j.detail;
                    else if (j.detail.reason) {
                      displayMsg = j.detail.reason;
                      if (j.detail.retry_after_seconds != null) {
                        var rt = i18n.retry_after || 'Retry after {n} seconds, or adjust rate_limit in config.';
                        displayGuide = rt.replace('{n}', String(j.detail.retry_after_seconds));
                      }
                    }
                    else displayMsg = JSON.stringify(j.detail);
                  }
                } catch (_) {}
                showError(displayMsg, displayGuide);
              }).catch(function () { showError(msg, guide); });
            } else {
              showError(msg, guide);
            }
          });
      });
    }

    if (statusRunning && statusRunning.getAttribute('data-running') === '1') {
      pollStatus();
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    try {
      initChart();
    } catch (e) {
      // Chart.js may fail to load (CDN/blocker); ensure scan controls still work
    }
    initScanControls();
  });
})();
