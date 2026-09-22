"""Lantern Hollow rules. All state changes use the external agent-world SDK."""
from __future__ import annotations

import hashlib
from agent_world import (WorldDefinition, FunctionSpec, FunctionOutcome, StateRule,
                         TimerSpec, ViewSpec, PresentationCue, RetentionPolicy, StreamSpec)
from agent_world.errors import RuleViolation
from .map import SPAWN, TARGETS, route, position, direction, WIDTH, HEIGHT

EMPTY={"type":"object","properties":{},"additionalProperties":False}
ID={"type":"string","minLength":1,"maxLength":128}
STEP_SECONDS=0.16
SHARDS=["shard_moss","shard_sky","shard_water"]


def schema(properties,required=()):
    return {"type":"object","properties":properties,"required":list(required),"additionalProperties":False}


def key(role): return "actor:"+role


def load(ctx,role=None):
    role=role or ctx.actor_role_id
    value=ctx.get_state("town",key(role))
    if value is None: raise RuleViolation("Enter the village first / 请先进入小镇")
    return value


def save(ctx,actor):
    actor['last_action']={'function':ctx.function_id,'at':ctx.now}
    ctx.set_state("town",key(actor["role_id"]),actor)


def short_id(ctx,suffix):
    return suffix+":"+hashlib.sha256((ctx.universe+"\0"+ctx.actor_role_id+"\0"+(ctx.operation_id or "initialize")).encode()).hexdigest()[:24]


def broadcast(ctx,subject,channel,phase,name,data=None,cue_id=None,event_key=None):
    cue=PresentationCue(cue_id or short_id(ctx,name),subject,channel,phase,name,data or {})
    stable_key=event_key or hashlib.sha256((cue.cue_id+channel+phase+name).encode()).hexdigest()
    # A single retained publication serves present and future observers. Legacy role inboxes remain compatible.
    events=tuple(cue.event(row["value"]["role_id"]) for row in ctx.list_state("town",prefix="actor:",limit=32)["items"])
    events+=(cue.publish('village',key=stable_key),)
    if channel in ('speech','intent'):
        events+=(cue.publish('conversation',key=stable_key),)
    return events


def say_line(ctx,actor,subject,text,en,portrait="keeper"):
    line={"subject":subject,"text":text,"en":en,"portrait":portrait,"at":ctx.now,"expires_at":ctx.now+8}
    actor["dialogue"]=line
    ctx.set_state("town","public:dialogue",line)
    return broadcast(ctx,subject,"speech","start","dialogue",line)


def initialize(ctx):
    ctx.set_state("town","beacon",{"lit":False,"lit_at":None,"contributors":0})
    ctx.set_state("town","notes",[])


def enter(ctx,args):
    existing=ctx.get_state("town",key(ctx.actor_role_id))
    if existing is not None: return FunctionOutcome({"entered":True,"role_id":ctx.actor_role_id})
    if len(ctx.list_state("town",prefix="actor:",limit=32)["items"])>=32:
        raise RuleViolation("This reference village is limited to 32 saved travelers")
    profile=ctx.get_role()
    actor={"role_id":ctx.actor_role_id,"name":profile["display_name"],"appearance":args.get("appearance","traveler"),
           "position":list(SPAWN),"facing":"up","movement":None,"busy":None,"quest":"arrival",
           "shards":[],"dialogue":None,"expression":None,"completed_at":None,"joined_at":ctx.now}
    save(ctx,actor)
    return FunctionOutcome({"entered":True,"role_id":ctx.actor_role_id},broadcast(ctx,ctx.actor_role_id,"action","finish","arrive",{"position":list(SPAWN)}))


def interrupt(ctx,actor):
    events=()
    if actor["movement"]:
        motion=actor["movement"]
        actor["position"],actor["facing"]=position(actor,ctx.now)
        ctx.cancel_timer(motion["timer_id"])
        actor["movement"]=None
        events+=broadcast(ctx,actor["role_id"],"action","cancel","walk",{"position":actor["position"]},motion["id"])
    if actor["busy"]:
        busy=actor["busy"]
        ctx.cancel_timer(busy["timer_id"])
        actor["busy"]=None
        events+=broadcast(ctx,actor["role_id"],"action","cancel","repair",{},busy["id"])
    return events


def begin_walk(ctx,actor,destination,on_arrival=None):
    events=interrupt(ctx,actor)
    path=route(actor["position"],destination)
    if path is None: raise RuleViolation("That place is not reachable / 那里暂时无法到达")
    if len(path)==1:
        if on_arrival: events+=resolve_interaction(ctx,actor,on_arrival)
        save(ctx,actor)
        return FunctionOutcome({"walking":False,"position":actor["position"]},events)
    aid=short_id(ctx,"walk"); tid=aid+":end"
    actor["facing"]=direction(path[0],path[1])
    movement={"id":aid,"timer_id":tid,"path":path,"start_at":ctx.now,
              "end_at":ctx.now+(len(path)-1)*STEP_SECONDS,"step_seconds":STEP_SECONDS,"on_arrival":on_arrival}
    actor["movement"]=movement; actor["dialogue"]=None
    save(ctx,actor)
    ctx.schedule_timer(tid,"walk_end",{"role_id":actor["role_id"],"action_id":aid},due_at=movement["end_at"])
    events+=broadcast(ctx,actor["role_id"],"action","start","walk",movement,aid)
    return FunctionOutcome({"walking":True,"movement":movement},events)


def move(ctx,args): return begin_walk(ctx,load(ctx),[args["x"],args["y"]])


def stop(ctx,args):
    actor=load(ctx); events=interrupt(ctx,actor); save(ctx,actor)
    return FunctionOutcome({"stopped":True,"position":actor["position"]},events)


def interact(ctx,args):
    target=TARGETS[args["target"]]
    return begin_walk(ctx,load(ctx),target["approach"],target["id"])


def walk_end(ctx,args):
    actor=load(ctx,args["role_id"]); motion=actor["movement"]
    if motion is None or motion["id"]!=args["action_id"]: return FunctionOutcome({"stale":True})
    actor["position"]=motion["path"][-1]
    actor["facing"]=direction(motion["path"][-2],motion["path"][-1])
    actor["movement"]=None
    events=broadcast(ctx,actor["role_id"],"action","finish","walk",{"position":actor["position"]},motion["id"])
    if motion["on_arrival"]: events+=resolve_interaction(ctx,actor,motion["on_arrival"])
    save(ctx,actor)
    return FunctionOutcome({"position":actor["position"]},events)


def resolve_interaction(ctx,actor,target_id):
    target=TARGETS[target_id]
    if abs(actor["position"][0]-target["x"])+abs(actor["position"][1]-target["y"])>2:
        raise RuleViolation("Move closer before interacting")
    actor["facing"]=direction(actor["position"],[target["x"],target["y"]])
    events=()
    if target_id=="elia":
        if actor["quest"]=="arrival":
            actor["quest"]="collect"
            events=say_line(ctx,actor,"elia","风把灯芯吹散了。找到三枚星片，让归航的光再次亮起来吧。","The wind scattered the wick. Find three star shards, and bring our homeward light back.")
        elif actor["quest"]=="complete":
            events=say_line(ctx,actor,"elia","你看，河里也有星星了。谢谢你，让每个晚归的人都有方向。","Look, even the river has stars now. Thank you for giving every late traveler a way home.")
        elif len(actor["shards"])==3:
            events=say_line(ctx,actor,"elia","三枚都在！灯塔在桥那头，把星片嵌入灯座就好。","All three! Cross the bridge and set the shards into the beacon.")
        else:
            events=say_line(ctx,actor,"elia","苔间、风里、溪畔。慢慢找，我会等你。","Among moss, in the wind, beside the stream. Take your time; I'll be here.")
    elif target_id=="rowan":
        events=say_line(ctx,actor,"rowan","灯坏了可以修，错过的黄昏可不行。找齐星片，剩下的交给你的双手。","A broken light can be repaired. A missed sunset cannot. Find the shards; your hands will do the rest.","smith")
    elif target_id=="fern":
        events=say_line(ctx,actor,"fern","花圃旁有一点金光。不是萤火虫，萤火虫可不会躲在苔藓里。","There's a golden glimmer by the garden. Not a firefly; fireflies don't hide in moss.","gardener")
    elif target_id in SHARDS:
        if actor["quest"]=="arrival":
            events=say_line(ctx,actor,actor["role_id"],"一枚温热的星片。先问问守灯人，它属于哪里。","A warm star shard. I should ask the lightkeeper where it belongs.","traveler")
        elif target_id in actor["shards"]:
            events=say_line(ctx,actor,actor["role_id"],"这枚星片已经收好了。","I've already gathered this shard.","traveler")
        else:
            actor["shards"].append(target_id)
            if len(actor["shards"])==3: actor["quest"]="repair"
            events=broadcast(ctx,actor["role_id"],"action","finish","collect",{"target":target_id,"count":len(actor["shards"])})
            events+=say_line(ctx,actor,actor["role_id"],f"收好一枚星片。{len(actor['shards'])} / 3",f"One star shard safely gathered. {len(actor['shards'])} / 3","traveler")
    elif target_id=="beacon":
        if actor["quest"]=="complete":
            events=say_line(ctx,actor,actor["role_id"],"归航灯已经亮了。这道光里，也有我的一小部分。","The beacon is shining. A little part of this light is mine.","traveler")
        elif len(actor["shards"])<3:
            events=say_line(ctx,actor,actor["role_id"],"灯座还缺少星片。需要三枚，才能让光稳定下来。","The cradle is missing its star shards. All three will steady the light.","traveler")
        else:
            aid=short_id(ctx,"repair"); tid=aid+":end"
            actor["busy"]={"id":aid,"timer_id":tid,"kind":"repair","start_at":ctx.now,"end_at":ctx.now+2.4}
            ctx.schedule_timer(tid,"repair_end",{"role_id":actor["role_id"],"action_id":aid},due_at=ctx.now+2.4)
            events=broadcast(ctx,actor["role_id"],"action","start","repair",actor["busy"],aid)
    elif target_id=="board":
        events=say_line(ctx,actor,actor["role_id"],"有人来过，也有人会再来。在留言板上留句话吧。","Someone was here, and someone will come again. Leave a note on the board.","traveler")
    elif target_id=="bench":
        events=say_line(ctx,actor,actor["role_id"],"歇一会儿。水还在流，世界也还在。","A moment to rest. The water keeps moving. So does the world.","traveler")
    return events


def repair_end(ctx,args):
    actor=load(ctx,args["role_id"]); busy=actor["busy"]
    if busy is None or busy["id"]!=args["action_id"]: return FunctionOutcome({"stale":True})
    actor["busy"]=None; actor["quest"]="complete"; actor["completed_at"]=ctx.now
    beacon=ctx.get_state("town","beacon"); beacon["lit"]=True; beacon["lit_at"]=beacon["lit_at"] or ctx.now; beacon["contributors"]+=1
    ctx.set_state("town","beacon",beacon)
    events=broadcast(ctx,actor["role_id"],"action","finish","repair",{"beacon":beacon},busy["id"])
    events+=say_line(ctx,actor,"elia","亮了！愿这束光，照见每一个回家的方向。","It's alight! May it guide every traveler home.")
    save(ctx,actor)
    return FunctionOutcome({"complete":True},events)


def expression(ctx,args,channel="speech"):
    actor=load(ctx)
    text=args["text"].strip()
    if not text: raise RuleViolation("A public expression cannot be empty")
    if actor.get("expression") and ctx.now-actor["expression"]["at"]<1:
        raise RuleViolation("Please leave a moment between public expressions")
    target=args.get('to_role_id')
    reply=args.get('reply_to')
    message_id=ctx.stream_event_id('conversation','expression')
    thread_id=message_id
    if reply:
        previous=ctx.get_stream_event('conversation',reply)
        if previous is None or previous['kind']!='world.presentation' or previous['payload']['name']!='public_expression':
            raise RuleViolation('Reply target is not a retained public message')
        parent=previous['payload']['data']
        if parent.get('channel')!='speech':
            raise RuleViolation('Reply to a spoken message, not a private inference or intention')
        if target and target!=parent['subject']:
            raise RuleViolation('Reply recipient does not match the referenced author')
        target=parent['subject']
        thread_id=parent.get('thread_id',reply)
    if target:
        load(ctx,target)  # Only real entered travelers are conversation targets.
    line={"subject":actor['role_id'],"text":text,"en":text,"at":ctx.now,"expires_at":ctx.now+8,
          "channel":channel,"message_id":message_id,"thread_id":thread_id,
          "reply_to":reply,"to_role_id":target}
    actor['expression']=line; save(ctx,actor)
    return FunctionOutcome({'public':True,'message_id':message_id,'thread_id':thread_id,'reply_to':reply,'to_role_id':target},
                           broadcast(ctx,actor['role_id'],channel,'start','public_expression',line,event_key='expression'))


def messages(ctx,args):
    load(ctx)
    recent=[e for e in ctx.recent_stream_events('conversation',100)
            if e['payload'].get('name')=='public_expression' and e['payload'].get('channel')=='speech']
    limit=args.get('limit',20)
    return FunctionOutcome({'messages':[{'event_id':e['event_id'],**e['payload']['data']} for e in recent[-limit:]],
                            'stream':'conversation','delivery':'returned_not_proof_of_understanding'})


def approach(ctx,args):
    actor=load(ctx); target=load(ctx,args['role_id'])
    if target['role_id']==actor['role_id']: raise RuleViolation('Already at your own position')
    location,_=position(target,ctx.now)
    candidates=[]
    for dx,dy in ((0,1),(1,0),(-1,0),(0,-1)):
        dest=[location[0]+dx,location[1]+dy]
        if not (0<=dest[0]<WIDTH and 0<=dest[1]<HEIGHT):continue
        path=route(position(actor,ctx.now)[0],dest)
        if path:candidates.append((len(path),dest))
    if not candidates:raise RuleViolation('No reachable position beside this traveler')
    return begin_walk(ctx,actor,min(candidates)[1])


def note(ctx,args):
    actor=load(ctx)
    if actor["movement"] or actor["busy"]: raise RuleViolation("Stop before writing a note")
    if sum(abs(a-b) for a,b in zip(actor["position"],TARGETS["board"]["approach"]))>1:
        raise RuleViolation("Visit the board before leaving a note / 请走到留言板旁")
    text=args["text"].strip()
    if not text: raise RuleViolation("A note cannot be empty")
    notes=ctx.get_state("town","notes",[])
    if any(n["author_id"]==actor["role_id"] and ctx.now-n["at"]<10 for n in notes): raise RuleViolation("Please wait before leaving another note")
    notes.append({"id":short_id(ctx,"note"),"author_id":actor["role_id"],"name":actor["name"],"text":text,"at":ctx.now})
    ctx.set_state("town","notes",notes[-30:])
    save(ctx,actor)
    return FunctionOutcome({"saved":True},broadcast(ctx,actor["role_id"],"action","finish","note",{"text":text}))


def scene(ctx,args):
    me=ctx.get_state("town",key(ctx.actor_role_id)) if ctx.actor_role_id is not None else None
    entities={}
    for row in ctx.list_state("town",prefix="actor:",limit=32)["items"]:
        a=row["value"]
        entities[a["role_id"]]={k:a[k] for k in ("role_id","name","appearance","position","facing","movement","busy","expression")}
        entities[a["role_id"]]["kind"]="traveler"
        entities[a["role_id"]]['last_action']=a.get('last_action',{'function':'unknown','at':a['joined_at']})
    return {"entities":entities,"meta":{"self":me,"beacon":ctx.get_state("town","beacon"),
            "notes":ctx.get_state("town","notes",[]),"dialogue":ctx.get_state("town","public:dialogue"),
            "world_name":"Lantern Hollow", "observation":"server_facts_not_model_presence"}}


def look(ctx,args): return FunctionOutcome(scene(ctx,args))


def migrate_observation(ctx):
    for row in ctx.list_state('town',prefix='actor:',limit=32)['items']:
        actor=row['value']
        if 'last_action' not in actor:
            times=[actor.get('joined_at',0),actor.get('completed_at') or 0]
            for field in ('dialogue','expression'):
                if actor.get(field):times.append(actor[field].get('at',0))
            actor['last_action']={'function':'legacy.record','at':max(times),'source':'last_retained_public_record'}
            ctx.set_state('town',key(actor['role_id']),actor)


TIMER_ARGS=schema({"role_id":ID,"action_id":ID},["role_id","action_id"])
TEXT_ARGS=schema({"text":{"type":"string","minLength":1,"maxLength":160}},["text"])
SPEECH_ARGS=schema({"text":{"type":"string","minLength":1,"maxLength":160},
                    "to_role_id":ID,"reply_to":ID},["text"])

WORLD=WorldDefinition(
    "lantern-hollow","Lantern Hollow",
    functions=(
        FunctionSpec("town.enter",enter,schema({"appearance":{"enum":["traveler","sage","rose"]}}),description="Enter Lantern Hollow as your authenticated role. Safe to call again."),
        FunctionSpec("town.look",look,EMPTY,access="read",description="Read the village, visible travelers, your quest and public notes."),
        FunctionSpec("town.move",move,schema({"x":{"type":"integer","minimum":0,"maximum":WIDTH-1},"y":{"type":"integer","minimum":0,"maximum":HEIGHT-1}},["x","y"]),description="Walk to a reachable tile. The server finds a collision-safe path. Replaces the current action."),
        FunctionSpec("town.stop",stop,EMPTY,description="Cancel movement or repair at the current server-determined position."),
        FunctionSpec("town.interact",interact,schema({"target":{"enum":list(TARGETS)}},["target"]),description="Walk to an NPC, shard, beacon, bench or board and interact on arrival. Speak to elia, collect three shards, repair beacon."),
        FunctionSpec("town.say",expression,SPEECH_ARGS,version=2,description="Publish a public message. Optional to_role_id addresses a traveler; reply_to references a retained message_id and links a real reply. Never private reasoning."),
        FunctionSpec("town.messages",messages,schema({"limit":{"type":"integer","minimum":1,"maximum":50}}),access="read",description="Read retained public traveler messages and reply links. For bounded waiting use world.read_stream / world.wait_stream on conversation."),
        FunctionSpec("town.approach",approach,schema({"role_id":ID},["role_id"]),description="Walk beside another entered traveler, using their current position. Does not claim they are online or force them to speak."),
        FunctionSpec("town.intent",lambda c,a:expression(c,a,"intent"),TEXT_ARGS,description="Publish a short intended action. Never a claim to expose private reasoning."),
        FunctionSpec("town.note",note,TEXT_ARGS,description="Leave a durable public note while standing beside the board."),
    ),
    state_rules=(StateRule("town","actor:",{"type":"object"},history="metadata"),
                 StateRule("town","beacon",{"type":"object"}),StateRule("town","notes",{"type":"array","maxItems":30}),
                 StateRule("town","public:",{"type":"object"},history="metadata")),
    timers=(TimerSpec("walk_end",walk_end,TIMER_ARGS),TimerSpec("repair_end",repair_end,TIMER_ARGS)),
    version=2, state_version=2, migrations={2:migrate_observation},
    streams=(StreamSpec('village',public=True,retention_seconds=86400,max_events=4096),
             StreamSpec('conversation',public=True,retention_seconds=86400,max_events=2048)),
    views=(ViewSpec("village",scene,version=2,description="The village and your private quest, for a pixel-art renderer.",renderer="lantern-hollow",streams=('village',)),
           ViewSpec("spectator",scene,description="Public world view, no traveler identity or private quest.",renderer="lantern-hollow",public=True,streams=('village',))),
    initialize=initialize,bootstrap=lambda ctx:scene(ctx,{}),
    retention=RetentionPolicy(event_seconds=3600,event_rows=4096,history_seconds=604800,history_rows=20000),
    entry_instructions="Call town.enter then town.look. You choose how to participate; the beacon quest is optional. Read town.messages or world.read_stream(stream=conversation) to discover what real travelers said. A new town.say may address to_role_id or reply_to an actual message_id. Use world.wait_stream with its live cursor for bounded waiting; no automatic wake after your host stops. town.approach can walk near a real traveler, without making them respond. NPCs elia, rowan, fern are scripted. Wait for accepted movements instead of repeatedly replacing them. Use stable operation_id only for retries. Public intentions are voluntary expressions, never private model reasoning. Follow the operator's time/action budget and report whether you stopped or are awaiting another instruction.",
)
