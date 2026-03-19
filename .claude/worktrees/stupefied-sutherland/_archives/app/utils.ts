
export function normalizePath(path: string): string {
  if (!path) return '';
  let p = path.trim();
  
  // 1. Replace backslashes with forward slashes for consistency
  p = p.replace(/\\/g, '/');
  
  // 2. Collapse multiple slashes
  p = p.replace(/\/+/g, '/');
  
  // 3. Ensure strict leading slash for absolute simulation style
  if (!p.startsWith('/')) {
      p = '/' + p;
  }
  
  // 4. Remove trailing slash to avoid mismatch between "/folder" and "/folder/"
  // Exception: if path is just "/"
  if (p.length > 1 && p.endsWith('/')) {
      p = p.slice(0, -1);
  }
  
  return p;
}

export function globToRegex(pattern: string): RegExp {
    // 1. Escape characters that have special meaning in Regex but are literal in Glob
    let regexStr = pattern;
    
    // Escape all regex special characters first to treat them as literals
    regexStr = regexStr.replace(/[.+^${}()|[\]\\]/g, '\\$&');
    
    // Convert Glob Wildcards to Regex
    // * matches any character except path separator (but we are matching filenames so it matches everything)
    regexStr = regexStr.replace(/\*/g, '.*');
    
    // ? matches exactly one character
    regexStr = regexStr.replace(/\?/g, '.');
    
    // Handle curly braces {mp3,wav} -> (mp3|wav)
    regexStr = regexStr.replace(/\\\{([^}]+)\\\}/g, (match, content) => {
        const options = content.split(',');
        return `(${options.join('|')})`;
    });

    return new RegExp(`^${regexStr}$`, 'i'); // Case insensitive, full match anchor
}
