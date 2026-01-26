# Implementation Plan: Midnight AI Glass UI Theme

**Branch**: `011-midnight-glass-ui` | **Date**: 2026-01-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-midnight-glass-ui/spec.md`

## Summary

Transform the Todo App frontend to a premium, portfolio-grade design using a **Midnight AI Glass** theme. This is a UI-only enhancement that applies glassmorphism effects, a new dark color palette, and polished visual feedback to task cards, forms, chat interface, and filter controls. No backend modifications required.

## Technical Context

**Language/Version**: TypeScript 5.6.3, React 18.3.1
**Primary Dependencies**: Next.js 14.2.21, Tailwind CSS 3.4.17, SWR 2.2.5
**Storage**: N/A (frontend-only, no data layer changes)
**Testing**: Manual visual testing, browser dev tools
**Target Platform**: Modern browsers (Chrome 80+, Firefox 75+, Safari 14+, Edge 80+)
**Project Type**: Web application (frontend)
**Performance Goals**: 60fps animations, <250ms transition feedback
**Constraints**: No backend changes, WCAG AA contrast (4.5:1), responsive 375px-1920px
**Scale/Scope**: ~15 files modified, ~500 lines of CSS/component changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | ✅ PASS | Specification approved before planning |
| II. Stateless Backend | ✅ N/A | UI-only feature, no backend changes |
| III. Clear Responsibility Boundaries | ✅ PASS | UI layer only, no cross-layer violations |
| IV. AI Safety Through Tools | ✅ N/A | No AI/MCP changes |
| V. Simplicity Over Cleverness | ✅ PASS | Using native CSS features, no complex libraries |
| VI. Deterministic Behavior | ✅ PASS | CSS-only changes, predictable rendering |

**Technical Constraints Check**:
| Constraint | Status |
|------------|--------|
| Frontend Chat UI: OpenAI ChatKit | ✅ Compatible (styling only) |
| No implementation before spec | ✅ Spec completed |
| No hardcoded secrets | ✅ N/A |

## Project Structure

### Documentation (this feature)

```text
specs/011-midnight-glass-ui/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research findings
├── data-model.md        # Data entities (UI-only, no DB changes)
├── quickstart.md        # Developer quickstart guide
├── contracts/           # API contracts (no changes)
│   └── README.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (from /sp.tasks)
```

### Source Code (repository root)

```text
frontend/
├── app/
│   ├── globals.css          # [MODIFY] CSS variables, glass utilities
│   ├── layout.tsx           # [MODIFY] Force dark mode class
│   ├── page.tsx             # [MODIFY] Landing page styling
│   ├── tasks/
│   │   └── page.tsx         # [MODIFY] Task list glass cards
│   └── chat/
│       └── page.tsx         # [MODIFY] Chat page styling
├── components/
│   ├── ui/
│   │   ├── Button.tsx       # [MODIFY] Button variants
│   │   ├── Card.tsx         # [MODIFY] Add glass variant
│   │   ├── Toast.tsx        # [MODIFY] Toast styling
│   │   └── Skeleton.tsx     # [MODIFY] Skeleton colors
│   ├── layout/
│   │   └── Header.tsx       # [MODIFY] Header glass styling
│   ├── tasks/
│   │   ├── FilterPanel.tsx  # [MODIFY] Glass dropdowns
│   │   ├── SortControls.tsx # [MODIFY] Glass controls
│   │   ├── TagInput.tsx     # [MODIFY] Tag chip styling
│   │   ├── DateTimePicker.tsx # [MODIFY] Input styling
│   │   ├── RecurrenceSelector.tsx # [MODIFY] Selector styling
│   │   └── ReminderList.tsx # [MODIFY] List styling
│   └── chat/
│       └── ChatContainer.tsx # [MODIFY] Glass panel, bubbles, typing
├── tailwind.config.ts       # [MODIFY] Color tokens, shadows, keyframes
└── contexts/
    └── ThemeContext.tsx     # [MODIFY] Force dark mode default
```

**Structure Decision**: Web application with frontend-only changes. All modifications are in the `frontend/` directory. No backend (`backend/`) changes required per FR-009.

## Complexity Tracking

No constitution violations. All changes follow established patterns:
- Tailwind utility classes (existing pattern)
- Component variant props (existing Card pattern)
- CSS custom properties (existing globals.css pattern)

---

## Implementation Phases

### Phase 1: Design System Foundation

**Objective**: Establish the Midnight AI Glass design tokens and utilities

#### 1.1 Update Tailwind Configuration

**File**: `frontend/tailwind.config.ts`

**Changes**:
1. Replace `dark` color palette with Midnight colors:
   - `dark-900`: `#0B0F1A` (background)
   - `dark-800`: `#12182B` (surface)
   - `dark-700`: `#1A2235` (elevated surface)
   - `dark-600`: `#232D42` (borders/inputs)

2. Update `primary` colors for accent gradient:
   - `primary-400`: `#5B8CFF` (gradient start)
   - `primary-500`: `#7B6CF6` (midpoint)
   - `primary-600`: `#8B5CF6` (gradient end)

3. Update semantic colors:
   - `success-500`: `#22C55E`
   - `warning-500`: `#FACC15`
   - `error-500`: `#EF4444`

4. Add custom shadows for glass effects:
   - `glow-accent`: Accent color glow
   - `glass`: Subtle border glow

5. Add keyframes for typing indicator:
   - `typing-bounce`: Bouncing dots animation

**Acceptance**: Tailwind config compiles without errors, colors available in utilities

#### 1.2 Update Global CSS

**File**: `frontend/app/globals.css`

**Changes**:
1. Update CSS variables for dark mode:
   - `--background`: Match `#0B0F1A`
   - `--card`: Match `#12182B`
   - `--foreground`: Match `#E5E7EB`

2. Add glass effect utilities:
   ```css
   .glass { /* Semi-transparent with blur */ }
   .glass-subtle { /* Less prominent glass */ }
   .input-glass { /* Form input glass styling */ }
   ```

3. Add typing indicator animation:
   ```css
   .typing-dot { /* Bouncing dot animation */ }
   ```

4. Update scrollbar colors for dark theme

5. Add gradient text utility for accent colors

**Acceptance**: CSS utilities apply correctly, no console errors

#### 1.3 Force Dark Mode

**File**: `frontend/app/layout.tsx`

**Changes**:
1. Add `dark` class to `<html>` element by default
2. Remove or disable light mode option in ThemeContext

**File**: `frontend/contexts/ThemeContext.tsx`

**Changes**:
1. Set default theme to `'dark'`
2. Always apply `dark` class regardless of preference

**Acceptance**: App loads in dark mode, no flash of light mode

---

### Phase 2: Core UI Components

**Objective**: Update base components with glass styling

#### 2.1 Card Component - Glass Variant

**File**: `frontend/components/ui/Card.tsx`

**Changes**:
1. Add `glass` variant to Card component:
   ```typescript
   variant: 'default' | 'bordered' | 'elevated' | 'glass'
   ```
2. Glass variant applies:
   - Semi-transparent background
   - Backdrop blur
   - Subtle border with accent tint
   - Soft shadow

3. Add `hover` prop for lift + glow effect

**Acceptance**: `<Card variant="glass">` renders with glass effect

#### 2.2 Button Component

**File**: `frontend/components/ui/Button.tsx`

**Changes**:
1. Update `primary` variant to use accent gradient
2. Update focus ring to use accent color
3. Ensure all variants have consistent dark theme styling
4. Add subtle glow on hover for primary buttons

**Acceptance**: Buttons match Midnight theme, gradient visible on primary

#### 2.3 Toast Component

**File**: `frontend/components/ui/Toast.tsx`

**Changes**:
1. Apply glass effect to toast container
2. Update success/error/info colors to Midnight palette
3. Ensure sufficient contrast for readability

**Acceptance**: Toasts render with glass effect, text readable

#### 2.4 Skeleton Component

**File**: `frontend/components/ui/Skeleton.tsx`

**Changes**:
1. Update skeleton background to Midnight surface color
2. Update pulse animation colors

**Acceptance**: Skeletons blend with glass UI during loading

---

### Phase 3: Task List UI

**Objective**: Transform task items into glass cards with full metadata display

#### 3.1 Task Page - Glass Cards

**File**: `frontend/app/tasks/page.tsx`

**Changes**:
1. Wrap each task item in `<Card variant="glass" hover>`
2. Display all metadata prominently:
   - Title (primary text)
   - Description preview (secondary text, truncated)
   - Priority badge (color-coded)
   - Tags as chips (accent gradient)
   - Due date (color-coded: overdue=red, today=warning, upcoming=default)
   - Reminder indicator (bell icon + count)
   - Recurrence label (text)
3. Completion checkbox with accent styling
4. Hover effect: translateY(-2px) + glow shadow

**Acceptance**: Task cards float with glass effect, all metadata visible

#### 3.2 Priority Badge Component

**File**: `frontend/app/tasks/page.tsx` (inline or extract)

**Changes**:
1. Create styled priority badge:
   - High: `#EF4444` background, white text
   - Medium: `#FACC15` background, dark text
   - Low: `#22C55E` background, white text
2. Rounded pill shape, consistent sizing

**Acceptance**: Priority immediately distinguishable by color

#### 3.3 Tag Chips

**File**: `frontend/components/tasks/TagInput.tsx`

**Changes**:
1. Update chip styling with accent gradient background
2. White text for contrast
3. Rounded pill shape
4. X button for removal in forms

**Acceptance**: Tags render as gradient chips

#### 3.4 Due Date Display

**File**: `frontend/app/tasks/page.tsx`

**Changes**:
1. Color-code due date text:
   - Overdue: Error red with "Overdue" prefix
   - Due today: Warning yellow
   - Due this week: Default text
   - Future: Secondary text
2. Format-friendly display (e.g., "Due in 3 days")

**Acceptance**: Due date urgency clear at a glance

#### 3.5 Reminder & Recurrence Indicators

**File**: `frontend/app/tasks/page.tsx`

**Changes**:
1. Add reminder indicator:
   - Bell icon when reminders exist
   - Count badge if multiple
   - Tooltip: "N reminders scheduled"
2. Add recurrence label:
   - Small text: "Recurring: daily/weekly/custom"
   - Icon indicator

**Acceptance**: Reminder/recurrence status visible on cards

---

### Phase 4: Task Forms

**Objective**: Apply glass styling to task creation/editing forms

#### 4.1 Form Container

**File**: `frontend/app/tasks/page.tsx`

**Changes**:
1. Wrap form in glass panel
2. Consistent spacing and layout

**Acceptance**: Form has glass panel appearance

#### 4.2 Input Fields

**Files**:
- `frontend/app/tasks/page.tsx`
- `frontend/components/tasks/DateTimePicker.tsx`
- `frontend/components/tasks/TagInput.tsx`
- `frontend/components/tasks/RecurrenceSelector.tsx`
- `frontend/components/tasks/ReminderList.tsx`

**Changes**:
1. Apply `input-glass` utility to all inputs
2. Focus state: accent glow ring
3. Placeholder text in secondary color
4. Consistent dark backgrounds

**Acceptance**: All form inputs styled consistently with glass effect

#### 4.3 Priority Selector

**File**: `frontend/app/tasks/page.tsx`

**Changes**:
1. Update button group styling
2. Selected state: accent gradient background
3. Unselected state: surface glass background
4. Smooth transition between states

**Acceptance**: Priority selection visually distinct

---

### Phase 5: Filter & Sort Controls

**Objective**: Apply glass styling to filter panel and sort controls

#### 5.1 Filter Panel

**File**: `frontend/components/tasks/FilterPanel.tsx`

**Changes**:
1. Glass panel background
2. Radio buttons / checkboxes with accent color
3. Dropdown selects with glass styling
4. Active filter badge with accent gradient

**Acceptance**: Filters integrated with glass theme

#### 5.2 Sort Controls

**File**: `frontend/components/tasks/SortControls.tsx`

**Changes**:
1. Dropdown with glass styling
2. Toggle button with accent highlight on active
3. Consistent with filter panel styling

**Acceptance**: Sort controls match filter panel aesthetic

---

### Phase 6: Chat Interface

**Objective**: Transform chat into glass panel with styled message bubbles

#### 6.1 Chat Container

**File**: `frontend/components/chat/ChatContainer.tsx`

**Changes**:
1. Apply glass effect to chat panel
2. Dark background with subtle blur
3. Consistent with overall theme

**Acceptance**: Chat panel has glass appearance

#### 6.2 Message Bubbles

**File**: `frontend/components/chat/ChatContainer.tsx`

**Changes**:
1. User messages:
   - Right-aligned
   - Accent gradient background
   - White text
   - Rounded corners (more on right)
2. AI messages:
   - Left-aligned
   - Surface glass background
   - Primary text color
   - Rounded corners (more on left)
3. Timestamps in secondary color, smaller text

**Acceptance**: User vs AI messages clearly distinct

#### 6.3 Typing Indicator

**File**: `frontend/components/chat/ChatContainer.tsx`

**Changes**:
1. Add typing indicator component:
   - 3 dots in a row
   - Bouncing animation (staggered)
   - Positioned like AI message bubble
2. Show when AI response is pending

**Acceptance**: Typing indicator animates smoothly during AI response

#### 6.4 Input Area

**File**: `frontend/components/chat/ChatContainer.tsx`

**Changes**:
1. Apply input-glass styling to textarea
2. Send button with accent color
3. Focus glow effect

**Acceptance**: Input area matches glass theme

---

### Phase 7: Header & Layout

**Objective**: Apply glass styling to navigation header

#### 7.1 Header

**File**: `frontend/components/layout/Header.tsx`

**Changes**:
1. Apply glass effect to header bar
2. Logo/branding with accent color
3. Navigation links with hover effects
4. Mobile menu with glass panel

**Acceptance**: Header integrates with glass theme

---

### Phase 8: Responsive & Polish

**Objective**: Ensure responsive behavior and final polish

#### 8.1 Responsive Testing

**All modified files**

**Changes**:
1. Test at 375px (mobile)
2. Test at 768px (tablet)
3. Test at 1024px (desktop)
4. Test at 1920px (large desktop)
5. Fix any overflow, truncation, or layout issues

**Acceptance**: UI usable at all viewport sizes

#### 8.2 Contrast Validation

**All modified files**

**Changes**:
1. Validate text contrast ratios (4.5:1 minimum)
2. Fix any failing contrast areas
3. Ensure focus states visible

**Acceptance**: WCAG AA compliance for text contrast

#### 8.3 Animation Performance

**All animated elements**

**Changes**:
1. Verify hover animations are 60fps
2. Check for jank during transitions
3. Ensure GPU-accelerated properties used (transform, opacity)

**Acceptance**: Smooth animations, no frame drops

#### 8.4 Functional Regression Test

**Manual testing**

**Test checklist**:
- [ ] Create task with all fields
- [ ] Edit task
- [ ] Complete/uncomplete task
- [ ] Delete task
- [ ] Filter by priority
- [ ] Filter by tags
- [ ] Filter by status
- [ ] Sort by all fields
- [ ] Send chat message
- [ ] Receive AI response
- [ ] Login/logout
- [ ] Responsive navigation

**Acceptance**: All existing functionality works

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Glass effect performance on low-end devices | Low | Medium | Use `will-change` sparingly, test on throttled CPU |
| Browser compatibility for backdrop-filter | Low | Low | Graceful fallback to solid background |
| Regression in existing functionality | Low | High | Manual smoke test all CRUD operations |
| Contrast issues with glass transparency | Medium | Medium | Validate all text against WCAG AA |

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Tailwind CSS 3.4+ | Existing | backdrop-filter utilities available |
| Next.js 14+ | Existing | CSS modules, app router |
| Modern browsers | Runtime | backdrop-filter support |

## Estimated Scope

| Phase | Files | Lines Changed (est.) |
|-------|-------|---------------------|
| 1. Design System | 3 | ~150 |
| 2. Core Components | 4 | ~100 |
| 3. Task List | 1-2 | ~150 |
| 4. Task Forms | 5 | ~80 |
| 5. Filters/Sort | 2 | ~50 |
| 6. Chat | 1 | ~100 |
| 7. Header | 1 | ~30 |
| 8. Polish | All | ~40 |
| **Total** | ~15 | ~700 |

---

## Next Steps

1. Run `/sp.tasks` to generate ordered implementation tasks
2. Execute tasks in sequence
3. Perform visual review after each phase
4. Complete functional regression test
5. Create commit with all changes
