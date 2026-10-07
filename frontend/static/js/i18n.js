/**
 * SafeHaul Kerala — i18n helper
 *
 * Loads a language JSON file (en.json or ml.json) and exposes:
 *   t(key)           → translated string, or the key itself if missing
 *   I18n.setLang(lc) → load a new language and re-render all data-i18n elements
 *
 * Usage in HTML:  <span data-i18n="header.title"></span>
 * Usage in JS:    t('header.title')
 *
 * Language files live in /static/i18n/<lc>.json
 * The active language is stored in localStorage key 'safehaul_lang'.
 */

const I18n = (() => {
  let _strings = {};
  let _lang = localStorage.getItem('safehaul_lang') || 'en';

  /** Resolve a dot-separated key from the strings object. */
  function _resolve(key) {
    return key.split('.').reduce((obj, k) => (obj && obj[k] !== undefined ? obj[k] : null), _strings);
  }

  /** Re-render every element carrying a data-i18n attribute. */
  function _applyToDOM() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const val = _resolve(key);
      if (val !== null) el.textContent = val;
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const val = _resolve(key);
      if (val !== null) el.setAttribute('placeholder', val);
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const val = _resolve(key);
      if (val !== null) el.setAttribute('title', val);
    });
  }

  /** Load language file and apply to DOM. Returns a Promise. */
  function _load(lc) {
    return fetch(`/static/i18n/${lc}.json`)
      .then(r => {
        if (!r.ok) throw new Error(`i18n: could not load ${lc}.json`);
        return r.json();
      })
      .then(data => {
        _strings = data;
        _lang = lc;
        localStorage.setItem('safehaul_lang', lc);
        document.documentElement.lang = lc;
        _applyToDOM();
      })
      .catch(err => {
        console.error(err);
        // If Malayalam fails, fall back to English silently.
        if (lc !== 'en') return _load('en');
      });
  }

  return {
    /** Initialise: load the stored/default language. Call once on DOMContentLoaded. */
    init() {
      return _load(_lang);
    },

    /** Switch language. lc = 'en' | 'ml' */
    setLang(lc) {
      return _load(lc);
    },

    /** Returns the current language code. */
    getLang() {
      return _lang;
    },

    /** Translate a key. Falls back to the key string if not found. */
    t(key) {
      const val = _resolve(key);
      return val !== null ? val : key;
    },
  };
})();

/** Shorthand global for use in templates and other JS modules. */
function t(key) {
  return I18n.t(key);
}
