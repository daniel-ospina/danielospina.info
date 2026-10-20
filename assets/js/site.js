/* danielospina.info — the only JS on the site */
(function () {
  'use strict';

  /* ---- mobile nav ---- */
  var nav = document.getElementById('site-nav');
  var toggle = nav && nav.querySelector('.nav__toggle');
  if (nav && toggle) {
    var setOpen = function (open) {
      nav.setAttribute('data-open', String(open));
      toggle.setAttribute('aria-expanded', String(open));
    };
    toggle.addEventListener('click', function () {
      setOpen(nav.getAttribute('data-open') !== 'true');
    });
    nav.querySelectorAll('.nav__links a').forEach(function (a) {
      a.addEventListener('click', function () { setOpen(false); });
    });
  }

  /* ---- footer year ---- */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* ---- forms ----
     To make a form submit for real, put the provider's URL on the <form> as
     data-endpoint="https://…". Until then the form does not pretend to send:
     it hands the visitor a working channel instead. */
  var CONTACT_EMAIL = 'daniel.ospinabotero@gmail.com';

  var FALLBACK = {
    contact: {
      text: 'This form isn\u2019t connected to a mail service yet \u2014 sending opens your email app instead, addressed to',
      href: 'mailto:' + CONTACT_EMAIL,
      label: CONTACT_EMAIL
    },
    newsletter: {
      text: 'The newsletter signup isn\u2019t connected yet.',
      href: '/book/',
      label: 'Get in touch instead'
    }
  };

  document.querySelectorAll('form[data-form]').forEach(function (form) {
    var kind = form.getAttribute('data-form');
    var endpoint = form.getAttribute('data-endpoint');
    var note = form.querySelector('[data-form-note]');

    if (endpoint) {
      form.setAttribute('action', endpoint);
      form.setAttribute('method', 'POST');
      return; /* the browser posts normally */
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var fb = FALLBACK[kind];
      var data = new FormData(form);
      var lines = [];
      data.forEach(function (v, k) { if (v) lines.push(k + ': ' + v); });

      if (kind === 'contact') {
        /* a mailto: link is a real, working channel — take them there */
        var subject = 'Website enquiry';
        var href = fb.href + '?subject=' + encodeURIComponent(subject) +
                   '&body=' + encodeURIComponent(lines.join('\n'));
        window.location.href = href;
      }

      if (!note || !fb) return;
      note.textContent = '';
      note.appendChild(document.createTextNode(fb.text + ' '));
      var a = document.createElement('a');
      a.href = fb.href;
      a.textContent = fb.label;
      if (fb.href.indexOf('http') === 0) {
        a.rel = 'noopener';
        a.target = '_blank';
      }
      note.appendChild(a);
    });
  });
})();
