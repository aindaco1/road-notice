#!/usr/bin/env python3
"""Read-only service/contract check, with one reusable GitHub incident on failure."""
import argparse, json, os, pathlib, subprocess, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
TITLE = 'Reporting service health'
def gh(*args):
    return subprocess.check_output(['gh', *args], text=True).strip()
def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--maintain-issue', action='store_true'); args = parser.parse_args()
    problems = []
    try:
        request = urllib.request.Request('https://crash.dustwave.xyz/v1/fine-me-not/health', headers={'User-Agent':'FineMeNot-maintenance'})
        with urllib.request.urlopen(request, timeout=20) as response:
            health = json.loads(response.read(4096))
        if health.get('ok') is not True or health.get('service') != 'fine-me-not-reports': problems.append('Service configuration check failed.')
    except Exception: problems.append('Service endpoint could not be reached or returned an invalid response.')
    try:
        for local, remote in [('report-contract.json', 'fine-me-not-v1.json'), ('report-fixture.json', 'fine-me-not-fixture.json')]:
            request = urllib.request.Request('https://raw.githubusercontent.com/aindaco1/ascii-vj-remix/main/crash-relay/contract/' + remote)
            with urllib.request.urlopen(request, timeout=20) as response: current = json.loads(response.read(65536))
            if current != json.loads((ROOT/'Sources/SupportCore/Resources'/local).read_text()): problems.append('The app and relay contracts differ.')
    except Exception: problems.append('Contract comparison is unavailable.')
    body = '\n'.join(sorted(set(problems))) if problems else 'The reporting endpoint and published contracts are healthy again.'
    print(body)
    if args.maintain_issue:
        repo = 'aindaco1/road-notice'
        issues = json.loads(gh('issue','list','--repo',repo,'--state','all','--search',TITLE+' in:title','--json','number,title,state','--limit','30'))
        issue = next((i for i in issues if i['title'] == TITLE), None)
        if problems and not issue:
            gh('issue','create','--repo',repo,'--title',TITLE,'--body',body)
        elif problems and issue and issue['state'] == 'CLOSED':
            gh('issue','reopen',str(issue['number']),'--repo',repo)
            gh('issue','edit',str(issue['number']),'--repo',repo,'--body',body)
        elif not problems and issue and issue['state'] == 'OPEN':
            gh('issue','close',str(issue['number']),'--repo',repo)
    raise SystemExit(1 if problems else 0)
if __name__ == '__main__': main()
