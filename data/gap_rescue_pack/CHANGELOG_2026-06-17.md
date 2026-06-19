# 2026-06-17 migration changelog

This file records the recent project changes that matter when copying `data/gap_rescue_pack/` to another machine.

## Data rescue status

- Original unanswerable Xingce questions: 58.
- Confirmed rescued questions: 8.
- Current unanswerable Xingce questions: 50.
- Shenlun material normalization: 507 JSON files copied into the migration pack; current material coverage is 512 / 652 records.
- Audit command: `python scripts/d17_list_unanswerable.py`.
- Latest audit snapshot: `data/gap_rescue_pack/snapshots/d17_unanswerable_after_2026-06-17.json`.

Confirmed rescued data:

- `src/data/xingce/yanyu/provincial_hunan_2020.json`
  - rescued `016`
  - answer: `C`
- `src/data/xingce/changshi/provincial_yunnan_2023.json`
  - rescued `055`
  - answer: `B`
- `src/data/xingce/yanyu/provincial_ningxia_2024.json`
  - rescued `052`
  - answer: `C`
  - source chain: complete PDF question text + Henan Huatu same-question analysis
- `src/data/xingce/yanyu/provincial_ningxia_2024.json`
  - rescued `053`
  - answer: `D`
  - source chain: complete PDF question text + Xingguang same-question analysis + original article cross-check
- `src/data/xingce/yanyu/provincial_ningxia_2024.json`
  - rescued `054`
  - answer: `B`
  - source chain: complete PDF question text + Henan Huatu same-question analysis
- `src/data/xingce/yanyu/provincial_ningxia_2024.json`
  - rescued `055`
  - answer: `D`
  - source chain: complete PDF question text + Henan Huatu/Xingguang same-question analysis + original article cross-check
- `src/data/xingce/yanyu/provincial_gansu_2024.json`
  - rescued `054`
  - answer: `D`
  - source chain: Henan/Ningxia 2024 same-question text + Xingguang same-question analysis + Jinbiaochi option-order cross-check
- `src/data/xingce/changshi/institution_2022_b.json`
  - rescued `034`
  - answer: `B`
  - source chain: Huatu B-class question-number page + Houzhi/Kaosydw full same-question text + Xinhua `Physicians Law` article cross-check

Correction recorded:

- `src/data/xingce/changshi/provincial_jilin_2024.json`
  - previous attempted rescue for `020` was invalidated.
  - reason: source question was actually Jilin 2024 question `079`, not `020`.
  - current state keeps `017-020` as unanswerable.
- `src/data/xingce/shuliang/institution_2022_c.json`
  - old explanation for `050` incorrectly described it as a possible data-analysis question.
  - corrected explanation: Huatu C-class estimate page locates it as a masked quantity question beginning with `工厂举办生产技能大赛`, with options `A.2 B.3 C.4 D.5`.
  - current state still keeps `050` as unanswerable because the key conditions are masked and no complete answer chain exists.

## Files intended for data migration

Copy the whole folder:

```powershell
data/gap_rescue_pack
```

On the target machine, from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File data/gap_rescue_pack/apply_gap_rescue.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File data/gap_rescue_pack/apply_gap_rescue.ps1
python scripts/d17_list_unanswerable.py
```

Expected post-migration result: 50 unanswerable Xingce questions.

For Shenlun material normalization, also run:

```powershell
python scripts/audit_shenlun_material.py
```

Expected post-migration Shenlun result: `has material = 512`, `missing material = 140`.

New source evidence stored in this pack:

- `data/gap_rescue_pack/sources/ningxia_2024_xingce_source.pdf`
- `data/gap_rescue_pack/sources/ningxia_2024_xingce_source.txt`
- `data/gap_rescue_pack/sources/ningxia_2024_xingce_lasee.docx`
- `data/gap_rescue_pack/sources/ningxia_2024_xingce_lasee.txt`
- `data/gap_rescue_pack/sources/ningxia_2024_yanyu_052_055_sources.md`
- `data/gap_rescue_pack/sources/gansu_2024_yanyu_054_sources.md`
- `data/gap_rescue_pack/sources/institution_2022_b_034_sources.md`
- `data/gap_rescue_pack/sources/unresolved_xingce_2026-06-17.md`
- `data/gap_rescue_pack/sources/beijing_2023_xingguang.pdf`
- `data/gap_rescue_pack/sources/beijing_2023_xingguang.txt`
- `data/gap_rescue_pack/sources/gansu_2024_xingguang.pdf`
- `data/gap_rescue_pack/sources/gansu_2024_xingguang.txt`
- `data/gap_rescue_pack/sources/jilin_2024_xingguang.pdf`
- `data/gap_rescue_pack/sources/jilin_2024_xingguang.txt`
- `data/gap_rescue_pack/sources/neimenggu_2023_xingguang.pdf`
- `data/gap_rescue_pack/sources/neimenggu_2023_xingguang.txt`
- `data/gap_rescue_pack/sources/shenlun_material_normalization_2026-06-18.md`
- `data/gap_rescue_pack/sources/shenlun_material_audit_after_2026-06-18.json`
- `data/gap_rescue_pack/sources/shenlun_material_normalization_preview_2026-06-18.json`

## Shenlun material normalization on 2026-06-18

The project previously had only 5 / 652 Shenlun records with a standalone `material` field. Most records stored the full exam paper in `content`, which made the frontend show long mixed text and left the material audit nearly empty.

This round added `scripts/normalize_shenlun_material.py` and used it to split existing Shenlun `content` text only. It did not fabricate new exam material, prompts, answers, or explanations.

Changes applied:

- `material` now contains the extracted given-material section.
- `content` now keeps title/notice plus the answer prompts, with extracted material removed.
- changed records include `meta.materialRescuedBy = "D23-content-normalization"` and `meta.materialSource = "existing content field"`.
- 507 changed Shenlun JSON files are mirrored under `data/gap_rescue_pack/files/src/data/shenlun/`.
- `apply_gap_rescue.ps1` now copies every file under `files/` recursively, so the target machine does not need a hand-maintained file whitelist.

Post-normalization audit:

- total Shenlun records: 652.
- has `material`: 512.
- missing `material`: 140.
- category breakdown: `duice` 9 / 16, `fenxi` 1 / 1, `guanche` 92 / 170, `guina` 1 / 1, `xiezuo` 409 / 464.

Remaining 140 were not hard-filled because their current text lacks stable material/prompt boundaries or appears truncated before作答要求. Continue only by locating the original PDF/web source and verifying the full卷面.

## Continued unresolved search on 2026-06-17

After the 8 confirmed rescues, the remaining 50 Xingce gaps were searched again. No additional question was written because the available public sources still mark the target questions as missing, default-A placeholders, or masked:

- Xinjiang 2023: AIPTA, Lasee, Yeyulingfeng, Gwyksw and local cache all mark `014-025`, `050`, and `060-065` as missing/default placeholders. Newdu's public pagination does not expose a complete source chain for these gaps.
- Beijing 2023: exam2 PDF, Kaosheng notes and Xingguang PDF mark large blocks including `017-027` and `111` as missing/default placeholders.
- Jilin 2024: AIPTA and Xingguang PDF mark `017-020`, `042-045`, `065-068`, and `077` as missing/default placeholders.
- Gansu 2024: AIPTA, a later Book118 upload and Xingguang PDF still mark `069-070`, `078`, and `087` as missing/default placeholders.
- Neimenggu 2023: AIPTA, local evidence and Xingguang PDF mark `018` as missing/default placeholder.
- Institution 2022 C: Huatu masks the critical conditions for `050`; Houzhi/Kaosydw-style public pages mark it as missing. The project explanation was corrected to identify it as a masked quantity question, not a data-analysis question.

These findings are recorded in `rescue_register.json` under `investigatedUnresolvedGroups` and in `sources/unresolved_xingce_2026-06-17.md`.

## Paused Xingce follow-up on 2026-06-19

- Re-ran `python scripts/d17_list_unanswerable.py`; Xingce remains at `total_unanswerable=50`.
- Rechecked the remaining groups with local JSON neighbors and external search caches. The remaining gaps are still:
  - Xinjiang 2023: 19 questions.
  - Jilin 2024: 13 questions.
  - Beijing 2023: 12 questions.
  - Gansu 2024: 4 questions.
  - Neimenggu 2023: 1 question.
  - Institution 2022 C: 1 question.
- Added partial raw search cache in `sources/followup_search_2026-06-19/`. This cache was stopped after the user asked to settle the record; treat it as next-round search context, not as verified data.
- No new question was written into `src/data/xingce/` because no candidate source provided the required complete chain: stem, options, answer, and matching source evidence.
- Next machine should resume from `sources/unresolved_xingce_2026-06-19.md` and `sources/followup_search_2026-06-19/`. Keep the rule: default `A`, `暂缺`, `题目正在征集`, and OCR-failed placeholders are not real question-bank data.

## Recent project maintenance outside pure data rescue

These changes were made in the source project and are not applied by `apply_gap_rescue.ps1`:

- Root cleanup:
  - moved temporary PNG screenshots out of the project root.
  - moved old audit outputs out of the project root.
  - moved one-off `test_homepage.py` out of the project root.
  - moved local Claude/context export folder `F--VsCodeproject-Ace-the-CSE/` out of the project root.
  - removed generated caches: `.next/`, `out/`, `.pytest_cache/`, `__pycache__/`, `tsconfig.tsbuildinfo`.
- Startup/debug context:
  - `start.bat` remains the user startup entry and must not be moved.
  - local Next cache was removed to avoid stale Turbopack/build artifacts.
  - `start.bat` was validated directly on 2026-06-18. It runs `npm run dev`, which resolves to `next dev --webpack`; dev server became ready on `http://localhost:3000`.
  - Browser verification after startup showed homepage title `Ace the CSE — 公务员考试学习平台` and 0 console errors / 0 console warnings after fixing the LCP image warning.
  - `npm run build` still times out in this workspace because `src/app/practice/[questionId]/page.tsx` statically expands every question through `generateStaticParams()`; with 20k+ questions this static export path is too heavy on the current F: drive. Dev startup is unaffected.
- Tooling cleanup:
  - `.gitignore` now ignores local temporary screenshots, local context exports, generated cleanup archive folders, and Android static export output.
  - `eslint.config.mjs` now ignores generated Android static assets and `data/tmp_*` evidence/cache files.
- Lint cleanup:
  - `npm run lint` currently exits with 0 warnings and 0 errors.
  - Fixed the remaining homepage LCP image warning by marking the above-the-fold `/img/decorative/seal-bo.svg` image as eager/priority.
  - Fixed warning sources in:
    - `src/app/error.tsx`
    - `src/app/exam/[examId]/ExamSessionClient.tsx`
    - `src/app/page.tsx`
    - `src/app/plan/page.tsx`
    - `src/app/practice/[questionId]/components/EssayAnswerArea.tsx`
    - `src/components/weather/BackgroundLayer.tsx`
    - `src/stores/idiomStore.ts`
    - `src/stores/statsStore.ts`
    - `src/types/user.ts`

## Review notes for another machine

- Do not treat placeholder/default `A` answers from public pages as real answer data.
- Do not rescue a question unless stem, options, answer, and source evidence are all verified.
- If the target machine only needs the data rescue, use `apply_gap_rescue.ps1`.
- If the target machine also wants the cleanup/tooling fixes, compare the Git commit that includes this changelog.
- For Ningxia 2024 yanyu `052-055`, do not use the `lasee` default-A placeholder. The migration pack records why `052` maps to `C` under this project's option order.
