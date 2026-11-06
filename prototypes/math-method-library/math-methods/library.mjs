import { createHash, randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, readdirSync, renameSync, rmSync } from 'node:fs';
import { basename, dirname, join } from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';

export const defaultDatabase = fileURLToPath(new URL('../.runtime/math-methods.sqlite', import.meta.url));
const cardsDirectory = fileURLToPath(new URL('./cards/', import.meta.url));
const version = 1;
const slug = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const levels = new Set(['high-school', 'undergraduate']);
const listFields = ['aliases', 'applies', 'steps', 'pitfalls', 'checks'];
const cardFields = ['id', 'title', 'domain', 'level', ...listFields, 'pattern', 'example'];
const stop = new Set(('about after also an and are as at be been before by can could do does equation equations find first for from ' +
  'have help how if in into is it just make many math maths me more my need next no of on only or pair paired pairing pairs please problem should some solve ' +
  'step steps than that the their them then these they this those through to using want was were what when where which will with work ' +
  'would your value values').split(' '));
const superscript = '⁰¹²³⁴⁵⁶⁷⁸⁹';
const languageCues = [
  ['percent change', [/\b(?:percent|percentage)\b|%/u, /\b(?:change[ds]?|fell|fall|rose|increas\w*|decreas\w*|drop\w*|reduc\w*)\b/u]],
  ['reverse percentage', [/\b(?:percent|percentage)\b|%/u, /\b(?:discount|markdown|markup|increase|decrease|tax)\b/u, /\b(?:original|before|start\w*|initial)\b/u]],
  ['cylinder volume', [/\b(?:tank|canister|pipe)\b/u, /\b(?:radius|diameter)\b/u, /\b(?:height|deep|depth|tall)\b/u]],
  ['arc length', [/\b(?:wedge|disk|circle|sector)\b/u, /\b(?:curved edge|curved length|arc)\b/u]],
  ['coordinate distance', [/\([^()]{1,32},[^()]{1,32}\)[^()]{0,80}\([^()]{1,32},[^()]{1,32}\)/u, /\b(?:distance|how (?:far|long)|length)\b/u]],
  ['similar triangles', [/\bshadows?\b/u, /\b(?:height|posts?|poles?|taller|tall)\b/u]],
  ['pythagorean theorem', [/\bladder\b/u, /\b(?:wall|ground)\b/u, /\b(?:foot|base|bottom)\b/u, /\b(?:height|high|length|long)\b/u]],
  ['right triangle ratios', [/\b(?:ramp|slope|incline|grade)\b/u, /\b(?:degrees|angle)\b/u, /\b(?:up|rise|height|vertical)\b/u]],
  ['unit conversion', [/\b(?:units?|convert)\b/u, /\b(?:same units?|express|convert|in)\b/u, /\b\d+(?:\.\d+)?\s*(?:cm|mm|km|m|in|ft|mi|lb|kg|mg|g|ml|l)\b/u]],
  ['inverse function', [/\binverse\b/u, /\b(?:function|defined|range|domain|[a-z]\s*\()/u]],
  ['inverse matrix', [/\bmatrix\b/u, /\b(?:undo|invert|inverse)\b/u]],
  ['graph shifts', [/\b(?:graph|function|curve)\b/u, /\b(?:shift(?:ed|ing)?|translat(?:e|ed|ion)|flip(?:ped|ping)?|stretch(?:ed|ing)?)\b/u]],
  ['implicit differentiation', [/\btangent\b/u, /\b(?:without (?:isolat|solv)\w*|implicit)\b/u]],
  ['closed interval method', [/\b(?:best|worst|maximum|minimum|largest|smallest|extrema)\b/u, /\b(?:interval|endpoints)\b/u]],
  ['disk method', [/\b(?:rotat\w*|revol\w*)\b/u, /\b(?:inner|outer)\b/u, /\b(?:radii|radius)\b/u]],
  ['null space', [/\b(?:matrix|transformation|operator)\b/u, /\b(?:mapped? to|sent to|sends|maps|annihilat\w*|kernel)\b/u, /\bzero\b/u]],
  ['rank nullity', [/\b(?:dimension|dim)\b/u, /\b(?:kernel|nullity)\b/u, /\b(?:domain|range|rank|image|outputs?)\b/u]],
  ['conditional probability', [/\b(?:among|given (?:that|they|he|she))\b/u, /\b(?:fraction|chance|probability|percentage|proportion|share)\b/u]],
  ['hypergeometric sampling', [/\b(?:draw|pull|pick|sample)\w*\b/u, /\b(?:without replac\w*|stay out|kept out|not returned)\b/u, /\b(?:exactly|chance|probability)\w*\b/u]],
  ['combinations versus permutations', [/\b(?:ways|arrange|line up|order matters|ordered)\b/u, /\b(?:line up|arrange|order matters|choose|select|swap)\b/u, /\b\d+\b/u]],
  ['posterior probability', [/\b(?:given that|after|if)\b/u, /\b(?:flagged|screened|tested positive|positive test|diagnos\w*)\b/u, /\b(?:chance|probability|truly|actually|really)\b/u]],
  ['posterior probability', [/\b(?:given|if)\b/u, /\b(?:likel\w*|chance|probability)\b/u, /\brates?\b/u, /\d[^%\n]{0,8}%[^%\n]{0,80}%/u]],
  ['stars and bars', [/\b(?:identical|indistinguishable)\b/u, /\b(?:distribut\w*|hand|give|share|allocat\w*)\b/u, /\b(?:each|everyone|per|groups?|bins?|people)\b/u]],
  ['factorial trailing zeros', [/\b(?:factorial|\d+!)/u, /\b(?:zeros?|zeroes)\b/u, /\b(?:trailing|end|ends)\b/u]],
  ['test for independence', [/\b(?:table|counts|categor\w*)\b/u, /\b(?:associated|association|independent|independence)\b/u, /\b(?:test|check|assess|determine)\b/u]],
  ['uniform convergence', [/\b(?:sequence|converge\w*)\b/u, /\b(?:for (?:every|all)|independent of)\b/u, /\b(?:one|same|single)\s+n\b/u]],
  ['directional derivative', [/\b(?:fastest|steepest|maximal|maximum)\b/u, /\b(?:increase\w*|decrease\w*|ascent|descent|direction)\b/u, /\b(?:around|point|at|function|gradient)\b/u]],
  ['composite simpson', [/\b1\s*,\s*4\s*,\s*2\s*,\s*4\s*,\s*1\b/u, /\b(?:interval|area|integral|estimate|weights?)\b/u]],
];

export class MethodQueryError extends Error {}

function requireValid(condition, message) {
  if (!condition) throw new Error(message);
}

function exactKeys(value, keys) {
  return value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
}

function validText(value) {
  return typeof value === 'string' && value.trim().length > 0 && value.length <= 700;
}

function validateCard(card, file) {
  requireValid(exactKeys(card, cardFields), `Invalid method card fields in ${file}`);
  requireValid(typeof card.id === 'string' && slug.test(card.id) &&
    typeof card.domain === 'string' && slug.test(card.domain) && levels.has(card.level),
    `Invalid id, domain, or level for ${card.id} in ${file}`);
  requireValid(validText(card.title) && validText(card.pattern), `Missing title or pattern for ${card.id}`);
  for (const field of listFields) {
    requireValid(Array.isArray(card[field]) && card[field].length > 0 && card[field].length <= 24 &&
      card[field].every(validText), `Invalid ${field} for ${card.id}`);
  }
  requireValid(exactKeys(card.example, ['problem', 'answer']) &&
    validText(card.example.problem) && validText(card.example.answer), `Invalid example for ${card.id}`);
  return card;
}

function loadCards(directory) {
  const cards = new Map();
  for (const file of readdirSync(directory, { withFileTypes: true }).filter(entry =>
    entry.isFile() && entry.name.endsWith('.json')).map(entry => entry.name).sort()) {
    const rows = JSON.parse(readFileSync(join(directory, file), 'utf8'));
    requireValid(Array.isArray(rows) && rows.length > 0, `Expected method cards in ${file}`);
    for (const row of rows) {
      const card = validateCard(row, file);
      requireValid(!cards.has(card.id), `Duplicate method id ${card.id}`);
      cards.set(card.id, card);
    }
  }
  requireValid(cards.size > 0, 'No math method cards found');
  return [...cards.values()].sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
}

function normalize(text) {
  return text.normalize('NFKC').toLowerCase().replace(/[−–]/gu, '-');
}

function notationTerms(query) {
  const raw = query.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]+/gu, digits =>
    '^' + [...digits].map(digit => superscript.indexOf(digit)).join('')).replace(/⁄/gu, '/');
  const text = normalize(raw);
  const cues = languageCues.filter(([, patterns]) => patterns.every(pattern => pattern.test(text))).map(([cue]) => cue);
  if (cues.includes('posterior probability')) cues.push('bayes theorem', 'base rate');
  if (cues.includes('test for independence')) cues.push('contingency table', 'chi square');
  const isEquation = /(?<![<>=!])=(?!=)/u.test(text);
  const quadratic = /[a-z]\s*\^\s*(?:\{2\}|2)(?![0-9])/u.test(text);
  const differentiation = /\b(?:differentiate|derivative|differentiat(?:ion|ing))\b/u.test(text);
  const integration = /∫|\\int\b|\b(?:integral|integrate|integration)\b/u.test(text);
  const derivativeOperator = /\bd\s*\/\s*d[a-z]\b/u.test(text);
  const differentiationRequest = differentiation || derivativeOperator;
  if (/√|\b(?:sqrt|radical)\b/u.test(text)) cues.push('radical square root');
  if (quadratic && /\b(?:how many|number of|real roots|real zeros|discriminant)\b/u.test(text)) {
    cues.push('quadratic discriminant');
  }
  if (integration) {
    cues.push('integral integration');
    if (/∞|\\infty\b|\b(?:infinite|infinity|unbounded)\b/u.test(text)) cues.push('improper integral');
    if (differentiation || derivativeOperator) cues.push('accumulation integral', 'variable limit');
    if (/\b[a-z](?:\s*\^\s*\d+)?\s*[⋅·×*]?\s*(?:sin\b|cos\b|ln\b|log\b|exp\b|e\s*\^)/u.test(text)) {
      cues.push('integration by parts');
    }
    if (/\b[a-z]\s*\([^()]{1,100}\^\s*(?:\{2\}|2)[^()]{0,100}\)\s*\^/u.test(text)) {
      cues.push('integration substitution');
    }
  }
  if (!integration && differentiationRequest &&
      /\b(?:sin|cos|tan|ln|log|exp|sqrt)\s*\((?!\s*[a-z]\s*\))[^)]+\)|\([^()]{1,100}[+\-][^()]{1,100}\)\s*\^/u.test(text)) {
    cues.push('chain rule', 'composite differentiation');
  }
  if (/\blim(?:it)?(?=[\s_{(])/u.test(text) && /→|->|\\to\b|\\rightarrow\b/u.test(text)) {
    cues.push('evaluate limit');
    if (/\)\s*\/\s*(?:\(|[a-z]\b)|\\(?:d?frac)\s*\{/u.test(text)) {
      cues.push('factor and cancel limit', 'removable discontinuity');
    }
  }
  const firstOrder = /\b([a-z])['′]\s*[+\-]([^=,'′\n]{1,100})=([^=,;\n]{1,100})/u.exec(text);
  if (firstOrder) {
    const [, dependent, left, right] = firstOrder;
    const linearTerm = new RegExp(`^[^${dependent}]*${dependent}\\s*(?:/[^${dependent}^]+)?$`, 'u');
    if (linearTerm.test(left.trim())) {
      const powered = new RegExp(`${dependent}\\s*\\^\\s*\\{?(?:[-+]|[02-9]|1\\d)`, 'u');
      if (powered.test(right)) cues.push('bernoulli equation', 'bernoulli substitution');
      else if (!right.includes(dependent)) cues.push('first order linear', 'integrating factor');
    }
  }
  if (/∑|\\sum\b/u.test(text)) cues.push('sum series summation');
  if (/\b(?:ln|log)(?=[\s_{(0-9])/u.test(text)) {
    cues.push(isEquation ? 'logarithmic equation' : 'logarithm logarithmic');
  }
  if (/≡[^;\n]{0,25}\b1\b[^;\n]{0,15}\bmod\b/u.test(text) && /\d\s*[a-z]\s*≡/u.test(text)) {
    cues.push('modular inverse');
  }
  if (/\b(?:sin|cos|tan)(?=[\s^{(0-9])/u.test(text)) cues.push('trigonometric');
  if (/\|[^|]+\|/u.test(text)) cues.push('absolute value');
  if (/[≤≥]|[<>]=?|\\(?:leq?|geq?)\b/u.test(text)) {
    cues.push(...(quadratic ? ['quadratic inequality', 'sign chart'] : ['inequality']));
  }
  if (/\bp\s*\([^)]*\|[^)]*\)/u.test(text)) cues.push('conditional probability');
  if (derivativeOperator || /(?:\bdy\s*\/\s*dx\b|[a-z]['′″])/u.test(text)) {
    cues.push(isEquation ? 'differential equation' : 'derivative differentiation');
  }
  if (!isEquation && quadratic && /\b(?:zeros|roots|factor)\b/u.test(text)) cues.push('quadratic polynomial');
  if (!isEquation && !cues.length && /\d\s*\/\s*\d\s*[+*/-]/u.test(text)) cues.push('fraction arithmetic');
  if (/\d\s*%\s*of\b/u.test(text)) cues.push('percent of amount');
  if (isEquation && !cues.length) {
    const formula = text.replace(/^\s*(?:solve|find|evaluate|simplify)\s*:?\s+/u, '').replace(/[\s?]/gu, '');
    if (/\/(?:\([^)]*[a-z]|[a-z])/u.test(formula)) cues.push('rational denominator');
    else if (quadratic) cues.push('quadratic');
    else if (/[a-z]\^(?:\{[3-9]\}|[3-9])/u.test(formula)) cues.push('polynomial');
    else if (/\d\s*\^\s*[{(]?[a-z]/u.test(formula)) cues.push('exponential');
    else if (/^[+\-()\d.]*[a-z][+\-()*\d./a-z]*=[+\-()*\d./a-z]+$/u.test(formula)) {
      cues.push(...(new Set(formula.match(/[a-z]/gu)).size === 1
        ? ['linear equation', 'one variable', 'balance method'] : ['literal equation', 'rearrange formula']));
    }
  }
  return cues;
}

function terms(text) {
  return [...new Set((normalize(text).match(/[\p{L}\p{N}]{2,}/gu) || []).filter(word =>
    /\p{L}/u.test(word) && !stop.has(word)))];
}

export function buildMethodLibrary({ database = defaultDatabase, directory = cardsDirectory } = {}) {
  const cards = loadCards(directory);
  const revision = createHash('sha256').update(JSON.stringify(cards)).digest('hex');
  mkdirSync(dirname(database), { recursive: true });
  const temporary = join(dirname(database), `.${basename(database)}-${randomUUID()}.tmp`);
  try {
    const db = new DatabaseSync(temporary);
    try {
      db.exec(`
        PRAGMA user_version = ${version};
        CREATE TABLE metadata (revision TEXT NOT NULL) STRICT;
        CREATE TABLE methods (
          id TEXT PRIMARY KEY, domain TEXT NOT NULL, level TEXT NOT NULL,
          card TEXT NOT NULL CHECK (json_valid(card))
        ) STRICT;
        CREATE VIRTUAL TABLE method_search USING fts5(
          id UNINDEXED, title, aliases, pattern, topic, explanation, tokenize = 'porter unicode61'
        );
        BEGIN;
      `);
      db.prepare('INSERT INTO metadata VALUES (?)').run(revision);
      const method = db.prepare('INSERT INTO methods VALUES (?, ?, ?, ?)');
      const index = db.prepare('INSERT INTO method_search VALUES (?, ?, ?, ?, ?, ?)');
      for (const card of cards) {
        method.run(card.id, card.domain, card.level, JSON.stringify(card));
        index.run(card.id, card.title, card.aliases.join(' '), card.pattern, card.domain.replaceAll('-', ' '),
          [...card.applies, ...card.steps].join(' '));
      }
      db.exec("INSERT INTO method_search(method_search) VALUES ('optimize'); COMMIT;");
      requireValid(db.prepare('PRAGMA quick_check').get().quick_check === 'ok', 'SQLite quick check failed');
      requireValid(db.prepare('SELECT count(*) AS count FROM method_search').get().count === cards.length,
        'Method index count differs from library');
    } finally {
      db.close();
    }
    renameSync(temporary, database);
  } finally {
    rmSync(temporary, { force: true });
  }
  return { database, methods: cards.length, revision };
}

export function openMethodLibrary(database = defaultDatabase) {
  const db = new DatabaseSync(database, { readOnly: true });
  try {
    requireValid(db.prepare('PRAGMA user_version').get().user_version === version,
      'Unsupported math method library schema');
    const { revision } = db.prepare('SELECT revision FROM metadata').get();
    const byId = db.prepare('SELECT card FROM methods WHERE id = ?');
    const lookup = db.prepare(`
      SELECT methods.card,
        highlight(method_search, 1, char(30), char(31)) || ' ' ||
        highlight(method_search, 2, char(30), char(31)) || ' ' ||
        highlight(method_search, 3, char(30), char(31)) || ' ' ||
        highlight(method_search, 4, char(30), char(31)) AS hits
      FROM method_search JOIN methods ON methods.id = method_search.id
      WHERE method_search MATCH ? AND (? IS NULL OR methods.domain = ?)
        AND (? IS NULL OR methods.level = ?)
      ORDER BY bm25(method_search, 0, 9, 7, 3, 1, .25), methods.id
      LIMIT ?
    `);
    const counts = db.prepare('SELECT level, domain, count(*) AS methods FROM methods GROUP BY level, domain ORDER BY level, domain');

    return {
      revision,
      get(id) {
        requireValid(typeof id === 'string' && slug.test(id), 'Invalid method id');
        const row = byId.get(id);
        return row ? JSON.parse(row.card) : null;
      },
      search({ query, domain = null, level = null, limit = 3 }) {
        if (typeof query !== 'string' || !query.trim() || query.length > 1600) {
          throw new MethodQueryError('Search must be 1–1,600 characters');
        }
        if (domain !== null && (typeof domain !== 'string' || domain.length > 60 || !slug.test(domain))) {
          throw new MethodQueryError('Invalid domain filter');
        }
        if (level !== null && !levels.has(level)) throw new MethodQueryError('Invalid level filter');
        if (!Number.isInteger(limit) || limit < 1 || limit > 8) {
          throw new MethodQueryError('Limit must be an integer from 1 to 8');
        }
        const cues = notationTerms(query);
        const words = [...new Set([...terms(cues.join(' ')), ...terms(query)])].slice(0, 32);
        if (!words.length) return [];
        const phrases = cues.filter(cue => cue.includes(' '));
        const quoted = items => [...new Set(items)].map(term => `"${term}"`).join(' OR ');
        const lexical = `{title aliases pattern topic} : (${quoted([...phrases, ...words])})`;
        const match = phrases.length ? `${lexical} OR explanation : (${quoted(phrases)})` : lexical;
        const needsCorroboration = cues.length === 0 && words.length >= 3;
        const rows = lookup.all(match, domain, domain, level, level, needsCorroboration ? 24 : limit);
        return rows.filter(row => {
          if (!needsCorroboration) return true;
          const highlighted = [...row.hits.matchAll(/\u001e([^\u001f]+)\u001f/gu)].map(hit => hit[1]).join(' ');
          return terms(highlighted).length >= 2;
        }).slice(0, limit).map(row => JSON.parse(row.card));
      },
      coverage() {
        return counts.all().map(row => ({ ...row }));
      },
      close() {
        db.close();
      },
    };
  } catch (error) {
    db.close();
    throw error;
  }
}
