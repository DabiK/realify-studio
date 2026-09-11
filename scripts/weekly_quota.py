"""Read only quota metadata from recent local Codex session events."""
import json
import os
from pathlib import Path


def snapshot():
    root = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex-mega'))) / 'sessions'
    found = []
    files = sorted(root.glob('*/*/*/*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)[:12]
    for path in files:
        with path.open() as source:
            for line in source:
                if 'rate_limits' not in line:
                    continue
                try:
                    event = json.loads(line)
                    rate = event.get('payload', {}).get('rate_limits') or {}
                    if rate.get('limit_id') != 'codex':
                        continue
                    for name in ['primary', 'secondary']:
                        window = rate.get(name) or {}
                        if window.get('window_minutes') == 10080:
                            found.append({'observed_at': event['timestamp'], 'remaining_percent': 100-window['used_percent'], 'resets_at': window['resets_at']})
                except (ValueError, KeyError, TypeError):
                    continue
    return max(found, key=lambda x: x['observed_at']) if found else None




def live_snapshot():
    """Read quota through Codex app-server; never start a model turn or spend credits."""
    import selectors
    import subprocess
    import time
    from datetime import datetime, timezone
    process = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, env={k:v for k,v in os.environ.items() if k not in ['OPENAI_API_KEY','CODEX_API_KEY']})
    def send(value):
        process.stdin.write((json.dumps(value)+'\n').encode()); process.stdin.flush()
    selector=selectors.DefaultSelector(); selector.register(process.stdout,selectors.EVENT_READ)
    send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'studio_quota','version':'0.1.0'},'capabilities':{}}})
    deadline=time.monotonic()+20; buffer=b''
    try:
        while time.monotonic()<deadline:
            if not selector.select(1):continue
            chunk=os.read(process.stdout.fileno(),65536)
            if not chunk:break
            buffer+=chunk
            while b'\n' in buffer:
                line,buffer=buffer.split(b'\n',1)
                if not line:continue
                response=json.loads(line)
                if response.get('id')==1:
                    if 'error' in response:return None
                    send({'method':'initialized'});send({'id':2,'method':'account/rateLimits/read','params':None})
                elif response.get('id')==2:
                    result=response.get('result',{})
                    rate=(result.get('rateLimitsByLimitId') or {}).get('codex') or result.get('rateLimits',{})
                    if rate.get('limitId')!='codex':return None
                    for name in ['primary','secondary']:
                        window=rate.get(name) or {}
                        if window.get('windowDurationMins')==10080:
                            return {'observed_at':datetime.now(timezone.utc).isoformat(),'remaining_percent':100-window['usedPercent'],'resets_at':window['resetsAt'],'source':'live_app_server'}
                    return None
    finally:
        selector.close();process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait()
    return None

if __name__ == '__main__':
    import sys
    print(json.dumps(live_snapshot() if '--live' in sys.argv else snapshot()))
