import type { Command, LocalCommandCall } from '../types/command.js'
const MACRO = globalThis.__RECOVERED_MACRO__ ?? {
  VERSION: '2.1.88',
  BUILD_TIME: 'recovered-from-sourcemap',
  FEEDBACK_CHANNEL: 'github',
  ISSUES_EXPLAINER: 'https://github.com/anthropics/claude-code/issues',
  PACKAGE_URL: 'https://www.npmjs.com/package/@anthropic-ai/claude-code',
  NATIVE_PACKAGE_URL: 'https://www.npmjs.com/package/@anthropic-ai/claude-code',
  VERSION_CHANGELOG: 'https://github.com/anthropics/claude-code/releases',
};


const call: LocalCommandCall = async () => {
  return {
    type: 'text',
    value: MACRO.BUILD_TIME
      ? `${MACRO.VERSION} (built ${MACRO.BUILD_TIME})`
      : MACRO.VERSION,
  }
}

const version = {
  type: 'local',
  name: 'version',
  description:
    'Print the version this session is running (not what autoupdate downloaded)',
  isEnabled: () => process.env.USER_TYPE === 'ant',
  supportsNonInteractive: true,
  load: () => Promise.resolve({ call }),
} satisfies Command

export default version
