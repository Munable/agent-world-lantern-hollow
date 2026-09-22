from __future__ import annotations
import asyncio
import unittest
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from tests.live import LiveServer


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_external_agent_and_browser_share_village(self):
        with LiveServer() as server:
            with httpx.Client(trust_env=False,timeout=10) as browser:
                browser.headers['X-Lantern-Client']='1'
                joined=browser.post(server.url+'/play/join',json={'name':'Human player'})
                self.assertEqual(joined.status_code,200,joined.text)
                player=browser.get(server.url+'/play/session').json()['role_id']
                invite=browser.post(server.url+'/play/agent',json={'name':'External agent'}).json()
                token_response=browser.post(server.url+'/v1/join/exchange',json={'ticket':invite['ticket']})
                self.assertEqual(token_response.status_code,200,token_response.text)
                identity=token_response.json()['identity']
                async with httpx.AsyncClient(trust_env=False,timeout=10,
                        headers={'Authorization':'Bearer '+identity['token']}) as http:
                    async with streamable_http_client(server.url+'/mcp',http_client=http) as (read,write):
                        async with ClientSession(read,write) as session:
                            await session.initialize()
                            listed=await session.list_tools()
                            names={tool.name for tool in listed.tools}
                            self.assertIn('town.enter',names)
                            self.assertIn('town.interact',names)
                            self.assertNotIn('walk_end',names)
                            enter=await session.call_tool('town.enter',arguments={'operation_id':'agent-entry','arguments':{}})
                            self.assertFalse(enter.is_error,enter.structured_content)
                            speech=await session.call_tool('town.say',arguments={'operation_id':'agent-hello',
                                'arguments':{'text':'Hello from an independent MCP client.'}})
                            self.assertFalse(speech.is_error,speech.structured_content)
                            replay=await session.call_tool('town.say',arguments={'operation_id':'agent-hello',
                                'arguments':{'text':'Hello from an independent MCP client.'}})
                            self.assertTrue(replay.structured_content['replayed'])
                            scene=browser.get(server.url+'/play/session').json()['view']['snapshot']
                            self.assertIn(identity['role_id'],scene['entities'])
                            self.assertIn(player,scene['entities'])
                            self.assertEqual(scene['entities'][identity['role_id']]['expression']['text'],
                                             'Hello from an independent MCP client.')
                            walk=await session.call_tool('town.move',arguments={'operation_id':'agent-walk',
                                'arguments':{'x':17,'y':21}})
                            self.assertFalse(walk.is_error,walk.structured_content)
                # Disconnect the Agent entirely; the server completes accepted movement.
                await asyncio.sleep(1.1)
                observed=browser.get(server.url+'/play/session').json()['view']['snapshot']
                self.assertEqual(observed['entities'][identity['role_id']]['position'],[17,21])
                self.assertIsNone(observed['entities'][identity['role_id']]['movement'])
                self.assertEqual(observed['entities'][player]['position'],[18,21])


if __name__=='__main__':unittest.main()
