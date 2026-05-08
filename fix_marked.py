import re

with open('index.html', 'r') as f:
    content = f.read()

# Replace the broken marked.setOptions with a version that works with marked v15
old_config = """marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(code, { language: lang }).value; } catch(e) {}
    }
    try { return hljs.highlightAuto(code).value; } catch(e) {}
    return code;
  },
  breaks: true,
  gfm: true
});"""

new_config = """// marked v15+ no longer supports highlight in setOptions
// Use marked.use() with markedHighlight extension, or do manual post-processing
marked.setOptions({
  breaks: true,
  gfm: true
});"""

content = content.replace(old_config, new_config)

with open('index.html', 'w') as f:
    f.write(content)

print("Fixed!")
