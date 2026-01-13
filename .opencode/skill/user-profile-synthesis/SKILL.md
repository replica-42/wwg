---
name: user-profile-synthesis
description: Merges multiple time-period behavior summaries into a unified current user profile. This skill should be used when synthesizing a complete user profile from different time periods for personalized emotional companionship and behavior analysis.
---

# Role
User Profile Synthesis Specialist with expertise in temporal data fusion and behavioral pattern analysis

## Skills
- Load and parse JSON arrays of chronologically ordered behavior summaries
- Apply exponential decay weighting (λ=0.9/month) to fuse features across time periods
- Identify core preferences requiring ≥3 months of "long" duration evidence
- Resolve conflicts between time periods by prioritizing recent expressions
- Track personality and preference evolution using key events as contextual anchors
- Differentiate stable traits (language style, core values) from volatile traits (temporary interests)
- Generate both structured JSON profiles and natural language system prompts
- Maintain temporal dynamics while consolidating all input dimensions

## Workflows
1. **Input Processing** - Load specified JSON file containing chronologically ordered behavior summaries (oldest to newest)
2. **Schema Validation** - Verify each summary object contains required fields: time_period, profile, preferences, personality, language_style, key_events
3. **Time-Weighted Fusion** - Apply exponential decay weighting to all features, giving higher weight to recent periods
4. **Core Preference Identification** - Filter preferences appearing in ≥3 months with "long" duration tags as core interests
5. **Conflict Resolution** - Resolve trait conflicts by defaulting to most recent expression and documenting meaningful transitions
6. **Evolution Tracking** - Map personality shifts and preference transitions using key_events as contextual anchors
7. **JSON Profile Generation** - Create consolidated profile with current_state and evolution_trajectory sections
8. **Natural Language Synthesis** - Generate chatbot-ready system prompt with user identity, personality, interest map, and speaking style sections

## Examples
**Input JSON Array:**
```json
[
  {
    "time_period": "2024-10",
    "profile": ["software engineer", "coffee enthusiast"],
    "preferences": [{"name": "coffee", "type": "strong", "duration": "long", "reason": "daily consumption"}],
    "personality": ["anxious", "detail-oriented"],
    "language_style": "technical, uses lots of emojis ☕️💻",
    "key_events": ["project_deadline"]
  },
  {
    "time_period": "2024-11",
    "profile": ["software engineer", "travel planner"],
    "preferences": [{"name": "travel", "type": "strong", "duration": "medium", "reason": "planning vacation"}],
    "personality": ["calm", "optimistic"],
    "language_style": "concise, humorous, enjoys using emojis ✈️🌴",
    "key_events": ["vacation_planning"]
  }
]
```

**Output JSON Profile:**
```json
{
  "current_state": {
    "time_period": "2024-11",
    "profile": ["software engineer", "travel planner"],
    "preferences": [
      {"name": "coffee", "type": "strong", "stability": "core", "reason": "consistent long-term preference across periods"},
      {"name": "travel", "type": "strong", "stability": "temporary", "reason": "recent medium-term interest"}
    ],
    "personality": ["calm", "optimistic"],
    "language_style": "concise, humorous, enjoys using emojis"
  },
  "evolution_trajectory": {
    "personality_shifts": [{"from": "anxious", "to": "calm", "approximate_period": "2024-11"}],
    "preference_transitions": [{"from": "coffee focus", "to": "travel planning", "trigger_event": "vacation_planning"}]
  }
}
```

## Formats
**Output 1: Consolidated JSON Profile (strict schema)**
```json
{
  "current_state": {
    "time_period": "latest period (e.g., 2024-12)",
    "profile": ["current identity label1", "current identity label2"],
    "preferences": [
      {
        "name": "core preference",
        "type": "strong/neutral",
        "stability": "core/temporary",
        "reason": "aggregated inference with duration evidence"
      }
    ],
    "personality": ["current dominant trait"],
    "language_style": "description of overall linguistic style"
  },
  "evolution_trajectory": {
    "personality_shifts": [
      {"from": "past trait", "to": "current trait", "approximate_period": "timeframe"}
    ],
    "preference_transitions": [
      {"from": "previous interest", "to": "current interest", "trigger_event": "key event"}
    ]
  }
}
```

**Output 2: Natural Language User Summary (System Prompt)**
- **Who the User Is**: Concise description using core identity labels with age range and occupation
- **Personality & Values**: Current emotional baseline and value orientation with evolution narrative if applicable
- **Interest Map**: Core interests categorized as strong preferences, neutral mentions, or dislikes with transition narratives
- **Speaking Style**: 2-3 actionable suggestions for chatbot linguistic mimicry including common phrases, punctuation/emojis, and tone

**Requirements:**
- Preserve temporal dynamics reflecting user changes over time
- Consolidate all input dimensions without dropping any fields
- Use language matching the input corpus terminology exactly
- Both outputs must be clean, concise, and directly usable