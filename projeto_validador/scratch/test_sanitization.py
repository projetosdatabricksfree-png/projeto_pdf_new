import re

def test_sanitization(file_path):
    if re.search(r'[;&|`${}]', file_path):
        return False, "Rejected (Suspicious)"
    return True, "Accepted (Safe)"

test_cases = [
    ("Tabuleiro (490 x 245) [FINAL].pdf", True),
    ("Job_123_Rev(2).pdf", True),
    ("Job; rm -rf /.pdf", False),
    ("Job $(whoami).pdf", False),
    ("Job | cat /etc/passwd.pdf", False),
]

for path, expected in test_cases:
    res, msg = test_sanitization(path)
    status = "PASS" if res == expected else "FAIL"
    print(f"[{status}] Path: {path:40} | Result: {msg}")
