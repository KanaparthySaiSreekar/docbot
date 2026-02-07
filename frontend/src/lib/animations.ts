import type { Variants, Transition } from 'framer-motion';

// --- Shared spring configs ---
const snappy: Transition = { type: 'spring', stiffness: 300, damping: 24 };
const bouncy: Transition = { type: 'spring', stiffness: 200, damping: 16 };
const gentle: Transition = { type: 'spring', stiffness: 120, damping: 20 };

// --- Upgraded existing variants ---

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.5 } },
};

export const slideUp: Variants = {
  hidden: { opacity: 0, y: 60, filter: 'blur(8px)' },
  visible: { opacity: 1, y: 0, filter: 'blur(0px)', transition: snappy },
};

export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -80, rotate: -3, filter: 'blur(6px)' },
  visible: { opacity: 1, x: 0, rotate: 0, filter: 'blur(0px)', transition: snappy },
};

export const slideInRight: Variants = {
  hidden: { opacity: 0, x: 80, rotate: 3, filter: 'blur(6px)' },
  visible: { opacity: 1, x: 0, rotate: 0, filter: 'blur(0px)', transition: snappy },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.7, rotate: -2, filter: 'blur(10px)' },
  visible: { opacity: 1, scale: 1, rotate: 0, filter: 'blur(0px)', transition: bouncy },
};

export const rotateIn: Variants = {
  hidden: { opacity: 0, rotate: -6, y: 40, scale: 0.9, filter: 'blur(6px)' },
  visible: { opacity: 1, rotate: 0, y: 0, scale: 1, filter: 'blur(0px)', transition: bouncy },
};

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.2,
    },
  },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 30, filter: 'blur(6px)' },
  visible: { opacity: 1, y: 0, filter: 'blur(0px)', transition: snappy },
};

// --- New variants ---

export const clipReveal: Variants = {
  hidden: { opacity: 0, clipPath: 'inset(20%)' },
  visible: {
    opacity: 1,
    clipPath: 'inset(0%)',
    transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const },
  },
};

export const blurFocus: Variants = {
  hidden: { opacity: 0, filter: 'blur(12px)', y: 10 },
  visible: { opacity: 1, filter: 'blur(0px)', y: 0, transition: gentle },
};

export const parallaxRise: Variants = {
  hidden: { opacity: 0, y: 100 },
  visible: { opacity: 1, y: 0, transition: gentle },
};

export const flipIn: Variants = {
  hidden: { opacity: 0, rotateX: 25, y: 40, scale: 0.92 },
  visible: {
    opacity: 1,
    rotateX: 0,
    y: 0,
    scale: 1,
    transition: bouncy,
  },
};

export const wideStaggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.2,
    },
  },
};

// --- Page transition (unchanged) ---

export const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' as const } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
};
