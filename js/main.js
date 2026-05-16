/**
 * Cute Flexi Maker — Parts Guide
 * Small, dependency-free progressive enhancements:
 *   - i18n: swap text from locales/<lang>.json based on data-i18n attributes
 *   - Active section highlight in the header nav
 *   - Show/hide back-to-top button on scroll
 *   - Click-to-zoom for page figures
 */

(function () {
    "use strict";

    /* ----------- Tiny helpers ----------- */

    function $(selector, scope) {
        return (scope || document).querySelector(selector);
    }

    function $$(selector, scope) {
        return Array.from((scope || document).querySelectorAll(selector));
    }


    /* ----------- i18n ----------- */

    var SUPPORTED_LANGS = ["en", "pt-BR", "es", "de"];
    var DEFAULT_LANG = "en";
    var STORAGE_KEY = "cfm-lang";

    function detectInitialLang() {
        var stored = null;
        try {
            stored = localStorage.getItem(STORAGE_KEY);
        } catch (_) { /* private mode */ }
        if (stored && SUPPORTED_LANGS.indexOf(stored) !== -1) {
            return stored;
        }
        var nav = (navigator.languages && navigator.languages[0]) || navigator.language || "";
        if (nav) {
            // exact match first (e.g. "pt-BR")
            for (var i = 0; i < SUPPORTED_LANGS.length; i++) {
                if (SUPPORTED_LANGS[i].toLowerCase() === nav.toLowerCase()) {
                    return SUPPORTED_LANGS[i];
                }
            }
            // base-language fallback (e.g. "pt" → "pt-BR", "de-AT" → "de")
            var navBase = nav.split("-")[0].toLowerCase();
            for (var j = 0; j < SUPPORTED_LANGS.length; j++) {
                if (SUPPORTED_LANGS[j].split("-")[0].toLowerCase() === navBase) {
                    return SUPPORTED_LANGS[j];
                }
            }
        }
        return DEFAULT_LANG;
    }

    var dictionary = {};

    function t(key) {
        return Object.prototype.hasOwnProperty.call(dictionary, key) ? dictionary[key] : null;
    }

    function applyTranslations() {
        // textContent
        $$("[data-i18n]").forEach(function (el) {
            var value = t(el.getAttribute("data-i18n"));
            if (value !== null) {
                el.textContent = value;
            }
        });
        // attribute translations: data-i18n-<attr>
        $$("[data-i18n-alt]").forEach(function (el) {
            var v = t(el.getAttribute("data-i18n-alt"));
            if (v !== null) { el.setAttribute("alt", v); }
        });
        $$("[data-i18n-aria-label]").forEach(function (el) {
            var v = t(el.getAttribute("data-i18n-aria-label"));
            if (v !== null) { el.setAttribute("aria-label", v); }
        });
        $$("[data-i18n-content]").forEach(function (el) {
            var v = t(el.getAttribute("data-i18n-content"));
            if (v !== null) { el.setAttribute("content", v); }
        });
        // document title
        var titleEl = document.querySelector("title[data-i18n]");
        if (titleEl) {
            var v = t(titleEl.getAttribute("data-i18n"));
            if (v !== null) { document.title = v; }
        }
    }

    function loadLocale(lang) {
        return fetch("locales/" + lang + ".json", { cache: "no-cache" })
            .then(function (res) {
                if (!res.ok) { throw new Error("locale " + lang + " not found"); }
                return res.json();
            });
    }

    function setLanguage(lang) {
        if (SUPPORTED_LANGS.indexOf(lang) === -1) { lang = DEFAULT_LANG; }
        return loadLocale(lang).then(function (dict) {
            dictionary = dict;
            document.documentElement.lang = lang;
            applyTranslations();
            try { localStorage.setItem(STORAGE_KEY, lang); } catch (_) {}
            var picker = $(".lang-picker");
            if (picker) { picker.value = lang; }
        }).catch(function (err) {
            if (lang !== DEFAULT_LANG) {
                console.warn("i18n:", err.message, "— falling back to", DEFAULT_LANG);
                return setLanguage(DEFAULT_LANG);
            }
            console.warn("i18n: default locale failed to load:", err.message);
        });
    }

    function setupLanguagePicker() {
        var picker = $(".lang-picker");
        if (!picker) { return; }
        picker.addEventListener("change", function () {
            setLanguage(picker.value);
        });
    }


    /* ----------- Active nav highlight ----------- */

    function setupActiveNavHighlight() {
        var navLinks = $$(".site-header__nav a[href^='#']");
        if (!navLinks.length || !("IntersectionObserver" in window)) {
            return;
        }

        var linkById = navLinks.reduce(function (map, link) {
            var id = link.getAttribute("href").slice(1);
            if (id) {
                map[id] = link;
            }
            return map;
        }, {});

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                var link = linkById[entry.target.id];
                if (!link) {
                    return;
                }
                if (entry.isIntersecting) {
                    Object.values(linkById).forEach(function (l) {
                        l.classList.remove("is-active");
                    });
                    link.classList.add("is-active");
                }
            });
        }, { rootMargin: "-40% 0px -55% 0px" });

        Object.keys(linkById).forEach(function (id) {
            var target = document.getElementById(id);
            if (target) {
                observer.observe(target);
            }
        });
    }


    /* ----------- Back-to-top button ----------- */

    function setupBackToTop() {
        var button = $(".back-to-top");
        if (!button) {
            return;
        }

        var showAfter = 600;

        function updateVisibility() {
            if (window.scrollY > showAfter) {
                button.hidden = false;
            } else {
                button.hidden = true;
            }
        }

        window.addEventListener("scroll", updateVisibility, { passive: true });
        button.addEventListener("click", function () {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });

        updateVisibility();
    }


    /* ----------- Click-to-zoom for figures ----------- */

    var ZOOM_SELECTOR = [
        ".parts-grid img",
        ".composite-figure img",
        ".text-layout__figure img",
        ".symbols-layout__preview img"
    ].join(", ");

    function setupImageZoom() {
        var modal = createZoomModal();
        document.body.appendChild(modal.root);

        $$(ZOOM_SELECTOR).forEach(function (img) {
            makeZoomable(img, modal);
        });
    }

    function makeZoomable(img, modal) {
        img.style.cursor = "zoom-in";
        img.setAttribute("tabindex", "0");
        img.setAttribute("role", "button");

        img.addEventListener("click", function () {
            modal.open(img);
        });
        img.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                modal.open(img);
            }
        });
    }

    function captionFor(img) {
        var figure = img.closest("figure");
        if (figure) {
            var cap = figure.querySelector("figcaption");
            if (cap && cap.textContent.trim()) {
                return cap.textContent.trim();
            }
        }
        return img.alt || "";
    }

    function createZoomModal() {
        var root = document.createElement("div");
        root.className = "zoom-modal";
        root.setAttribute("hidden", "");
        root.setAttribute("role", "dialog");
        root.setAttribute("aria-modal", "true");
        root.setAttribute("aria-labelledby", "zoom-modal-caption");

        var inner = document.createElement("div");
        inner.className = "zoom-modal__inner";
        root.appendChild(inner);

        var img = document.createElement("img");
        img.className = "zoom-modal__image";
        img.alt = "";
        inner.appendChild(img);

        var caption = document.createElement("p");
        caption.id = "zoom-modal-caption";
        caption.className = "zoom-modal__caption";
        inner.appendChild(caption);

        var closeBtn = document.createElement("button");
        closeBtn.className = "zoom-modal__close";
        closeBtn.type = "button";
        closeBtn.setAttribute("aria-label", "Close zoomed image");
        closeBtn.textContent = "×";
        root.appendChild(closeBtn);

        function open(sourceImg) {
            img.src = sourceImg.src;
            img.alt = sourceImg.alt || "";
            var label = captionFor(sourceImg);
            caption.textContent = label;
            caption.hidden = !label;
            root.hidden = false;
            document.body.style.overflow = "hidden";
            closeBtn.focus();
        }

        function close() {
            root.hidden = true;
            img.src = "";
            document.body.style.overflow = "";
        }

        root.addEventListener("click", function (event) {
            // close on backdrop or close button — never on the image itself
            if (event.target === root || event.target === closeBtn) {
                close();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !root.hidden) {
                close();
            }
        });

        injectZoomModalStyles();

        return { root: root, open: open, close: close };
    }

    function injectZoomModalStyles() {
        if (document.getElementById("zoom-modal-styles")) {
            return;
        }
        var style = document.createElement("style");
        style.id = "zoom-modal-styles";
        style.textContent = [
            ".zoom-modal {",
            "  position: fixed; inset: 0;",
            "  background: rgba(20, 14, 6, 0.86);",
            "  backdrop-filter: blur(4px);",
            "  -webkit-backdrop-filter: blur(4px);",
            "  z-index: 200;",
            "  display: flex; align-items: center; justify-content: center;",
            "  padding: 24px;",
            "  cursor: zoom-out;",
            "  animation: zoomFadeIn 0.18s ease-out;",
            "}",
            ".zoom-modal[hidden] { display: none; }",
            "@keyframes zoomFadeIn {",
            "  from { opacity: 0; }",
            "  to { opacity: 1; }",
            "}",
            ".zoom-modal__inner {",
            "  display: flex; flex-direction: column; align-items: center;",
            "  gap: 16px; cursor: default;",
            "  max-width: 100%;",
            "}",
            ".zoom-modal__image {",
            "  max-width: min(90vw, 720px);",
            "  max-height: 80vh;",
            "  width: auto; height: auto;",
            "  border-radius: 16px;",
            "  box-shadow: 0 20px 60px rgba(0,0,0,0.5);",
            "  background: rgba(245, 236, 220, 0.04);",
            "  animation: zoomImageIn 0.22s ease-out;",
            "}",
            "@keyframes zoomImageIn {",
            "  from { transform: scale(0.92); opacity: 0; }",
            "  to { transform: scale(1); opacity: 1; }",
            "}",
            ".zoom-modal__caption {",
            "  margin: 0;",
            "  color: #f5ecdc;",
            "  font-family: \"Borsok\", \"Fredoka\", var(--font-display, system-ui), sans-serif;",
            "  font-size: 1.1rem;",
            "  letter-spacing: 1px;",
            "  text-transform: uppercase;",
            "  text-align: center;",
            "}",
            ".zoom-modal__caption[hidden] { display: none; }",
            ".zoom-modal__close {",
            "  position: absolute; top: 16px; right: 20px;",
            "  width: 44px; height: 44px;",
            "  border-radius: 999px; border: none;",
            "  background: rgba(255,255,255,0.9); color: #2a2118;",
            "  font-size: 1.6rem; line-height: 1; cursor: pointer;",
            "  display: flex; align-items: center; justify-content: center;",
            "}",
            ".zoom-modal__close:hover { background: #fff; }",
            "@media (max-width: 600px) {",
            "  .zoom-modal__image { max-width: 92vw; max-height: 70vh; }",
            "}"
        ].join("\n");
        document.head.appendChild(style);
    }


    /* ----------- Init ----------- */

    function init() {
        setupLanguagePicker();
        setLanguage(detectInitialLang());
        setupActiveNavHighlight();
        setupBackToTop();
        setupImageZoom();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
}());
