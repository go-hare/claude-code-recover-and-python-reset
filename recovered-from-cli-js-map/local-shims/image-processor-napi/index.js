import sharp from 'sharp'

const nativeModule = {
  hasClipboardImage() {
    return false
  },
  readClipboardImage() {
    return null
  },
}

export function getNativeModule() {
  return nativeModule
}

export { sharp }

export default sharp
