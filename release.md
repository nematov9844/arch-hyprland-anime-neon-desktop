# Release Guide

## Versioning

Use semantic versioning: `MAJOR.MINOR.PATCH`  
Example: `1.0.0`

## Steps to Release

1. Update `VERSION`
2. Update `CHANGELOG.md`
3. Commit

```bash
git add .
git commit -m "release: v1.0.0"
```

4. Tag

```bash
git tag v1.0.0
git push origin v1.0.0
```

5. Create GitHub Release
   - Go to Releases
   - Create new release
   - Select tag
   - Add notes

## Release Checklist

- install.sh works
- doctor.sh clean
- README updated
- screenshots added
- version bumped
