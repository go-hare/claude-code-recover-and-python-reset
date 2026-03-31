import { createRequire } from 'module'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire(import.meta.url)
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function loadNativeModule() {
  const binaryPath = path.resolve(
    __dirname,
    '../../vendor/audio-capture',
    `${process.arch}-${process.platform}`,
    'audio-capture.node',
  )

  try {
    return require(binaryPath)
  } catch {
    return null
  }
}

const nativeModule = loadNativeModule()

export function isNativeAudioAvailable() {
  return typeof nativeModule?.isNativeAudioAvailable === 'function'
    ? nativeModule.isNativeAudioAvailable()
    : false
}

export function isNativeRecordingActive() {
  return typeof nativeModule?.isNativeRecordingActive === 'function'
    ? nativeModule.isNativeRecordingActive()
    : false
}

export function startNativeRecording(onData, onEnd) {
  return typeof nativeModule?.startNativeRecording === 'function'
    ? nativeModule.startNativeRecording(onData, onEnd)
    : false
}

export function stopNativeRecording() {
  if (typeof nativeModule?.stopNativeRecording === 'function') {
    nativeModule.stopNativeRecording()
  }
}

export default {
  isNativeAudioAvailable,
  isNativeRecordingActive,
  startNativeRecording,
  stopNativeRecording,
}
