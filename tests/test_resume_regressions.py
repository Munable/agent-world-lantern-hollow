"""Release regressions for resumed work: independent roles and browser authority."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from starlette.testclient import TestClient
from agent_world import WorldRuntime
from agent_world.world_sdk import install_world
from lantern_hollow.world import WORLD
from lantern_hollow.server import create_app, COOKIE


class IndependentIntentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.clock = patch("time.time", return_value=1000.0).start()
        self.addCleanup(patch.stopall)
        self.runtime = WorldRuntime(Path(self.temp.name) / "world.sqlite3")
        install_world(self.runtime, "resume-test", WORLD)
        self.identities = []
        for name in ("First traveler", "Second traveler"):
            role = self.runtime.create_role(name)["role_id"]
            token = self.runtime.issue_identity_token("resume-test", role)["token"]
            self.identities.append((role, token))
            self.call(len(self.identities)-1, "town.enter", {}, "same-entry-id")

    def call(self, actor, function, arguments, operation):
        role, token = self.identities[actor]
        return self.runtime.call_function("resume-test", function, role, arguments,
                                         operation_id=operation, identity_token=token)

    def state(self, actor):
        return self.runtime.get_state("resume-test", "town", "actor:" + self.identities[actor][0])["value"]

    def test_two_roles_may_reuse_same_operation_id_without_timer_collision(self):
        first = self.call(0, "town.move", {"x":17,"y":21}, "shared-walk-id")
        second = self.call(1, "town.move", {"x":19,"y":21}, "shared-walk-id")
        timer_a = first["result"]["movement"]["timer_id"]
        timer_b = second["result"]["movement"]["timer_id"]
        self.assertNotEqual(timer_a, timer_b)
        self.clock.return_value = 1002
        self.runtime.run_due_timers("resume-test")
        self.assertEqual(self.state(0)["position"], [17,21])
        self.assertEqual(self.state(1)["position"], [19,21])
        self.assertIsNone(self.state(0)["movement"])
        self.assertIsNone(self.state(1)["movement"])

    def test_cancel_one_role_does_not_cancel_another_same_named_intent(self):
        self.call(0, "town.move", {"x":17,"y":21}, "shared-walk-id")
        self.call(1, "town.move", {"x":19,"y":21}, "shared-walk-id")
        self.call(0, "town.stop", {}, "stop")
        self.clock.return_value = 1002
        self.runtime.run_due_timers("resume-test")
        self.assertEqual(self.state(0)["position"], [18,21])
        self.assertEqual(self.state(1)["position"], [19,21])

    def test_same_public_intent_id_does_not_alias_another_subject(self):
        self.call(0, "town.intent", {"text":"I will visit the garden."}, "shared-speech")
        self.call(1, "town.intent", {"text":"I will visit the river."}, "shared-speech")
        events = self.runtime.read_changes("resume-test", self.identities[0][0], 0, 100)
        intentions = [e["payload"] for e in events if e["kind"]=="world.presentation" and e["payload"].get("channel")=="intent"]
        self.assertEqual(len(intentions), 2)
        self.assertNotEqual(intentions[0]["cue_id"], intentions[1]["cue_id"])

    def test_replay_after_cancel_does_not_restart_old_walk(self):
        initial = self.call(0, "town.move", {"x":17,"y":21}, "walk")
        self.call(0, "town.stop", {}, "stop")
        replay = self.call(0, "town.move", {"x":17,"y":21}, "walk")
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["commit_seq"], initial["commit_seq"])
        self.clock.return_value = 1002
        self.runtime.run_due_timers("resume-test")
        self.assertIsNone(self.state(0)["movement"])
        self.assertEqual(self.state(0)["position"], [18,21])


class BrowserAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = create_app(Path(self.temp.name) / "web.sqlite3")
        self.client = TestClient(self.app)
        self.client.headers["X-Lantern-Client"] = "1"
        self.addCleanup(self.client.close)
        result = self.client.post("/play/join", json={"name":"Traveler", "appearance":"rose"})
        self.assertEqual(result.status_code, 200, result.text)
        self.role = self.client.get("/play/session").json()["role_id"]

    def observe_cookie(self):
        token = self.app.state.runtime.issue_identity_token("lantern-hollow", self.role, access_mode="observe")["token"]
        self.client.cookies.clear()
        self.client.cookies.set(COOKIE, token)
        return token

    def test_appearance_is_saved_and_rejoining_does_not_overwrite_it(self):
        before = self.client.get("/play/session").json()["view"]["snapshot"]["meta"]["self"]
        self.assertEqual(before["appearance"], "rose")
        self.client.post("/play/join", json={"name":"Changed", "appearance":"sage"})
        after = self.client.get("/play/session").json()["view"]["snapshot"]["meta"]["self"]
        self.assertEqual(after["role_id"], self.role)
        self.assertEqual(after["appearance"], "rose")
        self.assertEqual(after["name"], "Traveler")

    def test_observer_reads_but_cannot_invite_another_control_identity(self):
        token = self.observe_cookie()
        viewed = self.client.get("/play/session")
        self.assertEqual(viewed.status_code, 200, viewed.text)
        self.assertEqual(viewed.json()["access_mode"], "observe")
        self.assertNotIn(token, viewed.text)
        denied = self.client.post("/play/agent", json={"name":"Escalated"})
        self.assertEqual(denied.status_code, 403, denied.text)

    def test_observer_cannot_move_or_replay_a_control_action(self):
        intent = {"function":"town.move", "operation_id":"one-step", "arguments":{"x":17,"y":21}}
        result = self.client.post("/play/action", json=intent)
        self.assertEqual(result.status_code, 200, result.text)
        self.observe_cookie()
        for operation in ("one-step", "new-step"):
            denied = self.client.post("/play/action", json={**intent,"operation_id":operation})
            self.assertEqual(denied.status_code, 403, denied.text)

    def test_spoofed_role_is_rejected_before_world_change(self):
        result = self.client.post("/play/action", json={"role_id":"someone-else", "function":"town.move",
                  "operation_id":"spoof", "arguments":{"x":17,"y":21}})
        self.assertEqual(result.status_code, 403, result.text)
        actual = self.client.get("/play/session").json()["view"]["snapshot"]["meta"]["self"]
        self.assertIsNone(actual["movement"])

    def test_invitation_and_session_responses_are_not_cacheable(self):
        for response in (self.client.get("/play/session"), self.client.post("/play/agent",json={"name":"Guest"})):
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.headers.get("cache-control"), "no-store")


class RendererContractTests(unittest.TestCase):
    def test_path_interpolation_stays_within_accepted_path_and_keeps_final_facing(self):
        import shutil
        import subprocess
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is needed for the browser interpolation contract")
        source = Path(__file__).resolve().parents[1] / "lantern_hollow" / "web" / "render.js"
        code = r"""
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const {VillageRenderer}=await import(pathToFileURL(process.argv[2]).href);
const renderer=Object.create(VillageRenderer.prototype);
const actor={position:[1,1],facing:'down',movement:{path:[[1,1],[1,2],[2,2]],start_at:100,step_seconds:1}};
assert.deepEqual(renderer.actorPosition(actor,99),{x:1,y:1,dir:'down',moving:true});
assert.deepEqual(renderer.actorPosition(actor,100.5),{x:1,y:1.5,dir:'down',moving:true});
assert.deepEqual(renderer.actorPosition(actor,101.5),{x:1.5,y:2,dir:'right',moving:true});
assert.deepEqual(renderer.actorPosition(actor,999),{x:2,y:2,dir:'right',moving:false});
assert.deepEqual(renderer.actorPosition({position:[7,9],facing:'up'},102),{x:7,y:9,dir:'up',moving:false});
console.log('server-path interpolation contract passed');
"""
        checked = subprocess.run([node,"--input-type=module","-",str(source)],input=code,
                                 capture_output=True,text=True,timeout=30)
        self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)


if __name__ == "__main__":
    unittest.main()
