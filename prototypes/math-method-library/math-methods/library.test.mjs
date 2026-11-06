import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, rmdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { buildMethodLibrary, openMethodLibrary } from './library.mjs';

const studentCases = JSON.parse(readFileSync(new URL('./retrieval-cases.json', import.meta.url), 'utf8'));
const cases = [
  ['Solve √(t+7)=t+1', 'radical-equations'],
  ['Solve 7z−9=12', 'linear-equation'],
  ['What are the roots of z²+z−12=0?', ['quadratic-formula', 'factoring-and-zero-product', 'complete-the-square']],
  ['2/(x−1)=3/(x+2)', 'rational-equations'],
  ['15% of 360', 'percent-of-an-amount'],
  ['3/4+7/5', 'fraction-arithmetic'],
  ['C=A+B', 'rearrange-a-literal-equation'],
  ['Solve |2x−4|=7', 'absolute-value-cases'],
  ['Solve the inequality x²−4≤0', 'inequality-sign-chart'],
  ['Triangle with three sides 7, 8, 10, find angle with law of cosines', 'sine-and-cosine-rules'],
  ['Differentiate y=sin(4x^3)', 'calculus-chain-rule'],
  ['How do I find dy/dx if x^2+xy+y^2=12?', 'calculus-implicit-differentiation'],
  ['Evaluate integral x*cos(x) dx using a product technique', 'calculus-integration-by-parts'],
  ['Does the integral of 1/x from 1 to infinity converge?', 'calculus-improper-integral'],
  ['Find where the power series sum((x−2)^n/n) converges, including endpoints', 'calculus-power-series-interval'],
  ['Optimize the volume under a constraint using a multiplier', 'calculus-lagrange-multipliers'],
  ['Volume obtained by rotating a region around the y-axis using cylindrical shells', 'calculus-volume-cylindrical-shells'],
  ['Use Green’s theorem to turn circulation into a double integral', 'calculus-greens-theorem'],
  ["Find the IVP solution for y'=xy by separating variables", 'ode-separation-of-variables'],
  ["Solve y'+(2/x)y=x^2 with an integrating factor", 'ode-first-order-linear'],
  ['Find the basis for the kernel of A given its row echelon form', 'linear-null-space-basis'],
  ['Find the least squares fit through three points using normal equations', ['linear-least-squares', 'ordinary-least-squares-line']],
  ['Given a two-way table, find the chance of honor roll given that the student plays a sport', 'conditional-probability-from-counts'],
  ['What is the posterior probability of disease after a positive test with known sensitivity and false positive rate?', 'bayes-total-probability'],
  ['Draw 5 cards without replacement and find the probability of exactly two hearts', 'hypergeometric-sampling'],
  ['Build a Student t confidence interval for a population mean with unknown variance', 'student-t-mean-interval'],
  ['Find the modular inverse of 17 modulo 101 using the Euclidean algorithm', 'extended-euclid-inverse'],
  ['Prove the sum of the first n odd numbers by induction', 'induction-shifted-sum'],
  ['Approximate a root by Newton iteration using the derivative', 'newton-simple-root'],
  ['Use the supremum error to show uniform convergence of a function sequence', 'uniform-convergence-supremum'],
  ['How do I tell whether f of complex z is holomorphic?', 'cauchy-riemann-equations'],
  ['Find the maximum flow and certify a minimum cut from this residual graph', 'max-flow-min-cut'],
];

test('build, retrieve methods, and preserve the previous snapshot on invalid input', t => {
  const directory = mkdtempSync(join(tmpdir(), 'stepmargin-method-test-'));
  const database = join(directory, 'library.sqlite');
  const brokenCards = join(directory, 'broken');
  const invalidFile = join(brokenCards, 'invalid.json');
  mkdirSync(brokenCards);
  let library;

  try {
    const built = buildMethodLibrary({ database });
    assert.equal(buildMethodLibrary({ database }).revision, built.revision);
    const original = readFileSync(database);
    library = openMethodLibrary(database);
    assert.equal(library.revision, built.revision);
    assert.equal(library.coverage().reduce((n, row) => n + row.methods, 0), built.methods);
    assert.equal(library.get('not-a-method'), null);
    assert.deepEqual(library.search({ query: 'zebra wifi firmware' }), []);
    assert.deepEqual(library.search({ query: '" OR "*" --' }), []);
    assert.throws(() => library.search({ query: 'x'.repeat(1601) }), /1,600/);
    assert.throws(() => library.search({ query: 'calculus', limit: 9 }), /1 to 8/);
    const filtered = library.search({ query: 'integration', domain: 'calculus', level: 'undergraduate', limit: 2 });
    assert.equal(filtered.length, 2);
    assert.ok(filtered.every(card => card.domain === 'calculus' && card.level === 'undergraduate'));

    let first = 0;
    const misses = [];
    for (const [query, ids] of cases) {
      const expected = new Set(Array.isArray(ids) ? ids : [ids]);
      const results = library.search({ query }).map(card => card.id);
      if (expected.has(results[0])) first += 1;
      if (!results.some(id => expected.has(id))) misses.push({ query, expected: [...expected], results });
    }
    t.diagnostic(`${built.methods} cards. Retrieval hit@1 ${first}/${cases.length}. Hit@3 ${cases.length - misses.length}/${cases.length}.`);
    assert.deepEqual(misses, []);
    let studentFirst = 0;
    let studentHits = 0;
    let noMatch = 0;
    const studentMisses = [];
    for (const { query, ids } of studentCases) {
      const results = library.search({ query }).map(card => card.id);
      if (!ids.length) {
        if (!results.length) noMatch += 1;
        else studentMisses.push({ query, expected: ids, results });
        continue;
      }
      if (ids.includes(results[0])) studentFirst += 1;
      if (results.some(id => ids.includes(id))) studentHits += 1;
      else studentMisses.push({ query, expected: ids, results });
    }
    const positives = studentCases.filter(({ ids }) => ids.length).length;
    t.diagnostic(`Student phrasing hit@1 ${studentFirst}/${positives}. Hit@3 ${studentHits}/${positives}. No-match controls ${noMatch}/${studentCases.length - positives}.`);
    assert.deepEqual(studentMisses, []);
    assert.deepEqual(readFileSync(database), original);
    library.close();
    library = undefined;

    const card = { id: 'duplicate', title: 'Duplicate', domain: 'algebra', level: 'high-school',
      aliases: ['duplicate'], pattern: 'x', applies: ['x'], steps: ['x'], pitfalls: ['x'], checks: ['x'],
      example: { problem: 'x', answer: 'x' } };
    writeFileSync(invalidFile, JSON.stringify([card, card]));
    assert.throws(() => buildMethodLibrary({ database, directory: brokenCards }), /Duplicate method id/);
    assert.deepEqual(readFileSync(database), original);
  } finally {
    library?.close();
    rmSync(database, { force: true });
    rmSync(invalidFile, { force: true });
    rmdirSync(brokenCards);
    rmdirSync(directory);
  }
});
