from sortedcontainers import SortedSet
class Term:
    def __init__(self, term_id:int, postings_list:list[int]=[]):
        self.id = term_id
        self.postings_list: SortedSet = SortedSet(postings_list)

    def update(self, postings_list:list[int]=[]) -> None:
        self.postings_list.update(postings_list)

    @property
    def freq(self):
        return len(self.postings_list)
    
class InvertedIndex:
    def __init__(self):
        self.dictionary:dict[str, Term] = {}

    def update(self, term:str, postings_list:list[int]=[]) -> None:
            if term not in self.dictionary:
                self.dictionary[term] = Term(len(self.dictionary), postings_list)
            else:
                self.dictionary[term].update(postings_list)

    @property
    def length(self):
        return len(self.dictionary)
    
    def get_term(self, term:str):
        return self.dictionary.get(term, Term(-1))

    def _get_term_list(self, value:list[str|Term]) -> list[Term]:
        new_value:list[Term] = []
        for i in range(len(value)):
            v = value[i]
            if type(v) == str:
                new_value.append(self.get_term(v))
            elif type(v) == Term:
                new_value.append(v)
                
        return new_value

    def q_and(self, value:list[str|Term]) -> Term:
        new_value = self._get_term_list(value)
        result = new_value[0]
        for t in new_value[1:]:
            result.postings_list = result.postings_list & t.postings_list
        return result

    def q_or(self, value:list[str|Term]) -> Term:
        new_value = self._get_term_list(value)
        result = new_value[0]
        for t in new_value[1:]:
            result.postings_list = result.postings_list | t.postings_list
        return result

    def q_not(self, value:list[str|Term]) -> Term:
        new_value = self._get_term_list(value)
        result = new_value[0]
        for t in new_value[1:]:
            result.postings_list = result.postings_list - t.postings_list
        return result

    def Query(self, term:Term) ->list[int]:
        return list(term.postings_list)

    def save(self) ->None:
        import pickle
        from config import CONFIG
        import os.path as path
        with open(path.join(CONFIG.P_DATA, CONFIG.INVERT_INDEX_FILE), "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls):
        import pickle
        from config import CONFIG
        import os.path as path
        if not path.exists(path.join(CONFIG.P_DATA, CONFIG.INVERT_INDEX_FILE)):
            raise FileNotFoundError
        else:
            with open(path.join(CONFIG.P_DATA, CONFIG.INVERT_INDEX_FILE), "rb") as f:
                return pickle.load(f)
