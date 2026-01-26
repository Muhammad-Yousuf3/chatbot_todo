# Quickstart: Midnight AI Glass UI Theme

**Feature**: 011-midnight-glass-ui
**Date**: 2026-01-25

## Prerequisites

- Node.js 20+
- pnpm (or npm/yarn)
- Frontend project at `frontend/`

## Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
pnpm install

# Start development server
pnpm dev
```

The app will be available at `http://localhost:3000`

## Development Workflow

### 1. Design System Changes

All design token changes are in:
- `frontend/tailwind.config.ts` - Color palette, shadows, animations
- `frontend/app/globals.css` - CSS variables, base styles, utilities

### 2. Component Updates

Components to modify are in:
- `frontend/components/ui/` - Base UI components (Button, Card, Toast)
- `frontend/components/tasks/` - Task-specific components
- `frontend/components/chat/` - Chat interface
- `frontend/components/layout/` - Header, Footer

### 3. Page Updates

Pages to update:
- `frontend/app/tasks/page.tsx` - Task list and forms
- `frontend/app/chat/page.tsx` - Chat interface
- `frontend/app/layout.tsx` - Root layout (dark mode class)

## Key Files Quick Reference

| File | Purpose |
|------|---------|
| `tailwind.config.ts` | Color tokens, shadows, keyframes |
| `globals.css` | CSS variables, utilities, base styles |
| `components/ui/Card.tsx` | Glass card variant |
| `components/ui/Button.tsx` | Button styling |
| `app/tasks/page.tsx` | Task list styling |
| `components/chat/ChatContainer.tsx` | Chat bubbles, typing indicator |

## Testing Changes

### Visual Testing

1. Navigate to `/tasks` - Verify glass cards, hover effects, priority badges
2. Create a task - Verify form inputs have glass styling
3. Navigate to `/chat` - Verify message bubbles, typing indicator
4. Test hover states on all interactive elements
5. Resize browser to test responsive behavior (375px to 1920px)

### Functional Testing

Ensure all existing functionality works:
- [ ] Create task (with all fields)
- [ ] Edit task
- [ ] Complete/uncomplete task
- [ ] Delete task
- [ ] Filter by priority/tags/status
- [ ] Sort by different fields
- [ ] Send chat message
- [ ] Receive AI response

### Accessibility Testing

- [ ] Check color contrast (WCAG AA: 4.5:1 for text)
- [ ] Verify keyboard navigation
- [ ] Test focus states are visible

## Useful Commands

```bash
# Start dev server
pnpm dev

# Build for production
pnpm build

# Type check
pnpm tsc --noEmit

# Lint
pnpm lint
```

## Debugging Tips

### Glass Effect Not Showing

1. Check if `dark` class is on `<html>` element
2. Verify `backdrop-filter` browser support
3. Check for parent elements with `overflow: hidden` (can clip blur)

### Colors Look Wrong

1. Verify `tailwind.config.ts` changes are saved
2. Restart dev server after config changes
3. Clear browser cache

### Hover Effects Not Working

1. Check `transition` property is set
2. Verify `hover:` prefix classes are applied
3. Check for conflicting CSS specificity

## File Checklist for Implementation

Phase 1 - Design System:
- [ ] `tailwind.config.ts` - Update colors, add glass utilities
- [ ] `globals.css` - Update CSS variables, add glass classes

Phase 2 - Core Components:
- [ ] `components/ui/Card.tsx` - Add glass variant
- [ ] `components/ui/Button.tsx` - Update styling
- [ ] `app/layout.tsx` - Force dark mode class

Phase 3 - Task UI:
- [ ] `app/tasks/page.tsx` - Glass cards, form styling
- [ ] `components/tasks/FilterPanel.tsx` - Glass dropdowns
- [ ] `components/tasks/SortControls.tsx` - Glass controls

Phase 4 - Chat UI:
- [ ] `components/chat/ChatContainer.tsx` - Glass panel, bubbles, typing indicator

Phase 5 - Polish:
- [ ] Test all pages for consistency
- [ ] Fix any contrast issues
- [ ] Verify responsive behavior
