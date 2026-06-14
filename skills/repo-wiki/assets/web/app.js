/* repo-wiki — app.js — page view: /api/page + frontmatter + body + TOC */

(function () {
  "use strict";

  const tree = document.getElementById("tree");
  const contentInner = document.getElementById("content-inner");

  // ── staleness state (fetched once at boot) ──────────────────────────────────
  // _status = { stale: { "path/page.md": {action, source, changed} }, unverified: [...] }
  var _status = null;

  function fetchStatus() {
    fetch("/api/status")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        _status = data;
        // Re-render sidebar pills once status arrives (sidebar may already be built)
        updateSidebarPills();
      })
      .catch(function () {
        // Non-fatal: proceed without staleness data
        _status = { stale: {}, unverified: [] };
      });
  }

  /** Return {state, label} for a page path: "fresh" | "stale" | "unverified" */
  function pageState(path) {
    if (!_status) return null;
    if (_status.stale && _status.stale[path]) return { state: "stale", label: "stale" };
    if (_status.unverified && _status.unverified.indexOf(path) !== -1) return { state: "unverified", label: "?" };
    return { state: "fresh", label: "fresh" };
  }

  /** Render a small staleness pill span, or "" if status not yet loaded. */
  function renderPill(path) {
    var ps = pageState(path);
    if (!ps) return "";
    return '<span class="status-pill ' + ps.state + '">' + escHtml(ps.label) + '</span>';
  }

  /** Update all sidebar link pills after status is loaded. */
  function updateSidebarPills() {
    if (!_status) return;
    document.querySelectorAll(".page-item a[data-path]").forEach(function (a) {
      var path = a.dataset.path;
      // Find or create the pill span
      var pill = a.querySelector(".status-pill");
      if (!pill) {
        pill = document.createElement("span");
        a.appendChild(pill);
      }
      var ps = pageState(path);
      if (ps) {
        pill.className = "status-pill " + ps.state;
        pill.textContent = ps.label;
      }
    });
  }

  // ── helpers ─────────────────────────────────────────────────────────────────

  function setActive(path) {
    document.querySelectorAll(".page-item a").forEach(function (a) {
      a.classList.toggle("active", a.dataset.path === path);
    });
  }

  function escHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Slugify a heading text into an anchor id (same logic as GitHub). */
  function slugify(text) {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .trim()
      .replace(/[\s_]+/g, "-");
  }

  /** Render the frontmatter fields we care about as a compact table. */
  var FM_FIELDS = ["type", "source", "covers", "verified_against", "status"];

  function renderFrontmatterTable(fm) {
    var rows = FM_FIELDS.filter(function (k) { return fm[k] !== undefined && fm[k] !== ""; });
    if (!rows.length) return "";
    var html = '<table class="fm-table"><tbody>';
    rows.forEach(function (k) {
      var v = fm[k];
      if (Array.isArray(v)) v = v.join(", ");
      html += "<tr><th>" + escHtml(k) + "</th><td>" + escHtml(String(v)) + "</td></tr>";
    });
    html += "</tbody></table>";
    return html;
  }

  /**
   * Parse h2/h3 headings from rendered HTML and return [{level, text, id}].
   * We add id attributes to those headings as a side-effect after insertion.
   */
  function buildTocItems(container) {
    var items = [];
    container.querySelectorAll("h2, h3").forEach(function (el) {
      var text = el.textContent.trim();
      var id = slugify(text);
      // Ensure unique ids by appending a counter when needed
      var existing = document.getElementById(id);
      if (existing && existing !== el) {
        var n = 2;
        while (document.getElementById(id + "-" + n)) n++;
        id = id + "-" + n;
      }
      el.id = id;
      items.push({ level: parseInt(el.tagName[1], 10), text: text, id: id });
    });
    return items;
  }

  function renderToc(items) {
    if (!items.length) return "";
    var html = '<nav class="page-toc" aria-label="On this page"><p class="toc-title">On this page</p><ul>';
    items.forEach(function (item) {
      html +=
        '<li class="toc-' + item.level + '">' +
        '<a href="#' + escHtml(item.id) + '">' + escHtml(item.text) + "</a></li>";
    });
    html += "</ul></nav>";
    return html;
  }

  /** Wire IntersectionObserver to highlight the active TOC link (cheap, no layout). */
  function wireActiveToc(contentEl) {
    var tocLinks = document.querySelectorAll(".page-toc a[href^='#']");
    if (!tocLinks.length || !window.IntersectionObserver) return;
    var active = null;
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var id = entry.target.id;
            tocLinks.forEach(function (a) {
              var on = a.getAttribute("href") === "#" + id;
              a.classList.toggle("toc-active", on);
              if (on) active = a;
            });
          }
        });
      },
      { rootMargin: "-10% 0px -80% 0px", threshold: 0 }
    );
    contentEl.querySelectorAll("h2, h3").forEach(function (h) { observer.observe(h); });
  }

  // ── page rendering ──────────────────────────────────────────────────────────

  function navigateTo(path) {
    location.hash = encodeURIComponent(path);
    setActive(path);

    // Show a loading state while fetching
    contentInner.innerHTML = '<p class="welcome">Loading…</p>';

    fetch("/api/page?path=" + encodeURIComponent(path))
      .then(function (r) {
        if (!r.ok) return r.json().then(function (e) { throw new Error(e.error || "HTTP " + r.status); });
        return r.json();
      })
      .then(function (data) {
        renderPage(data);
      })
      .catch(function (err) {
        contentInner.innerHTML =
          '<p class="page-error">Failed to load <code>' + escHtml(path) + "</code>: " + escHtml(String(err)) + "</p>";
      });
  }

  /** Render covers chips from frontmatter. */
  function renderCoversChips(fm) {
    var covers = fm.covers || [];
    if (typeof covers === "string") covers = covers ? [covers] : [];
    if (!covers.length) return "";
    var html = '<span class="covers-label">covers:</span>';
    covers.forEach(function (glob) {
      html += '<span class="covers-chip">' + escHtml(glob) + '</span>';
    });
    return html;
  }

  /** Render staleness badge for the page header. */
  function renderHeaderBadge(path) {
    return renderPill(path);
  }

  // ── comment feature state ────────────────────────────────────────────────────

  var _currentPagePath = null;   // path of currently loaded page
  var _currentMarkdown = "";     // raw markdown of current page (for line lookup)

  // ── comment: floating button ─────────────────────────────────────────────────

  var _commentBtn = null;
  var _commentModal = null;
  var _commentPendingRange = null;  // saved Range when modal opens

  function ensureCommentBtn() {
    if (_commentBtn) return _commentBtn;
    _commentBtn = document.createElement("button");
    _commentBtn.className = "comment-float-btn";
    _commentBtn.textContent = "💬 Comment";
    _commentBtn.setAttribute("aria-label", "Add comment to selection");
    document.body.appendChild(_commentBtn);
    _commentBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      var sel = window.getSelection();
      if (sel && sel.rangeCount) {
        _commentPendingRange = sel.getRangeAt(0).cloneRange();
      }
      openCommentModal();
    });
    return _commentBtn;
  }

  function hideCommentBtn() {
    if (_commentBtn) {
      _commentBtn.style.display = "none";
    }
  }

  /** Return the .page-body article element if it exists, else null. */
  function getPageBodyEl() {
    return contentInner.querySelector("article.page-body");
  }

  /**
   * Return true if the given Node is fully inside the page body content area
   * (the <article class="page-body">), but NOT inside the page-header (title,
   * frontmatter table, etc.) or the backlinks section.
   */
  function isInsideContentBody(node) {
    var body = getPageBodyEl();
    if (!body) return false;
    // Walk up from node to see if it's inside page-body
    var el = node.nodeType === 3 ? node.parentElement : node;
    if (!body.contains(el)) return false;
    // Exclude page-header (title, fm table)
    var header = body.querySelector(".page-header");
    if (header && header.contains(el)) return false;
    // Exclude backlinks section
    var backlinks = body.querySelector(".backlinks-section");
    if (backlinks && backlinks.contains(el)) return false;
    return true;
  }

  document.addEventListener("selectionchange", function () {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.toString().trim()) {
      hideCommentBtn();
      return;
    }
    // Selection must be non-empty
    var selText = sel.toString();
    if (!selText.trim()) {
      hideCommentBtn();
      return;
    }
    // Check both anchor and focus nodes are inside content body
    if (sel.rangeCount === 0) {
      hideCommentBtn();
      return;
    }
    var range = sel.getRangeAt(0);
    if (!isInsideContentBody(range.startContainer) ||
        !isInsideContentBody(range.endContainer)) {
      hideCommentBtn();
      return;
    }

    // Position the floating button near the end of the selection
    var rect = range.getBoundingClientRect();
    var btn = ensureCommentBtn();
    btn.style.display = "flex";
    // Position just below the selection rectangle
    var top = rect.bottom + window.scrollY + 6;
    var left = rect.left + window.scrollX + (rect.width / 2);
    btn.style.top = top + "px";
    btn.style.left = left + "px";
  });

  // Hide the button when clicking outside (but not when clicking the button or modal)
  document.addEventListener("mousedown", function (e) {
    if (_commentBtn && e.target !== _commentBtn &&
        !(_commentModal && _commentModal.contains(e.target))) {
      hideCommentBtn();
    }
  });

  // ── comment: modal ───────────────────────────────────────────────────────────

  function openCommentModal() {
    var sel = window.getSelection();
    var selectedText = sel ? sel.toString() : "";
    if (!selectedText.trim()) return;

    hideCommentBtn();
    if (_commentModal) _commentModal.remove();

    var modal = document.createElement("div");
    modal.className = "comment-modal-overlay";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", "Add a comment");

    var previewText = selectedText.length > 120
      ? selectedText.slice(0, 120) + "…"
      : selectedText;

    modal.innerHTML =
      '<div class="comment-modal">' +
        '<p class="comment-modal-preview">' + escHtml(previewText) + '</p>' +
        '<textarea class="comment-modal-textarea" placeholder="Your comment…" rows="4"></textarea>' +
        '<p class="comment-modal-error" hidden></p>' +
        '<div class="comment-modal-actions">' +
          '<button class="comment-modal-submit" type="button">Submit</button>' +
          '<button class="comment-modal-cancel" type="button">Cancel</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(modal);
    _commentModal = modal;

    var textarea = modal.querySelector(".comment-modal-textarea");
    var submitBtn = modal.querySelector(".comment-modal-submit");
    var cancelBtn = modal.querySelector(".comment-modal-cancel");
    var errorEl = modal.querySelector(".comment-modal-error");

    // Focus the textarea
    setTimeout(function () { textarea.focus(); }, 0);

    function closeModal() {
      modal.remove();
      _commentModal = null;
      _commentPendingRange = null;
    }

    function showError(msg) {
      errorEl.textContent = msg;
      errorEl.hidden = false;
    }

    cancelBtn.addEventListener("click", closeModal);

    // Click-outside closes
    modal.addEventListener("mousedown", function (e) {
      if (e.target === modal) closeModal();
    });

    // Esc closes
    modal.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeModal();
    });

    submitBtn.addEventListener("click", function () {
      var commentText = textarea.value.trim();
      if (!commentText) {
        showError("Please enter a comment.");
        textarea.focus();
        return;
      }

      // Gather data
      var pageText = selectedText;
      var section = findNearestHeading(_commentPendingRange);
      var lines = findLinesInMarkdown(_currentMarkdown, pageText);

      var payload = {
        page: _currentPagePath || "",
        selected_text: pageText,
        comment: commentText,
        section: section,
        line: lines.line,
        end_line: lines.end_line
      };

      submitBtn.disabled = true;
      submitBtn.textContent = "Sending…";
      errorEl.hidden = true;

      fetch("/api/comment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })
        .then(function (r) {
          return r.json().then(function (d) { return { ok: r.ok, data: d }; });
        })
        .then(function (res) {
          if (!res.ok) {
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit";
            showError(res.data.error || "Server error");
            return;
          }
          // Success — show brief confirmation then close
          modal.querySelector(".comment-modal").innerHTML =
            '<p class="comment-modal-success">Comment sent.</p>';
          // Clear selection
          if (window.getSelection) window.getSelection().removeAllRanges();
          setTimeout(closeModal, 1200);
        })
        .catch(function (err) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Submit";
          showError("Network error: " + String(err));
        });
    });
  }

  /**
   * Find the nearest preceding heading text relative to the saved selection range.
   * Walks the DOM backwards from the range start to find the closest h2/h3/h4/h5.
   */
  function findNearestHeading(range) {
    if (!range) return "";
    var body = getPageBodyEl();
    if (!body) return "";
    // Collect all headings in body (excluding page-header)
    var headings = [];
    body.querySelectorAll("h2, h3, h4, h5").forEach(function (h) {
      // Skip headings inside the page-header
      var header = body.querySelector(".page-header");
      if (header && header.contains(h)) return;
      headings.push(h);
    });
    if (!headings.length) return "";

    // Find the last heading that comes before the selection start
    var startNode = range.startContainer;
    var best = null;
    headings.forEach(function (h) {
      // compareDocumentPosition: 4 means startNode follows h
      var pos = h.compareDocumentPosition(startNode);
      // DOCUMENT_POSITION_FOLLOWING = 4, or contains = 8+4
      if (pos & 4 /* following */ || pos & 8 /* contained by */) {
        best = h;
      }
    });
    return best ? best.textContent.trim() : "";
  }

  /**
   * Given raw markdown and a selected text string, find the 1-based start line
   * and end_line of the first occurrence. Returns {line, end_line} — both null
   * if not found.
   */
  function findLinesInMarkdown(markdown, selectedText) {
    if (!markdown || !selectedText) return { line: null, end_line: null };
    var idx = markdown.indexOf(selectedText);
    if (idx === -1) {
      // Try trimmed version (whitespace collapse)
      var trimmed = selectedText.trim();
      idx = markdown.indexOf(trimmed);
      if (idx === -1) return { line: null, end_line: null };
      selectedText = trimmed;
    }
    // Count newlines before idx for start line
    var before = markdown.slice(0, idx);
    var startLine = before.split("\n").length;  // 1-based
    var selLines = selectedText.split("\n").length;
    var endLine = startLine + selLines - 1;
    return { line: startLine, end_line: endLine };
  }

  // ── page rendering ──────────────────────────────────────────────────────────

  function renderPage(data) {
    var fm = data.frontmatter || {};
    var md = data.markdown || "";
    var pagePath = data.path;

    // Cache raw markdown and path for comment line-anchor computation
    _currentMarkdown = md;
    _currentPagePath = pagePath;

    // Render markdown body via vendored marked
    var bodyHtml = window.marked ? window.marked.parse(md) : "<pre>" + escHtml(md) + "</pre>";

    // Build the page header area
    var title = fm.title || pagePath.replace(/^.*\//, "").replace(/\.md$/, "");

    // Page meta: staleness pill + covers chips
    var metaHtml = renderHeaderBadge(pagePath) + renderCoversChips(fm);

    var headerHtml =
      '<header class="page-header">' +
      "<h1>" + escHtml(title) + "</h1>" +
      '<div class="page-meta-placeholder">' + metaHtml + '</div>' +
      renderFrontmatterTable(fm) +
      "</header>";

    // Assemble the layout: TOC rail + body column
    // We insert body first into a temp container to query headings for TOC
    var tempDiv = document.createElement("div");
    tempDiv.innerHTML = bodyHtml;

    var tocItems = buildTocItems(tempDiv);

    // Build final layout (backlinks placeholder div appended after body)
    var layoutHtml =
      '<div class="page-layout">' +
      '<article class="page-body">' +
      headerHtml +
      tempDiv.innerHTML +
      '<div class="backlinks-section" id="backlinks-section">' +
      '<p class="backlinks-title">Backlinks</p>' +
      '<p class="backlinks-empty">Loading backlinks…</p>' +
      '</div>' +
      "</article>" +
      renderToc(tocItems) +
      "</div>";

    contentInner.innerHTML = layoutHtml;

    // Wire TOC active tracking
    wireActiveToc(contentInner);

    // Scroll content pane to top
    var contentPane = document.getElementById("content");
    if (contentPane) contentPane.scrollTop = 0;

    // Fetch and render backlinks asynchronously
    fetchBacklinks(pagePath);
  }

  /** Fetch /api/backlinks and update the backlinks section. */
  function fetchBacklinks(pagePath) {
    fetch("/api/backlinks?path=" + encodeURIComponent(pagePath))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var section = document.getElementById("backlinks-section");
        if (!section) return;
        var backlinks = data.backlinks || [];
        if (!backlinks.length) {
          section.innerHTML =
            '<p class="backlinks-title">Backlinks</p>' +
            '<p class="backlinks-empty">No backlinks.</p>';
          return;
        }
        var html = '<p class="backlinks-title">Backlinks</p><ul class="backlinks-list">';
        backlinks.forEach(function (b) {
          var label = b.path.replace(/\.md$/, "");
          html +=
            '<li>' +
            '<a href="#" class="backlinks-link" data-path="' + escHtml(b.path) + '">' +
            escHtml(label) +
            '<span class="backlinks-line">:' + b.line + '</span>' +
            '</a>' +
            '<p class="backlinks-snippet">' + escHtml(b.snippet) + '</p>' +
            '</li>';
        });
        html += '</ul>';
        section.innerHTML = html;
        // Wire clicks
        section.addEventListener("click", function (e) {
          var a = e.target.closest("a.backlinks-link[data-path]");
          if (!a) return;
          e.preventDefault();
          navigateTo(a.dataset.path);
        });
      })
      .catch(function () {
        var section = document.getElementById("backlinks-section");
        if (section) {
          section.innerHTML =
            '<p class="backlinks-title">Backlinks</p>' +
            '<p class="backlinks-empty">Could not load backlinks.</p>';
        }
      });
  }

  function pageLabel(page) {
    // Prefer a human-readable slug: strip leading folder path + .md
    var name = page.path.replace(/^[^/]+\//, "").replace(/\.md$/, "");
    // replace hyphens/underscores with spaces and title-case first letter
    return name.replace(/[-_]/g, " ").replace(/^./, function (c) {
      return c.toUpperCase();
    });
  }

  // ── render sidebar ──────────────────────────────────────────────────────────

  function buildSidebar(data) {
    var html = "";

    var folders = data.folders || [];
    var pages = data.pages || [];

    // Index pages by folder
    var byFolder = {};
    var loose = [];
    pages.forEach(function (p) {
      var slash = p.path.indexOf("/");
      if (slash === -1) {
        loose.push(p);
      } else {
        var folder = p.path.slice(0, slash);
        (byFolder[folder] = byFolder[folder] || []).push(p);
      }
    });

    // Folders with known purpose
    folders.forEach(function (f) {
      var fps = byFolder[f.name] || [];
      html += '<div class="folder-group" role="group" aria-label="' + escHtml(f.name) + '">';
      html +=
        '<div class="folder-label"><span class="folder-icon">▸</span>' +
        escHtml(f.name) +
        "</div>";
      if (fps.length > 0) {
        html += '<ul class="page-list">';
        fps.forEach(function (p) {
          html +=
            '<li class="page-item"><a href="#" data-path="' +
            escHtml(p.path) +
            '" title="' +
            escHtml(p.summary || p.path) +
            '">' +
            '<span class="page-label-text">' + escHtml(pageLabel(p)) + "</span>" +
            renderPill(p.path) +
            "</a></li>";
        });
        html += "</ul>";
      }
      html += "</div>";
      // remove from byFolder so we don't re-render in the "orphan" pass
      delete byFolder[f.name];
    });

    // Orphan folders (pages in a folder not listed in data.folders)
    Object.keys(byFolder)
      .sort()
      .forEach(function (folder) {
        var fps = byFolder[folder];
        html += '<div class="folder-group" role="group" aria-label="' + escHtml(folder) + '">';
        html +=
          '<div class="folder-label"><span class="folder-icon">▸</span>' +
          escHtml(folder) +
          "</div>";
        html += '<ul class="page-list">';
        fps.forEach(function (p) {
          html +=
            '<li class="page-item"><a href="#" data-path="' +
            escHtml(p.path) +
            '">' +
            '<span class="page-label-text">' + escHtml(pageLabel(p)) + "</span>" +
            renderPill(p.path) +
            "</a></li>";
        });
        html += "</ul></div>";
      });

    // Loose pages (no folder)
    if (loose.length > 0) {
      html += '<ul class="page-list loose-pages">';
      loose.forEach(function (p) {
        html +=
          '<li class="page-item"><a href="#" data-path="' +
          escHtml(p.path) +
          '">' +
          '<span class="page-label-text">' + escHtml(pageLabel(p)) + "</span>" +
          renderPill(p.path) +
          "</a></li>";
      });
      html += "</ul>";
    }

    if (!html) {
      html = '<p class="tree-loading">Wiki is empty — run <code>kb.py init</code> and seed some pages.</p>';
    }

    tree.innerHTML = html;

    // delegate clicks on page links
    tree.addEventListener("click", function (e) {
      var a = e.target.closest("a[data-path]");
      if (!a) return;
      e.preventDefault();
      navigateTo(a.dataset.path);
    });

    // restore hash on load
    var hash = location.hash.slice(1);
    if (hash) {
      var decoded = decodeURIComponent(hash);
      navigateTo(decoded);
    }
  }

  // ── search ──────────────────────────────────────────────────────────────────

  var searchResults = document.getElementById("search-results");
  var searchInput = document.getElementById("search-input");
  var _searchTimer = null;

  function showTree() {
    tree.hidden = false;
    if (searchResults) searchResults.hidden = true;
  }

  function showSearchResults(results, q) {
    tree.hidden = true;
    searchResults.hidden = false;
    if (!results.length) {
      searchResults.innerHTML = '<p class="search-empty">No results for <em>' + escHtml(q) + '</em></p>';
      return;
    }
    var html = '<ul class="search-list">';
    results.forEach(function (r) {
      var label = r.path.replace(/\.md$/, "");
      html +=
        '<li class="search-item">' +
        '<a href="#" class="search-path" data-path="' + escHtml(r.path) + '">' +
        escHtml(label) +
        '<span class="search-line">:' + r.line + '</span>' +
        '</a>' +
        '<p class="search-snippet">' + escHtml(r.snippet) + '</p>' +
        '</li>';
    });
    html += '</ul>';
    searchResults.innerHTML = html;
  }

  function doSearch(q) {
    q = q.trim();
    if (!q) {
      showTree();
      return;
    }
    fetch("/api/search?q=" + encodeURIComponent(q))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        showSearchResults(data.results || [], q);
      })
      .catch(function () {
        searchResults.hidden = false;
        tree.hidden = true;
        searchResults.innerHTML = '<p class="search-empty">Search failed.</p>';
      });
  }

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      clearTimeout(_searchTimer);
      var q = searchInput.value;
      if (!q.trim()) {
        showTree();
        return;
      }
      _searchTimer = setTimeout(function () { doSearch(q); }, 250);
    });
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        searchInput.value = "";
        showTree();
      }
    });
  }

  if (searchResults) {
    searchResults.addEventListener("click", function (e) {
      var a = e.target.closest("a[data-path]");
      if (!a) return;
      e.preventDefault();
      navigateTo(a.dataset.path);
    });
  }

  // ── boot ────────────────────────────────────────────────────────────────────

  // Fetch staleness status in parallel with the tree — updates sidebar pills when ready.
  fetchStatus();

  fetch("/api/tree")
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(buildSidebar)
    .catch(function (err) {
      tree.innerHTML =
        '<div class="tree-error">Failed to load wiki tree: ' + escHtml(String(err)) + "</div>";
    });
})();
