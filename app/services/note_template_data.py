"""Definities van de ingebouwde notitiesjablonen (pure gegevens, zie note_templates.py).

Een sjabloon is een geordende lijst modules: {"type", "title", "optional", "default", "config"}.
Voor type "fields" bevat config["fields"] de veldlijst. Variabelen: {{title}} {{date}}
{{datetime}} {{week}}."""

CAT_PLAN = "Planning"
CAT_MEET = "Vergaderen & communicatie"
CAT_PROJ = "Projecten & uitvoering"
CAT_DECI = "Besluiten & probleemoplossing"
CAT_KNOW = "Kennis & documentatie"
CAT_PERS = "Persoonlijke productiviteit"

CATEGORIES = [CAT_PLAN, CAT_MEET, CAT_PROJ, CAT_DECI, CAT_KNOW, CAT_PERS]


def _f(name, label, type="text", **kw):
    return {"name": name, "label": label, "type": type, **kw}


TEMPLATES = [
    {
        "key": "meeting_notes",
        "name": "Vergadernotulen",
        "category": CAT_MEET,
        "icon": "🗒️",
        "description": "Agenda, discussie, besluiten en actiepunten van een vergadering.",
        "tags": "meeting",
        "title_pattern": "Vergadering {{date}}",
        "modules": [
            {"type": "fields", "title": "Gegevens", "config": {"fields": [
                _f("title", "Titel", required=True, default="{{title}}"),
                _f("when", "Datum en tijd", default="{{datetime}}"),
                _f("participants", "Deelnemers", "textarea", placeholder="Namen, één per regel"),
                _f("purpose", "Doel", "textarea"),
            ]}},
            {"type": "agenda", "title": "Agenda"},
            {"type": "notes", "title": "Discussienotities"},
            {"type": "decisions", "title": "Besluiten"},
            {"type": "action_items", "title": "Actiepunten"},
            {"type": "questions", "title": "Open vragen", "optional": True},
            {"type": "fields", "title": "Volgende vergadering", "optional": True, "config": {"fields": [
                _f("next_date", "Datum", "date"), _f("next_topic", "Onderwerp"),
            ]}},
        ],
    },
    {
        "key": "weekly_planning",
        "name": "Weekplanning",
        "category": CAT_PLAN,
        "icon": "📅",
        "description": "Doelen, prioriteiten, geplande taken en deadlines voor de week.",
        "tags": "planning",
        "title_pattern": "Weekplanning week {{week}}",
        "modules": [
            {"type": "fields", "title": "Week", "config": {"fields": [
                _f("week", "Week", default="Week {{week}}"),
                _f("start", "Van", "date", default="{{date}}"),
                _f("end", "Tot", "date"),
            ]}},
            {"type": "checklist", "title": "Hoofddoelen"},
            {"type": "checklist", "title": "Prioriteiten"},
            {"type": "action_items", "title": "Geplande taken"},
            {"type": "milestones", "title": "Belangrijke deadlines"},
            {"type": "risks", "title": "Risico's en blokkades", "optional": True},
            {"type": "notes", "title": "Terugblik einde van de week", "optional": True},
        ],
    },
    {
        "key": "small_project",
        "name": "Klein project",
        "category": CAT_PROJ,
        "icon": "🚀",
        "description": "Doel, scope, mijlpalen, acties, verantwoordelijkheden en risico's van een klein project.",
        "tags": "project",
        "title_pattern": "Project: {{title}}",
        "modules": [
            {"type": "fields", "title": "Project", "config": {"fields": [
                _f("name", "Projectnaam", required=True, default="{{title}}"),
                _f("objective", "Doel", "textarea"),
                _f("outcome", "Verwacht resultaat", "textarea"),
                _f("scope", "Scope", "textarea"),
                _f("exclusions", "Buiten scope", "textarea"),
                _f("deadline", "Deadline", "date"),
            ]}},
            {"type": "milestones", "title": "Mijlpalen"},
            {"type": "action_items", "title": "Acties"},
            {"type": "roles", "title": "Verantwoordelijkheden"},
            {"type": "checklist", "title": "Afhankelijkheden", "optional": True},
            {"type": "risks", "title": "Risico's", "optional": True},
            {"type": "checklist", "title": "Afrondingscriteria"},
        ],
    },
    {
        "key": "step_by_step",
        "name": "Stappenplan",
        "category": CAT_PROJ,
        "icon": "🪜",
        "description": "Genummerde stappen met eigenaar, deadline en status, plus validatie en probleemoplossing.",
        "tags": "plan",
        "title_pattern": "Stappenplan: {{title}}",
        "modules": [
            {"type": "fields", "title": "Doel", "config": {"fields": [_f("objective", "Doel", "textarea", required=True)]}},
            {"type": "checklist", "title": "Vereisten vooraf", "optional": True},
            {"type": "steps", "title": "Stappen"},
            {"type": "checklist", "title": "Validatie / afrondingscriteria"},
            {"type": "notes", "title": "Probleemoplossing", "optional": True},
        ],
    },
    {
        "key": "roles_responsibilities",
        "name": "Rollen en verantwoordelijkheden",
        "category": CAT_PROJ,
        "icon": "🧩",
        "description": "Wie doet wat: rol, persoon, bevoegdheden, afhankelijkheden en escalatie.",
        "tags": "rollen",
        "title_pattern": "Rollen: {{title}}",
        "modules": [
            {"type": "fields", "title": "Initiatief", "config": {"fields": [
                _f("initiative", "Project of initiatief", required=True, default="{{title}}"),
            ]}},
            {"type": "roles", "title": "Rollen"},
            {"type": "checklist", "title": "Afhankelijkheden", "optional": True},
            {"type": "questions", "title": "Open vragen", "optional": True},
        ],
    },
    {
        "key": "daily_planning",
        "name": "Dagplanning",
        "category": CAT_PLAN,
        "icon": "☀️",
        "description": "Top 3 voor vandaag, taken en een korte terugblik.",
        "tags": "planning",
        "title_pattern": "Dagplanning {{date}}",
        "modules": [
            {"type": "fields", "title": "Dag", "config": {"fields": [_f("day", "Datum", "date", default="{{date}}")]}},
            {"type": "checklist", "title": "Top 3 voor vandaag"},
            {"type": "action_items", "title": "Taken"},
            {"type": "notes", "title": "Terugblik", "optional": True},
        ],
    },
    {
        "key": "checklist",
        "name": "Checklist",
        "category": CAT_PLAN,
        "icon": "☑️",
        "description": "Een eenvoudige afvinklijst.",
        "title_pattern": "Checklist {{date}}",
        "modules": [{"type": "checklist", "title": "Checklist"}],
    },
    {
        "key": "daily_standup",
        "name": "Dagelijkse stand-up",
        "category": CAT_MEET,
        "icon": "🧍",
        "description": "Gisteren, vandaag en blokkades.",
        "tags": "meeting",
        "title_pattern": "Stand-up {{date}}",
        "modules": [
            {"type": "notes", "title": "Gisteren"},
            {"type": "notes", "title": "Vandaag"},
            {"type": "questions", "title": "Blokkades"},
        ],
    },
    {
        "key": "retrospective",
        "name": "Retrospective",
        "category": CAT_DECI,
        "icon": "🔁",
        "description": "Wat ging goed, wat kan beter, en verbeteracties.",
        "tags": "retro",
        "title_pattern": "Retrospective {{date}}",
        "modules": [
            {"type": "notes", "title": "Wat ging goed"},
            {"type": "notes", "title": "Wat kan beter"},
            {"type": "action_items", "title": "Verbeteracties"},
        ],
    },
    {
        "key": "decision_log",
        "name": "Besluitenlog",
        "category": CAT_DECI,
        "icon": "⚖️",
        "description": "Opties met voor- en nadelen en het uiteindelijke besluit.",
        "tags": "besluit",
        "title_pattern": "Besluit: {{title}}",
        "modules": [
            {"type": "fields", "title": "Vraagstuk", "config": {"fields": [
                _f("question", "Wat moet er besloten worden?", "textarea", required=True),
                _f("date", "Datum", "date", default="{{date}}"),
            ]}},
            {"type": "pros_cons", "title": "Voor- en nadelen"},
            {"type": "decisions", "title": "Besluit"},
        ],
    },
    {
        "key": "standard_note",
        "name": "Standaardnotitie",
        "category": CAT_KNOW,
        "icon": "📝",
        "description": "Een lege notitie met een titel en vrije tekst.",
        "title_pattern": "{{title}}",
        "modules": [{"type": "notes", "title": ""}],
    },
    {
        "key": "how_to",
        "name": "Werkinstructie",
        "category": CAT_KNOW,
        "icon": "🛠️",
        "description": "How-to met vereisten, stappen en links.",
        "tags": "howto",
        "title_pattern": "Hoe: {{title}}",
        "modules": [
            {"type": "fields", "title": "Doel", "config": {"fields": [_f("goal", "Wat bereik je hiermee?", "textarea")]}},
            {"type": "checklist", "title": "Vereisten", "optional": True},
            {"type": "steps", "title": "Stappen"},
            {"type": "links", "title": "Links en referenties", "optional": True},
        ],
    },
    {
        "key": "daily_journal",
        "name": "Dagboek",
        "category": CAT_PERS,
        "icon": "📖",
        "description": "Een korte dagelijkse terugblik.",
        "tags": "dagboek",
        "title_pattern": "Dagboek {{date}}",
        "modules": [
            {"type": "notes", "title": "Hoe was mijn dag"},
            {"type": "checklist", "title": "Waar ben ik dankbaar voor"},
        ],
    },
    {
        "key": "weekly_review",
        "name": "Weekreview",
        "category": CAT_PERS,
        "icon": "🔍",
        "description": "Wat lukte, wat niet, en focus voor volgende week.",
        "tags": "review",
        "title_pattern": "Weekreview week {{week}}",
        "modules": [
            {"type": "notes", "title": "Wat lukte"},
            {"type": "notes", "title": "Wat lukte niet"},
            {"type": "checklist", "title": "Focus volgende week"},
        ],
    },
]
