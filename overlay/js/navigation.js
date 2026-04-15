/**
 * navigation.js — Open Circuits sidebar navigation
 *
 * Builds a collapsible sidebar table of contents from the current page's
 * h2 headings, extracts prev/next chapter links from Kuphaldt's existing
 * image navigation, injects a clean bottom chapter nav, and highlights the
 * current section as the reader scrolls.
 *
 * No external dependencies. Vanilla JS only.
 */
(function () {
  'use strict';

  var SIDEBAR_ID   = 'oc-sidebar';
  var TOGGLE_ID    = 'oc-nav-toggle';
  var SCRIM_ID     = 'oc-sidebar-scrim';
  var STORAGE_KEY  = 'oc-sidebar-open';
  var MOBILE_BREAK = 769;

  /* ── 1. Extract Kuphaldt prev/next/index from image nav links ─────────── */
  function extractChapterNav() {
    var result = { prev: null, next: null, index: null };
    var links = document.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
      var a   = links[i];
      var img = a.querySelector('img');
      if (!img) continue;
      var src  = (img.getAttribute('src') || '').toLowerCase();
      var href = a.getAttribute('href');
      if (!href) continue;
      if (src.indexOf('previous') !== -1)  result.prev  = href;
      else if (src.indexOf('next') !== -1) result.next  = href;
      else if (src.indexOf('contents') !== -1) result.index = href;
    }
    return result;
  }

  /* ── 2. Build TOC items from h2 headings ─────────────────────────────── */
  function buildTocItems() {
    var items    = [];
    var headings = document.querySelectorAll('h2');
    for (var i = 0; i < headings.length; i++) {
      var h2 = headings[i];
      // Anchor: prefer id on h2, fall back to <a name="..."> inside it
      var anchor = h2.id || '';
      if (!anchor) {
        var a = h2.querySelector('a[name]');
        if (a) anchor = a.getAttribute('name') || '';
      }
      var text = h2.textContent.trim();
      // Skip copyright/colophon sections that appear on some pages
      if (anchor && text && text.toLowerCase().indexOf('copyright') === -1) {
        items.push({ anchor: anchor, text: text, el: h2 });
      }
    }
    return items;
  }

  /* ── 3. Render sidebar content ────────────────────────────────────────── */
  function renderSidebar(tocItems, nav) {
    var sidebar = document.getElementById(SIDEBAR_ID);
    if (!sidebar) return;

    var html = '';

    // Chapter navigation (prev / contents / next)
    html += '<div class="oc-chnav">';
    if (nav.index) {
      html += '<a class="oc-chnav__index" href="' + nav.index + '">Contents</a>';
    }
    var arrows = '';
    if (nav.prev) {
      arrows += '<a class="oc-chnav__arrow oc-chnav__prev" href="' + nav.prev +
                '" aria-label="Previous chapter">\u2190 Prev</a>';
    }
    if (nav.next) {
      arrows += '<a class="oc-chnav__arrow oc-chnav__next" href="' + nav.next +
                '" aria-label="Next chapter">Next \u2192</a>';
    }
    if (arrows) {
      html += '<div class="oc-chnav__arrows">' + arrows + '</div>';
    }
    html += '</div>';

    // Table of contents
    if (tocItems.length) {
      html += '<nav class="oc-toc" aria-label="Sections on this page">';
      html += '<p class="oc-toc__heading">On this page</p>';
      html += '<ol class="oc-toc__list">';
      for (var i = 0; i < tocItems.length; i++) {
        var item    = tocItems[i];
        var escaped = item.text
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;');
        html += '<li class="oc-toc__item">';
        html += '<a class="oc-toc__link" href="#' + encodeURIComponent(item.anchor) +
                '" data-anchor="' + item.anchor + '">' + escaped + '</a>';
        html += '</li>';
      }
      html += '</ol>';
      html += '</nav>';
    }

    sidebar.innerHTML = html;
  }

  /* ── 4. Inject bottom chapter navigation ─────────────────────────────── */
  function renderBottomNav(nav) {
    if (!nav.prev && !nav.next) return;
    var footer = document.querySelector('.oc-footer');
    if (!footer) return;

    var el = document.createElement('nav');
    el.className = 'oc-bottomnav';
    el.setAttribute('aria-label', 'Chapter navigation');

    var html = '';
    if (nav.prev) {
      html += '<a class="oc-bottomnav__prev" href="' + nav.prev + '">\u2190 Previous</a>';
    } else {
      html += '<span class="oc-bottomnav__spacer"></span>';
    }
    if (nav.index) {
      html += '<a class="oc-bottomnav__index" href="' + nav.index + '">Contents</a>';
    }
    if (nav.next) {
      html += '<a class="oc-bottomnav__next" href="' + nav.next + '">Next \u2192</a>';
    } else {
      html += '<span class="oc-bottomnav__spacer"></span>';
    }
    el.innerHTML = html;
    footer.before(el);
  }

  /* ── 5. Hide Kuphaldt image navigation ───────────────────────────────── */
  function hideImageNav() {
    var links = document.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
      var a   = links[i];
      var img = a.querySelector('img');
      if (!img) continue;
      var src = (img.getAttribute('src') || '').toLowerCase();
      if (src.indexOf('previous') !== -1 ||
          src.indexOf('next')     !== -1 ||
          src.indexOf('contents') !== -1) {
        a.hidden = true;
      }
    }
  }

  /* ── 6. Scroll spy — highlight active TOC section ────────────────────── */
  function setupScrollSpy(tocItems) {
    if (!tocItems.length) return;

    function getHeaderHeight() {
      var prop = getComputedStyle(document.documentElement)
        .getPropertyValue('--oc-header-h');
      return (parseInt(prop, 10) || 52) + 16;
    }

    function update() {
      var threshold = window.scrollY + getHeaderHeight();
      var active    = tocItems[0].anchor;
      for (var i = 0; i < tocItems.length; i++) {
        var top = tocItems[i].el.getBoundingClientRect().top + window.scrollY;
        if (top <= threshold) {
          active = tocItems[i].anchor;
        }
      }
      var tlinks = document.querySelectorAll('.oc-toc__link');
      for (var j = 0; j < tlinks.length; j++) {
        var isActive = tlinks[j].getAttribute('data-anchor') === active;
        tlinks[j].classList.toggle('is-active', isActive);
      }
    }

    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* ── 7. Sidebar toggle ────────────────────────────────────────────────── */
  function setupToggle() {
    var toggle  = document.getElementById(TOGGLE_ID);
    var sidebar = document.getElementById(SIDEBAR_ID);
    if (!toggle || !sidebar) return;

    // Mobile scrim (tap-to-close backdrop)
    var scrim = document.createElement('div');
    scrim.id = SCRIM_ID;
    scrim.className = 'oc-sidebar-scrim';
    scrim.setAttribute('aria-hidden', 'true');
    document.body.appendChild(scrim);

    function isDesktop() {
      return window.matchMedia('(min-width: ' + MOBILE_BREAK + 'px)').matches;
    }

    function setOpen(open) {
      document.body.classList.toggle('sidebar-closed', !open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      try { localStorage.setItem(STORAGE_KEY, open ? 'true' : 'false'); } catch (e) {}
    }

    // Restore saved preference; default: open on desktop, closed on mobile
    var saved;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    var initialOpen = (saved !== null) ? (saved === 'true') : isDesktop();
    setOpen(initialOpen);

    toggle.addEventListener('click', function () {
      var isOpen = !document.body.classList.contains('sidebar-closed');
      setOpen(!isOpen);
    });

    scrim.addEventListener('click', function () {
      setOpen(false);
    });
  }

  /* ── init ─────────────────────────────────────────────────────────────── */
  function init() {
    var nav      = extractChapterNav();
    var tocItems = buildTocItems();
    renderSidebar(tocItems, nav);
    renderBottomNav(nav);
    hideImageNav();
    setupScrollSpy(tocItems);
    setupToggle();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
