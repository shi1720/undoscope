"""Read/recover MCP surface with immutable host-bound identity.

This local stdio demo is intentionally not a multi-tenant authentication service.
Populate the database using the trusted administrative CLI, then bind one process
per authenticated recovery scope. There is no model-controlled inverse/target tool.
"""
import argparse
from mcp.server.fastmcp import FastMCP
from .store import Context, RecoveryStore
from .policies import visible

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database",required=True)
    p.add_argument("--tenant",required=True)
    p.add_argument("--principal",required=True)
    p.add_argument("--run",required=True)
    args=p.parse_args()
    context=Context(args.tenant,args.principal,args.run)
    mcp=FastMCP("UndoScope")
    @mcp.tool()
    def recover_effect(receipt_id: str) -> dict:
        """Request effect-scoped compensation. Conflicts and denials require review."""
        store=RecoveryStore(args.database)
        try: return store.compensate(context,receipt_id)
        finally: store.close()
    # No raw SQL, arbitrary writes, identity fields, policy selector, or ablation flags.
    mcp.run(transport="stdio")
if __name__=="__main__": main()
