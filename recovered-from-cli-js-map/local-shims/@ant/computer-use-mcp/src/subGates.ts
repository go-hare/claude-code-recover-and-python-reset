import type { CuSubGates } from "./types.js";

export const ALL_SUB_GATES_OFF: Readonly<CuSubGates> = Object.freeze({
  pixelValidation: false,
  clipboardPasteMultiline: false,
  mouseAnimation: false,
  hideBeforeAction: false,
  autoTargetDisplay: false,
  clipboardGuard: false,
});

export const ALL_SUB_GATES_ON: Readonly<CuSubGates> = Object.freeze({
  pixelValidation: true,
  clipboardPasteMultiline: true,
  mouseAnimation: true,
  hideBeforeAction: true,
  autoTargetDisplay: true,
  clipboardGuard: true,
});
