import { useState } from 'react'
import { major, minor, patch } from 'semver'
const MACRO = globalThis.__RECOVERED_MACRO__ ?? {
  VERSION: '2.1.88',
  BUILD_TIME: 'recovered-from-sourcemap',
  FEEDBACK_CHANNEL: 'github',
  ISSUES_EXPLAINER: 'https://github.com/anthropics/claude-code/issues',
  PACKAGE_URL: 'https://www.npmjs.com/package/@anthropic-ai/claude-code',
  NATIVE_PACKAGE_URL: 'https://www.npmjs.com/package/@anthropic-ai/claude-code',
  VERSION_CHANGELOG: 'https://github.com/anthropics/claude-code/releases',
};


export function getSemverPart(version: string): string {
  return `${major(version, { loose: true })}.${minor(version, { loose: true })}.${patch(version, { loose: true })}`
}

export function shouldShowUpdateNotification(
  updatedVersion: string,
  lastNotifiedSemver: string | null,
): boolean {
  const updatedSemver = getSemverPart(updatedVersion)
  return updatedSemver !== lastNotifiedSemver
}

export function useUpdateNotification(
  updatedVersion: string | null | undefined,
  initialVersion: string = MACRO.VERSION,
): string | null {
  const [lastNotifiedSemver, setLastNotifiedSemver] = useState<string | null>(
    () => getSemverPart(initialVersion),
  )

  if (!updatedVersion) {
    return null
  }

  const updatedSemver = getSemverPart(updatedVersion)
  if (updatedSemver !== lastNotifiedSemver) {
    setLastNotifiedSemver(updatedSemver)
    return updatedSemver
  }
  return null
}
