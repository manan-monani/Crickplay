# Debug Prompt

> Use this prompt to systematically debug issues.

## Trigger

Use when: Encountering bugs, errors, or unexpected behavior.

## Debug Process

### Step 1: Gather Information

```
## Bug Report

**What happened:**
[Description of the issue]

**Expected behavior:**
[What should happen]

**Actual behavior:**
[What actually happens]

**Error message (if any):**
```

[Paste error message]

```

**Steps to reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Environment:**
- Node version:
- OS:
- Browser (if applicable):
- Relevant dependencies:
```

### Step 2: Analyze

```
## Analysis

**Possible causes:**
1. [Cause 1]
2. [Cause 2]
3. [Cause 3]

**Related code locations:**
- `path/to/file1.ts:lineNumber`
- `path/to/file2.ts:lineNumber`

**Similar past issues:**
- [Reference to similar issue if any]
```

### Step 3: Investigate

```
## Investigation

**Hypothesis:** [What I think is causing the issue]

**Test approach:**
1. [How to verify the hypothesis]
2. [What to check]

**Debug steps:**
1. Add logging at [location]
2. Check [specific values]
3. Verify [condition]
```

### Step 4: Fix and Verify

```
## Solution

**Root cause:**
[Explanation of the root cause]

**Fix:**
[Description of the fix]

**Files changed:**
- `path/to/file.ts` - [What changed]

**Verification:**
- [ ] Issue no longer reproducible
- [ ] Related tests pass
- [ ] No regression in related functionality
- [ ] Edge cases handled
```

## Common Issue Checklist

### Null/Undefined Errors

- [ ] Check optional chaining (`?.`)
- [ ] Verify data exists before access
- [ ] Check async/await handling
- [ ] Verify API response structure

### Database Errors

- [ ] Check connection string
- [ ] Verify table/column names
- [ ] Check data types match
- [ ] Look for constraint violations

### Authentication Errors

- [ ] Verify token validity
- [ ] Check auth headers
- [ ] Confirm user permissions
- [ ] Check session expiration

### API Errors

- [ ] Verify request format
- [ ] Check response handling
- [ ] Look for CORS issues
- [ ] Verify endpoint URL

### Performance Issues

- [ ] Check for N+1 queries
- [ ] Look for missing indexes
- [ ] Check for memory leaks
- [ ] Profile slow functions

## Debugging Commands

```bash
# Check logs
npm run logs

# Run specific test
npm test -- --grep "test name"

# Debug mode
npm run dev:debug

# Check database
npm run db:console
```

## Post-Fix Actions

1. Document the issue and fix in decisions.md if significant
2. Add regression test if applicable
3. Update related documentation
4. Check for similar issues elsewhere in codebase
