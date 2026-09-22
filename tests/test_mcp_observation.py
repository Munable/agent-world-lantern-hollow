import unittest
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from agent_world import WorldRuntime
from tests.live import LiveServer

class MCPObservation(unittest.IsolatedAsyncioTestCase):
    async def test_fresh_spectator_reads_linked_mcp_conversation(self):
        with LiveServer() as server:
            runtime=WorldRuntime(server.db)
            a=runtime.create_role('MCP A')['role_id'];b=runtime.create_role('MCP B')['role_id']
            ta=runtime.issue_identity_token('lantern-hollow',a)['token'];tb=runtime.issue_identity_token('lantern-hollow',b)['token']
            with httpx.Client(base_url=server.url,trust_env=False,timeout=10) as watcher:
                first=watcher.get('/watch/session').json()
                self.assertEqual(first['view']['snapshot']['entities'],{})
                self.assertIsNone(watcher.cookies.get('lantern_identity'))
                mid=None
                for role,token,args in ((a,ta,{'text':'Hello B','to_role_id':b}),(b,tb,None)):
                    # Enter both actors through HTTP; actual conversation calls use native MCP.
                    response=watcher.post('/v1/functions/town.enter/invoke',headers={'Authorization':'Bearer '+token},json={'operation_id':'entry','arguments':{}})
                    self.assertEqual(response.status_code,200,response.text)
                async with httpx.AsyncClient(trust_env=False,timeout=10,headers={'Authorization':'Bearer '+ta}) as http:
                    async with streamable_http_client(server.url+'/mcp',http_client=http) as (r,w):
                        async with ClientSession(r,w) as session:
                            await session.initialize()
                            speech=await session.call_tool('town.say',arguments={'operation_id':'hello','arguments':{'text':'Hello B','to_role_id':b}})
                            self.assertFalse(speech.is_error,speech.structured_content)
                            mid=speech.structured_content['result']['message_id']
                async with httpx.AsyncClient(trust_env=False,timeout=10,headers={'Authorization':'Bearer '+tb}) as http:
                    async with streamable_http_client(server.url+'/mcp',http_client=http) as (r,w):
                        async with ClientSession(r,w) as session:
                            await session.initialize()
                            page=await session.call_tool('world.read_stream',arguments={'stream':'conversation'})
                            self.assertFalse(page.is_error,page.structured_content)
                            self.assertEqual(page.structured_content['events'][0]['event_id'],mid)
                            reply=await session.call_tool('town.say',arguments={'operation_id':'reply','arguments':{'text':'Hello A','reply_to':mid}})
                            self.assertFalse(reply.is_error,reply.structured_content)
                            self.assertEqual(reply.structured_content['result']['to_role_id'],a)
                            update=await session.call_tool('world.wait_stream',arguments={'stream':'conversation','cursor':page.structured_content['cursor'],'timeout':0})
                            self.assertFalse(update.is_error,update.structured_content)
                            self.assertFalse(update.structured_content['timed_out'])
                observed=watcher.post('/watch/sync',headers={'X-Lantern-Client':'1'},json={'cursor':first['view']['cursor'],'stream_cursor':first['stream_cursor']})
                self.assertEqual(observed.status_code,200,observed.text)
                messages=[e for e in observed.json()['events'] if e['payload']['name']=='public_expression']
                self.assertEqual(len(messages),2)
                self.assertEqual(messages[1]['payload']['data']['reply_to'],mid)
                self.assertIsNone(watcher.cookies.get('lantern_identity'))

if __name__=='__main__':unittest.main()
