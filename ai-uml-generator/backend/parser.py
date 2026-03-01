import spacy
from collections import Counter

# --- Helper Functions ---

def is_potential_class(token):
    # Must be a noun, not a pronoun, and not a stop word
    if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
        # Favor capitalized words, but allow others
        if token.is_title:
            return True
        # Allow common nouns if they are not too generic
        if token.pos_ == 'NOUN' and token.lemma_ not in ['system', 'information', 'data', 'user']:
             return True
    return False

def get_class_candidates(doc):
    """Extract potential class names from the document."""
    # Using noun chunks is more robust than individual nouns
    candidates = [chunk.root for chunk in doc.noun_chunks if is_potential_class(chunk.root)]
    
    # Count frequency to find most important nouns
    counts = Counter(c.lemma_ for c in candidates)
    
    # Return unique class names (lemmas), favoring more common ones
    # This is a heuristic: top 10 most frequent nouns are likely classes
    top_lemmas = [lemma for lemma, count in counts.most_common(10)]
    
    # Get the original token for the top lemmas to preserve capitalization
    final_classes = []
    seen_lemmas = set()
    for token in candidates:
        if token.lemma_ in top_lemmas and token.lemma_ not in seen_lemmas:
            final_classes.append(token)
            seen_lemmas.add(token.lemma_)
            
    return final_classes

# --- Main Parser Logic ---

def extract_components(text: str, nlp_model):
    """
    Analyzes text to extract UML components and relationships.
    """
    doc = nlp_model(text)
    components = []
    
    # 1. Identify Classes
    class_tokens = get_class_candidates(doc)
    class_names = {token.text.capitalize() for token in class_tokens}
    
    for name in class_names:
        components.append({"name": name, "type": "Class", "confidence": 0.90})

    # 2. Identify Attributes and Methods (Simplified)
    # This is a very basic approach. A more advanced version would use dependency parsing
    # to link attributes/methods to the correct class.
    for token in doc:
        # A noun following a class name might be an attribute
        if token.pos_ == 'NOUN' and token.head.text.capitalize() in class_names:
            if not token.is_stop and token.lemma_ not in class_names:
                 components.append({
                     "name": token.lemma_, 
                     "type": "Attribute", 
                     "confidence": 0.75
                 })
        
        # A verb where the subject is a class might be a method
        if token.pos_ == 'VERB' and token.head.pos_ == 'NOUN':
             if token.head.text.capitalize() in class_names:
                 components.append({
                     "name": f"{token.lemma_}()", 
                     "type": "Method", 
                     "confidence": 0.80
                 })

    # 3. Identify Relationships (Placeholder)
    relationships = []
    # Example: "User has a profile." -> User -- Profile
    for token in doc:
        if token.lemma_ in ["have", "include", "contain"] and token.head.text.capitalize() in class_names:
            for child in token.children:
                if child.pos_ in ['NOUN', 'PROPN'] and child.text.capitalize() in class_names:
                    relationships.append({
                        "source": token.head.text.capitalize(),
                        "target": child.text.capitalize(),
                        "type": "Association",
                        "confidence": 0.70
                    })

    # Remove duplicate components (by name and type)
    unique_components = []
    seen = set()
    for comp in components:
        identifier = (comp['name'], comp['type'])
        if identifier not in seen:
            unique_components.append(comp)
            seen.add(identifier)

    return unique_components, relationships