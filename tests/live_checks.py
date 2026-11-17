"""Opt-in network/browser checks. Run from project root: python -m tests.live_checks is not required; use python tests/live_checks.py."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from src.portal import open_property
from src.downloads import download_zip

CASES=[
 ('PR-client',-23.266165,-53.290072,'PR-4107256-605F909883AA43049A3F13A649F9C99A'),
 ('AM-sample',-8.2652558333,-67.6735275,'AM-1300706-111C0E910ABA41318B276FFC8663B290'),
]

def run():
 results=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='chrome',headless=True)
  try:
   for name,lat,lon,expected in CASES:
    context=browser.new_context(locale='pt-BR')
    selected=[]
    try:
     code=open_property(context.new_page(),lat,lon,timeout=35,progress=lambda *a:None,on_selected=selected.append)
     assert code==expected,(code,expected)
     results.append({'case':name+' browser match','status':'PASS','car':code})
    except Exception as e:
     results.append({'case':name+' browser match','status':'FAIL','error':str(e)})
    finally: context.close()
    if selected:
     try:
      with tempfile.TemporaryDirectory() as folder:
       path=download_zip(selected[0].id_origin,Path(folder)/'property.zip')
       results.append({'case':name+' physical ZIP save','status':'PASS','bytes':path.stat().st_size})
     except Exception as e: results.append({'case':name+' physical ZIP save','status':'FAIL','error':str(e)})
    else: results.append({'case':name+' physical ZIP save','status':'NOT RUN','reason':'Property not verified'})
    print(json.dumps(results[-2:]),flush=True)
  finally: browser.close()
 return results

if __name__=='__main__':
 results=run()
 if len(sys.argv)>1: Path(sys.argv[1]).write_text(json.dumps(results,indent=2),encoding='utf-8')
 sys.exit(any(r['status']=='FAIL' for r in results))
