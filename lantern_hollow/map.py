"""Original reference-world geography. Rendering and collision share this definition."""
from __future__ import annotations

from collections import deque
import math

WIDTH, HEIGHT, TILE = 40, 26, 16
SPAWN = (18, 21)
BUILDINGS = [
    {"id": "inn", "x": 5, "y": 5, "w": 7, "h": 5, "kind": "inn"},
    {"id": "workshop", "x": 4, "y": 15, "w": 6, "h": 4, "kind": "workshop"},
    {"id": "tower", "x": 32, "y": 5, "w": 4, "h": 5, "kind": "tower"},
]
TREES = [(2,5),(3,11),(13,6),(16,3),(22,4),(26,7),(1,16),(12,16),(14,22),
         (25,22),(27,18),(37,13),(36,20),(7,23),(32,23),(1,22),(37,4)]
TARGETS = {
    "elia": {"id":"elia", "kind":"npc", "name":"艾莉娅", "en":"Elia", "x":28,"y":10, "approach":[27,10], "portrait":"keeper"},
    "rowan": {"id":"rowan", "kind":"npc", "name":"罗温", "en":"Rowan", "x":11,"y":18, "approach":[11,19], "portrait":"smith"},
    "fern": {"id":"fern", "kind":"npc", "name":"芙恩", "en":"Fern", "x":13,"y":10, "approach":[13,11], "portrait":"gardener"},
    "shard_moss": {"id":"shard_moss", "kind":"shard", "name":"苔间星片", "en":"Moss shard", "x":6,"y":21,"approach":[7,21]},
    "shard_sky": {"id":"shard_sky", "kind":"shard", "name":"风中星片", "en":"Sky shard", "x":22,"y":6,"approach":[22,7]},
    "shard_water": {"id":"shard_water", "kind":"shard", "name":"溪畔星片", "en":"River shard", "x":33,"y":17,"approach":[32,17]},
    "beacon": {"id":"beacon", "kind":"beacon", "name":"归航灯塔", "en":"The homeward beacon", "x":34,"y":10,"approach":[34,11]},
    "board": {"id":"board", "kind":"board", "name":"旅人留言板", "en":"Traveler's board", "x":19,"y":13,"approach":[19,14]},
    "bench": {"id":"bench", "kind":"bench", "name":"溪边长椅", "en":"Riverside bench", "x":24,"y":17,"approach":[24,18]},
}


def terrain(x:int,y:int)->str:
    if x < 1 or x >= WIDTH-1 or y < 2 or y >= HEIGHT-1:
        return "cliff"
    # A narrow northern stream widens as it leaves the village. Two real bridges.
    center = 29 if y < 16 else 28 if y < 21 else 27
    if center <= x <= center+1:
        return "bridge" if y in (11,12,20) else "water"
    if y in (11,12) and 8 <= x <= 36 or 17 <= x <= 19 and 10 <= y <= 23:
        return "path"
    if y in (19,20) and 6 <= x <= 34 or x in (10,11) and 10 <= y <= 20:
        return "path"
    if (x-19)**2+(y-11)**2 <= 14:
        return "stone"
    return "grass"


def walkable(x:int,y:int)->bool:
    if not 0<=x<WIDTH or not 0<=y<HEIGHT or terrain(x,y) in {"cliff","water"}:
        return False
    for b in BUILDINGS:
        if b["x"]<=x<b["x"]+b["w"] and b["y"]<=y<b["y"]+b["h"]:
            return False
    if (x,y) in TREES:
        return False
    if any(t["x"]==x and t["y"]==y for t in TARGETS.values()):
        return False
    # Tree and fountain at the plaza are rendered with matching collision.
    if (x,y) in {(17,7),(18,7),(20,11),(21,11),(20,12),(21,12)}:
        return False
    return True


def route(start,goal):
    start,goal=tuple(start),tuple(goal)
    if not walkable(*goal):
        return None
    queue=deque([start]); parents={start:None}
    while queue:
        p=queue.popleft()
        if p==goal:
            result=[]
            while p is not None:
                result.append(list(p)); p=parents[p]
            return result[::-1]
        for dx,dy in ((0,1),(1,0),(0,-1),(-1,0)):
            nxt=(p[0]+dx,p[1]+dy)
            if nxt not in parents and walkable(*nxt):
                parents[nxt]=p; queue.append(nxt)
    return None


def direction(a,b,default="down"):
    dx,dy=b[0]-a[0],b[1]-a[1]
    return "right" if dx>0 else "left" if dx<0 else "down" if dy>0 else "up" if dy<0 else default


def position(actor,now):
    move=actor.get("movement")
    if not move:
        return list(actor["position"]),actor.get("facing","down")
    steps=max(0,math.floor((now-move["start_at"])/move["step_seconds"]))
    steps=min(steps,len(move["path"])-1)
    facing=direction(move["path"][max(0,steps-1)],move["path"][steps],actor.get("facing","down"))
    return list(move["path"][steps]),facing


def manifest():
    return {"width":WIDTH,"height":HEIGHT,"tile":TILE,"spawn":list(SPAWN),
            "tiles":[[terrain(x,y) for x in range(WIDTH)] for y in range(HEIGHT)],
            "blocked":[[x,y] for y in range(HEIGHT) for x in range(WIDTH) if not walkable(x,y)],
            "buildings":BUILDINGS,"trees":[list(p) for p in TREES],"targets":list(TARGETS.values())}
