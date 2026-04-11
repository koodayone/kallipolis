export type SchoolConfig = {
  name: string;
  logoPath: string;      // compact logo for nav/header use
  brandColor: string;
  brandColorLight: string; // readable accent on dark backgrounds
  brandColorDim: string;   // subtle tint for badge backgrounds on light surfaces
  brandColorDark: string;  // card/surface color in dark mode UI
  brandColorNeon: string;  // high-saturation accent for map markers on dark backgrounds
};

// --- Color derivation utilities ---

function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h = 0;
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / d + 2) / 6;
  else h = ((r - g) / d + 4) / 6;
  return [h * 360, s * 100, l * 100];
}

function hslToHex(h: number, s: number, l: number): string {
  const hNorm = h / 360, sNorm = s / 100, lNorm = l / 100;
  const hue2rgb = (p: number, q: number, t: number) => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  if (sNorm === 0) {
    const v = Math.round(lNorm * 255);
    return `#${v.toString(16).padStart(2, "0").repeat(3)}`;
  }
  const q = lNorm < 0.5 ? lNorm * (1 + sNorm) : lNorm + sNorm - lNorm * sNorm;
  const p = 2 * lNorm - q;
  const r = Math.round(hue2rgb(p, q, hNorm + 1 / 3) * 255);
  const g = Math.round(hue2rgb(p, q, hNorm) * 255);
  const b = Math.round(hue2rgb(p, q, hNorm - 1 / 3) * 255);
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

export function deriveSchoolPalette(brandColor: string): Pick<SchoolConfig, "brandColor" | "brandColorLight" | "brandColorDim" | "brandColorDark" | "brandColorNeon"> {
  const [h, s, l] = hexToHsl(brandColor);

  // Edge case: near-neutral (grey) — no meaningful hue, fall back to slate
  const isNeutral = s < 12;

  // brandColorDark — card surface in dark mode
  // Preserve hue, push to very dark (L~12%), reduce saturation
  const darkL = 12;
  const darkS = isNeutral ? 8 : Math.min(s * 0.55, 30);
  const brandColorDark = hslToHex(h, darkS, darkL);

  // brandColorLight — text/accent on dark backgrounds
  // If brand color is already light (L > 55%), use it near as-is; otherwise push to ~68%
  const lightL = l > 55 ? Math.min(l + 10, 88) : 68;
  const lightS = isNeutral ? 15 : Math.min(s * 0.85, 70);
  const brandColorLight = hslToHex(h, lightS, lightL);

  // brandColorDim — badge/tint background on light surfaces
  // Very light wash: L~95%, low saturation
  const dimS = isNeutral ? 5 : Math.min(s * 0.5, 25);
  const brandColorDim = hslToHex(h, dimS, 95);

  // brandColorNeon — high-saturation accent for map markers on dark backgrounds
  // Preserve hue, push saturation high, adjust lightness by perceptual hue band
  // Shift hues near the background (H~223) away to avoid blending with #060d1f
  let brandColorNeon: string;
  if (isNeutral) {
    brandColorNeon = "#c9a84c";
  } else {
    // Hue-shift blues near background hue (223°) toward cyan/sky blue
    const BG_HUE = 223;
    const SHIFT_RANGE = 20;
    let neonH = h;
    const hueDist = Math.abs(h - BG_HUE);
    if (hueDist < SHIFT_RANGE) {
      // Push away from BG_HUE — toward cyan (lower hue values)
      neonH = BG_HUE - SHIFT_RANGE - (SHIFT_RANGE - hueDist);
    }

    const neonS = Math.max(85, s);
    let neonL: number;
    if (neonH >= 50 && neonH <= 170) {
      neonL = 55; // yellows/greens — perceptually bright, keep L lower
    } else if (neonH < 50 || neonH > 330) {
      neonL = 60; // reds/oranges
    } else {
      neonL = 65; // blues/purples — perceptually dark, push L higher
    }
    brandColorNeon = hslToHex(neonH, neonS, neonL);
  }

  return { brandColor, brandColorLight, brandColorDim, brandColorDark, brandColorNeon };
}

// --- School config ---

export function makeSchoolConfig(
  name: string,
  logoPath: string,
  brandColorHex: string,
): SchoolConfig {
  return { name, logoPath, ...deriveSchoolPalette(brandColorHex) };
}

export const schoolConfig: SchoolConfig = makeSchoolConfig(
  "Foothill College",
  "/logos/foothill.png",
  "#7B2D3E"
);
