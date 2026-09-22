from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from agent_world import WorldRuntime, PresentationCue
from agent_world.world_sdk import install_world
from lantern_hollow.world import WORLD
from lantern_hollow.legacy_history import import_public_history

class LegacyHistory(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/'v1.sqlite3';self.w=WorldRuntime(Path(self.tmp.name)/'current.sqlite3')
        install_world(self.w,'lantern-hollow',WORLD)
        with closing(sqlite3.connect(self.source)) as c:
            c.execute('CREATE TABLE world_definitions(universe TEXT,world_id TEXT,version INTEGER)')
            c.execute("INSERT INTO world_definitions VALUES('lantern-hollow','lantern-hollow',1)")
            c.execute('CREATE TABLE events(seq INTEGER,universe TEXT,actor_role_id TEXT,kind TEXT,payload_json TEXT,created_at REAL)')
            cue=PresentationCue('old-cue','old-actor','speech','start','public_expression',{'text':'A past public message','subject':'old-actor','channel':'speech'}).event('old-recipient')
            for i in range(3):c.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(i+1,'lantern-hollow','old-actor','world.presentation',json.dumps(cue.payload),100.0))
            c.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(4,'lantern-hollow','old-actor','private.kind',json.dumps({'text':'NEVER_IMPORT_PRIVATE'}),100.0))
            c.commit()
    def test_public_fanout_deduplicated_with_original_time_and_no_fake_action(self):
        result=import_public_history(self.w,self.source)
        self.assertEqual(result['village'],1);self.assertEqual(result['conversation'],1)
        page=self.w.read_stream('lantern-hollow','conversation')
        self.assertEqual(page['events'][0]['occurred_at'],100.0)
        self.assertNotIn('NEVER_IMPORT_PRIVATE',str(page))
        with self.w._conn(readonly=True) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM operations').fetchone()[0],0)
    def test_import_is_idempotent(self):
        import_public_history(self.w,self.source)
        self.assertTrue(import_public_history(self.w,self.source)['already_imported'])
        self.assertEqual(len(self.w.read_stream('lantern-hollow','village')['events']),1)
    def test_wrong_source_world_is_rejected(self):
        with closing(sqlite3.connect(self.source)) as c:
            c.execute("UPDATE world_definitions SET world_id='private-world'");c.commit()
        with self.assertRaises(ValueError):import_public_history(self.w,self.source)

if __name__=='__main__':unittest.main()
