module.exports = {
  preset: '@react-native/jest-preset',
  // react-native-image-picker (and a couple of its RN-ecosystem peers) ship
  // ESM source under node_modules — the default preset only transforms
  // react-native itself, so without this the App smoke test fails to even
  // import HomeScreen with "Cannot use import statement outside a module".
  transformIgnorePatterns: [
    'node_modules/(?!(react-native|@react-native|react-native-image-picker|react-native-sqlite-storage|@shopify/react-native-skia|react-native-fast-tflite|react-native-safe-area-context|react-native-url-polyfill)/)',
  ],
};
