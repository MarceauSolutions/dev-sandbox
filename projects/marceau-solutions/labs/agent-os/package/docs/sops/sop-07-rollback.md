# SOP 07 — Rollback

> Procedure for reverting a bad deployment.

## When to Roll Back
- Application crashes on start
- Critical functionality broken
- Data corruption detected
- Security vulnerability introduced

## Steps

### 1. Identify the bad commit
```bash
git log --oneline -10
```

### 2. Revert (preferred — preserves history)
```bash
git revert <commit-hash>
git push origin main
```

### 3. Re-deploy
Follow SOP 03 deployment steps with the reverted code.

### 4. Post-mortem
- What broke?
- Why wasn't it caught in testing?
- What check should be added to prevent recurrence?

## Emergency: Hard Reset (last resort)
Only if revert doesn't work:
```bash
git reset --hard <known-good-commit>
git push --force origin main  # DANGEROUS — confirm with user first
```
