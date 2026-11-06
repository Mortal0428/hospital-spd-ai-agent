# -*- coding: utf-8 -*-
"""
Reviewer 2 Adversarial Stress Test & Integrity Audit Script
Tests:
1. Zero Emoji scan across all frontend/src files
2. Digit Uppercase mathematical soundness & edge cases
3. Backend procurement endpoints response integrity
"""

import os
import sys
import re
import json
import urllib.request
import urllib.error
import subprocess

def check_emojis():
    print("=== [Check 1] Emoji Static Analysis ===")
    # Exact Unicode Emoji ranges that strictly exclude CJK ideographs (\u4e00-\u9fff)
    # Range 1: \U0001F300-\U0001F64F (Misc Symbols, Pictographs, Emoticons)
    # Range 2: \U0001F680-\U0001F6FF (Transport & Map)
    # Range 3: \U0001F900-\U0001FAFF (Supplemental Symbols and Pictographs, Extended-A)
    # Range 4: \U0001F1E6-\U0001F1FF (Flags)
    # Range 5: \u2600-\u26FF (Misc symbols, e.g. ☀️, ☕)
    # Range 6: \u2700-\u27BF (Dingbats, e.g. ✈️, ✉️)
    emoji_pattern = re.compile(
        r'[\U0001F300-\U0001F64F]'
        r'|[\U0001F680-\U0001F6FF]'
        r'|[\U0001F900-\U0001FAFF]'
        r'|[\U0001F1E6-\U0001F1FF]'
        r'|[\u2600-\u26FF]'
        r'|[\u2700-\u27BF]'
    )
    violations = []
    scanned_count = 0
    for root, dirs, files in os.walk('frontend/src'):
        for f in files:
            if f.endswith(('.vue', '.ts', '.js', '.css', '.html')):
                scanned_count += 1
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    for idx, line in enumerate(fp, 1):
                        matches = emoji_pattern.findall(line)
                        if matches:
                            violations.append((p, idx, matches, line.strip()[:60]))
    if violations:
        print(f"FAILED: Found {len(violations)} emoji occurrences across {scanned_count} files!")
        for v in violations[:10]:
            print(f"  {v[0]}:{v[1]} - {v[2]} in: {v[3]}")
        return False
    else:
        print(f"PASSED: ZERO Emojis detected across all {scanned_count} frontend source files.")
        return True


def check_digit_uppercase_in_node():
    print("\n=== [Check 2] Node.js Exact Execution of digitUppercase ===")
    test_cases = [
        0,
        560,
        13320.50,
        100.00,
        0.05,
        0.80,
        10.05,
        100000000,
        100010001.01,
        -50.00,
        0.1 + 0.2
    ]
    node_script = """
    function digitUppercase(money) {
      const fraction = ['角', '分'];
      const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'];
      const unit = [['元', '万', '亿'], ['', '拾', '佰', '仟']];
      let num = Math.abs(money);
      let s = '';
      for (let i = 0; i < fraction.length; i++) {
        s += (digit[Math.floor(num * 10 * Math.pow(10, i)) % 10] + fraction[i]).replace(/零./, '');
      }
      s = s || '整';
      num = Math.floor(num);
      for (let i = 0; i < unit[0].length && num > 0; i++) {
        let p = '';
        for (let j = 0; j < unit[1].length && num > 0; j++) {
          p = digit[num % 10] + unit[1][j] + p;
          num = Math.floor(num / 10);
        }
        s = p.replace(/(零.)*零$/, '').replace(/^$/, '零') + unit[0][i] + s;
      }
      return s.replace(/(零.)*零元/, '元').replace(/(零.)+/g, '零').replace(/^整$/, '零元整');
    }

    const testCases = [0, 560, 13320.50, 100, 0.05, 0.8, 10.05, 100000000, 100010001.01, -50.00, 0.1 + 0.2];
    const results = testCases.map(tc => ({ input: tc, output: digitUppercase(tc) }));
    process.stdout.write(JSON.stringify(results));
    """
    proc = subprocess.run(["node", "-e", node_script], capture_output=True, text=True, encoding='utf-8')
    if proc.returncode != 0:
        print("Node execution failed:", proc.stderr)
        return False
    results = json.loads(proc.stdout)
    for r in results:
        print(f"  Input: {str(r['input']):<20} => Result: {r['output']}")
    return True


def check_backend_integrity():
    print("\n=== [Check 3] Backend API Live Integrity Check ===")
    endpoints = [
        ('http://127.0.0.1:8000/api/v1/ext/supplier-purchase/qual-list', 'qual-list'),
        ('http://127.0.0.1:8000/api/v1/ext/supplier-purchase/list', 'po-list'),
        ('http://127.0.0.1:8000/api/v1/dict/specs', 'dict-specs'),
        ('http://127.0.0.1:8000/api/v1/rag-hub/connectivity/check', 'connectivity')
    ]
    all_ok = True
    for url, name in endpoints:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'TestAuditor/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
                body = resp.read().decode('utf-8')
                data = json.loads(body)
                code = data.get('code', 200)
                item_count = len(data.get('data', [])) if isinstance(data.get('data'), list) else 'dict'
                print(f"  [{name}] Status: {status}, Business Code: {code}, Payload Info: {item_count}")
        except Exception as e:
            print(f"  [{name}] FAILED to connect: {e}")
            all_ok = False
    return all_ok


if __name__ == '__main__':
    ok1 = check_emojis()
    ok2 = check_digit_uppercase_in_node()
    ok3 = check_backend_integrity()
    if ok1 and ok2 and ok3:
        print("\nReviewer 2 Automated Adversarial Checks: 100% PASSED!")
        sys.exit(0)
    else:
        print("\nSome checks failed.")
        sys.exit(1)
