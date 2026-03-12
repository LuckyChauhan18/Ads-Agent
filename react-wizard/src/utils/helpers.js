/**
 * Classname merge utility – combines class strings, filtering out falsy values.
 * Lightweight alternative to clsx/classnames.
 */
export function cn(...inputs) {
  return inputs.filter(Boolean).join(' ');
}
