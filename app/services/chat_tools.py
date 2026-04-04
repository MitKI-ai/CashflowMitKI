"""Tool definitions for LLM Chat — maps natural language to entity CRUD."""

TOOL_DEFINITIONS = [
    {
        "name": "create_account",
        "description": "Erstellt ein neues Bankkonto (Girokonto, Sparkonto, Depot, Festgeld).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name des Kontos, z.B. 'Girokonto Sparkasse'"},
                "type": {"type": "string", "enum": ["checking", "savings", "investment", "deposit"]},
                "bank_name": {"type": "string", "description": "Name der Bank"},
                "balance": {"type": "number", "description": "Aktueller Kontostand in EUR"},
            },
            "required": ["name", "type"],
        },
    },
    {
        "name": "list_accounts",
        "description": "Zeigt alle Bankkonten des Users.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "create_standing_order",
        "description": "Erstellt einen neuen Dauerauftrag (Gehalt, Miete, Versicherung, Sparplan).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name des Dauerauftrags"},
                "type": {"type": "string", "enum": ["income", "expense", "savings_transfer"]},
                "amount": {"type": "number", "description": "Betrag in EUR"},
                "frequency": {"type": "string", "enum": ["monthly", "biweekly", "quarterly", "yearly"]},
                "execution_day": {"type": "integer", "description": "Tag im Monat (1-28)", "minimum": 1, "maximum": 28},
            },
            "required": ["name", "type", "amount"],
        },
    },
    {
        "name": "create_direct_debit",
        "description": "Erstellt eine neue Lastschrift (Strom, Gas, Internet, Versicherung).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name der Lastschrift"},
                "creditor": {"type": "string", "description": "Name des Gläubigers"},
                "amount": {"type": "number", "description": "Betrag in EUR"},
                "frequency": {"type": "string", "enum": ["monthly", "quarterly", "yearly"]},
                "expected_day": {"type": "integer", "description": "Erwarteter Tag im Monat (1-28)"},
            },
            "required": ["name", "amount"],
        },
    },
    {
        "name": "create_transaction",
        "description": "Erstellt eine einzelne Transaktion (Einkauf, Einnahme, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Beschreibung der Transaktion"},
                "amount": {"type": "number", "description": "Betrag in EUR"},
                "type": {"type": "string", "enum": ["income", "expense"]},
                "category": {"type": "string", "description": "Kategorie (z.B. food, transport, entertainment)"},
                "transaction_date": {"type": "string", "description": "Datum im Format YYYY-MM-DD"},
            },
            "required": ["description", "amount", "type", "transaction_date"],
        },
    },
    {
        "name": "create_investment",
        "description": "Erstellt eine neue Geldanlage (ETF, Aktie, Crypto, Festgeld).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name der Anlage"},
                "type": {"type": "string", "enum": ["etf", "stock", "crypto", "bond", "real_estate", "other"]},
                "current_value": {"type": "number", "description": "Aktueller Wert in EUR"},
                "invested_amount": {"type": "number", "description": "Eingezahlter Betrag in EUR"},
                "broker": {"type": "string", "description": "Name des Brokers"},
                "isin": {"type": "string", "description": "ISIN-Nummer"},
            },
            "required": ["name", "type", "current_value"],
        },
    },
    {
        "name": "create_savings_goal",
        "description": "Erstellt ein Sparziel (Notgroschen, Urlaub, Rente).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name des Sparziels"},
                "type": {"type": "string", "enum": ["emergency", "vacation_luxury", "retirement"]},
                "target_amount": {"type": "number", "description": "Zielbetrag in EUR"},
                "current_amount": {"type": "number", "description": "Aktuell gespartes in EUR"},
            },
            "required": ["name", "type", "target_amount"],
        },
    },
    {
        "name": "update_savings_goal",
        "description": "Aktualisiert ein bestehendes Sparziel (z.B. aktuellen Betrag ändern).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name des Sparziels zum Identifizieren"},
                "target_amount": {"type": "number"},
                "current_amount": {"type": "number"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "create_budget_alert",
        "description": "Erstellt eine Budget-Warnung für eine Kategorie.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name der Warnung"},
                "category": {"type": "string", "description": "Kategorie (z.B. food, transport)"},
                "monthly_limit": {"type": "number", "description": "Monatliches Limit in EUR"},
            },
            "required": ["name", "category", "monthly_limit"],
        },
    },
    {
        "name": "get_cashflow_summary",
        "description": "Zeigt die aktuelle Cashflow-Zusammenfassung (Einnahmen, Ausgaben, Netto).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_net_worth",
        "description": "Zeigt das Gesamtvermögen (Konten + Geldanlagen).",
        "input_schema": {"type": "object", "properties": {}},
    },
]
