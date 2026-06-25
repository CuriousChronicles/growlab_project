# Product Decisions

## Demand Labels

GradBridge reports raw counts first. Labels are only supporting language derived from the share of distinct employers in the selected snapshot that mention a skill.

- Core demand: at least 55% of distinct employers in the selected snapshot mention the skill.
- Growing signal: at least 30% and less than 55% mention the skill.
- Differentiator: at least 12% and less than 30% mention the skill.
- Low signal: less than 12% mention the skill.

The UI must always show the listing count and snapshot size alongside the label.

## Evidence Coverage

Evidence coverage is not an employability, hireability, or interview probability score. It is a transparent summary of visible proof against recurring skills in the selected market snapshot:

- Strong proof: 1.0
- Hidden proof: 0.75
- Adjacent proof: 0.45
- No proof yet: 0.0

The score is used to compare role pathways inside the MVP only. It should not be presented as a prediction.
