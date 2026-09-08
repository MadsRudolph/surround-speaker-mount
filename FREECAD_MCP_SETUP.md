# FreeCAD MCP connection

Detection on 2026-09-08: **no FreeCAD MCP tools are exposed to this agent**, and no FreeCAD server entry appears in this machine's Codex configuration. FreeCAD 1.1.3, Blender 5.2.0 and `/usr/bin/uvx` are installed. Blender MCP tools are exposed. The deliverables were generated using local CAD runtimes; no FreeCAD MCP connection was needed or installed.

Use the [neka-nat FreeCAD MCP bridge](https://github.com/neka-nat/freecad-mcp). It comprises a FreeCAD GUI addon (RPC endpoint) and a separate Python MCP process. `/usr/bin/FreeCAD` itself does **not** speak MCP over stdio.

1. Install its addon for this Arch Linux / FreeCAD 1.1 environment:

```bash
git clone https://github.com/neka-nat/freecad-mcp.git ~/Projects/freecad-mcp
mkdir -p ~/.local/share/FreeCAD/v1-1/Mod
cp -r ~/Projects/freecad-mcp/addon/FreeCADMCP ~/.local/share/FreeCAD/v1-1/Mod/
```

2. Launch `/usr/bin/FreeCAD`, choose the **MCP Addon** workbench, then **Start RPC Server** in its toolbar. Leave FreeCAD running. Keep the bridge local; remote access is unnecessary.

3. Add this to an MCP client supporting `mcpServers` JSON, merging with existing entries:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "/usr/bin/uvx",
      "args": ["freecad-mcp", "--only-text-feedback"]
    }
  }
}
```

For this Codex installation, the equivalent entry in `~/.codex/config.toml` is:

```toml
[mcp_servers.freecad]
command = "/usr/bin/uvx"
args = ["freecad-mcp", "--only-text-feedback"]
```

4. Restart the agent/client. Confirm FreeCAD tools appear, then ask it to create a temporary document and execute:

```python
import FreeCAD as App
import Part
doc = App.newDocument('MCP_Connection_Test')
obj = doc.addObject('PartDesign::Body', 'TestBody')
feature = obj.newObject('PartDesign::Feature', 'TestCube')
feature.Shape = Part.makeBox(10, 10, 10)
doc.recompute()
print(feature.Shape.Volume)  # Expected 1000 mm^3
```

Confirm the returned value and visible cube. If tools appear but RPC calls fail, check the addon and running GUI; if tools are absent, check client config and restart. Close the temporary document afterward. This setup guide was verified against upstream instructions; installation and connection testing were not performed here.
