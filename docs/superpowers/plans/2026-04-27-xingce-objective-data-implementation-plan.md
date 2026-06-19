# 行测客观题库100%闭环实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立国考行测客观题的规则基线、统一审计器、逐年修复流水线，并让模拟考试页面只消费审计通过的完整卷。

**Architecture:** 先用规则文件把“每年每卷应该长什么样”钉死，再用统一审计器扫描`src/data/xingce/`产出异常清单和Manifest，最后按`2025→2024→2023→...`顺序逐年清零异常，并在前端只展示`ready=true`的卷。实施过程中先做不触碰脏前端文件的脚本和规则层，再收口页面与类型修复。

**Tech Stack:** Python3、JSON、Next.js16、React19、TypeScript、Node.js、PowerShell、Git

---

## 文件职责映射

- `scripts/config/xingce_exam_specs.json`
  记录国考行测每年每卷的标准总题数与五大模块分布。
- `scripts/config/xingce_option_exceptions.json`
  记录合法非4选项题、图片依赖题等审计例外。
- `scripts/audit_xingce.py`
  统一扫描`src/data/xingce/`，产出结构化异常清单与Manifest。
- `src/data/meta/xingce_exam_manifest.json`
  前端唯一可信的卷完整度来源。
- `tests/scripts/test_xingce_specs.py`
  校验规则文件格式和关键年份标准值。
- `tests/scripts/test_audit_xingce.py`
  校验审计器在夹具数据上的异常识别和Manifest输出。
- `scripts/auto_fix_options.py`
  收敛为共享的按题号补选项入口，优先覆盖2025年国考文本题。
- `src/app/exam/page.tsx`
  改为读取Manifest而不是写死2024三套卷。
- `src/app/practice/page.tsx`
  统一`ExamLevel`类型并与题库筛选一致。
- `src/app/practice/[questionId]/page.tsx`
  维持题目详情入口稳定。
- `src/app/practice/[questionId]/QuestionPageClient.tsx`
  恢复当前丢失文件，保证题目详情页可编译。

## Task 1：建立国考行测规则基线

**Files:**
- Create: `scripts/config/xingce_exam_specs.json`
- Create: `scripts/config/xingce_option_exceptions.json`
- Create: `tests/scripts/test_xingce_specs.py`

- [ ] **Step 1: 写规则层失败测试**

```python
import json
import unittest
from pathlib import Path


class XingceSpecTests(unittest.TestCase):
    def test_national_2025_specs_exist(self):
        path = Path("scripts/config/xingce_exam_specs.json")
        self.assertTrue(path.exists())

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["national"]["2025"]["fushengjia"]["total"], 135)
        self.assertEqual(data["national"]["2025"]["dishi"]["modules"]["shuliang"], 10)
        self.assertEqual(data["national"]["2025"]["xingzhengzhifa"]["modules"]["ziliao"], 15)

    def test_national_2016_and_2023_specs_exist(self):
        data = json.loads(Path("scripts/config/xingce_exam_specs.json").read_text(encoding="utf-8"))
        self.assertEqual(data["national"]["2016"]["dishi"]["total"], 130)
        self.assertEqual(data["national"]["2023"]["fushengjia"]["total"], 135)

    def test_option_exceptions_file_exists(self):
        path = Path("scripts/config/xingce_option_exceptions.json")
        self.assertTrue(path.exists())
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.scripts.test_xingce_specs -v`

Expected: FAIL，提示规则文件不存在。

- [ ] **Step 3: 写最小规则文件实现**

```json
{
  "national": {
    "2025": {
      "fushengjia": { "total": 135, "modules": { "changshi": 20, "yanyu": 40, "shuliang": 15, "panduan": 40, "ziliao": 20 } },
      "dishi": { "total": 130, "modules": { "changshi": 20, "yanyu": 40, "shuliang": 10, "panduan": 40, "ziliao": 20 } },
      "xingzhengzhifa": { "total": 130, "modules": { "changshi": 20, "yanyu": 40, "shuliang": 15, "panduan": 40, "ziliao": 15 } }
    }
  }
}
```

`xingce_option_exceptions.json`先以最小结构落地：

```json
{
  "national": {}
}
```

然后把2015-2025所有国考卷标准补齐。

- [ ] **Step 4: 重新运行测试并确认通过**

Run: `python -m unittest tests.scripts.test_xingce_specs -v`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/config/xingce_exam_specs.json scripts/config/xingce_option_exceptions.json tests/scripts/test_xingce_specs.py
git commit -m "feat(data): 建立国考行测规则基线"
git push
```

## Task 2：实现统一审计器和Manifest生成

**Files:**
- Create: `scripts/audit_xingce.py`
- Create: `tests/scripts/test_audit_xingce.py`
- Create: `src/data/meta/xingce_exam_manifest.json`

- [ ] **Step 1: 写审计器失败测试**

```python
import json
import subprocess
import unittest
from pathlib import Path


class AuditXingceTests(unittest.TestCase):
    def test_audit_generates_manifest(self):
        result = subprocess.run(
            ["python", "scripts/audit_xingce.py", "--source", "national", "--write-manifest"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        manifest = Path("src/data/meta/xingce_exam_manifest.json")
        self.assertTrue(manifest.exists())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertIn("generatedAt", data)
        self.assertIn("exams", data)
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.scripts.test_audit_xingce -v`

Expected: FAIL，提示`audit_xingce.py`不存在或Manifest未生成。

- [ ] **Step 3: 写最小审计器实现**

```python
def main():
    summary = {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "exams": []
    }
    Path("src/data/meta").mkdir(parents=True, exist_ok=True)
    Path("src/data/meta/xingce_exam_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

然后逐步补上：

1. 遍历`src/data/xingce/*/national_*.json`
2. 依据规则文件聚合题量与模块分布
3. 识别缺号、重号、选项不全、字段不一致
4. 生成`ready`与`issues`

- [ ] **Step 4: 重新运行测试并确认通过**

Run: `python -m unittest tests.scripts.test_audit_xingce -v`

Expected: PASS

- [ ] **Step 5: 增加一次真实数据审计运行**

Run: `python scripts/audit_xingce.py --source national --write-manifest --report-json tmp/national_audit.json`

Expected: 生成真实国考审计结果和Manifest。

- [ ] **Step 6: 提交**

```bash
git add scripts/audit_xingce.py tests/scripts/test_audit_xingce.py src/data/meta/xingce_exam_manifest.json tmp/national_audit.json
git commit -m "feat(data): 新增统一行测审计器与Manifest"
git push
```

## Task 3：修复2025年国考行测到100%

**Files:**
- Modify: `scripts/auto_fix_options.py`
- Modify: `scripts/extract_missing_options.py`
- Modify: `scripts/extract_questions.py`
- Modify: `src/data/xingce/changshi/national_2025_*.json`
- Modify: `src/data/xingce/yanyu/national_2025_*.json`
- Modify: `src/data/xingce/shuliang/national_2025_*.json`
- Modify: `src/data/xingce/panduan/national_2025_*.json`
- Modify: `src/data/xingce/ziliao/national_2025_*.json`
- Modify: `scripts/config/xingce_option_exceptions.json`

- [ ] **Step 1: 写2025年审计失败断言**

```python
import json
import subprocess
import unittest
from pathlib import Path


class Audit2025ZeroIssueTests(unittest.TestCase):
    def test_national_2025_has_zero_issues(self):
        result = subprocess.run(
            ["python", "scripts/audit_xingce.py", "--source", "national", "--year", "2025", "--report-json", "tmp/national_2025.json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        report = json.loads(Path("tmp/national_2025.json").read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["issueCount"], 0)
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.scripts.test_audit_2025_zero -v`

Expected: FAIL，当前2025仍有21道选项不完整。

- [ ] **Step 3: 实现共享补选项逻辑并修2025数据**

重点动作：

1. 让`auto_fix_options.py`支持批量读取2025异常清单，而不是只写死8道题。
2. 对失败题保留人工核验页码与上下文。
3. 审核所有2025文本题是否达到4选项；合法例外登记到`xingce_option_exceptions.json`。
4. 修完后重新生成Manifest。

- [ ] **Step 4: 重新运行2025审计并确认通过**

Run: `python scripts/audit_xingce.py --source national --year 2025 --write-manifest --report-json tmp/national_2025.json`

Expected: `issueCount = 0`

- [ ] **Step 5: 提交**

```bash
git add scripts/auto_fix_options.py scripts/extract_missing_options.py scripts/extract_questions.py scripts/config/xingce_option_exceptions.json src/data/xingce/changshi/national_2025_*.json src/data/xingce/yanyu/national_2025_*.json src/data/xingce/shuliang/national_2025_*.json src/data/xingce/panduan/national_2025_*.json src/data/xingce/ziliao/national_2025_*.json src/data/meta/xingce_exam_manifest.json tmp/national_2025.json
git commit -m "fix(data): 修复2025国考行测到100%"
git push
```

## Task 4：修复2024-2023年国考行测异常

**Files:**
- Modify: `src/data/xingce/*/national_2024_*.json`
- Modify: `src/data/xingce/*/national_2023_*.json`
- Modify: `scripts/extract_specific_questions.py`
- Modify: `scripts/batch_fix_2022_2015.py`
- Modify: `scripts/audit_xingce.py`

- [ ] **Step 1: 写2024-2023年失败断言**

```python
for year in ("2024", "2023"):
    result = subprocess.run(
        ["python", "scripts/audit_xingce.py", "--source", "national", "--year", year, "--report-json", f"tmp/national_{year}.json"],
        capture_output=True,
        text=True,
        check=False,
    )
    self.assertEqual(result.returncode, 0, msg=result.stderr)
    report = json.loads(Path(f"tmp/national_{year}.json").read_text(encoding="utf-8"))
    self.assertEqual(report["summary"]["issueCount"], 0)
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.scripts.test_audit_recent_years_zero -v`

Expected: FAIL，2023至少存在`dishi=129`、`fushengjia=134`异常。

- [ ] **Step 3: 按年份修复并复跑审计**

顺序：

1. 2024三卷
2. 2023三卷

每修完一年必须执行：

Run: `python scripts/audit_xingce.py --source national --year <year> --write-manifest --report-json tmp/national_<year>.json`

Expected: `issueCount = 0`

- [ ] **Step 4: 提交**

```bash
git add src/data/xingce/*/national_2024_*.json src/data/xingce/*/national_2023_*.json scripts/extract_specific_questions.py scripts/batch_fix_2022_2015.py scripts/audit_xingce.py src/data/meta/xingce_exam_manifest.json tmp/national_2024.json tmp/national_2023.json
git commit -m "fix(data): 修复2024和2023国考行测异常"
git push
```

## Task 5：修复2022-2015年国考行测剩余异常并接入前端

**Files:**
- Modify: `src/data/xingce/*/national_2022_*.json`
- Modify: `src/data/xingce/*/national_2021_*.json`
- Modify: `src/data/xingce/*/national_2020_*.json`
- Modify: `src/data/xingce/*/national_2019_*.json`
- Modify: `src/data/xingce/*/national_2018_*.json`
- Modify: `src/data/xingce/*/national_2017_*.json`
- Modify: `src/data/xingce/*/national_2016_*.json`
- Modify: `src/data/xingce/*/national_2015_*.json`
- Modify: `src/lib/questionLoader.ts`
- Modify: `src/types/question.ts`
- Modify: `src/app/exam/page.tsx`
- Modify: `src/app/practice/page.tsx`
- Modify: `src/app/practice/[questionId]/page.tsx`
- Modify: `src/app/practice/[questionId]/QuestionPageClient.tsx`

- [ ] **Step 1: 写全量国考零异常失败断言**

```python
result = subprocess.run(
    ["python", "scripts/audit_xingce.py", "--source", "national", "--report-json", "tmp/national_full.json", "--write-manifest"],
    capture_output=True,
    text=True,
    check=False,
)
self.assertEqual(result.returncode, 0, msg=result.stderr)
report = json.loads(Path("tmp/national_full.json").read_text(encoding="utf-8"))
self.assertEqual(report["summary"]["issueCount"], 0)
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m unittest tests.scripts.test_audit_national_zero -v`

Expected: FAIL，至少2016、2019、2023等年份仍有异常。

- [ ] **Step 3: 逐年清零2015-2022异常**

每修完一年运行：

Run: `python scripts/audit_xingce.py --source national --year <year> --report-json tmp/national_<year>.json`

Expected: `issueCount = 0`

- [ ] **Step 4: 将前端切换到Manifest**

实现目标：

1. `src/app/exam/page.tsx`不再写死2024。
2. `src/app/practice/page.tsx`统一`ExamLevel`类型。
3. 恢复`QuestionPageClient.tsx`，让`tsc`可通过。

- [ ] **Step 5: 跑最终验证**

Run: `python scripts/audit_xingce.py --source national --report-json tmp/national_full.json --write-manifest`

Expected: `issueCount = 0`

Run: `npx.cmd tsc --noEmit --pretty false`

Expected: 与本阶段相关的题库/页面不再报错。

- [ ] **Step 6: 提交**

```bash
git add src/data/xingce/*/national_2022_*.json src/data/xingce/*/national_2021_*.json src/data/xingce/*/national_2020_*.json src/data/xingce/*/national_2019_*.json src/data/xingce/*/national_2018_*.json src/data/xingce/*/national_2017_*.json src/data/xingce/*/national_2016_*.json src/data/xingce/*/national_2015_*.json src/lib/questionLoader.ts src/types/question.ts src/app/exam/page.tsx src/app/practice/page.tsx src/app/practice/[questionId]/page.tsx src/app/practice/[questionId]/QuestionPageClient.tsx src/data/meta/xingce_exam_manifest.json tmp/national_full.json
git commit -m "feat(data): 完成国考行测100%闭环并切换前端口径"
git push
```

## 计划自检

- 设计范围只覆盖行测客观题，未混入申论。
- 规则文件、审计器、逐年修复、前端Manifest接入都有明确任务覆盖。
- 每个任务都包含失败验证、最小实现、再次验证和提交步骤。
- 由于当前工作区已有未提交前端改动，执行时必须先做脚本和规则层任务，再在修改前端文件前重新审查差异，避免误覆盖他人改动。
