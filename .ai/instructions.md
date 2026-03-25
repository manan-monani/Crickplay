# AI Agent Detailed Instructions

> Extended workflow instructions for AI agents. This file provides detailed protocols beyond the CLAUDE.md master file.

## Decision Making Framework

### When to Ask User vs Act Autonomously

**Act Autonomously:**
- Creating/modifying code files within scope
- Creating branches (following naming convention)
- Making commits (following commit convention)
- Running tests
- Updating documentation
- Reading files and exploring codebase

**Ask User First:**
- Pushing to remote repository
- Merging branches
- Deleting branches or files
- Making architectural decisions
- Changing dependencies
- Modifying production configurations
- Any destructive git operations

### Problem Decomposition Protocol

When facing a complex task:

1. **Analyze** - Understand the full scope
2. **Decompose** - Break into subtasks (max 5 levels deep)
3. **Sequence** - Order by dependencies
4. **Estimate** - Rate complexity (S/M/L/XL)
5. **Document** - Record in tasks.md
6. **Execute** - Work through sequentially
7. **Validate** - Test each component
8. **Integrate** - Combine and test whole

---

## Code Implementation Protocol

### Before Writing Code

1. Search codebase for similar implementations
2. Check if utility/helper already exists
3. Review related tests for expected behavior
4. Consider edge cases upfront
5. Plan the implementation approach

### While Writing Code

1. Follow existing code style and patterns
2. Add inline comments for complex logic
3. Use meaningful variable/function names
4. Handle errors appropriately
5. Consider performance implications

### After Writing Code

1. Self-review the changes
2. Run related tests
3. Format code (prettier/eslint)
4. Update related documentation
5. Commit with proper message

---

## Git Workflow Details

### Branch Naming Examples

```
feature/user-authentication
feature/payment-integration
feature/dashboard-analytics

fix/login-redirect-loop
fix/memory-leak-in-cache
fix/null-pointer-user-profile

refactor/database-queries
refactor/component-structure

experiment/new-caching-strategy
experiment/ai-recommendations

hotfix/security-patch-auth
hotfix/critical-payment-bug
```

### Commit Message Examples

```
feat(auth): implement JWT refresh token mechanism

- Add refresh token endpoint
- Store refresh tokens in Redis
- Implement token rotation
- Add tests for token refresh

Closes #123
```

```
fix(api): resolve race condition in user update

The user update endpoint was experiencing race conditions
when multiple updates occurred simultaneously.

- Add optimistic locking
- Implement retry logic
- Add transaction wrapper

Fixes #456
```

### Merge Strategy

1. Always merge `develop` into feature branch first
2. Resolve conflicts in feature branch
3. Run all tests after merge
4. Create PR for review (if applicable)
5. Squash commits if too granular

---

## Memory Management Protocol

### What to Store in Memory Files

**tasks.md:**
- All tasks (past, present, future)
- Task status and priority
- Blockers and dependencies
- Completion dates

**decisions.md:**
- Architectural choices made
- Why alternatives were rejected
- Trade-offs considered
- Links to relevant discussions

**architecture.md:**
- System overview
- Component relationships
- Data flow diagrams (text-based)
- Integration points

### Memory Update Frequency

| File | Update When |
|------|-------------|
| tasks.md | Task status changes, new tasks discovered |
| decisions.md | Significant technical decision made |
| architecture.md | System structure changes |

---

## Error Handling Protocol

### When Errors Occur

1. **Log** - Capture full error details
2. **Analyze** - Understand root cause
3. **Document** - Record in relevant memory file if recurring
4. **Fix** - Implement appropriate solution
5. **Test** - Verify fix works
6. **Prevent** - Add tests to prevent regression

### Common Error Categories

| Category | Action |
|----------|--------|
| Build errors | Fix immediately, commit fix |
| Test failures | Investigate, fix or update test |
| Runtime errors | Debug, fix, add error handling |
| Dependency issues | Check compatibility, update carefully |

---

## Quality Checkpoints

### Before Starting Implementation
- [ ] Read relevant memory files
- [ ] Understand existing patterns
- [ ] Plan implementation approach
- [ ] Identify potential risks

### Before Committing
- [ ] Code compiles without errors
- [ ] Tests pass
- [ ] Code formatted properly
- [ ] No debug statements left
- [ ] Commit message follows convention

### Before Pushing
- [ ] All local commits are clean
- [ ] Branch is up to date with develop
- [ ] Documentation updated
- [ ] tasks.md updated
- [ ] User confirmation obtained

### Before Merging
- [ ] All CI checks pass
- [ ] Code reviewed (self or peer)
- [ ] No merge conflicts
- [ ] Feature documentation complete
- [ ] Related tasks marked done
