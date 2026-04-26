/**
 * GSAP motion helpers for CHRONOS.
 *
 * Every helper is a no-op when `prefers-reduced-motion: reduce` is set —
 * we respect accessibility without forcing callers to branch.
 */
import { gsap } from 'gsap';

export const prefersReducedMotion = (): boolean =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** Stagger-fade children of a container in on mount. */
export function staggerFadeIn(
  container: Element | null,
  selector = '> *',
  options: { duration?: number; stagger?: number; y?: number } = {},
): gsap.core.Tween | undefined {
  if (!container || prefersReducedMotion()) return undefined;
  const targets = container.querySelectorAll(selector);
  if (targets.length === 0) return undefined;
  return gsap.fromTo(
    targets,
    { opacity: 0, y: options.y ?? 12 },
    {
      opacity: 1,
      y: 0,
      duration: options.duration ?? 0.4,
      stagger: options.stagger ?? 0.05,
      ease: 'power2.out',
    },
  );
}

/** Count-up number animation. Returns a controller so the caller can .kill(). */
export function countUp(
  el: Element | null,
  to: number,
  options: { duration?: number; precision?: number; suffix?: string } = {},
): { kill: () => void } | undefined {
  if (!el || prefersReducedMotion()) {
    if (el) el.textContent = `${to.toFixed(options.precision ?? 0)}${options.suffix ?? ''}`;
    return undefined;
  }
  const state = { v: 0 };
  const tween = gsap.to(state, {
    v: to,
    duration: options.duration ?? 0.9,
    ease: 'power2.out',
    onUpdate: () => {
      el.textContent = `${state.v.toFixed(options.precision ?? 0)}${options.suffix ?? ''}`;
    },
  });
  return { kill: () => tween.kill() };
}

/** Fill a horizontal bar from 0 to `pct` (0-100) on mount. */
export function fillBar(
  el: Element | null,
  pct: number,
  options: { duration?: number; delay?: number } = {},
): gsap.core.Tween | undefined {
  if (!el) return undefined;
  const target = Math.max(0, Math.min(100, pct));
  if (prefersReducedMotion()) {
    (el as HTMLElement).style.width = `${target}%`;
    return undefined;
  }
  return gsap.fromTo(
    el,
    { width: '0%' },
    {
      width: `${target}%`,
      duration: options.duration ?? 0.8,
      delay: options.delay ?? 0.1,
      ease: 'power2.out',
    },
  );
}

/** Crossfade content in — used for tab panel transitions. */
export function crossfadeIn(
  el: Element | null,
  options: { duration?: number } = {},
): gsap.core.Tween | undefined {
  if (!el || prefersReducedMotion()) return undefined;
  return gsap.fromTo(
    el,
    { opacity: 0, y: 8 },
    { opacity: 1, y: 0, duration: options.duration ?? 0.25, ease: 'power2.out' },
  );
}

/** PlayStation "power-on" hover enlarge — attaches listeners; returns cleanup. */
export function attachPowerOn(el: HTMLElement | null, scale = 1.04): () => void {
  if (!el || prefersReducedMotion()) return () => {};
  const enter = () => {
    gsap.to(el, { scale, duration: 0.18, ease: 'power2.out' });
  };
  const leave = () => {
    gsap.to(el, { scale: 1, duration: 0.2, ease: 'power2.out' });
  };
  el.addEventListener('mouseenter', enter);
  el.addEventListener('mouseleave', leave);
  el.addEventListener('focus', enter);
  el.addEventListener('blur', leave);
  return () => {
    el.removeEventListener('mouseenter', enter);
    el.removeEventListener('mouseleave', leave);
    el.removeEventListener('focus', enter);
    el.removeEventListener('blur', leave);
  };
}
