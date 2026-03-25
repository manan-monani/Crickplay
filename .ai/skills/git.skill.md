# Git Skill

> Skill for performing git operations following project conventions.

## Purpose

This skill enables AI agents to perform version control operations following the project's git conventions and best practices.

## Available Operations

### 1. Create Branch

**When to use:** Starting new feature, fix, or experimental work.

**Command:**
```bash
git checkout <base-branch>
git pull origin <base-branch>
git checkout -b <branch-type>/<branch-name>
```

**Branch naming:**
- `feature/<descriptive-name>` - New features
- `fix/<issue-description>` - Bug fixes
- `refactor/<what>` - Code refactoring
- `experiment/<idea>` - Experimental work
- `hotfix/<critical-fix>` - Production fixes

### 2. Make Commit

**When to use:** After completing a logical unit of work.

**Command:**
```bash
git add <files>
git commit -m "<type>(<scope>): <description>"
```

**Commit types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code restructure
- `perf` - Performance
- `test` - Tests
- `build` - Build system
- `ci` - CI/CD
- `chore` - Maintenance

### 3. Push to Remote

**When to use:** After completing work, before session end (with user permission).

**Command:**
```bash
git push -u origin <branch-name>
```

### 4. Sync with Base

**When to use:** Before starting work, periodically during long features.

**Command:**
```bash
git fetch origin
git merge origin/<base-branch>
```

### 5. Create Tag

**When to use:** After release or significant milestone.

**Command:**
```bash
git tag -a v<version> -m "<tag message>"
git push origin v<version>
```

### 6. Revert Changes

**When to use:** When changes need to be undone.

**Command:**
```bash
# Revert specific commit
git revert <commit-hash>

# Soft reset (keep changes)
git reset --soft HEAD~1
```

## Usage Examples

### Starting New Feature

```bash
# 1. Ensure on develop and up to date
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/user-authentication

# 3. Make changes and commit
git add src/auth/login.ts
git commit -m "feat(auth): add login endpoint"

# 4. Continue development...
```

### Quick Bug Fix

```bash
# 1. Create fix branch
git checkout develop
git checkout -b fix/null-pointer-user-api

# 2. Fix and commit
git add src/api/user.ts
git commit -m "fix(api): handle null user in getUser endpoint"

# 3. Push (with user permission)
git push -u origin fix/null-pointer-user-api
```

## Pre-Commit Checklist

- [ ] Code compiles without errors
- [ ] Tests pass
- [ ] No debug statements left
- [ ] Files are properly staged
- [ ] Commit message follows convention

## Error Recovery

### Committed to Wrong Branch
```bash
git log  # Note the commit hash
git reset --soft HEAD~1
git stash
git checkout correct-branch
git stash pop
git add .
git commit -m "..."
```

### Need to Undo Last Commit
```bash
# Keep changes
git reset --soft HEAD~1

# Discard changes (careful!)
git reset --hard HEAD~1
```

### Merge Conflict
```bash
# View conflicting files
git status

# After resolving
git add <resolved-files>
git commit -m "merge: resolve conflicts with develop"
```
