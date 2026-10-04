// Manual Jest mock — the real package is backed by a native Nitro module
// that doesn't exist in the plain-Node Jest environment. Mirrors just enough
// of the real API shape (see node_modules/react-native-fast-tflite/lib/typescript)
// for component smoke tests to mount without hitting real inference.
module.exports = {
  loadTensorflowModel: jest.fn(async () => ({
    delegates: [],
    inputs: [{ name: 'input', dataType: 'float32', shape: [1, 224, 224, 3] }],
    outputs: [{ name: 'output', dataType: 'float32', shape: [1, 576] }],
    runSync: jest.fn(() => [new Float32Array(576).buffer]),
    run: jest.fn(async () => [new Float32Array(576).buffer]),
  })),
};
