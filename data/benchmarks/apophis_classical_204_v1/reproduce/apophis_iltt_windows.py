import subprocess,sys,concurrent.futures
dates=['2028-01-01T00:00:00','2028-08-01T00:00:00','2028-09-01T00:00:00','2029-06-01T00:00:00','2029-07-01T00:00:00','2029-11-01T00:00:00']
def run(job):
 try:subprocess.run([sys.executable,'runs/apophis_iltt_diagnose.py',*job],timeout=105,check=True)
 except Exception as exc:print(job,str(exc),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,[(d,v) for d in dates for v in ['bounded','extended']]))
