"""Explicit one-time import of this example's previously public broadcast cues, never generic private events."""
from __future__ import annotations
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from agent_world import WorldRuntime
from agent_world.presentation import validate_cue

MARKER='lantern-hollow:legacy-public-history:v1'

def import_public_history(runtime, source_db, universe='lantern-hollow'):
    source=Path(source_db).resolve()
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as c:
        c.row_factory=sqlite3.Row
        definition=c.execute('SELECT world_id,version FROM world_definitions WHERE universe=?',(universe,)).fetchone()
        if definition is None or definition['world_id']!='lantern-hollow' or definition['version']!=1:
            raise ValueError('only the known v1 Lantern Hollow public broadcast schema may be imported')
        rows=c.execute("SELECT seq,actor_role_id,payload_json,created_at FROM events WHERE universe=? AND kind='world.presentation' ORDER BY seq",(universe,)).fetchall()
    unique={}
    for row in rows:
        payload=json.loads(row['payload_json']);validate_cue(payload)
        # v1 Lantern Hollow broadcast intentionally copied each of these public cues to every entered role.
        key=json.dumps([row['actor_role_id'],row['created_at'],payload],sort_keys=True,ensure_ascii=False,separators=(',',':'))
        unique.setdefault(key,{'payload':payload,'actor':row['actor_role_id'],'at':row['created_at'],'first_seq':row['seq']})
    ordered=sorted(unique.items(),key=lambda item:(item[1]['at'],item[1]['first_seq']))
    imported={'village':0,'conversation':0}
    with runtime._lock,runtime._conn() as c:
        c.execute('BEGIN IMMEDIATE')
        marker=c.execute('SELECT meta_value FROM runtime_meta WHERE meta_key=?',(MARKER,)).fetchone()
        if marker:return {'already_imported':True,**json.loads(marker[0])}
        current=c.execute('SELECT world_id FROM world_definitions WHERE universe=?',(universe,)).fetchone()
        if current is None or current[0]!='lantern-hollow':raise ValueError('wrong destination world')
        if c.execute('SELECT 1 FROM stream_events WHERE universe=? LIMIT 1',(universe,)).fetchone():
            raise ValueError('import must happen during upgrade before new shared events are accepted')
        for key,item in ordered:
            cue=json.loads(json.dumps(item['payload']))
            data=cue['data']
            digest=hashlib.sha256((universe+'|'+key).encode()).hexdigest()
            streams=['village']+(['conversation'] if cue['channel'] in ('speech','intent') else [])
            if cue['name']=='public_expression':
                mid='awe_'+hashlib.sha256(('conversation:'+digest).encode()).hexdigest()
                data.update(message_id=mid,thread_id=mid,reply_to=None,to_role_id=None)
            data['import_source']='legacy_public_broadcast'
            for stream in streams:
                eid='awe_'+hashlib.sha256((stream+':'+digest).encode()).hexdigest()
                c.execute('INSERT INTO stream_heads(universe,stream) VALUES(?,?) ON CONFLICT DO NOTHING',(universe,stream))
                c.execute('UPDATE stream_heads SET head=head+1 WHERE universe=? AND stream=?',(universe,stream))
                seq=c.execute('SELECT head FROM stream_heads WHERE universe=? AND stream=?',(universe,stream)).fetchone()[0]
                c.execute('INSERT INTO stream_events(universe,stream,seq,event_id,actor_role_id,kind,payload_json,created_at) VALUES(?,?,?,?,?,?,?,?)',
                          (universe,stream,seq,eid,item['actor'],'world.presentation',json.dumps(cue,ensure_ascii=False),item['at']))
                imported[stream]+=1
        c.execute('INSERT INTO runtime_meta(meta_key,meta_value) VALUES(?,?)',(MARKER,json.dumps(imported)))
    return {'already_imported':False,**imported}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True);parser.add_argument('--db',required=True)
    args=parser.parse_args()
    print(json.dumps(import_public_history(WorldRuntime(args.db),args.source)))

if __name__=='__main__':main()
