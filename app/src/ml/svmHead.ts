// JS port of model/leafscout_ml/svm_head.py:predict_with_weights — must stay
// numerically identical to that Python reference implementation. The Python
// test suite (model/tests/test_svm_head.py) checks the Python side agrees
// with sklearn's own .predict(); this file is the on-device twin of that math.
export interface SvmHeadWeights {
  classes: string[];
  coef: number[][]; // (n_classes, n_features)
  intercept: number[]; // (n_classes,)
  feature_dim: number;
}

export interface Prediction {
  predictedClass: string;
  confidence: number; // softmax-over-decision-scores, NOT a calibrated probability
  classProbabilities: Record<string, number>;
}

export function predictWithWeights(embedding: Float32Array, weights: SvmHeadWeights): Prediction {
  const { classes, coef, intercept } = weights;
  const scores = new Array<number>(classes.length);

  for (let c = 0; c < classes.length; c++) {
    let dot = 0;
    const row = coef[c];
    for (let i = 0; i < row.length; i++) {
      dot += row[i] * embedding[i];
    }
    scores[c] = dot + intercept[c];
  }

  const maxScore = Math.max(...scores);
  const expScores = scores.map((s) => Math.exp(s - maxScore));
  const sumExp = expScores.reduce((a, b) => a + b, 0);
  const probs = expScores.map((e) => e / sumExp);

  let bestIdx = 0;
  for (let c = 1; c < scores.length; c++) {
    if (scores[c] > scores[bestIdx]) bestIdx = c;
  }

  const classProbabilities: Record<string, number> = {};
  classes.forEach((cls, i) => {
    classProbabilities[cls] = probs[i];
  });

  return {
    predictedClass: classes[bestIdx],
    confidence: probs[bestIdx],
    classProbabilities,
  };
}
