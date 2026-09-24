"""Frozen-candidate frontend gate: repeatable tests plus optional real-time endurance.
Results distinguish engineering gates from externally unverified physical devices.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,os,re,subprocess,sys,time,traceback
ROOT=Path(__file__).resolve().parents[1]


def source_hashes():
    files=[]
    for directory in ('lantern_hollow','examples/protocol-client','tools','tests'):
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'node_modules' not in p.parts and p.suffix in ('.py','.js','.mjs','.css','.html','.json','.png','.zip','.txt'))
    files.extend([ROOT/'pyproject.toml',ROOT/'.github/workflows/tests.yml'])
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def run(command,output,label,timeout=600):
    started=time.time();log=output/(label+'.log')
    env=os.environ.copy();env['PYTHONUTF8']='1';env['FRONTEND_BROWSER']='chromium'
    # Do not let a stale test path resolve a different repository's tests package.
    env['PYTHONPATH']=str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
    with log.open('w',encoding='utf-8') as stream:
        try:result=subprocess.run(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout);code=result.returncode
        except subprocess.TimeoutExpired:code=124
    # Browser tooling may include ephemeral fixture credentials in failure logs.
    raw=log.read_text(encoding='utf-8',errors='replace');log.write_text(re.sub(r'awid_[A-Za-z0-9_-]+','[REDACTED_FIXTURE_CREDENTIAL]',raw),encoding='utf-8')
    item={'label':label,'command':['python' if v==sys.executable else v for v in command],'exit_code':code,'started_at':started,'elapsed_seconds':time.time()-started,'log':str(log.relative_to(ROOT))}
    print(json.dumps(item),flush=True)
    (output/(label+'.json')).write_text(json.dumps(item,indent=2),encoding='utf-8')
    if code:raise RuntimeError(label+' failed: '+log.read_text(encoding='utf-8')[-5000:])
    return item


def round_tests(output,number,axe,browsers):
    prefix='pass'+str(number);commands=[('unit',[sys.executable,'-m','unittest','discover','-s','tests','-q']),('camera',['node','tests/camera.test.mjs']),('nameplate',['node','tests/nameplate.test.mjs']),('frontend-contract',['node','tests/frontend_contract.test.mjs']),('public-contract',['node','tests/public_protocol.test.mjs'])]
    for tool in ('browser_check','check_edges','check_observation','check_onboarding','check_semantic_presentation','check_camera','check_sample_assets'):
        commands.append((tool,[sys.executable,'tools/'+tool+'.py']))
    folder=str(output.relative_to(ROOT))+'/'+prefix
    commands.extend([('experience',[sys.executable,'tools/check_frontend_experience.py','--soak-seconds','90']),('faults',[sys.executable,'tools/check_frontend_faults.py','--output',folder+'/faults']),('visual',[sys.executable,'tools/check_visual_matrix.py','--output',folder+'/visual']),('browser-matrix',[sys.executable,'tools/check_browser_matrix.py','--browsers',browsers,'--axe',str(axe),'--output',folder+'/browsers']),('accessibility',[sys.executable,'tools/check_accessibility_gate.py','--axe',str(axe),'--output',folder+'/accessibility']),('wheel',[sys.executable,'-m','pip','wheel','--no-deps','--wheel-dir',str(output/'wheels'),'.'])])
    results=[]
    for name,command in commands:
        print('RUN',prefix,name,flush=True);results.append(run(command,output,prefix+'-'+name,timeout=1200))
    return results


def endurance(output):
    # Quiet and active 30-minute phases run in sequence alongside a separate
    # 60-minute dual-client run. Each owns a different temporary database/server.
    def phase(mode,seconds):
        dest=str(output.relative_to(ROOT))+'/endurance-'+mode
        return run([sys.executable,'tools/check_frontend_endurance.py','--mode',mode,'--seconds',str(seconds),'--output',dest],output,'endurance-'+mode,seconds+240)
    def quiet_active():return [phase('quiet',1800),phase('active',1800)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(quiet_active);b=pool.submit(phase,'dual',3600)
        return a.result()+[b.result()]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--axe',required=True);p.add_argument('--browsers',default='chromium,edge,firefox,webkit');p.add_argument('--endurance',action='store_true');args=p.parse_args()
    output=(ROOT/args.output).resolve();output.relative_to(ROOT);output.mkdir(parents=True,exist_ok=True)
    if (output/'summary.json').exists():p.error('Use a new result directory; preserve earlier evidence')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();before=source_hashes()
    report={'source_commit':commit,'started_at':time.time(),'status':'running','rounds':[],'source_hashes':before,'physical_devices':'external-unverified','endurance_scheduling':'Distinct temporary worlds on the same host; quiet30 then active30 alongside dual60. No clock acceleration. Not a server throughput benchmark.'}
    def save():(output/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    save()
    try:
        report['rounds'].append(round_tests(output,1,Path(args.axe),args.browsers));assert before==source_hashes(),'Candidate changed in pass1';save()
        if args.endurance:report['endurance']=endurance(output);assert before==source_hashes(),'Candidate changed during endurance';save()
        report['rounds'].append(round_tests(output,2,Path(args.axe),args.browsers));assert before==source_hashes(),'Candidate changed in pass2'
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==commit,'Commit changed during gate'
        report.update(status='passed',finished_at=time.time(),source_unchanged=True);save()
    except Exception as exc:report.update(status='failed',error=str(exc),traceback=traceback.format_exc(),finished_at=time.time(),source_unchanged=before==source_hashes());save();raise
    print(json.dumps({k:v for k,v in report.items() if k not in ('rounds','source_hashes','endurance')}),flush=True)

if __name__=='__main__':main()
