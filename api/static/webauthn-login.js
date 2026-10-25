// Browser WebAuthn helper for /{locale}/login (Phase 1b). Requires secure context (HTTPS or localhost).
(function () {
  var script = document.currentScript;
  if (!script) return;
  var nextUrl = script.getAttribute('data-next') || '/en/';
  var elStatus = document.getElementById('login-status');
  var btn = document.getElementById('btn-webauthn');

  function msg(key, fallback) {
    return script.getAttribute('data-i18n-' + key) || fallback;
  }

  function setStatus(text) {
    if (elStatus) elStatus.textContent = text || '';
  }

  function base64urlToBuffer(b64url) {
    var pad = '='.repeat((4 - (b64url.length % 4)) % 4);
    var b64 = (b64url + pad).replace(/-/g, '+').replace(/_/g, '/');
    var str = atob(b64);
    var buf = new Uint8Array(str.length);
    for (var i = 0; i < str.length; i++) buf[i] = str.charCodeAt(i);
    return buf.buffer;
  }

  function bufferToBase64url(buf) {
    var bytes = new Uint8Array(buf);
    var binary = '';
    for (var i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  function prepareCreateOptions(json) {
    var o = JSON.parse(JSON.stringify(json));
    o.challenge = base64urlToBuffer(o.challenge);
    if (o.user && o.user.id) o.user.id = base64urlToBuffer(o.user.id);
    if (o.excludeCredentials && o.excludeCredentials.length) {
      o.excludeCredentials = o.excludeCredentials.map(function (c) {
        return { type: c.type, id: base64urlToBuffer(c.id), transports: c.transports };
      });
    }
    return o;
  }

  function prepareRequestOptions(json) {
    var o = JSON.parse(JSON.stringify(json));
    o.challenge = base64urlToBuffer(o.challenge);
    if (o.allowCredentials && o.allowCredentials.length) {
      o.allowCredentials = o.allowCredentials.map(function (c) {
        return { type: c.type, id: base64urlToBuffer(c.id), transports: c.transports };
      });
    }
    return o;
  }

  function credToRegistrationJSON(cred) {
    var r = cred.response;
    return {
      id: cred.id,
      rawId: bufferToBase64url(cred.rawId),
      type: cred.type,
      response: {
        clientDataJSON: bufferToBase64url(r.clientDataJSON),
        attestationObject: bufferToBase64url(r.attestationObject),
      },
    };
  }

  function credToAuthenticationJSON(cred) {
    var r = cred.response;
    var out = {
      id: cred.id,
      rawId: bufferToBase64url(cred.rawId),
      type: cred.type,
      response: {
        clientDataJSON: bufferToBase64url(r.clientDataJSON),
        authenticatorData: bufferToBase64url(r.authenticatorData),
        signature: bufferToBase64url(r.signature),
        userHandle: r.userHandle && r.userHandle.byteLength
          ? bufferToBase64url(r.userHandle)
          : null,
      },
    };
    return out;
  }

  if (!window.PublicKeyCredential) {
    setStatus(msg('not-supported', 'WebAuthn is not available in this browser.'));
    return;
  }

  if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    setStatus(msg('no-window', 'Use HTTPS or localhost for WebAuthn.'));
    return;
  }

  function redirectNext() {
    window.location.href = nextUrl;
  }

  function runRegister() {
    setStatus(msg('working', 'Working…'));
    return fetch('/auth/webauthn/registration/options', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
      credentials: 'same-origin',
    })
      .then(function (r) {
        if (!r.ok) throw new Error('options ' + r.status);
        return r.json();
      })
      .then(function (data) {
        var opts = prepareCreateOptions(data.options);
        return navigator.credentials.create({ publicKey: opts }).then(function (cred) {
          return fetch('/auth/webauthn/registration/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
              state: data.state,
              credential: credToRegistrationJSON(cred),
            }),
          });
        });
      })
      .then(function (r) {
        if (!r.ok) throw new Error('verify ' + r.status);
        setStatus(msg('done', 'Registered. Redirecting…'));
        redirectNext();
      });
  }

  function runAuth() {
    setStatus(msg('working', 'Working…'));
    return fetch('/auth/webauthn/authentication/options', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
      credentials: 'same-origin',
    })
      .then(function (r) {
        if (!r.ok) throw new Error('options ' + r.status);
        return r.json();
      })
      .then(function (data) {
        var opts = prepareRequestOptions(data.options);
        return navigator.credentials.get({ publicKey: opts }).then(function (cred) {
          if (!cred) throw new Error('cancelled');
          return fetch('/auth/webauthn/authentication/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
              state: data.state,
              credential: credToAuthenticationJSON(cred),
            }),
          });
        });
      })
      .then(function (r) {
        if (!r.ok) throw new Error('verify ' + r.status);
        setStatus(msg('done', 'Signed in. Redirecting…'));
        redirectNext();
      });
  }

  setStatus(msg('status-fetch', 'Checking passkey status…'));
  fetch('/auth/webauthn/status', { credentials: 'same-origin' })
    .then(function (r) {
      if (!r.ok) throw new Error('status ' + r.status);
      return r.json();
    })
    .then(function (st) {
      if (!btn) return;
      btn.hidden = false;
      var n = st.registered_credentials || 0;
      if (n === 0) {
        btn.textContent = msg('register', 'Register passkey');
        btn.onclick = function () {
          runRegister().catch(function (e) {
            setStatus(msg('fail', 'Failed: ') + (e && e.message ? e.message : String(e)));
          });
        };
      } else {
        btn.textContent = msg('signin', 'Sign in with passkey');
        btn.onclick = function () {
          runAuth().catch(function (e) {
            setStatus(msg('fail', 'Failed: ') + (e && e.message ? e.message : String(e)));
          });
        };
      }
      setStatus('');
    })
    .catch(function (e) {
      setStatus(msg('fail', 'Could not load WebAuthn status: ') + (e && e.message ? e.message : String(e)));
    });
})();
