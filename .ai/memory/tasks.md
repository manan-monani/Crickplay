# Task Tracker

> Persistent task tracking for AI agents. Update this file as tasks progress.

---

## Quick Status

| Status | Count |
|--------|-------|
| Backlog | 0 |
| Todo | 0 |
| In Progress | 0 |
| Done | 0 |

**Last Updated:** [Date]
**Current Focus:** [Current task or priority]

---

## In Progress

<!-- Tasks currently being worked on -->

### [TASK-001] Example Task
- **Priority:** P1
- **Size:** M
- **Started:** 2024-XX-XX
- **Branch:** `feature/example`
- **Description:** Brief description of the task
- **Progress:**
  - [x] Subtask 1
  - [ ] Subtask 2
  - [ ] Subtask 3

---

## Todo

<!-- Tasks ready to be picked up -->

<!--
### [TASK-XXX] Task Title
- **Priority:** P1/P2/P3
- **Size:** S/M/L/XL
- **Dependencies:** None | TASK-XXX
- **Description:** What needs to be done
-->

---

## Backlog

<!-- Tasks identified but not yet ready -->

<!--
### [TASK-XXX] Task Title
- **Priority:** P3
- **Description:** Brief description
- **Notes:** Any context or considerations
-->

---

## Blocked

<!-- Tasks that cannot proceed -->

<!--
### [TASK-XXX] Task Title
- **Blocked By:** Reason
- **Since:** Date
- **Unblock Action:** What would unblock this
-->

---

## Done

<!-- Completed tasks (keep recent 10, archive older) -->

<!--
### [TASK-XXX] Task Title ✓
- **Completed:** 2024-XX-XX
- **Branch:** `feature/xxx` (merged)
- **Summary:** Brief summary of what was done
- **Commits:** abc1234, def5678
-->

---

## Archive

<!-- Link to archived tasks -->
See `docs/archive/tasks-archive.md` for older completed tasks.

---

## Task Templates

### Feature Task
```markdown
### [TASK-XXX] Feature: [Name]
- **Priority:** P1
- **Size:** L
- **Dependencies:** None
- **Description:** Implement [feature description]
- **Acceptance Criteria:**
  - [ ] Criterion 1
  - [ ] Criterion 2
- **Subtasks:**
  - [ ] Design component
  - [ ] Implement backend
  - [ ] Add tests
  - [ ] Documentation
```

### Bug Fix Task
```markdown
### [TASK-XXX] Fix: [Bug Description]
- **Priority:** P0
- **Size:** S
- **Related Issue:** #123
- **Description:** Fix [bug description]
- **Steps to Reproduce:**
  1. Step 1
  2. Step 2
- **Expected vs Actual:** What should happen vs what happens
```

### Refactor Task
```markdown
### [TASK-XXX] Refactor: [What]
- **Priority:** P2
- **Size:** M
- **Description:** Refactor [description]
- **Motivation:** Why this refactor is needed
- **Scope:**
  - [ ] File/component 1
  - [ ] File/component 2
```

---

## Priority Guide

| Priority | Description | Response |
|----------|-------------|----------|
| P0 | Critical/Blocking | Immediate |
| P1 | High - Core work | Current session |
| P2 | Medium - Enhancement | Next available |
| P3 | Low - Nice to have | When time permits |

## Size Guide

| Size | Complexity | Typical Time |
|------|------------|--------------|
| S | Simple, single file | < 1 hour |
| M | Moderate, few files | 1-4 hours |
| L | Complex, many files | 4-8 hours |
| XL | Very complex | 1+ days |
