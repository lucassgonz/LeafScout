// Per-crop disease metadata: display name + the short, actionable guidance
// read out to the farmer. Matches the `disease_classes` row shape in
// ARCHITECTURE.md §7.1 (SQLite) / §7.2 (Supabase). English per the
// competition's language requirement.
export type CropId = 'coffee' | 'cassava' | 'bean';

export interface DiseaseClassInfo {
  id: string; // must match the SVM head's class label exactly (see model/artifacts/<crop>_head.json)
  cropId: CropId;
  nameEn: string;
  descriptionEn: string;
  recommendedAction: string;
}

export const CROPS: { id: CropId; displayName: string }[] = [
  { id: 'coffee', displayName: 'Coffee (Arabica)' },
  { id: 'cassava', displayName: 'Cassava' },
  { id: 'bean', displayName: 'Common bean' },
];

export const DISEASE_CLASSES: DiseaseClassInfo[] = [
  // Coffee — BRACOL classes
  {
    id: 'healthy',
    cropId: 'coffee',
    nameEn: 'Healthy',
    descriptionEn: 'No signs of leaf miner, rust, phoma, or cercospora detected.',
    recommendedAction: 'Keep monitoring weekly. No action needed right now.',
  },
  {
    id: 'rust',
    cropId: 'coffee',
    nameEn: 'Coffee leaf rust',
    descriptionEn: 'Orange-yellow powdery spots on the underside of the leaf — the most damaging coffee disease worldwide.',
    recommendedAction: 'Show this to your extension officer this week. Consider a copper-based fungicide if rust is spreading fast.',
  },
  {
    id: 'leaf_miner',
    cropId: 'coffee',
    nameEn: 'Coffee leaf miner',
    descriptionEn: 'Pale, winding tunnels inside the leaf made by the miner larva.',
    recommendedAction: 'Remove and destroy badly mined leaves. Report to your cooperative if spreading across the plot.',
  },
  {
    id: 'phoma',
    cropId: 'coffee',
    nameEn: 'Phoma leaf spot',
    descriptionEn: 'Dark brown spots with a yellow halo, often after cold or wet weather.',
    recommendedAction: 'Improve plot drainage and spacing. Show to the extension officer if spots keep spreading.',
  },
  {
    id: 'cercospora',
    cropId: 'coffee',
    nameEn: 'Cercospora leaf spot (brown eye spot)',
    descriptionEn: 'Circular brown spots with a lighter center, common on stressed plants.',
    recommendedAction: 'Check plant nutrition and shade levels. Show to the extension officer if severe.',
  },

  // Cassava — Makerere/NaCRRI classes
  {
    id: 'healthy',
    cropId: 'cassava',
    nameEn: 'Healthy',
    descriptionEn: 'No signs of mosaic, brown streak, bacterial blight, or green mottle detected.',
    recommendedAction: 'Keep monitoring. No action needed right now.',
  },
  {
    id: 'mosaic_disease',
    cropId: 'cassava',
    nameEn: 'Cassava mosaic disease',
    descriptionEn: 'Pale yellow-green mosaic patterns and leaf distortion — spread by whitefly.',
    recommendedAction: 'Uproot and destroy severely affected plants. Ask your extension officer about disease-resistant cuttings for the next planting.',
  },
  {
    id: 'brown_streak',
    cropId: 'cassava',
    nameEn: 'Cassava brown streak disease',
    descriptionEn: 'Brown streaks on stems and a dry, corky rot inside the roots — often invisible above ground until harvest.',
    recommendedAction: 'This disease can ruin roots with no visible leaf symptoms. Show this to your extension officer before the next harvest.',
  },
  {
    id: 'bacterial_blight',
    cropId: 'cassava',
    nameEn: 'Cassava bacterial blight',
    descriptionEn: 'Angular, water-soaked leaf spots and wilting shoots.',
    recommendedAction: 'Avoid working in wet fields (spreads the bacteria). Show to your extension officer if wilting spreads.',
  },
  {
    id: 'green_mottle',
    cropId: 'cassava',
    nameEn: 'Cassava green mottle',
    descriptionEn: 'Light green mottling on leaves, generally milder than mosaic disease.',
    recommendedAction: 'Keep monitoring. Mention it at your next extension officer visit.',
  },

  // Bean — iBean classes
  {
    id: 'healthy',
    cropId: 'bean',
    nameEn: 'Healthy',
    descriptionEn: 'No signs of rust or angular leaf spot detected.',
    recommendedAction: 'Keep monitoring weekly. No action needed right now.',
  },
  {
    id: 'rust',
    cropId: 'bean',
    nameEn: 'Bean rust',
    descriptionEn: 'Small reddish-brown powdery pustules on the leaf underside.',
    recommendedAction: 'Remove heavily infected leaves. Show to your extension officer if spreading across the plot.',
  },
  {
    id: 'angular_leaf_spot',
    cropId: 'bean',
    nameEn: 'Angular leaf spot',
    descriptionEn: 'Grey-brown angular spots bound by leaf veins.',
    recommendedAction: 'Avoid overhead irrigation. Show to your extension officer if spots keep spreading.',
  },
];

export function diseaseInfo(cropId: CropId, classId: string): DiseaseClassInfo | undefined {
  return DISEASE_CLASSES.find((d) => d.cropId === cropId && d.id === classId);
}

// Below this confidence, the guardrail routes to a human instead of showing
// a diagnosis — see ARCHITECTURE.md §3 "Guardrail layer" / §9 Responsible AI.
export const CONFIDENCE_THRESHOLD = 0.55;
