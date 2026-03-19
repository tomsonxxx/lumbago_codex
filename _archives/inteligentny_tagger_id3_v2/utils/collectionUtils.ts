import { AudioFile, SmartCollection, Rule, ID3Tags } from '../types';

const checkRule = (file: AudioFile, rule: Rule): boolean => {
    const tags = file.fetchedTags || file.originalTags;
    const fieldValue = tags[rule.field as keyof ID3Tags];

    // Handle 'is_empty' and 'is_not_empty' for any field
    if (rule.operator === 'is_empty') {
        return fieldValue === undefined || fieldValue === null || fieldValue === '';
    }
    if (rule.operator === 'is_not_empty') {
        return fieldValue !== undefined && fieldValue !== null && fieldValue !== '';
    }
    
    // If the field is empty and the operator is not checking for emptiness, it can't be a match.
    if (fieldValue === undefined || fieldValue === null || fieldValue === '') {
        return false;
    }

    // Handle different value types (string vs. number)
    if (typeof fieldValue === 'string') {
        const value = String(rule.value).toLowerCase();
        const field = fieldValue.toLowerCase();

        switch (rule.operator) {
            case 'is':
                return field === value;
            case 'is_not':
                return field !== value;
            case 'contains':
                return field.includes(value);
            case 'not_contains':
                return !field.includes(value);
            default:
                return false;
        }
    } else if (typeof fieldValue === 'number') {
        const value = Number(rule.value);
        if (isNaN(value)) return false;

        switch (rule.operator) {
            case 'is':
                return fieldValue === value;
            case 'is_not':
                return fieldValue !== value;
            case 'is_greater_than':
                return fieldValue > value;
            case 'is_less_than':
                return fieldValue < value;
            case 'is_in_range':
                if (Array.isArray(rule.value) && rule.value.length === 2) {
                    const [min, max] = rule.value.map(Number);
                    if (isNaN(min) || isNaN(max)) return false;
                    return fieldValue >= min && fieldValue <= max;
                }
                return false;
            default:
                return false;
        }
    }
    return false;
};

export const filterFilesByRules = (files: AudioFile[], collection: SmartCollection): AudioFile[] => {
    if (!collection.rules || collection.rules.length === 0) {
        return files;
    }

    return files.filter(file => {
        if (collection.logic === 'AND') {
            return collection.rules.every(rule => checkRule(file, rule));
        } else { // OR logic
            return collection.rules.some(rule => checkRule(file, rule));
        }
    });
};