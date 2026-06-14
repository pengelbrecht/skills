/* repo-wiki — app.js — walking skeleton: sidebar tree from /api/tree
 *
 * Seam: clicking a page updates location.hash only — actual rendering
 * lives in the NEXT tick (c05). marked.min.js is vendored and available
 * globally via <script src="/marked.min.js"> for that tick to use.
 */

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

  function navigateTo(path) {
    location.hash = encodeURIComponent(path);
    setActive(path);
    // content rendering placeholder — next tick wires this up
    contentInner.innerHTML =
      '<p class="welcome">Page: <code>' +
      escHtml(path) +
      '</code><br><span style="color:var(--muted);font-size:.875rem">Full rendering coming in the next tick.</span></p>';
  }

  function escHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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
