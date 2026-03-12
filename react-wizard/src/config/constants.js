// ─── Wizard Step Definitions ───────────────────────────────────────────────
// Single source of truth for step metadata — used by Wizard.jsx for the step
// indicator nav. Update here to add/remove/rename steps app-wide.
export const WIZARD_STEPS = [
  { id: 1, name: 'Product',       icon: 'Package' },
  { id: 2, name: 'Curate',        icon: 'Database' },
  { id: 3, name: 'Research',      icon: 'Brain' },
  { id: 4, name: 'Strategy',      icon: 'Target' },
  { id: 5, name: 'Pattern',       icon: 'Layout' },
  { id: 6, name: 'Script',        icon: 'FileText' },
  { id: 7, name: 'Avatar',        icon: 'User' },
  { id: 8, name: 'Storyboard',    icon: 'Video' },
  { id: 9, name: 'Video Preview', icon: 'Sparkles' },
];

// ─── Auth ──────────────────────────────────────────────────────────────────
export const TOKEN_KEY  = 'spectra_token';
export const USER_KEY   = 'spectra_user';

// ─── Validation Rules (mirror backend rules in api/routes/auth.py) ─────────
export const USERNAME_REGEX    = /^[a-zA-Z0-9_]{3,30}$/;
export const MIN_PASSWORD_LEN  = 6;
export const MAX_PASSWORD_LEN  = 128;
