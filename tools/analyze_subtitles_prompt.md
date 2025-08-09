# Subtitle Content Analysis Prompt

**Copy and paste this prompt with your subtitle file content into Claude Code to generate metadata.json**

---

You are an expert film analyst. Analyze the provided English subtitle file and generate structured metadata for translation purposes. 

**TASK:** Create a comprehensive JSON metadata file with the following information:

```json
{
  "film_metadata": {
    "genre": "string - primary genre (drama, comedy, action, etc.)",
    "subgenres": ["list", "of", "secondary", "genres"],
    "setting": {
      "location": "string - geographic location/country",
      "time_period": "string - when story takes place",
      "environment": ["list", "of", "main", "settings"]
    },
    "tone": "string - overall emotional tone (serious, lighthearted, tense, etc.)"
  },
  "characters": {
    "main_characters": ["list", "of", "main", "character", "names"],
    "secondary_characters": ["list", "of", "secondary", "character", "names"],
    "character_relationships": "string - brief description of key relationships"
  },
  "themes": {
    "primary_themes": ["list", "of", "main", "themes"],
    "cultural_elements": ["list", "of", "cultural", "references"],
    "sensitive_topics": ["list", "of", "sensitive", "content", "areas"]
  },
  "translation_context": {
    "target_language": "Romanian",
    "register": "string - formal/informal/mixed appropriate for content",
    "special_terminology": {
      "proper_nouns": ["names", "places", "to", "preserve"],
      "cultural_terms": ["terms", "requiring", "careful", "translation"],
      "technical_terms": ["specialized", "vocabulary", "if", "any"]
    },
    "translation_notes": [
      "Specific guidance for Romanian translation",
      "Cultural adaptation notes",
      "Tone preservation guidelines"
    ]
  },
  "story_summary": "2-3 sentence summary of the plot for translation context"
}
```

**INSTRUCTIONS:**
1. Read through ALL the subtitle content carefully
2. Identify patterns in dialogue and character interactions  
3. Detect cultural, religious, or regional references
4. Note the emotional register and formality level
5. Create translation-specific guidance based on the content
6. Respond with ONLY valid JSON format, no additional explanation

**SUBTITLE CONTENT TO ANALYZE:**
```
[PASTE YOUR SUBTITLE FILE CONTENT HERE]
```

---

**Usage:**
1. Copy this prompt
2. Replace `[PASTE YOUR SUBTITLE FILE CONTENT HERE]` with your actual subtitle content  
3. Paste into Claude Code
4. Save the JSON response as `metadata.json`
5. Use with `prep_translation.py --metadata metadata.json`