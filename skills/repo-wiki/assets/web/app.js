/* repo-wiki — app.js — page view: /api/page + frontmatter + body + TOC */

(function () {
  "use strict";

  const tree = document.getElementById("tree");
  const contentInner = document.getElementById("content-inner");

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

  function renderPage(data) {
    var fm = data.frontmatter || {};
    var md = data.markdown || "";

    // Render markdown body via vendored marked
    var bodyHtml = window.marked ? window.marked.parse(md) : "<pre>" + escHtml(md) + "</pre>";

    // Build the page header area
    // Placeholder spot: staleness badge + covers chips + backlinks go here in later ticks (rcs)
    var title = fm.title || data.path.replace(/^.*\//, "").replace(/\.md$/, "");
    var headerHtml =
      '<header class="page-header">' +
      "<h1>" + escHtml(title) + "</h1>" +
      '<div class="page-meta-placeholder"><!-- staleness badge + covers chips + backlinks (rcs) --></div>' +
      renderFrontmatterTable(fm) +
      "</header>";

    // Assemble the layout: TOC rail + body column
    // We insert body first into a temp container to query headings for TOC
    var tempDiv = document.createElement("div");
    tempDiv.innerHTML = bodyHtml;

    var tocItems = buildTocItems(tempDiv);

    // Build final layout
    var layoutHtml =
      '<div class="page-layout">' +
      '<article class="page-body">' + headerHtml + tempDiv.innerHTML + "</article>" +
      renderToc(tocItems) +
      "</div>";

    contentInner.innerHTML = layoutHtml;

    // Wire TOC active tracking
    wireActiveToc(contentInner);

    // Scroll content pane to top
    var contentPane = document.getElementById("content");
    if (contentPane) contentPane.scrollTop = 0;
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
            escHtml(pageLabel(p)) +
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
            escHtml(pageLabel(p)) +
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
          escHtml(pageLabel(p)) +
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

  // ── boot ────────────────────────────────────────────────────────────────────

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
