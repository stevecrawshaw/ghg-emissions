# One CLI command > Multiple tool calls

## Essential Commands

  1. Pattern Search:
    - rg -n "pattern" --glob '!node_modules/*' instead of multiple Grep calls
  2. File Finding:
    - fdfind filename or fdfind .ext directory instead of Glob tool
    - (Ubuntu uses 'fdfind' instead of 'fd' to avoid naming conflicts)
    - fd if on Windows
  3. File Preview:
    - batcat -n filepath for syntax-highlighted preview with line numbers
    - (Ubuntu uses 'batcat' instead of 'bat' to avoid naming conflicts)
    - bat if on Windows
  4. Bulk Refactoring:
    - rg -l "pattern" | xargs sed -i 's/old/new/g' for mass replacements
    - RESPECT WHITE SPACE in .py files
  5. Project Structure:
    - tree directories for quick overview
    - "cmd //c tree" if on Windows
  6. JSON Inspection:
    - jq '.key' file.json for quick JSON parsing
  7. Get help: Use e.g. rg --help

## The Game-Changing Pattern

# Find files → Pipe to xargs → Apply sed transformation

  rg -l "find_this" | xargs sed -i 's/replace_this/with_this/g'

  Efficiently replace dozens of Edit tool calls!

  Before reaching for Read/Edit/Glob tools, ask:

- Can rg find this pattern faster?
- Can fdfind locate these files quicker?
- Can sed fix all instances at once?
- Can jq extract this JSON data directly?
