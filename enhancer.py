import re
import random
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Ensure datasets are available
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
except Exception:
    pass

# Dictionaries for transformations
SIMILES = {
    "bright": [
        "like the morning sun", "as bright as a newborn star", "like a diamond in the rough", 
        "as bright as a polished mirror", "like a beacon in the dark", "as bright as daylight", "like a flare in the night"
    ],
    "dark": [
        "like a moonless night", "as dark as pitch", "like the bottom of the ocean", 
        "as dark as a cave", "like a shadowed alley", "as dark as charcoal", "like a sky without stars"
    ],
    "cold": [
        "as ice", "like a winter breeze", "as cold as the arctic", 
        "like a frozen lake", "as cold as marble", "like bitter frost", "as cold as an empty stare"
    ],
    "hot": [
        "like a blazing furnace", "as hot as the desert sun", "like molten lava", 
        "as hot as a roaring fire", "like a midsummer afternoon", "as hot as boiling water", "like dragon's breath"
    ],
    "beautiful": [
        "like a blooming rose", "as beautiful as a painting", "like a sunrise over the mountains", 
        "as beautiful as a melody", "like a flawless gem", "as beautiful as a dream", "like a starry night"
    ],
    "strong": [
        "as an oak tree", "like a mountain", "as strong as an ox", 
        "like a steel cable", "as strong as a tidal wave", "like an unshakable fortress", "as strong as a bear"
    ],
    "fast": [
        "like lightning", "as fast as a cheetah", "like a racing arrow", 
        "as fast as the wind", "like a shooting star", "as fast as a gazelle", "like a bullet"
    ],
    "slow": [
        "like molasses", "as slow as a snail", "like a creeping glacier", 
        "as slow as a turtle", "like a lazy river", "as slow as time waiting", "like a sluggish crawl"
    ],
    "quiet": [
        "as the grave", "like a falling leaf", "as quiet as a mouse", 
        "like a gentle whisper", "as quiet as freshly fallen snow", "like an empty room", "as quiet as a secret"
    ],
    "loud": [
        "like thunder", "as loud as a siren", "like a roaring lion", 
        "as loud as an explosion", "like a crashing wave", "as loud as a brass band", "like a pounding drum"
    ],
    "soft": [
        "as silk", "like a feather", "as soft as velvet", 
        "like a baby's cheek", "as soft as a cloud", "like a spring breeze", "as soft as a whisper"
    ],
    "heavy": [
        "like a boulder", "as heavy as lead", "like a sinking anchor", 
        "as heavy as a mountain", "like an anvil", "as heavy as a burdened heart", "like crushed stone"
    ]
}

METAPHORS = {
    "life": "a journey",
    "time": "a thief",
    "love": "a battlefield",
    "world": "a stage",
    "mind": "an ocean",
    "heart": "a fragile glass",
    "sun": "a golden coin",
    "moon": "a silver lantern",
    "city": "a concrete jungle",
    "hope": "a beacon"
}

PERSONIFICATION_VERBS = {
    "wind": ["whispered", "howled", "danced", "sighed"],
    "sun": ["smiled", "peeked", "greeted"],
    "moon": ["watched", "guarded", "hid"],
    "ocean": ["roared", "breathed", "swallowed"],
    "tree": ["reached", "stood guard", "wept"],
    "shadow": ["crept", "danced", "lingered"],
    "fire": ["devoured", "danced", "breathed"],
    "stars": ["winked", "shimmered with joy", "gossiped"]
}

HYPERBOLES = {
    "tired": [
        "tired beyond words", "exhausted to the very bone", "so tired I could sleep for a century",
        "running entirely on fumes", "dead on my feet", "drained of all life", "worn down to nothing"
    ],
    "hungry": [
        "starving to death", "so hungry I could eat a horse", "famished beyond belief",
        "empty as a black hole", "craving food for an eternity", "dying of hunger", "ravenous enough to eat the plates"
    ],
    "old": [
        "older than dirt", "as old as the hills", "ancient history",
        "before the dawn of time", "an absolute dinosaur", "older than the stars", "around since the earth cooled"
    ],
    "long": [
        "an eternity", "a million years", "for ages",
        "an endless stretch", "a lifetime", "forever and a day", "longer than human history"
    ],
    "many": [
        "a million", "countless beyond measure", "numberless like the stars",
        "a mountain of", "an infinite sea", "billions upon billions", "more than anyone could ever count"
    ],
    "good": [
        "the best in the whole wide world", "absolutely perfect in every way", "too good to be true",
        "the greatest thing since sliced bread", "flawless beyond compare", "a true masterpiece", "magical beyond reality"
    ],
    "bad": [
        "the absolute worst thing imaginable", "a complete and utter disaster", "horrific beyond words",
        "a nightmare come to life", "terrible beyond belief", "the end of the world", "an unmitigated catastrophe"
    ]
}

def capitalize_first(text):
    if not text:
        return text
    return text[0].upper() + text[1:]

def enhance_text(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) < 6:
        return {
            "error": "Input must contain at least 6 lines of text for poetic enhancement.",
            "original": text,
            "enhanced": "",
            "devices_added": [],
            "modifications": []
        }

    devices_used = set()
    enhanced_lines = []
    modifications = []

    for line in lines:
        sentences = sent_tokenize(line)
        enhanced_sentences = []
        
        for sentence in sentences:
            tokens = word_tokenize(sentence)
            tagged = nltk.pos_tag(tokens)
            
            new_tokens = []
            i = 0
            # Track if we modified this sentence to avoid overloading it
            modified = False 
            used_device = ""
            used_algo = ""
            
            while i < len(tokens):
                word = tokens[i]
                pos = tagged[i][1]
                word_lower = word.lower()
                
                # 1. Simile (Adjective match)
                if not modified and pos.startswith('JJ') and word_lower in SIMILES and random.random() > 0.3:
                    chosen_simile = random.choice(SIMILES[word_lower])
                    new_tokens.append(word)
                    new_tokens.append(chosen_simile)
                    devices_used.add("Simile")
                    used_device = "Simile"
                    used_algo = f"Detected Adjective '{word}'. Applied matching Simile template: '{chosen_simile}'."
                    modified = True
                    i += 1
                    continue
                
                # 2. Metaphor (Noun + is/was)
                if not modified and pos.startswith('NN') and word_lower in METAPHORS and (i + 1 < len(tokens)):
                    next_word = tokens[i+1].lower()
                    if next_word in ['is', 'was', 'are', 'were']:
                        new_tokens.append(word)
                        new_tokens.append(tokens[i+1])
                        new_tokens.append(METAPHORS[word_lower])
                        devices_used.add("Metaphor")
                        used_device = "Metaphor"
                        used_algo = f"Detected Noun '{word}' followed by 'BE' verb. Applied Metaphor replacement: '{METAPHORS[word_lower]}'."
                        modified = True
                        
                        if i + 2 < len(tokens) and tokens[i+2].lower() in ['a', 'an', 'the']:
                            i += 3
                            if i < len(tokens) and tagged[i][1].startswith('NN'):
                                i += 1 # skip old noun
                        else:
                            i += 2
                        continue

                # 3. Personification (Inanimate Noun + Verb replacement)
                if not modified and pos.startswith('NN') and word_lower in PERSONIFICATION_VERBS and i + 1 < len(tokens):
                    next_pos = tagged[i+1][1]
                    if next_pos.startswith('VB'): # replacing the verb
                        replacement_verb = random.choice(PERSONIFICATION_VERBS[word_lower])
                        new_tokens.append(word)
                        new_tokens.append(replacement_verb)
                        devices_used.add("Personification")
                        used_device = "Personification"
                        used_algo = f"Detected Inanimate Noun '{word}' followed by Verb. Replaced Action with human verb '{replacement_verb}'."
                        modified = True
                        i += 2
                        continue

                # 4. Hyperbole (Adjective replacement)
                if not modified and pos.startswith('JJ') and word_lower in HYPERBOLES and random.random() > 0.3:
                    chosen_hyp = random.choice(HYPERBOLES[word_lower])
                    new_tokens.append(chosen_hyp)
                    devices_used.add("Hyperbole")
                    used_device = "Hyperbole"
                    used_algo = f"Detected Adjective '{word}'. Exaggerated to Hyperbole template: '{chosen_hyp}'."
                    modified = True
                    i += 1
                    continue
                
                # 5. Alliteration (just appending a repeated consonant adjective occasionally)
                if not modified and pos.startswith('NN') and random.random() > 0.8:
                    first_char = word_lower[0]
                    if first_char.isalpha():
                        alliteration_adjs = {
                            's': ['silent', 'silver', 'soft', 'solemn'],
                            'b': ['bright', 'bold', 'brave', 'bitter'],
                            'w': ['wild', 'wandering', 'whispering', 'warm'],
                            'm': ['mystic', 'mellow', 'majestic'],
                            'd': ['dark', 'deep', 'distant', 'dreamy']
                        }
                        if first_char in alliteration_adjs:
                            prepended_adj = random.choice(alliteration_adjs[first_char])
                            new_tokens.append(prepended_adj)
                            new_tokens.append(word)
                            devices_used.add("Alliteration")
                            used_device = "Alliteration"
                            used_algo = f"Detected Noun '{word}' starting with '{first_char}'. Inserted matching beginning-consonant Adjective '{prepended_adj}'."
                            modified = True
                            i += 1
                            continue

                new_tokens.append(word)
                i += 1
            
            clean_sentence = " ".join(new_tokens)
            clean_sentence = re.sub(r'\s+([?.!,:;\'"])', r'\1', clean_sentence)
            final_sent = capitalize_first(clean_sentence)
            enhanced_sentences.append(final_sent)
            
            if modified:
                modifications.append({
                    "device": used_device,
                    "original_sentence": sentence,
                    "enhanced_sentence": final_sent,
                    "algorithm": used_algo
                })
            
        enhanced_lines.append(" ".join(enhanced_sentences))

    if len(enhanced_lines) >= 3 and random.random() > 0.5:
        anaphora_phrases = ["And yet, ", "Beyond the horizon, ", "In the stillness, "]
        chosen = random.choice(anaphora_phrases)
        enhanced_lines[-2] = chosen + capitalize_first(enhanced_lines[-2])
        enhanced_lines[-1] = chosen + capitalize_first(enhanced_lines[-1])
        devices_used.add("Anaphora")
        modifications.append({
            "device": "Anaphora",
            "original_sentence": "[Applied to ending sentences]",
            "enhanced_sentence": f"{enhanced_lines[-2]} ... {enhanced_lines[-1]}",
            "algorithm": f"Inserted uniform anaphoric marker '{chosen}' at the beginning of consecutive concluding clauses."
        })

    final_enhanced = "\n".join(enhanced_lines)

    return {
        "original": text,
        "enhanced": final_enhanced,
        "devices_added": list(devices_used),
        "modifications": modifications
    }
