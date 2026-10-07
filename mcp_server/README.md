# MCP-server voor Productivity Suite

Laat een MCP-compatibele agent (bv. Hermes, Claude Desktop/Code) de app direct als tools
gebruiken: taken, notities, snippets en kanban (28 tools). Het is een dunne laag bovenop de
JSON-API (`/api/v1`, zie `../AGENT_API.md`) — elke tool roept één API-route aan.

## Installeren (op de machine waar de agent draait)

De server heeft een **eigen venv** nodig: de `mcp`-library eist een nieuwere Starlette dan de
app zelf pint, dus installeer 'm niet in de venv/Docker-image van de app.

```bash
cd productivity-suite
python3 -m venv mcp_server/.venv
mcp_server/.venv/bin/pip install -r mcp_server/requirements.txt httpx
```

Maak onder Account → API-token een token aan.

## Koppelen aan Hermes (`~/.hermes/config.yaml`)

```yaml
mcp_servers:
  productivity:
    command: "/pad/naar/productivity-suite/mcp_server/.venv/bin/python"
    args: ["/pad/naar/productivity-suite/mcp_server/server.py"]
    env:
      PRODUCTIVITY_URL: "http://192.168.2.200:8887"
      PRODUCTIVITY_TOKEN: "<je-token>"
    # optioneel: gevaarlijke tools uitsluiten
    # tools:
    #   exclude: [delete_*]
```

Voor Claude Desktop/Code: zelfde `command`/`args`/`env` in de MCP-configuratie van die client.

## Tools

`health` · taken: `list_tasks`, `get_task`, `create_task`, `update_task` (ook afvinken met
`done`), `delete_task`, `restore_task` · notities: `list_notes`, `get_note`, `create_note`,
`update_note`, `delete_note` · snippets: `list_snippets`, `get_snippet`, `create_snippet`,
`update_snippet`, `delete_snippet` · kanban: `get_kanban_board`, `list_kanban_cards`,
`create_kanban_card`, `update_kanban_card`, `move_kanban_card`,
`toggle_kanban_checklist_item`, `delete_kanban_card`, `list_kanban_swimlanes`,
`create_kanban_swimlane`, `rename_kanban_swimlane`, `delete_kanban_swimlane`.

Een fout van de API komt terug als leesbare melding (bv. `API-fout 404 ...: Taak niet
gevonden`). Beperking: een deadline of kaartkleur wissen kan alleen via de API zelf
(`"deadline": null`), niet via de tools.
