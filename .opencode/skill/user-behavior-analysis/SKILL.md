---
name: user-behavior-analysis
description: Analyzes user behavior and preferences from social media posts within a specific time period. Use when analyzing user data for personalized emotional companionship and behavior patterns.
---

When analyzing user behavior, always:

1. **Call the `query` tool**: Fetch the social media posts using the provided start and end times, ensuring the time window includes the month of focus with a 14-day buffer before.
2. **Time Period Adjustment**: Adjust the time window to start 14 days before the target month and end at the last day of the target month. Focus on analyzing the behavior within the target month.
3. **Profile Extraction**: Extract the user’s potential age, occupation, and identity labels based on content and language use.
4. **Preference Analysis**: Identify strong and neutral preferences toward specific people, things, events, and viewpoints. Clarify the reasoning based on frequency and emotional tone. Classify each preference as short-term (lasting days), medium-term (weeks), or long-term (months+).
5. **Personality Profiling**: Analyze the user’s emotional tendencies (e.g., optimism, anxiety, calmness) and potential value system keywords (e.g., self-actualization, family, friendship, social responsibility).
6. **Language Style**: Identify the user’s language habits, including common phrases, high-frequency words, emoji use, punctuation preferences, and speaking style.
7. **Key Events Identification**: Extract significant events mentioned or implied in the posts that may influence behavior (e.g., "product_launch", "personal_milestone", "travel").
8. **Historical Context**: Call the `get_historical_profiles` tool to retrieve extracted monthly profiles from the current month to T-6 months for reference. Use this context only to inform stability assessments, but base all analysis primarily on the current month's raw corpus.

Additional Requirements:

- **Highlight Changes**: If the user’s preferences or emotional tone shift significantly, make sure to highlight these changes with reasoning.
- **Contextual Notes**: If the user’s preferences seem to align with certain life events or external factors, include relevant notes in the analysis.

**Output Format (strict JSON):**

```json
{
  "time_period": "target month (e.g., 2024-12)",
  "profile": ["label1", "label2"],
  "preferences": [
    {"name": "specific thing", "type": "strong/neutral", "duration": "short/medium/long", "reason": "inferred basis"}
  ],
  "personality": ["optimistic", "self-confident"],
  "language_style": "concise, humorous, enjoys using emojis",
  "key_events": ["event1", "event2"]
}
```

The language used in the generated preference must match the input corpus. Remember to keep the analysis focused on the user’s behavior and emotional state throughout the time window. The output should provide insights into the user’s personality and preferences, helping to create a more personalized and empathetic interaction.
