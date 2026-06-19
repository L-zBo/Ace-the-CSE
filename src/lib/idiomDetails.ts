export interface IdiomDetailExample {
  kind: 'dictionary' | 'question' | 'fallback';
  text: string;
  answerText?: string;
}

export interface IdiomDetailRecord {
  word: string;
  meaning: string;
  examples: IdiomDetailExample[];
}

interface IdiomDetailsPayload {
  generatedAt: string;
  count: number;
  items: Record<string, IdiomDetailRecord>;
}

let cachedPayload: IdiomDetailsPayload | null = null;
let pendingPayload: Promise<IdiomDetailsPayload> | null = null;

async function loadIdiomDetails(): Promise<IdiomDetailsPayload> {
  if (cachedPayload) return cachedPayload;
  if (!pendingPayload) {
    pendingPayload = fetch('/idioms-detail.json', {
      cache: 'force-cache',
    })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Failed to load idiom details: ${res.status}`);
        }
        return (await res.json()) as IdiomDetailsPayload;
      })
      .then((payload) => {
        cachedPayload = payload;
        return payload;
      })
      .catch((error) => {
        pendingPayload = null;
        throw error;
      });
  }
  return pendingPayload;
}

export async function getIdiomDetail(word: string): Promise<IdiomDetailRecord | null> {
  try {
    const payload = await loadIdiomDetails();
    return payload.items[word] ?? null;
  } catch {
    return null;
  }
}

