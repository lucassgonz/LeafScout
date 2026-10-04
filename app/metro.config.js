const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

/**
 * Metro configuration
 * https://reactnative.dev/docs/metro
 *
 * @type {import('@react-native/metro-config').MetroConfig}
 */
const config = {
  resolver: {
    // .tflite must be treated as a binary asset (bundled, not parsed as JS)
    // so `require('./assets/model/backbone.tflite')` resolves to a module
    // id react-native-fast-tflite can load — see src/ml/model.ts.
    assetExts: [...getDefaultConfig(__dirname).resolver.assetExts, 'tflite'],
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
