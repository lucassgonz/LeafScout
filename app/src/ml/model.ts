import { loadTensorflowModel, type TfliteModel } from 'react-native-fast-tflite';
import beanHead from '../../assets/model/bean_head.json';
import cassavaHead from '../../assets/model/cassava_head.json';
import coffeeHead from '../../assets/model/coffee_head.json';
import type { CropId } from '../data/diseaseClasses';
import { imageUriToModelInput } from './imagePreprocess';
import { predictWithWeights, type Prediction, type SvmHeadWeights } from './svmHead';

const HEADS: Partial<Record<CropId, SvmHeadWeights>> = {
  coffee: coffeeHead as SvmHeadWeights,
  cassava: cassavaHead as SvmHeadWeights,
  bean: beanHead as SvmHeadWeights,
};

export const AVAILABLE_CROPS: CropId[] = Object.keys(HEADS) as CropId[];

let backboneModel: TfliteModel | null = null;
let loadingPromise: Promise<TfliteModel> | null = null;

async function getBackbone(): Promise<TfliteModel> {
  if (backboneModel) return backboneModel;
  if (!loadingPromise) {
    loadingPromise = loadTensorflowModel(require('../../assets/model/backbone_mobilenet_v3_small.tflite'), []);
  }
  backboneModel = await loadingPromise;
  return backboneModel;
}

// Call once at app startup (e.g. in App.tsx) so the first photo doesn't pay
// the model-load latency — see ARCHITECTURE.md §3, "under a second" demo claim.
export async function preloadModel(): Promise<void> {
  await getBackbone();
}

export interface ClassifyResult extends Prediction {
  cropId: CropId;
}

export async function classifyLeafPhoto(uri: string, cropId: CropId): Promise<ClassifyResult> {
  const headWeights = HEADS[cropId];
  if (!headWeights) {
    throw new Error(`No trained head available yet for crop "${cropId}"`);
  }

  const model = await getBackbone();
  const inputPixels = await imageUriToModelInput(uri);

  const outputs = model.runSync([inputPixels.buffer as ArrayBuffer]);
  const embedding = new Float32Array(outputs[0]);

  const prediction = predictWithWeights(embedding, headWeights);
  return { ...prediction, cropId };
}
