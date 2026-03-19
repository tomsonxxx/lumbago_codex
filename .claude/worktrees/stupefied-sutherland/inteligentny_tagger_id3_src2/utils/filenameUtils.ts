import { ID3Tags } from '../types';

export const generatePath = (
  pattern: string,
  tags: ID3Tags,
  originalFilename: string
): string => {
  const extension = originalFilename.split('.').pop() || 'mp3';
  
  // Get the most complete set of tags available
  const effectiveTags = { ...tags };
  
  const trackNumber = effectiveTags.trackNumber 
    ? String(effectiveTags.trackNumber).split('/')[0].trim().padStart(2, '0') 
    : '00';

  const discNumber = effectiveTags.discNumber
    ? String(effectiveTags.discNumber).split('/')[0].trim()
    : '1';

  let newName = pattern
    .replace(/\[artist\]/gi, effectiveTags.artist || 'Unknown Artist')
    .replace(/\[albumArtist\]/gi, effectiveTags.albumArtist || effectiveTags.artist || 'Unknown Artist')
    .replace(/\[album\]/gi, effectiveTags.album || 'Unknown Album')
    .replace(/\[title\]/gi, effectiveTags.title || 'Unknown Title')
    .replace(/\[year\]/gi, effectiveTags.year || '0000')
    .replace(/\[genre\]/gi, effectiveTags.genre || 'Unknown Genre')
    .replace(/\[trackNumber\]/gi, trackNumber)
    .replace(/\[discNumber\]/gi, discNumber)
    .replace(/\[composer\]/gi, effectiveTags.composer || 'Unknown Composer')
    .replace(/\[copyright\]/gi, effectiveTags.copyright || '')
    .replace(/\[originalArtist\]/gi, effectiveTags.originalArtist || '')
    .replace(/\[encodedBy\]/gi, effectiveTags.encodedBy || '');


  // Sanitize each path component individually to handle subdirectories correctly.
  const sanitizedParts = newName.split('/').map(part => {
    // Trim leading/trailing whitespace
    let sanitizedPart = part.trim();
    // Replace multiple spaces with a single space
    sanitizedPart = sanitizedPart.replace(/\s+/g, ' ');
    // Replace invalid characters for filenames/paths.
    // This regex handles both Windows and Unix-like systems.
    sanitizedPart = sanitizedPart.replace(/[\\?%*:|"<>]/g, '-');
    // Remove leading dots that might hide files on Unix-like systems.
    sanitizedPart = sanitizedPart.replace(/^\.+/, '');
    // A part should not be empty, if it is (e.g. from "//"), replace with an underscore.
    return sanitizedPart || '_';
  });
  
  // Remove empty parts that might result from trailing slashes or empty placeholders
  const finalParts = sanitizedParts.filter(p => p && p !== '_');

  return finalParts.join('/') + `.${extension}`;
};