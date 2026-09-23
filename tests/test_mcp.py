import asyncio
from pathlib import Path
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from undoscope import Context, RecoveryStore
from undoscope.bench import CTX


def test_real_mcp_transport(tmp_path):
    path=tmp_path/"mcp.db"
    s=RecoveryStore(path);s.seed(CTX)
    rid=s.forward(CTX,"grant",{"member":"contractor"})
    s.peer(CTX,{"op":"grant","member":"contractor"},eid="peer-grant")
    s.close()
    async def run():
        params=StdioServerParameters(command=sys.executable,args=["-m","undoscope.mcp_server","--database",str(path),
            "--tenant","acme","--principal","agent","--run","run-1"])
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as client:
                await client.initialize()
                listing=await client.list_tools()
                assert [t.name for t in listing.tools]==["recover_effect"]
                assert set(listing.tools[0].inputSchema["properties"])=={"receipt_id"}
                result=await client.call_tool("recover_effect",{"receipt_id":rid})
                assert not result.isError
                assert "compensated" in str(result.content)
                repeat=await client.call_tool("recover_effect",{"receipt_id":rid})
                assert "already_compensated" in str(repeat.content)
    asyncio.run(run())
    s=RecoveryStore(path)
    assert s.inspect(CTX)["grants"]=={"peer-grant":"contractor"}
    s.close()
