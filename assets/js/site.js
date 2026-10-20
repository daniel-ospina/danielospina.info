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
     data-endpoint="https://…". Until then the form does NOT pretend to send:
     it tells the visitor the honest thing and points at a channel that works. */
  var FALLBACK = {
    contact: {
      text: 'This form isn\u2019t connected yet \u2014 the fastest way to reach me is LinkedIn.',
      href: 'https://www.linkedin.com/in/daniel-ospina-77976985',
      label: 'Message me on LinkedIn'
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
      a.focus();
    });
  });
})();
