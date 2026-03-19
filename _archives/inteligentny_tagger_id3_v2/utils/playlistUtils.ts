/**
 * Handles reordering an array of track IDs.
 * @param list The original array of track IDs.
 * @param startIndex The starting index of the item to move.
 * @param endIndex The ending index where the item should be moved.
 * @returns A new array with the item moved to the new position.
 */
export const handleTrackReorder = (
  list: string[],
  startIndex: number,
  endIndex: number
): string[] => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);

  return result;
};
