import type { SurfaceKind, SurfaceStyle } from "./types";

export interface SurfacePaint {
  backgroundImage: string;
  backgroundPosition?: string;
  backgroundSize?: string;
}

function px(value: number): string {
  return `${Number(Math.max(0.1, value).toFixed(2))}px`;
}

function repeatingLine(angle: number, color: string, weight: number, scale: number): string {
  return `repeating-linear-gradient(${angle}deg, ${color} 0 ${px(weight)}, transparent ${px(weight)} ${px(scale)})`;
}

export function surfacePaint(
  kind: SurfaceKind,
  color: string,
  scaleValue: number,
  weightValue: number,
  angle: number,
): SurfacePaint {
  const scale = Math.max(4, scaleValue);
  const weight = Math.min(Math.max(0.1, weightValue), scale / 2);
  const grain = Math.max(1, weight);

  switch (kind) {
    case "paper-grain":
      return {
        backgroundImage: [
          `radial-gradient(circle at 18% 23%, ${color} 0 ${px(grain)}, transparent ${px(grain)})`,
          `radial-gradient(circle at 73% 61%, ${color} 0 ${px(grain * 0.72)}, transparent ${px(grain * 0.72)})`,
          `radial-gradient(circle at 41% 82%, ${color} 0 ${px(grain * 0.55)}, transparent ${px(grain * 0.55)})`,
        ].join(", "),
        backgroundSize: [
          `${px(scale)} ${px(scale * 0.88)}`,
          `${px(scale * 0.73)} ${px(scale * 0.69)}`,
          `${px(scale * 1.17)} ${px(scale * 0.91)}`,
        ].join(", "),
      };
    case "paper-fibers":
      return {
        backgroundImage: [
          repeatingLine(angle + 7, color, weight, scale),
          repeatingLine(angle + 83, color, weight * 0.62, scale * 1.7),
          repeatingLine(angle - 31, color, weight * 0.38, scale * 2.3),
        ].join(", "),
      };
    case "flecked-paper":
      return {
        backgroundImage: [
          `radial-gradient(ellipse at 22% 18%, ${color} 0 ${px(grain * 1.8)}, transparent ${px(grain * 2)})`,
          `radial-gradient(ellipse at 81% 67%, ${color} 0 ${px(grain * 1.25)}, transparent ${px(grain * 1.5)})`,
          `radial-gradient(ellipse at 47% 91%, ${color} 0 ${px(grain * 0.8)}, transparent ${px(grain)})`,
        ].join(", "),
        backgroundSize: [
          `${px(scale * 1.3)} ${px(scale)}`,
          `${px(scale * 0.8)} ${px(scale * 1.6)}`,
          `${px(scale * 1.9)} ${px(scale * 1.2)}`,
        ].join(", "),
      };
    case "dry-brush":
      return {
        backgroundImage: [
          `repeating-linear-gradient(${angle}deg, transparent 0 ${px(scale * 0.18)}, ${color} ${px(scale * 0.18)} ${px(scale * 0.18 + weight * 2.4)}, transparent ${px(scale * 0.18 + weight * 2.4)} ${px(scale)})`,
          `repeating-linear-gradient(${angle + 2}deg, transparent 0 ${px(scale * 0.54)}, ${color} ${px(scale * 0.54)} ${px(scale * 0.54 + weight)}, transparent ${px(scale * 0.54 + weight)} ${px(scale * 1.35)})`,
        ].join(", "),
      };
    case "linear-rhythm":
      return { backgroundImage: repeatingLine(angle, color, weight, scale) };
    case "scanlines":
      return { backgroundImage: repeatingLine(0, color, weight, Math.max(4, scale * 0.35)) };
    case "diagonal-hatch":
      return { backgroundImage: repeatingLine(angle || 45, color, weight, scale) };
    case "crosshatch":
      return {
        backgroundImage: [
          repeatingLine(angle || 45, color, weight, scale),
          repeatingLine((angle || 45) + 90, color, weight, scale),
        ].join(", "),
      };
    case "woven":
      return {
        backgroundImage: [
          repeatingLine(0, color, weight * 1.6, scale),
          repeatingLine(90, color, weight * 1.6, scale),
          repeatingLine(0, color, weight * 0.5, scale / 2),
          repeatingLine(90, color, weight * 0.5, scale / 2),
        ].join(", "),
      };
    case "technical-grid":
      return {
        backgroundImage: [
          repeatingLine(0, color, weight, scale),
          repeatingLine(90, color, weight, scale),
        ].join(", "),
      };
    case "micro-grid":
      return {
        backgroundImage: [
          repeatingLine(0, color, weight, scale / 4),
          repeatingLine(90, color, weight, scale / 4),
          repeatingLine(0, color, weight * 1.8, scale),
          repeatingLine(90, color, weight * 1.8, scale),
        ].join(", "),
      };
    case "isometric-grid":
      return {
        backgroundImage: [
          repeatingLine(30, color, weight, scale),
          repeatingLine(90, color, weight, scale),
          repeatingLine(150, color, weight, scale),
        ].join(", "),
      };
    case "point-field":
      return {
        backgroundImage: `radial-gradient(circle, ${color} 0 ${px(weight)}, transparent ${px(weight)})`,
        backgroundSize: `${px(scale)} ${px(scale)}`,
      };
    case "halftone":
      return {
        backgroundImage: [
          `radial-gradient(circle, ${color} 0 ${px(weight * 1.8)}, transparent ${px(weight * 1.9)})`,
          `radial-gradient(circle, ${color} 0 ${px(weight)}, transparent ${px(weight * 1.1)})`,
        ].join(", "),
        backgroundPosition: `0 0, ${px(scale / 2)} ${px(scale / 2)}`,
        backgroundSize: `${px(scale)} ${px(scale)}, ${px(scale)} ${px(scale)}`,
      };
    case "checkerboard":
      return {
        backgroundImage: [
          `linear-gradient(${45 + angle}deg, ${color} 25%, transparent 25% 75%, ${color} 75%)`,
          `linear-gradient(${-45 + angle}deg, ${color} 25%, transparent 25% 75%, ${color} 75%)`,
        ].join(", "),
        backgroundSize: `${px(scale)} ${px(scale)}`,
      };
    case "concentric-rings":
      return {
        backgroundImage: `repeating-radial-gradient(circle at 50% 50%, transparent 0 ${px(Math.max(0, scale - weight))}, ${color} ${px(Math.max(0, scale - weight))} ${px(scale)})`,
      };
    case "topographic":
      return {
        backgroundImage: [
          `repeating-radial-gradient(ellipse at 18% 38%, transparent 0 ${px(scale - weight)}, ${color} ${px(scale - weight)} ${px(scale)})`,
          `repeating-radial-gradient(ellipse at 82% 67%, transparent 0 ${px(scale * 1.35 - weight)}, ${color} ${px(scale * 1.35 - weight)} ${px(scale * 1.35)})`,
        ].join(", "),
        backgroundSize: `130% 115%, 170% 150%`,
      };
    case "sunburst": {
      return {
        backgroundImage: [0, 30, 60, 90, 120, 150]
          .map((offset) => repeatingLine(angle + offset, color, weight, scale))
          .join(", "),
      };
    }
    case "waves":
      return {
        backgroundImage: [
          `repeating-radial-gradient(ellipse at 0 50%, transparent 0 ${px(scale - weight)}, ${color} ${px(scale - weight)} ${px(scale)})`,
          `repeating-radial-gradient(ellipse at 100% 50%, transparent 0 ${px(scale * 1.5 - weight)}, ${color} ${px(scale * 1.5 - weight)} ${px(scale * 1.5)})`,
        ].join(", "),
        backgroundSize: `50% 100%, 50% 100%`,
        backgroundPosition: `left center, right center`,
      };
    case "terrazzo":
      return {
        backgroundImage: [
          `linear-gradient(${angle}deg, transparent 42%, ${color} 42% 58%, transparent 58%)`,
          `linear-gradient(${angle + 117}deg, transparent 38%, ${color} 38% 54%, transparent 54%)`,
          `radial-gradient(ellipse at 48% 87%, ${color} 0 ${px(weight * 1.4)}, transparent ${px(weight * 1.6)})`,
        ].join(", "),
        backgroundSize: [
          `${px(scale * 1.3)} ${px(scale)}`,
          `${px(scale)} ${px(scale * 1.45)}`,
          `${px(scale * 0.75)} ${px(scale * 0.9)}`,
        ].join(", "),
      };
  }
}

export function paintForSurface(surface: SurfaceStyle, color: string): SurfacePaint {
  return surfacePaint(surface.kind, color, surface.scalePx, surface.weightPx, surface.angleDeg);
}
