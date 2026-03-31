const MACRO = globalThis.__RECOVERED_MACRO__ ?? {
  VERSION: '2.1.88',
  BUILD_TIME: 'recovered-from-sourcemap',
  FEEDBACK_CHANNEL: 'github',
  ISSUES_EXPLAINER: 'https://github.com/anthropics/claude-code/issues',
  PACKAGE_URL: 'https://www.npmjs.com/package/@anthropic-ai/claude-code',
  NATIVE_PACKAGE_URL: 'https://www.npmjs.com/package/@anthropic-ai/claude-code',
  VERSION_CHANGELOG: 'https://github.com/anthropics/claude-code/releases',
};

/**
 * User-Agent string helpers.
 *
 * Kept dependency-free so SDK-bundled code (bridge, cli/transports) can
 * import without pulling in auth.ts and its transitive dependency tree.
 */

export function getClaudeCodeUserAgent(): string {
  return `claude-code/${MACRO.VERSION}`
}
