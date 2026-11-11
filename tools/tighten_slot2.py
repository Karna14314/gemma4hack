with open('docs/SLOT2_ORTHOGONAL_RESOURCE_PAPER.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect Table 2 and Table 3
import re
print("Initial whitespace:", len(text.split()))
print("Initial regex:", len(re.findall(r'[A-Za-z0-9]+', text)))
