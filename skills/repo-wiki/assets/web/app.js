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

  /** Render a small staleness pill span. Only code-tracked pages (fresh/stale) get a
   *  pill; pages with no `covers` ("unverified") are a normal, permanent state and show
   *  no badge — a wall of grey "?" on a fresh wiki reads as alarming when nothing is wrong. */
  function renderPill(path) {
    var ps = pageState(path);
    if (!ps || ps.state === "unverified") return "";
    return '<span class="status-pill ' + ps.state + '">' + escHtml(ps.label) + '</span>';
  }

  /** Update all sidebar link pills after status is loaded. */
  function updateSidebarPills() {
    if (!_status) return;
    document.querySelectorAll(".page-item a[data-path]").forEach(function (a) {
      var path = a.dataset.path;
      var ps = pageState(path);
      var pill = a.querySelector(".status-pill");
      // No badge for not-code-tracked ("unverified") pages — remove any stale pill.
      if (!ps || ps.state === "unverified") {
        if (pill) pill.remove();
        return;
      }
      if (!pill) {
        pill = document.createElement("span");
        a.appendChild(pill);
      }
      pill.className = "status-pill " + ps.state;
      pill.textContent = ps.label;
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
    // Expand the folder containing this page (if any)
    var folder = folderOfPath(path);
    if (folder) expandFolder(folder);

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

  var _currentPagePath = null;       // path of currently loaded page
  var _currentMarkdown = "";         // raw markdown of current page (for line lookup)
  var _currentFrontmatterLines = 0;  // number of lines occupied by the frontmatter block

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

      // Offset line anchors by frontmatter_lines so they match the real on-disk
      // file line numbers (the server strips frontmatter from the returned markdown,
      // but the agent reads the full file including frontmatter).
      var fmLines = _currentFrontmatterLines || 0;
      var adjustedLine = lines.line != null ? lines.line + fmLines : null;
      var adjustedEndLine = lines.end_line != null ? lines.end_line + fmLines : null;

      var payload = {
        page: _currentPagePath || "",
        selected_text: pageText,
        comment: commentText,
        section: section,
        line: adjustedLine,
        end_line: adjustedEndLine
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

    // Cache raw markdown, path, and frontmatter line count for comment line-anchor computation.
    // frontmatter_lines is the number of lines in the stripped block (both --- delimiters +
    // any trailing blank line) so line anchors can be offset to match real on-disk numbers.
    _currentMarkdown = md;
    _currentPagePath = pagePath;
    _currentFrontmatterLines = data.frontmatter_lines || 0;

    // Render markdown body via vendored marked
    var bodyHtml = window.marked ? window.marked.parse(md) : "<pre>" + escHtml(md) + "</pre>";

    // Build the page header area
    // For INDEX.md pages without a frontmatter title, use folder name or "Home"
    var defaultTitle;
    if (/(?:^|\/)INDEX\.md$/.test(pagePath)) {
      var slash = pagePath.lastIndexOf("/");
      defaultTitle = slash === -1 ? "Home" : pagePath.slice(0, slash);
    } else {
      defaultTitle = pagePath.replace(/^.*\//, "").replace(/\.md$/, "");
    }
    var title = fm.title || defaultTitle;

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

  // ── folder collapse / localStorage helpers ─────────────────────────────────

  var LS_PREFIX = "repo-wiki:folder-collapsed:";

  function isFolderCollapsed(folderName) {
    try {
      return localStorage.getItem(LS_PREFIX + folderName) === "1";
    } catch (e) {
      return false;
    }
  }

  function setFolderCollapsed(folderName, collapsed) {
    try {
      if (collapsed) {
        localStorage.setItem(LS_PREFIX + folderName, "1");
      } else {
        localStorage.removeItem(LS_PREFIX + folderName);
      }
    } catch (e) { /* non-fatal */ }
  }

  /** Return the folder name that contains the given page path, or null. */
  function folderOfPath(pagePath) {
    if (!pagePath) return null;
    var slash = pagePath.indexOf("/");
    return slash === -1 ? null : pagePath.slice(0, slash);
  }

  /** Toggle a folder's collapsed state (called from chevron click). */
  function toggleFolder(folderName) {
    var group = tree.querySelector('.folder-group[data-folder="' + CSS.escape(folderName) + '"]');
    if (!group) return;
    var btn = group.querySelector(".folder-chevron-btn");
    var list = group.querySelector(".page-list");
    var collapsed = group.classList.toggle("folder-collapsed");
    if (btn) {
      btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
      btn.textContent = collapsed ? "▸" : "▾";
    }
    if (list) {
      list.hidden = collapsed;
    }
    setFolderCollapsed(folderName, collapsed);
  }

  /** Ensure a folder is expanded (called when navigating into it). */
  function expandFolder(folderName) {
    var group = tree.querySelector('.folder-group[data-folder="' + CSS.escape(folderName) + '"]');
    if (!group) return;
    if (!group.classList.contains("folder-collapsed")) return; // already open
    var btn = group.querySelector(".folder-chevron-btn");
    var list = group.querySelector(".page-list");
    group.classList.remove("folder-collapsed");
    if (btn) {
      btn.setAttribute("aria-expanded", "true");
      btn.textContent = "▾";
    }
    if (list) {
      list.hidden = false;
    }
    setFolderCollapsed(folderName, false);
  }

  /** Build HTML for one folder group. collapsed = initial collapsed state. */
  function buildFolderGroupHtml(folderName, fps, collapsed, summary) {
    var escapedName = escHtml(folderName);
    var chevron = collapsed ? "▸" : "▾";
    var html = '<div class="folder-group' + (collapsed ? " folder-collapsed" : "") + '"' +
      ' data-folder="' + escapedName + '"' +
      ' role="group" aria-label="' + escapedName + '">';

    html += '<div class="folder-label">' +
      '<button class="folder-chevron-btn" aria-label="Toggle ' + escapedName + '" aria-expanded="' + (collapsed ? "false" : "true") + '" data-folder-toggle="' + escapedName + '">' + chevron + '</button>' +
      '<button class="folder-name-btn" data-folder-index="' + escapedName + '" title="' + (summary ? escHtml(summary) : 'Open ' + escapedName + '/INDEX.md') + '">' + escapedName + '</button>' +
      '</div>';

    if (fps.length > 0) {
      html += '<ul class="page-list"' + (collapsed ? ' hidden' : '') + '>';
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
    return html;
  }

  // ── render sidebar ──────────────────────────────────────────────────────────

  function buildSidebar(data) {
    var html = "";

    var folders = data.folders || [];
    var pages = data.pages || [];

    // The active folder (so we can force it expanded even if collapsed in localStorage)
    var activeFolder = folderOfPath(_currentPagePath);

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
      // Force-expand the active folder; otherwise restore persisted state
      var collapsed = (f.name === activeFolder) ? false : isFolderCollapsed(f.name);
      html += buildFolderGroupHtml(f.name, fps, collapsed, f.summary || "");
      // remove from byFolder so we don't re-render in the "orphan" pass
      delete byFolder[f.name];
    });

    // Orphan folders (pages in a folder not listed in data.folders)
    Object.keys(byFolder)
      .sort()
      .forEach(function (folder) {
        var fps = byFolder[folder];
        var collapsed = (folder === activeFolder) ? false : isFolderCollapsed(folder);
        html += buildFolderGroupHtml(folder, fps, collapsed, "");
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
    // NOTE: the click handler and the initial hash-restore are wired once at boot
    // (see the boot section below) — do NOT add them here or they accumulate on
    // every _refreshSidebar() call.
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

  // ── live auto-refresh (poll mtime) ─────────────────────────────────────────
  //
  // Every POLL_MS:
  //   1. If a page is open and the modal is closed and no text is selected,
  //      check /api/changed?path=<current> — if mtime increased, re-fetch + re-render
  //      in place, preserving scroll position.
  //   2. Check /api/revision (max mtime across all .md files) — if it changed,
  //      refresh the sidebar tree + status pills so new/edited pages appear.
  //
  // One interval, cleared and reset on navigation so a stale path never fires.

  var POLL_MS = 1500;

  var _pollTimer = null;
  var _lastKnownMtime = null;   // mtime of the currently-viewed file (from /api/page)
  var _lastRevision   = null;   // last seen /api/revision value

  /** True when we should skip the page refresh (modal open or text selected). */
  function _shouldSkipRefresh() {
    // Comment modal is open
    if (_commentModal) return true;
    // Text is currently selected
    var sel = window.getSelection();
    if (sel && !sel.isCollapsed && sel.toString().trim()) return true;
    return false;
  }

  /** Refresh the sidebar tree and status pills without losing the active page state. */
  function _refreshSidebar() {
    Promise.all([
      fetch("/api/tree").then(function (r) { return r.json(); }),
      fetch("/api/status").then(function (r) { return r.json(); })
    ]).then(function (results) {
      var treeData   = results[0];
      var statusData = results[1];
      // Update status state so pills render correctly
      _status = statusData;
      // Rebuild the sidebar HTML
      buildSidebar(treeData);
      // Re-apply active highlight WITHOUT re-navigating (hash-restore only runs at boot).
      if (_currentPagePath) setActive(_currentPagePath);
    }).catch(function () { /* non-fatal */ });
  }

  /**
   * Re-render the current page in place, preserving scroll position.
   * Called when the poll detects that the file's mtime has increased.
   */
  function _refreshCurrentPage(newMtime) {
    if (!_currentPagePath) return;
    var contentPane = document.getElementById("content");
    var savedScroll = contentPane ? contentPane.scrollTop : 0;

    fetch("/api/page?path=" + encodeURIComponent(_currentPagePath))
      .then(function (r) {
        if (!r.ok) return null;
        return r.json();
      })
      .then(function (data) {
        if (!data || data.error) return;
        // Only re-render if we're still on the same page
        if (data.path !== _currentPagePath) return;
        // Update the known mtime before re-rendering (renderPage sets _currentMarkdown etc.)
        _lastKnownMtime = data.mtime != null ? data.mtime : newMtime;
        renderPage(data);
        // Restore scroll (renderPage resets to 0; override immediately after)
        if (contentPane && savedScroll > 0) {
          contentPane.scrollTop = savedScroll;
        }
        // Keep active highlight correct
        setActive(_currentPagePath);
      })
      .catch(function () { /* non-fatal */ });
  }

  /** One tick of the poll loop. */
  function _pollTick() {
    var skip = _shouldSkipRefresh();

    // — Page freshness check —
    if (!skip && _currentPagePath && _lastKnownMtime != null) {
      (function (path, knownMtime) {
        fetch("/api/changed?path=" + encodeURIComponent(path))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.mtime != null && data.mtime > knownMtime) {
              _refreshCurrentPage(data.mtime);
            }
          })
          .catch(function () { /* non-fatal */ });
      })(_currentPagePath, _lastKnownMtime);
    }

    // — Sidebar revision check (always, regardless of modal/selection) —
    fetch("/api/revision")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.revision == null) return;
        if (_lastRevision === null) {
          // First reading — just store it, don't trigger a refresh
          _lastRevision = data.revision;
          return;
        }
        if (data.revision > _lastRevision) {
          _lastRevision = data.revision;
          _refreshSidebar();
        }
      })
      .catch(function () { /* non-fatal */ });
  }

  /** Start (or restart) the poll timer. Called on every navigation. */
  function _startPoll() {
    if (_pollTimer) clearInterval(_pollTimer);
    _pollTimer = setInterval(_pollTick, POLL_MS);
  }

  // Patch navigateTo to capture the mtime from /api/page and (re)start the poll.
  var _origNavigateTo = navigateTo;
  navigateTo = function (path) {
    // Reset known mtime before the new page loads; will be set after renderPage
    _lastKnownMtime = null;
    _origNavigateTo(path);
    _startPoll();
  };

  // Patch renderPage to capture mtime from the API response.
  var _origRenderPage = renderPage;
  renderPage = function (data) {
    _origRenderPage(data);
    if (data.mtime != null) {
      _lastKnownMtime = data.mtime;
    }
  };

  // ── boot ────────────────────────────────────────────────────────────────────

  // Wire the tree click handler ONCE here so it is never duplicated by _refreshSidebar()
  // calling buildSidebar() on every revision change.
  tree.addEventListener("click", function (e) {
    // Chevron toggle button — collapse/expand the folder, no navigation
    var chevronBtn = e.target.closest("button[data-folder-toggle]");
    if (chevronBtn) {
      e.preventDefault();
      toggleFolder(chevronBtn.dataset.folderToggle);
      return;
    }
    // Folder name button — open folder's INDEX.md
    var nameBtn = e.target.closest("button[data-folder-index]");
    if (nameBtn) {
      e.preventDefault();
      var folder = nameBtn.dataset.folderIndex;
      // Ensure the folder is expanded when navigating into it
      expandFolder(folder);
      navigateTo(folder + "/INDEX.md");
      return;
    }
    // Regular page link
    var a = e.target.closest("a[data-path]");
    if (!a) return;
    e.preventDefault();
    navigateTo(a.dataset.path);
  });

  // Wire the Home button (sidebar title) to load root INDEX.md
  var homeBtn = document.getElementById("sidebar-home-btn");
  if (homeBtn) {
    homeBtn.addEventListener("click", function () {
      navigateTo("INDEX.md");
    });
  }

  // Fetch staleness status in parallel with the tree — updates sidebar pills when ready.
  fetchStatus();

  fetch("/api/tree")
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function (data) {
      buildSidebar(data);
      // Restore hash navigation ONCE at initial boot only — NOT on sidebar refreshes.
      var hash = location.hash.slice(1);
      if (hash) {
        var decoded = decodeURIComponent(hash);
        navigateTo(decoded);
      } else {
        // Landing state: no hash → try to load root INDEX.md as the home page.
        fetch("/api/page?path=INDEX.md")
          .then(function (r) {
            if (!r.ok) return null;
            return r.json();
          })
          .then(function (pageData) {
            if (pageData && !pageData.error) {
              renderPage(pageData);
            }
            // If INDEX.md doesn't exist, the "Select a page…" placeholder remains.
          })
          .catch(function () { /* fall through to placeholder */ });
      }
    })
    .catch(function (err) {
      tree.innerHTML =
        '<div class="tree-error">Failed to load wiki tree: ' + escHtml(String(err)) + "</div>";
    });

  // Start the revision poll immediately so the sidebar also refreshes when no page is open.
  _startPoll();
})();
