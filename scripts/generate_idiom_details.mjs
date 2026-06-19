import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..');
const IDIOMS_FILE = path.join(ROOT, 'src', 'data', 'idioms_raw.json');
const YANYU_DIR = path.join(ROOT, 'src', 'data', 'xingce', 'yanyu');
const OUTPUT_FILE = path.join(ROOT, 'public', 'idioms-detail.json');
const DICT_URL = 'https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/idiom.json';

function normalize(text) {
  return String(text ?? '')
    .replace(/\u3000/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function cleanOptionText(text) {
  return normalize(text)
    .replace(/^[A-Da-d][．.、)）\s]*/, '')
    .replace(/[“”"'《》【】()（）]/g, '')
    .trim();
}

function splitTokens(text) {
  return cleanOptionText(text)
    .split(/[、，,；;\/\s]+/)
    .map((token) => token.replace(/[。！？!?：:·]/g, '').trim())
    .filter(Boolean);
}

function extractMeaningFromText(word, text) {
  const source = normalize(text);
  if (!source || !source.includes(word)) return '';

  const markers = ['意思是', '意为', '指', '比喻', '形容', '用于', '表示', '用来'];
  const around = source.slice(Math.max(0, source.indexOf(word) - 18), source.indexOf(word) + 160);

  for (const marker of markers) {
    const idx = around.indexOf(marker);
    if (idx === -1) continue;
    let candidate = around.slice(idx + marker.length);
    candidate = candidate.replace(/^[：:，,、\s]*/, '');
    const stop = candidate.search(/[。；;！？?!\n\r]/);
    if (stop >= 0) candidate = candidate.slice(0, stop);
    candidate = candidate.trim();
    if (
      candidate.length >= 2 &&
      candidate.length <= 120 &&
      !/正确答案|本题|选项|排除|保留|验证|代入|第一步|第二步|A项|B项|C项|D项/.test(candidate)
    ) {
      return candidate;
    }
  }

  return '';
}

function summarizeQuestionText(text, maxLen = 180) {
  let value = normalize(text).replace(/\s*（.*?）\s*/g, ' ');
  value = value
    .replace(/依次填入(?:画|划)?横线(?:部分|处)?最恰当的一项是[:：]?$/g, '')
    .replace(/填入(?:画|划)?横线(?:部分|处)?最恰当的一项是[:：]?$/g, '')
    .replace(/下列.*?最恰当的一项是[:：]?$/g, '')
    .trim();
  if (value.length <= maxLen) return value;
  return `${value.slice(0, maxLen - 1).trim()}…`;
}

function resolveAnswerLabels(answer) {
  if (Array.isArray(answer)) return answer.map((item) => String(item).trim()).filter(Boolean);
  return String(answer ?? '')
    .split(/[、,\/\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function getCorrectOption(question) {
  const labels = resolveAnswerLabels(question.answer);
  if (!Array.isArray(question.options) || labels.length === 0) return '';
  const selected = question.options.filter((opt) => labels.includes(String(opt.label).trim()));
  if (!selected.length) return '';
  return selected.map((opt) => cleanOptionText(opt.content)).filter(Boolean).join(' / ');
}

function isWordToken(token, rawWordSet) {
  return rawWordSet.has(token);
}

async function loadQuestions() {
  const files = await readdir(YANYU_DIR, { withFileTypes: true });
  const questions = [];
  for (const entry of files) {
    if (!entry.isFile() || !entry.name.endsWith('.json')) continue;
    const fullPath = path.join(YANYU_DIR, entry.name);
    const data = JSON.parse(await readFile(fullPath, 'utf8'));
    for (const item of data) questions.push(item);
  }
  return questions;
}

async function loadDictionary() {
  const response = await fetch(DICT_URL);
  if (!response.ok) {
    throw new Error(`Failed to fetch dictionary: ${response.status}`);
  }
  const data = await response.json();
  const map = new Map();
  for (const item of data) {
    if (item && typeof item === 'object' && item.word) {
      map.set(item.word, item);
    }
  }
  return map;
}

async function main() {
  const idioms = JSON.parse(await readFile(IDIOMS_FILE, 'utf8'));
  const questions = await loadQuestions();
  const dictMap = await loadDictionary();
  const rawWordSet = new Set(idioms.map((item) => item.word));

  const meaningCandidates = new Map();
  const questionExamples = new Map();
  const sourceQuestionsByWord = new Map();

  for (const idiom of idioms) {
    sourceQuestionsByWord.set(idiom.word, []);
    meaningCandidates.set(idiom.word, []);
    questionExamples.set(idiom.word, []);
  }

  for (const question of questions) {
    const allOptionText = Array.isArray(question.options)
      ? question.options.map((opt) => cleanOptionText(opt.content)).join(' / ')
      : '';
    const tokens = splitTokens(allOptionText);
    const correctText = getCorrectOption(question);
    const correctTokens = splitTokens(correctText);
    const contentText = summarizeQuestionText(question.content, 180);

    for (const token of tokens) {
      if (!isWordToken(token, rawWordSet)) continue;
      sourceQuestionsByWord.get(token)?.push(question.id);
      const candidate = extractMeaningFromText(token, question.explanation);
      if (candidate) meaningCandidates.get(token)?.push(candidate);
    }

    for (const token of correctTokens) {
      if (!isWordToken(token, rawWordSet)) continue;
      const list = questionExamples.get(token);
      if (!list || list.length >= 3) continue;
      list.push({
        kind: 'question',
        text: contentText,
      });
    }
  }

  const items = {};
  for (const idiom of idioms) {
    const dict = dictMap.get(idiom.word);
    const candidates = meaningCandidates.get(idiom.word) ?? [];
    const meaning = dict?.explanation
      ? normalize(dict.explanation)
      : candidates.sort((a, b) => a.length - b.length)[0] ?? '';

    const examples = [];
    const seen = new Set();
    for (const example of questionExamples.get(idiom.word) ?? []) {
      const key = `${example.text}|${example.answerText ?? ''}`;
      if (seen.has(key)) continue;
      seen.add(key);
      examples.push(example);
    }

    const dictExample = normalize(dict?.example ?? '');
    if (dictExample && dictExample !== '无' && examples.length < 3) {
      examples.push({
        kind: 'fallback',
        text: dictExample,
      });
    }

    if (!meaning && idiom.originalExplanation) {
      const fallback = extractMeaningFromText(idiom.word, idiom.originalExplanation);
      if (fallback) {
        items[idiom.word] = {
          word: idiom.word,
          meaning: fallback,
          examples,
        };
        continue;
      }
    }

    items[idiom.word] = {
      word: idiom.word,
      meaning,
      examples,
    };
  }

  const payload = {
    generatedAt: new Date().toISOString(),
    count: idioms.length,
    items,
  };

  await writeFile(OUTPUT_FILE, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
  console.log(`Wrote ${path.relative(ROOT, OUTPUT_FILE)} (${idioms.length} idioms)`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
