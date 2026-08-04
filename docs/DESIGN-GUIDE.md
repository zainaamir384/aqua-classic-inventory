# Design System Guide
# Aqua Classic Water Filters — Pitch Black Dual-Theme UI

> **Theme Version:** 3.0 (v0 Pitch Black Dark Theme & Clean Light Theme)

---

## Design Token Specs

### Pitch-Black Dark Palette (`html[data-theme="dark"]`)
- **Background Base:** `#070a12` (Pitch Black)
- **Glass Surface:** `#0d1527` (Deep Dark Slate)
- **Header Surface:** `#090d16`
- **Glass Card Border:** `rgba(255, 255, 255, 0.09)`
- **Accent Cyan:** `#38bdf8` (Highlights & active tabs)
- **Accent Emerald:** `#10b981` (Profit & Good stock status)
- **Accent Amber:** `#f59e0b` (Warning status)
- **Accent Rose:** `#f43f5e` (Critical stock alerts)

### Clean Light Palette (`html[data-theme="light"]`)
- **Background Base:** `#f8fafc` (Light Slate Base)
- **Surface:** `#ffffff` (Pure White Cards)
- **Header Surface:** `#f1f5f9`
- **Border:** `#e2e8f0`
- **Accent Primary:** `#0284c7` (Primary Blue)

### Component Specifications
1. **Liquid Glass Buttons:** `background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%); backdrop-filter: blur(8px); transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);`
2. **Page Load Transitions:** `slideFadeIn` keyframe animation (`0% { opacity: 0; transform: translateY(8px); }`).
3. **Fit-Tight Tables:** Compact padding (`0.55rem 0.65rem`) with `+ Stock`, `- Deduct`, `Edit`, `Delete` buttons.
4. **Toast Notifications:** Pinned top-right floating stack (`top: 80px`, `right: 1.5rem`) with 18px locked SVG icons.
