# Clinical Design System - Aarozi Healthcare

**Author**: Senior Nuxt/Vue UI/UX Engineer & LIS Domain Specialist  
**Design Philosophy**: Clinical clarity, dense information architecture, zero decorative distraction, high contrast, keyboard-first workstation efficiency.

---

## 1. Visual Foundation & Color Palette

The Aarozi Healthcare interface utilizes a restrained, clinical palette that prioritizes data readability and minimizes eye fatigue during long laboratory shifts.

### A. Core Neutral Surfaces
- **App Canvas (Light)**: `#F8FAFC` (`bg-slate-50`)
- **Card / Surface (Light)**: `#FFFFFF` (`bg-white`)
- **Subtle Surface / Table Alt**: `#F1F5F9` (`bg-slate-100`)
- **Border Neutral**: `#E2E8F0` (`border-slate-200`)
- **Dividers & Sub-borders**: `#CBD5E1` (`border-slate-300`)
- **Canvas (Dark)**: `#0B0F17` (`dark:bg-slate-950`)
- **Card / Surface (Dark)**: `#1E293B` (`dark:bg-slate-800`)

### B. Brand & Action Colors
- **Primary Navy**: `#0F172A` (`slate-900` / `navy`) - Primary navigation, institutional branding, headers.
- **Medical Teal Accent**: `#0D9488` (`teal-600` / `#14B8A6` `teal-500`) - Interactive focal points, active tabs, primary action buttons, verified checkmarks.
- **Teal Light Background**: `#F0FDFA` (`teal-50`) - Selection highlights, active table row backgrounds.

### C. Clinical Status & Alert Semantics
- **Normal / Approved / Paid**:
  - Text: `#065F46` (`emerald-800`), Background: `#D1FAE5` (`emerald-100`), Border: `#A7F3D0` (`emerald-200`)
- **Low Flag (`L`) / Info / Draft**:
  - Text: `#1E40AF` (`blue-800`), Background: `#DBEAFE` (`blue-100`), Border: `#BFDBFE` (`blue-200`)
- **High Flag (`H`) / Warning / Pending**:
  - Text: `#92400E` (`amber-800`), Background: `#FEF3C7` (`amber-100`), Border: `#FDE68A` (`amber-200`)
- **Critical Panic Value (`LL` / `HH`) / Cancelled / Rejected**:
  - Text: `#991B1B` (`red-800`), Background: `#FEE2E2` (`red-100`), Border: `#FECACA` (`red-200`), Pulse: `animate-pulse`
- **Quarantined / Specimen Issue**:
  - Text: `#6B21A8` (`purple-800`), Background: `#F3E8FF` (`purple-100`), Border: `#E9D5FF` (`purple-200`)

---

## 2. Typography & Numerical Formatting

- **Font Family**: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif.
- **Tabular Clinical Figures**: Laboratory numeric results, patient UHIDs, accession barcodes, and invoice amounts MUST use monospace/tabular figures (`font-mono tabular-nums`) to ensure strict vertical alignment across columns.

| Scale | Tailwind Class | Size / Line-Height | Weight | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **H1** | `text-2xl font-bold` | 24px / 32px | 700 | Main operational page headers |
| **H2** | `text-lg font-semibold` | 18px / 28px | 600 | Card sections, modal titles, drawer headers |
| **H3** | `text-base font-medium` | 16px / 24px | 500 | Table group headers, form fieldsets |
| **Body** | `text-sm font-normal` | 14px / 20px | 400 | Standard labels, table cells, paragraph text |
| **Body Bold** | `text-sm font-semibold` | 14px / 20px | 600 | Patient names, key clinical metrics |
| **Caption** | `text-xs font-normal` | 12px / 16px | 400 | Helper text, timestamps, reference ranges |
| **Badge / Tag** | `text-xs font-semibold` | 11px / 14px | 600 | Status indicators, result flags (`L`, `H`, `CRIT`) |

---

## 3. Atomic Components & UI Primitives

### A. Buttons (`Button.vue`)
- **Variants**:
  - `primary`: Background `bg-teal-600 hover:bg-teal-700 text-white font-medium shadow-sm transition`
  - `secondary`: Background `bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium`
  - `danger`: Background `bg-red-600 hover:bg-red-700 text-white font-medium shadow-sm`
  - `ghost`: Transparent with `hover:bg-slate-100 text-slate-600`
- **Sizes**: `sm` (px-2.5 py-1 text-xs), `md` (px-3.5 py-2 text-sm), `lg` (px-4 py-2.5 text-base).
- **State Handling**: Disabled button displays `opacity-50 cursor-not-allowed`, loading button displays inline spinning SVG.

### B. Form Inputs (`Input.vue`, `Select.vue`, `Checkbox.vue`)
- **Styling**: `border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 bg-white text-slate-900 transition`.
- **Validation**:
  - Valid: standard border.
  - Invalid: `border-red-500 focus:ring-red-400 focus:border-red-500`, accompanied by `<p class="mt-1 text-xs text-red-600">Error message</p>`.
- **Labels**: Explicit `<label>` elements linked with `id`/`for` attributes, with required indicators (`<span class="text-red-500">*</span>`).

### C. Data Tables (`DataTable.vue`)
- **Density**: Compact table rows with `py-2.5 px-3` padding.
- **Header**: Sticky header (`sticky top-0 bg-slate-100 text-slate-600 font-semibold text-xs uppercase tracking-wider`).
- **Row Hover & Selection**: `hover:bg-slate-50 cursor-pointer`, selected rows highlighted with `bg-teal-50/60`.
- **Pagination & Sorting**: Integrated pagination controls (`Showing 1 to 50 of 1,280 results`) with sorting arrows on sortable columns.

### D. Status Badges (`Badge.vue`)
- Compact badges with rounded pill format (`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium`).
- Pre-bound to domain statuses: `draft`, `collected`, `received`, `verified`, `released`, `paid`, `cancelled`, `quarantine`.

### E. Modals, Drawers & Confirmation Dialogs
- Backdrop with smooth fade `bg-slate-900/50 backdrop-blur-sm`.
- Centered modal container with responsive width bounds (`max-w-lg`, `max-w-2xl`, `max-w-4xl`).
- High-priority confirmation dialogs for critical clinical actions (e.g., patient merge, result amendment, specimen rejection, blood unit discard).

### F. Toasts & Alert Banners (`ToastProvider.vue`)
- Floating toasts in top-right viewport: Success, Error, Warning, Info.
- Auto-dismiss after 4 seconds with manual close button.
- Global offline banner: Persistent yellow/amber banner when connection to local LAN server is lost.

---

## 4. Keyboard Navigation & Laboratory Workstation Shortcuts

In clinical laboratory environments, switching between mouse and keyboard causes significant throughput bottlenecks. The design system mandates global and module-level keyboard bindings:

| Key Combination | Scope | Action |
| :--- | :--- | :--- |
| `Ctrl + K` / `Cmd + K` | Global | Focus global patient / accession search |
| `F2` | Global | Quick-open New Patient Registration modal |
| `F3` | Global | Quick-open New Diagnostic Order modal |
| `F4` | Pathology Workstation | Focus accession barcode scanner input |
| `Enter` / `Down Arrow` | Result Entry Grid | Move focus to next test parameter result cell |
| `Up Arrow` | Result Entry Grid | Move focus to previous test parameter result cell |
| `Ctrl + S` | Result Entry / Billing | Save draft results / Save invoice |
| `Ctrl + Enter` | Result Entry | Submit results for Pathologist Verification |
| `Escape` | Global | Close active modal, drawer, or search dropdown |

---

## 5. Responsive Breakpoints & Multi-Device Strategy

1. **Desktop Workstation (`>= 1280px` / `xl`)**:
   - Primary operational environment for Pathology Workstations, Accessioning Desks, and Billing Counters.
   - Fixed full-height layout with collapsible sidebar and dual-pane master-detail views.
2. **Tablet (`768px - 1024px` / `md` to `lg`)**:
   - Phlebotomy mobile trays, ward sample collection, blood donor screening stations.
   - Collapsed sidebar (icon-only or drawer), touch-friendly targets (`min-h-[44px]`).
3. **Mobile (`< 768px`)**:
   - Doctor report viewing, patient self-service portal, administrative overview.
   - Single-column stacked layouts, bottom sheets for filters and actions.
