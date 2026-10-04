import { AlphaType, ColorType, Skia } from '@shopify/react-native-skia';

// MobileNetV3Small was exported with include_preprocessing=True (see
// model/leafscout_ml/embeddings.py), so it expects RAW 0-255 float RGB
// input at 224x224 — no manual normalization here, Keras's own
// preprocessing layer is baked into the .tflite graph.
const MODEL_INPUT_SIZE = 224;

/**
 * Decode an image file (local `file://...` URI, as returned by the image
 * picker), resize to 224x224, and return raw RGB pixels as a flat
 * Float32Array (H*W*3, row-major, no alpha channel) — the exact layout
 * react-native-fast-tflite's input ArrayBuffer needs for this model.
 */
export async function imageUriToModelInput(uri: string): Promise<Float32Array> {
  const data = await Skia.Data.fromURI(uri);
  const image = Skia.Image.MakeImageFromEncoded(data);
  if (!image) {
    throw new Error(`Could not decode image at ${uri}`);
  }

  try {
    const surface = Skia.Surface.MakeOffscreen(MODEL_INPUT_SIZE, MODEL_INPUT_SIZE);
    if (!surface) {
      throw new Error('Could not create offscreen Skia surface for resizing');
    }
    const canvas = surface.getCanvas();
    const srcRect = Skia.XYWHRect(0, 0, image.width(), image.height());
    const dstRect = Skia.XYWHRect(0, 0, MODEL_INPUT_SIZE, MODEL_INPUT_SIZE);
    canvas.drawImageRect(image, srcRect, dstRect, Skia.Paint());
    surface.flush();

    const resized = surface.makeImageSnapshot();
    const pixels = resized.readPixels(0, 0, {
      width: MODEL_INPUT_SIZE,
      height: MODEL_INPUT_SIZE,
      colorType: ColorType.RGBA_8888,
      alphaType: AlphaType.Unpremul,
    }) as Uint8Array | null;

    if (!pixels) {
      throw new Error('readPixels returned null');
    }

    const out = new Float32Array(MODEL_INPUT_SIZE * MODEL_INPUT_SIZE * 3);
    let o = 0;
    for (let i = 0; i < pixels.length; i += 4) {
      out[o++] = pixels[i]; // R
      out[o++] = pixels[i + 1]; // G
      out[o++] = pixels[i + 2]; // B
      // skip alpha (pixels[i + 3])
    }
    return out;
  } finally {
    image.dispose();
  }
}
