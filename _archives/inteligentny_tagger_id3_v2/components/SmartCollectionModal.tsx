import React, { useState, useEffect, useMemo } from 'react';
import { SmartCollection, Rule, RuleLogic, RuleOperator, AudioFile, ID3Tags } from '../types';
import { filterFilesByRules } from '../utils/collectionUtils';

// Assume uuid is loaded globally
declare const uuid: { v4: () => string; };

interface SmartCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (collection: SmartCollection) => void;
  files: AudioFile[];
  collectionToEdit?: SmartCollection;
}

const tagFields: { id: keyof ID3Tags; name: string; type: 'string' | 'number' }[] = [
  { id: 'title', name: 'Tytuł', type: 'string' },
  { id: 'artist', name: 'Artysta', type: 'string' },
  { id: 'album', name: 'Album', type: 'string' },
  { id: 'genre', name: 'Gatunek', type: 'string' },
  { id: 'year', name: 'Rok', type: 'number' },
  { id: 'bpm', name: 'BPM', type: 'number' },
  { id: 'key', name: 'Tonacja', type: 'string' },
  { id: 'comments', name: 'Komentarz', type: 'string' },
];

const operators: { id: RuleOperator; name: string; types: ('string' | 'number')[] }[] = [
  { id: 'is', name: 'jest równe', types: ['string', 'number'] },
  { id: 'is_not', name: 'nie jest równe', types: ['string', 'number'] },
  { id: 'contains', name: 'zawiera', types: ['string'] },
  { id: 'not_contains', name: 'nie zawiera', types: ['string'] },
  { id: 'is_greater_than', name: 'jest większe niż', types: ['number'] },
  { id: 'is_less_than', name: 'jest mniejsze niż', types: ['number'] },
  { id: 'is_in_range', name: 'jest w zakresie', types: ['number'] },
  { id: 'is_empty', name: 'jest puste', types: ['string', 'number'] },
  { id: 'is_not_empty', name: 'nie jest puste', types: ['string', 'number'] },
];

const SmartCollectionModal: React.FC<SmartCollectionModalProps> = ({ isOpen, onClose, onSave, files, collectionToEdit }) => {
  const [name, setName] = useState('');
  const [logic, setLogic] = useState<RuleLogic>('AND');
  const [rules, setRules] = useState<Rule[]>([]);

  useEffect(() => {
    if (isOpen) {
      if (collectionToEdit) {
        setName(collectionToEdit.name);
        setLogic(collectionToEdit.logic);
        setRules(collectionToEdit.rules);
      } else {
        setName('');
        setLogic('AND');
        setRules([{ id: uuid.v4(), field: 'artist', operator: 'contains', value: '' }]);
      }
    }
  }, [isOpen, collectionToEdit]);

  const handleRuleChange = (id: string, newRule: Partial<Rule>) => {
    setRules(rules.map(r => r.id === id ? { ...r, ...newRule } : r));
  };

  const addRule = () => {
    setRules([...rules, { id: uuid.v4(), field: 'artist', operator: 'contains', value: '' }]);
  };

  const removeRule = (id: string) => {
    setRules(rules.filter(r => r.id !== id));
  };
  
  const handleSave = () => {
      const newCollection: SmartCollection = {
          id: collectionToEdit?.id || uuid.v4(),
          name,
          logic,
          rules,
      };
      onSave(newCollection);
  }
  
  const matchingFilesCount = useMemo(() => {
    const tempCollection: SmartCollection = { id: '', name, logic, rules };
    return filterFilesByRules(files, tempCollection).length;
  }, [files, name, logic, rules]);


  if (!isOpen) return null;
  
  const renderRuleInput = (rule: Rule) => {
    const fieldType = tagFields.find(f => f.id === rule.field)?.type || 'string';

    if (rule.operator === 'is_empty' || rule.operator === 'is_not_empty') {
      return <div className="w-full h-9"></div>; // Placeholder to keep layout consistent
    }
    
    if (rule.operator === 'is_in_range') {
        const rangeValue = Array.isArray(rule.value) ? rule.value : [0, 0];
        return (
            <div className="flex items-center gap-2 w-full">
                <input
                    type="number"
                    value={rangeValue[0]}
                    onChange={(e) => handleRuleChange(rule.id, { value: [Number(e.target.value), rangeValue[1]] })}
                    className="w-1/2 bg-slate-900 border-slate-600 rounded-md p-1.5 text-sm"
                />
                <span className="text-slate-400">-</span>
                 <input
                    type="number"
                    value={rangeValue[1]}
                    onChange={(e) => handleRuleChange(rule.id, { value: [rangeValue[0], Number(e.target.value)] })}
                    className="w-1/2 bg-slate-900 border-slate-600 rounded-md p-1.5 text-sm"
                />
            </div>
        )
    }

    return (
      <input
        type={fieldType === 'number' ? 'number' : 'text'}
        value={rule.value as string | number}
        onChange={(e) => handleRuleChange(rule.id, { value: e.target.value })}
        className="w-full bg-slate-900 border-slate-600 rounded-md p-1.5 text-sm"
      />
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-3xl mx-4 max-h-[90vh] flex flex-col transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-white mb-4">Kreator Inteligentnej Kolekcji</h2>
        
        <div className="mb-4">
            <label htmlFor="collectionName" className="block text-sm font-medium text-slate-300">Nazwa kolekcji</label>
            <input
                type="text"
                id="collectionName"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 w-full bg-slate-900 border border-slate-600 rounded-md py-2 px-3 text-white"
                placeholder="np. Techno 128-130 BPM"
            />
        </div>

        <div className="mb-4 p-4 bg-slate-900/50 rounded-md flex-grow overflow-y-auto">
            <div className="flex items-center mb-3">
                <label className="text-sm font-medium text-slate-300 mr-4">Dopasuj</label>
                <div className="flex rounded-md bg-slate-700 p-1 text-sm">
                    <button onClick={() => setLogic('AND')} className={`px-3 py-1 rounded ${logic === 'AND' ? 'bg-indigo-600' : ''}`}>wszystkie</button>
                    <button onClick={() => setLogic('OR')} className={`px-3 py-1 rounded ${logic === 'OR' ? 'bg-indigo-600' : ''}`}>dowolną</button>
                </div>
                <label className="text-sm font-medium text-slate-300 ml-2">z poniższych reguł:</label>
            </div>
            
            <div className="space-y-2">
                {rules.map((rule) => {
                    const fieldType = tagFields.find(f => f.id === rule.field)?.type || 'string';
                    const availableOperators = operators.filter(op => op.types.includes(fieldType));
                    
                    return (
                        <div key={rule.id} className="flex items-center gap-2">
                            <select value={rule.field} onChange={(e) => handleRuleChange(rule.id, { field: e.target.value as keyof ID3Tags })} className="bg-slate-700 rounded p-2 text-sm">
                                {tagFields.map(field => <option key={field.id} value={field.id}>{field.name}</option>)}
                            </select>
                            <select value={rule.operator} onChange={(e) => handleRuleChange(rule.id, { operator: e.target.value as RuleOperator })} className="bg-slate-700 rounded p-2 text-sm w-40">
                                {availableOperators.map(op => <option key={op.id} value={op.id}>{op.name}</option>)}
                            </select>
                            {renderRuleInput(rule)}
                            <button onClick={() => removeRule(rule.id)} className="p-2 text-red-400 hover:bg-red-900/50 rounded">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" /></svg>
                            </button>
                        </div>
                    );
                })}
            </div>
             <button onClick={addRule} className="mt-3 p-2 text-green-400 hover:bg-green-900/50 rounded flex items-center text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" /></svg>
                Dodaj regułę
            </button>
        </div>
        
        <p className="text-sm text-slate-400 mb-4">
            Znaleziono pasujących utworów: <span className="font-bold text-accent-cyan">{matchingFilesCount}</span>
        </p>


        <div className="flex justify-end space-x-4 mt-auto pt-4 border-t border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700 rounded-md hover:bg-slate-600">Anuluj</button>
          <button onClick={handleSave} disabled={!name || rules.length === 0} className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed">Zapisz Kolekcję</button>
        </div>
        <style>{`.animate-fade-in-scale { animation: fade-in-scale 0.2s ease-out forwards; } @keyframes fade-in-scale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }`}</style>
      </div>
    </div>
  );
};

export default SmartCollectionModal;