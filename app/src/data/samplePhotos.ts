import { Image } from 'react-native';
import type { CropId } from './diseaseClasses';

// One real training-set leaf photo per crop, bundled so judges (or you,
// tonight) can see a full diagnosis without needing a real camera/photo —
// useful on the iOS Simulator, which has no camera at all. This is a demo
// convenience, NOT a model evaluation: these exact images were in the
// training split, so a correct result here is a smoke test that the
// capture->preprocess->inference->SVM pipeline runs end-to-end, not
// evidence of accuracy (that's what model/artifacts/model_registry.json's
// held-out test + 5-fold CV numbers are for).
const SAMPLE_SOURCES: Record<CropId, number> = {
  coffee: require('../../assets/samples/coffee_sample.jpg'),
  cassava: require('../../assets/samples/cassava_sample.jpg'),
  bean: require('../../assets/samples/bean_sample.jpg'),
};

export function sampleLeafPhotoUri(cropId: CropId): string {
  const resolved = Image.resolveAssetSource(SAMPLE_SOURCES[cropId]);
  if (!resolved) {
    throw new Error(`No bundled sample photo for crop "${cropId}"`);
  }
  return resolved.uri;
}
