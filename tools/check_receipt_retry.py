"""A manual retry must consume the original receipt, not create a duplicate Action."""
from pathlib import Path
import argparse, json, sys, os
from playwright.sync_api import sync_playwright, expect

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--output',required=True)
    args=parser.parse_args();root=Path(args.root);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root));os.environ['PYTHONPATH']=str(root)+os.pathsep+os.environ.get('PYTHONPATH','')
    from tests.live import LiveServer
    report={'status':'running','case':'action_and_all_receipts_lost_then_user_retries'}
    with LiveServer() as server, sync_playwright() as p:
        browser=p.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1280,'height':900})
        posted=[];errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:posted.append(r.post_data_json['operation_id']) if r.url.endswith('/play/action') else None)
        try:
            page.goto(server.url,wait_until='domcontentloaded');expect(page.locator('#join-mode')).to_be_enabled()
            page.click('#join-mode');page.fill('#name','Receipt retry probe');page.click('#join')
            expect(page.locator('#say')).to_be_enabled();page.click('#say')
            page.fill('#modal textarea','One action, even after a manual retry.')
            def lose_action(route):
                response=route.fetch();assert response.status==200;route.abort()
            page.route('**/play/action',lose_action,times=1)
            page.route('**/play/receipt/**',lambda route:route.abort(),times=4)
            submit=page.locator('#modal form button[type=submit]');submit.click()
            expect(submit).to_be_enabled(timeout=15000)
            pending=page.evaluate("sessionStorage.getItem('lh.pending')")
            assert pending is not None,'The ambiguous action must remain recoverable'
            assert len(posted)==1,posted
            page.unroute('**/play/receipt/**')
            submit.click();expect(page.locator('#modal')).not_to_be_visible(timeout=15000)
            expect(page.locator('#timeline')).to_contain_text('One action, even after a manual retry.')
            assert page.evaluate("sessionStorage.getItem('lh.pending')") is None
            report.update(post_count=len(posted),distinct_operations=len(set(posted)),page_errors=errors)
            assert len(posted)==1,report
            assert not errors,errors
            report['status']='passed'
        except Exception as error:
            report.update(status='failed',error=str(error),post_count=len(posted),distinct_operations=len(set(posted)),page_errors=errors)
            page.screenshot(path=str(out/'failure.png'),full_page=True)
        finally:
            browser.close()
            (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    if report['status']!='passed':raise SystemExit(1)
if __name__=='__main__':main()
