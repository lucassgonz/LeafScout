import { predictWithWeights, type SvmHeadWeights } from '../svmHead';

// A tiny 2-feature, 3-class head with hand-picked, well-separated weights —
// mirrors the synthetic fixtures in model/tests/test_svm_head.py so both
// sides of the Python<->JS port are exercised the same way.
const toyWeights: SvmHeadWeights = {
  classes: ['healthy', 'rust', 'angular_leaf_spot'],
  coef: [
    [5, 0],
    [0, 5],
    [-5, -5],
  ],
  intercept: [0, 0, 0],
  feature_dim: 2,
};

describe('predictWithWeights', () => {
  it('picks the class whose weight vector the embedding aligns with', () => {
    const result = predictWithWeights(new Float32Array([1, 0]), toyWeights);
    expect(result.predictedClass).toBe('healthy');
  });

  it('picks a different class for a different-aligned embedding', () => {
    const result = predictWithWeights(new Float32Array([0, 1]), toyWeights);
    expect(result.predictedClass).toBe('rust');
  });

  it('picks the third class for a negative-aligned embedding', () => {
    const result = predictWithWeights(new Float32Array([-1, -1]), toyWeights);
    expect(result.predictedClass).toBe('angular_leaf_spot');
  });

  it('class probabilities sum to 1', () => {
    const result = predictWithWeights(new Float32Array([1, 0]), toyWeights);
    const sum = Object.values(result.classProbabilities).reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1, 6);
  });

  it('confidence is the max class probability', () => {
    const result = predictWithWeights(new Float32Array([1, 0]), toyWeights);
    const maxProb = Math.max(...Object.values(result.classProbabilities));
    expect(result.confidence).toBeCloseTo(maxProb, 6);
  });

  it('is deterministic for the same input', () => {
    const a = predictWithWeights(new Float32Array([1, 0.2]), toyWeights);
    const b = predictWithWeights(new Float32Array([1, 0.2]), toyWeights);
    expect(a).toEqual(b);
  });

  it('a near-zero embedding gives low-margin, roughly uniform confidence', () => {
    const result = predictWithWeights(new Float32Array([0, 0]), toyWeights);
    // all three scores are 0 -> softmax should be ~uniform (~0.33 each)
    expect(result.confidence).toBeLessThan(0.4);
  });

  it('matches the shape of a real exported head (bean_head.json)', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const beanHead = require('../../../assets/model/bean_head.json') as SvmHeadWeights;
    expect(beanHead.classes.length).toBeGreaterThan(0);
    expect(beanHead.coef.length).toBe(beanHead.classes.length);
    expect(beanHead.coef[0].length).toBe(beanHead.feature_dim);

    const fakeEmbedding = new Float32Array(beanHead.feature_dim).fill(0.01);
    const result = predictWithWeights(fakeEmbedding, beanHead);
    expect(beanHead.classes).toContain(result.predictedClass);
    expect(result.confidence).toBeGreaterThan(0);
    expect(result.confidence).toBeLessThanOrEqual(1);
  });
});
